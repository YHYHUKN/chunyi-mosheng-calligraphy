"""
训练流程 - AI书法风格解耦模型训练
"""
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import os
import time
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.style_encoder import StyleEncoder, ContentEncoder
from models.generator import DualBranchGenerator, Discriminator
from models.losses import CalligraphyLoss


class CalligraphyTrainer:
    """
    书法创作模型训练器
    
    训练策略：
    1. 阶段一：仅训练编码器+判别器，学习风格特征提取
    2. 阶段二：联合训练生成器+判别器，学习风格解耦生成
    3. 阶段三：全模型微调，精细调整生成质量
    """
    
    def __init__(self, config):
        self.config = config
        self.device = torch.device(config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu'))
        
        # 超参数
        self.lr_g = config.get('lr_g', 1e-4)
        self.lr_d = config.get('lr_d', 4e-4)
        self.batch_size = config.get('batch_size', 8)
        self.num_epochs = config.get('num_epochs', 200)
        self.style_dim = config.get('style_dim', 128)
        self.content_dim = config.get('content_dim', 256)
        self.num_styles = config.get('num_styles', 12)
        self.image_size = config.get('image_size', 256)
        
        # 初始化模型
        self._init_models()
        
        # 损失函数
        self.loss_fn = CalligraphyLoss()
        
        # 优化器
        self.opt_g = torch.optim.Adam(self.generator.parameters(), lr=self.lr_g, betas=(0.5, 0.999))
        self.opt_d = torch.optim.Adam(self.discriminator.parameters(), lr=self.lr_d, betas=(0.5, 0.999))
        self.opt_style = torch.optim.Adam(self.style_encoder.parameters(), lr=self.lr_g, betas=(0.5, 0.999))
        self.opt_content = torch.optim.Adam(self.content_encoder.parameters(), lr=self.lr_g, betas=(0.5, 0.999))
        
        # 学习率调度器
        self.scheduler_g = torch.optim.lr_scheduler.CosineAnnealingLR(self.opt_g, T_max=self.num_epochs)
        self.scheduler_d = torch.optim.lr_scheduler.CosineAnnealingLR(self.opt_d, T_max=self.num_epochs)
        
        # 训练状态
        self.current_epoch = 0
        self.best_fid = float('inf')
        
        print(f"[INFO] 使用设备: {self.device}")
    
    def _init_models(self):
        """初始化所有模型"""
        self.style_encoder = StyleEncoder(style_dim=self.style_dim).to(self.device)
        self.content_encoder = ContentEncoder(content_dim=self.content_dim).to(self.device)
        self.generator = DualBranchGenerator(
            content_dim=self.content_dim,
            style_dim=self.style_dim
        ).to(self.device)
        self.discriminator = Discriminator(num_styles=self.num_styles).to(self.device)
        
        # 权重初始化
        self._init_weights(self.style_encoder)
        self._init_weights(self.content_encoder)
        self._init_weights(self.generator)
        self._init_weights(self.discriminator)
        
        # 打印参数量
        total_params = sum(p.numel() for p in self.generator.parameters())
        print(f"[INFO] 生成器参数量: {total_params / 1e6:.2f}M")
    
    def _init_weights(self, model):
        """权重初始化 - Xavier均匀分布"""
        for m in model.modules():
            if isinstance(m, (nn.Conv2d, nn.ConvTranspose2d, nn.Linear)):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, (nn.InstanceNorm2d, nn.BatchNorm2d)):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)
    
    def train_epoch(self, dataloader):
        """训练一个epoch"""
        self.style_encoder.train()
        self.content_encoder.train()
        self.generator.train()
        self.discriminator.train()
        
        total_loss_g = 0
        total_loss_d = 0
        num_batches = 0
        
        for batch in dataloader:
            images = batch['image'].to(self.device)
            skeletons = batch['skeleton'].to(self.device)
            style_labels = batch['style_label'].to(self.device)
            
            B = images.size(0)
            
            # ======= 判别器训练 =======
            self.opt_d.zero_grad()
            
            # 真实图片
            d_real_adv, d_real_style = self.discriminator(images)
            
            # 生成图片
            with torch.no_grad():
                style_vec = self.style_encoder(images)
                content_feat = self.content_encoder(skeletons)
                fake_images = self.generator(content_feat, style_vec)
            
            d_fake_adv, d_fake_style = self.discriminator(fake_images.detach())
            
            loss_d, d_metrics = self.loss_fn.compute_discriminator_loss(
                d_real_adv, d_fake_adv,
                style_labels, d_fake_style
            )
            
            # 风格分类损失（判别器对真实图片的风格分类）
            loss_d_style_cls = nn.CrossEntropyLoss()(d_real_style, style_labels)
            loss_d = loss_d + loss_d_style_cls
            
            loss_d.backward()
            self.opt_d.step()
            
            # ======= 生成器训练 =======
            self.opt_g.zero_grad()
            self.opt_style.zero_grad()
            self.opt_content.zero_grad()
            
            # 重新生成
            style_vec = self.style_encoder(images)
            content_feat = self.content_encoder(skeletons)
            fake_images = self.generator(content_feat, style_vec)
            
            d_fake_adv, d_fake_style = self.discriminator(fake_images)
            
            loss_g, g_metrics = self.loss_fn.compute_generator_loss(
                fake_images, images, images,
                d_fake_adv, d_fake_style,
                style_labels
            )
            
            loss_g.backward()
            
            # 梯度裁剪 - 防止梯度爆炸
            torch.nn.utils.clip_grad_norm_(self.generator.parameters(), max_norm=1.0)
            torch.nn.utils.clip_grad_norm_(self.style_encoder.parameters(), max_norm=1.0)
            
            self.opt_g.step()
            self.opt_style.step()
            self.opt_content.step()
            
            total_loss_g += g_metrics['adv'] + g_metrics['perc'] + g_metrics['style']
            total_loss_d += d_metrics['d_adv']
            num_batches += 1
        
        avg_loss_g = total_loss_g / max(num_batches, 1)
        avg_loss_d = total_loss_d / max(num_batches, 1)
        
        return avg_loss_g, avg_loss_d
    
    def generate_samples(self, text, style_name, dataloader=None):
        """
        推理生成 - 给定文本和风格，生成书法作品
        
        Args:
            text: 要生成的文本
            style_name: 风格名称（需在style_library中注册）
        Returns:
            生成的图片列表
        """
        self.generator.eval()
        self.style_encoder.eval()
        self.content_encoder.eval()
        
        generated_chars = []
        
        with torch.no_grad():
            for char in text:
                # 1. 获取字形骨架（从数据集或生成）
                # 这里用占位骨架（实际应从骨架缓存获取）
                skeleton = self._get_char_skeleton(char)
                
                # 2. 获取目标风格向量
                style_vec = self._get_style_vector(style_name)
                
                # 3. 编码 + 生成
                content_feat = self.content_encoder(skeleton)
                generated = self.generator(content_feat, style_vec)
                
                # 4. 后处理
                img = self._postprocess(generated)
                generated_chars.append(img)
        
        return generated_chars
    
    def _get_char_skeleton(self, char: str) -> torch.Tensor:
        """获取字符骨架（占位实现）"""
        # 实际应从预计算的骨架缓存中读取
        skeleton = torch.zeros(1, 1, 256, 256, device=self.device)
        return skeleton
    
    def _get_style_vector(self, style_name: str) -> torch.Tensor:
        """获取目标风格向量"""
        # 实际应从风格库中读取
        style_vec = torch.randn(1, self.style_dim, device=self.device)
        style_vec = torch.nn.functional.normalize(style_vec, dim=1)
        return style_vec
    
    def _postprocess(self, generated: torch.Tensor) -> object:
        """后处理生成结果"""
        # [-1, 1] → [0, 255]
        img = generated.squeeze().cpu().numpy()
        img = ((img + 1) * 127.5).clip(0, 255).astype('uint8')
        return img
    
    def save_checkpoint(self, epoch, save_dir='checkpoints'):
        """保存检查点"""
        Path(save_dir).mkdir(parents=True, exist_ok=True)
        
        checkpoint = {
            'epoch': epoch,
            'style_encoder': self.style_encoder.state_dict(),
            'content_encoder': self.content_encoder.state_dict(),
            'generator': self.generator.state_dict(),
            'discriminator': self.discriminator.state_dict(),
            'opt_g': self.opt_g.state_dict(),
            'opt_d': self.opt_d.state_dict(),
        }
        
        path = os.path.join(save_dir, f'checkpoint_epoch_{epoch:03d}.pth')
        torch.save(checkpoint, path)
        print(f"[INFO] 保存检查点: {path}")
    
    def load_checkpoint(self, checkpoint_path):
        """加载检查点"""
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.style_encoder.load_state_dict(checkpoint['style_encoder'])
        self.content_encoder.load_state_dict(checkpoint['content_encoder'])
        self.generator.load_state_dict(checkpoint['generator'])
        self.discriminator.load_state_dict(checkpoint['discriminator'])
        self.current_epoch = checkpoint.get('epoch', 0)
        print(f"[INFO] 加载检查点: {checkpoint_path}, epoch={self.current_epoch}")


def main():
    """主训练流程"""
    config = {
        'device': 'cuda' if torch.cuda.is_available() else 'cpu',
        'batch_size': 8,
        'num_epochs': 200,
        'lr_g': 1e-4,
        'lr_d': 4e-4,
        'style_dim': 128,
        'content_dim': 256,
        'num_styles': 12,
        'image_size': 256,
    }
    
    print("=" * 60)
    print("  春意墨生 - AI书法创作系统 模型训练")
    print("=" * 60)
    
    trainer = CalligraphyTrainer(config)
    
    # 训练循环
    for epoch in range(trainer.current_epoch, config['num_epochs']):
        epoch_start = time.time()
        
        loss_g, loss_d = trainer.train_epoch(None)  # 需要传入实际dataloader
        
        epoch_time = time.time() - epoch_start
        
        print(f"Epoch [{epoch+1:03d}/{config['num_epochs']}] "
              f"Loss_G: {loss_g:.4f}  Loss_D: {loss_d:.4f}  "
              f"Time: {epoch_time:.1f}s")
        
        # 更新学习率
        trainer.scheduler_g.step()
        trainer.scheduler_d.step()
        
        # 定期保存
        if (epoch + 1) % 20 == 0:
            trainer.save_checkpoint(epoch + 1)
    
    # 保存最终模型
    trainer.save_checkpoint(config['num_epochs'], 'checkpoints/final')
    
    print("\n[INFO] 训练完成！")


if __name__ == '__main__':
    main()

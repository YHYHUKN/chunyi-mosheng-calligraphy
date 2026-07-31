"""
损失函数 - 针对书法生成优化的多维度损失
感知损失 + 风格损失 + 对抗损失 + 内容重建损失
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models


class VGGFeatureExtractor(nn.Module):
    """
    VGG特征提取器 - 用于计算感知损失和风格损失
    使用预训练VGG19提取多尺度纹理特征
    """
    
    def __init__(self):
        super().__init__()
        vgg = models.vgg19(weights=models.VGG19_Weights.IMAGENET1K_V1)
        # 加载归一化层
        self.register_buffer('mean', torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1))
        self.register_buffer('std', torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1))
        
        # 提取多层特征
        self.blocks = nn.ModuleList([
            vgg.features[:4],   # relu1_2 - 低层纹理
            vgg.features[4:9],  # relu2_2 - 中层结构
            vgg.features[9:18], # relu3_4 - 高层语义
        ])
        
        # 冻结参数
        for param in self.parameters():
            param.requires_grad = False
    
    def forward(self, x):
        """
        Args:
            x: (B, 1, H, W) 灰度图
        Returns:
            features: 多层特征列表
        """
        # 灰度转RGB
        if x.size(1) == 1:
            x = x.repeat(1, 3, 1, 1)
        
        # 确保在同一设备上
        device = x.device
        mean = self.mean.to(device)
        std = self.std.to(device)
        x = (x - mean) / std
        
        features = []
        for block in self.blocks:
            block = block.to(device)
            x = block(x)
            features.append(x)
        
        return features


class CalligraphyLoss(nn.Module):
    """
    书法创作综合损失函数
    
    L_total = λ1*L_adv + λ2*L_perc + λ3*L_style + λ4*L_content + λ5*L_style_cls
    
    - L_adv:    对抗损失 - 提升生成图片的真实感
    - L_perc:   感知损失 - 匹配笔画细节的纹理特征
    - L_style:  风格损失 - 匹配笔法墨法的统计特征
    - L_content:内容重建损失 - 保持字形结构准确
    - L_style_cls: 风格分类损失 - 确保风格一致性
    """
    
    def __init__(self,
                 lambda_adv=1.0,
                 lambda_perc=10.0,
                 lambda_style=5.0,
                 lambda_content=1.0,
                 lambda_style_cls=1.0):
        super().__init__()
        
        self.lambda_adv = lambda_adv
        self.lambda_perc = lambda_perc
        self.lambda_style = lambda_style
        self.lambda_content = lambda_content
        self.lambda_style_cls = lambda_style_cls
        
        # 感知/风格损失用的特征提取器
        self.vgg = VGGFeatureExtractor()
        
        # 对抗损失（BCE + 特征匹配）
        self.bce = nn.BCEWithLogitsLoss()
        
        # 内容损失
        self.content_loss = nn.L1Loss()
    
    def adversarial_loss(self, disc_real, disc_fake):
        """
        对抗损失：LSGAN（最小二乘GAN）
        更稳定的训练，避免梯度消失
        """
        loss_real = F.mse_loss(disc_real, torch.ones_like(disc_real))
        loss_fake = F.mse_loss(disc_fake, torch.zeros_like(disc_fake))
        return loss_real + loss_fake
    
    def adversarial_loss_generator(self, disc_fake):
        """生成器对抗损失"""
        return F.mse_loss(disc_fake, torch.ones_like(disc_fake))
    
    def perceptual_loss(self, generated, target):
        """
        感知损失：在VGG特征空间计算L1距离
        捕获笔画细节、墨色渐变等高层纹理特征
        """
        gen_feats = self.vgg(generated)
        tgt_feats = self.vgg(target)
        
        loss = 0
        for gf, tf in zip(gen_feats, tgt_feats):
            loss += F.l1_loss(gf, tf)
        
        return loss / len(gen_feats)
    
    def style_loss(self, generated, style_reference):
        """
        风格损失：Gram矩阵匹配
        捕获笔法粗细、墨色浓淡、飞白纹理等风格统计特征
        """
        gen_feats = self.vgg(generated)
        ref_feats = self.vgg(style_reference)
        
        loss = 0
        for gf, rf in zip(gen_feats, ref_feats):
            loss += F.mse_loss(self._gram_matrix(gf), self._gram_matrix(rf))
        
        return loss / len(gen_feats)
    
    def content_reconstruction_loss(self, generated, target):
        """
        内容重建损失：像素级L1 + 边缘检测一致性
        确保字形结构准确，笔画位置不偏移
        """
        # 像素级L1
        pixel_loss = self.content_loss(generated, target)
        
        # 边缘一致性损失（Sobel算子）
        edge_loss = self._edge_loss(generated, target)
        
        return pixel_loss + 0.5 * edge_loss
    
    def style_classification_loss(self, style_logits, target_style_idx):
        """
        风格分类损失：确保生成的作品被正确分类为目标风格
        """
        return F.cross_entropy(style_logits, target_style_idx)
    
    def _gram_matrix(self, x):
        """计算Gram矩阵 - 风格的统计表示"""
        B, C, H, W = x.size()
        features = x.view(B, C, H * W)
        gram = torch.bmm(features, features.transpose(1, 2))
        gram = gram / (C * H * W)
        return gram
    
    def _edge_loss(self, generated, target):
        """边缘一致性损失 - Sobel边缘检测"""
        # Sobel核
        sobel_x = torch.tensor([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]],
                               dtype=generated.dtype, device=generated.device)
        sobel_y = torch.tensor([[-1, -2, -1], [0, 0, 0], [1, 2, 1]],
                               dtype=generated.dtype, device=generated.device)
        
        sobel_x = sobel_x.view(1, 1, 3, 3)
        sobel_y = sobel_y.view(1, 1, 3, 3)
        
        def get_edges(img):
            if img.size(1) == 1:
                edge_x = F.conv2d(img, sobel_x, padding=1)
                edge_y = F.conv2d(img, sobel_y, padding=1)
            else:
                gray = img.mean(dim=1, keepdim=True)
                edge_x = F.conv2d(gray, sobel_x, padding=1)
                edge_y = F.conv2d(gray, sobel_y, padding=1)
            return torch.sqrt(edge_x ** 2 + edge_y ** 2 + 1e-6)
        
        return F.l1_loss(get_edges(generated), get_edges(target))
    
    def compute_generator_loss(self,
                               generated,
                               target,
                               style_reference,
                               disc_fake_adv,
                               disc_fake_style,
                               target_style_idx):
        """
        计算生成器总损失
        """
        # 对抗损失
        l_adv = self.adversarial_loss_generator(disc_fake_adv)
        
        # 感知损失
        l_perc = self.perceptual_loss(generated, target)
        
        # 风格损失
        l_style = self.style_loss(generated, style_reference)
        
        # 内容重建损失
        l_content = self.content_reconstruction_loss(generated, target)
        
        # 风格分类损失
        l_style_cls = self.style_classification_loss(disc_fake_style, target_style_idx)
        
        # 总损失
        total = (self.lambda_adv * l_adv +
                 self.lambda_perc * l_perc +
                 self.lambda_style * l_style +
                 self.lambda_content * l_content +
                 self.lambda_style_cls * l_style_cls)
        
        return total, {
            'adv': l_adv.item(),
            'perc': l_perc.item(),
            'style': l_style.item(),
            'content': l_content.item(),
            'style_cls': l_style_cls.item(),
        }
    
    def compute_discriminator_loss(self, disc_real_adv, disc_fake_adv,
                                   disc_real_style, disc_fake_style):
        """
        计算判别器总损失
        """
        # 真假判别损失
        l_adv = self.adversarial_loss(disc_real_adv, disc_fake_adv)
        
        # 风格分类损失
        l_style_cls = F.cross_entropy(disc_real_style, disc_fake_style) if disc_real_style is not None else torch.tensor(0.0)
        
        return l_adv, {
            'd_adv': l_adv.item(),
            'd_style_cls': l_style_cls.item() if torch.is_tensor(l_style_cls) else 0,
        }

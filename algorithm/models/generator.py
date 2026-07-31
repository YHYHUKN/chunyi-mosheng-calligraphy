"""
双分支生成器 + 风格解耦模块 - DualBranchGenerator
将内容特征与风格特征独立编码后可控融合，生成书法作品
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class AdaptiveInstanceNorm(nn.Module):
    """
    AdaIN - 自适应实例归一化
    核心风格注入机制：用风格向量调制特征图的统计量（均值+方差）
    """
    
    def __init__(self, num_features, style_dim):
        super().__init__()
        self.norm = nn.InstanceNorm2d(num_features, affine=False)
        self.fc = nn.Linear(style_dim, num_features * 2)
    
    def forward(self, x, style_vector):
        """
        Args:
            x: 内容特征图 (B, C, H, W)
            style_vector: 风格向量 (B, style_dim)
        """
        h = self.fc(style_vector)
        gamma, beta = h.chunk(2, dim=1)
        gamma = gamma.unsqueeze(2).unsqueeze(3)  # (B, C, 1, 1)
        beta = beta.unsqueeze(2).unsqueeze(3)
        
        x = self.norm(x)
        x = gamma * x + beta
        return x


class StyleModulatedConvBlock(nn.Module):
    """
    风格调制卷积块 - 上采样 + AdaIN + 卷积
    生成器的基本构建单元
    """
    
    def __init__(self, in_channels, out_channels, style_dim, upsample=True):
        super().__init__()
        self.upsample = upsample
        self.adain = AdaptiveInstanceNorm(in_channels, style_dim)
        self.conv = nn.Conv2d(in_channels, out_channels, 3, stride=1, padding=1)
        self.adain_out = AdaptiveInstanceNorm(out_channels, style_dim)
    
    def forward(self, x, style_vector):
        if self.upsample:
            x = F.interpolate(x, scale_factor=2, mode='nearest')
        x = self.adain(x, style_vector)
        x = F.leaky_relu(x, 0.2, inplace=True)
        x = self.conv(x)
        x = self.adain_out(x, style_vector)
        return x


class DualBranchGenerator(nn.Module):
    """
    双分支生成器 - 论文核心网络架构
    
    分支1（内容分支）：接收字形骨架特征，负责笔画结构与布局
    分支2（风格分支）：接收风格向量，通过AdaIN逐步注入笔法、墨法特征
    
    两分支在每个尺度上通过特征融合模块合并，最终输出书法图片
    """
    
    def __init__(self, content_dim=256, style_dim=128, output_channels=1, image_size=128):
        super().__init__()
        self.content_dim = content_dim
        self.style_dim = style_dim
        
        # ---- 内容分支：内容特征 → 逐层上采样 ----
        # 从 16x16 逐步上采样到 256x256
        self.content_up = nn.ModuleList([
            StyleModulatedConvBlock(content_dim, 512, style_dim, upsample=True),   # 16→32
            StyleModulatedConvBlock(512, 256, style_dim, upsample=True),           # 32→64
            StyleModulatedConvBlock(256, 128, style_dim, upsample=True),           # 64→128
            StyleModulatedConvBlock(128, 64, style_dim, upsample=True),            # 128→256
        ])
        
        # ---- 风格分支：风格向量 → 多尺度特征图 ----
        # 将风格向量扩展为不同尺度的风格特征
        # 起始尺寸动态计算，与ContentEncoder输出一致
        # image_size=128 -> spatial=8, image_size=64 -> spatial=4
        self._spatial_base = image_size // 16  # ContentEncoder下采样4次: /2^4
        self.style_fc = nn.Linear(style_dim, 64 * self._spatial_base * self._spatial_base)
        self.style_up = nn.ModuleList([
            nn.Sequential(
                nn.ConvTranspose2d(64, 512, 4, stride=2, padding=1),
                nn.InstanceNorm2d(512),
                nn.LeakyReLU(0.2, inplace=True),
            ),   # 8→16
            nn.Sequential(
                nn.ConvTranspose2d(512, 256, 4, stride=2, padding=1),
                nn.InstanceNorm2d(256),
                nn.LeakyReLU(0.2, inplace=True),
            ),   # 16→32
            nn.Sequential(
                nn.ConvTranspose2d(256, 128, 4, stride=2, padding=1),
                nn.InstanceNorm2d(128),
                nn.LeakyReLU(0.2, inplace=True),
            ),   # 32→64
            nn.Sequential(
                nn.ConvTranspose2d(128, 64, 4, stride=2, padding=1),
                nn.InstanceNorm2d(64),
                nn.LeakyReLU(0.2, inplace=True),
            ),   # 64→128
        ])
        
        # ---- 特征融合模块（每个尺度一个）----
        # content_up 输出通道：512, 256, 128, 64
        # style_up   输出通道：512, 256, 128, 64
        self.fusions = nn.ModuleList([
            FeatureFusionBlock(512, 512),
            FeatureFusionBlock(256, 256),
            FeatureFusionBlock(128, 128),
            FeatureFusionBlock(64,  64),
        ])
        
        # ---- 最终输出层 ----
        self.output_conv = nn.Sequential(
            nn.Conv2d(64, 32, 3, stride=1, padding=1),
            nn.InstanceNorm2d(32),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(32, output_channels, 3, stride=1, padding=1),
            nn.Tanh(),  # 输出范围 [-1, 1]
        )
    
    def forward(self, content_features, style_vector):
        """
        Args:
            content_features: 内容编码器输出的特征图 (B, content_dim, H', W')
            style_vector: 风格编码器输出的风格向量 (B, style_dim)
        Returns:
            generated_image: 生成的书法图片 (B, 1, 128, 128)
        """
        B = content_features.size(0)
        
        # 内容分支逐层上采样
        content_feats = []
        x = content_features
        for block in self.content_up:
            x = block(x, style_vector)
            content_feats.append(x)
        
        # 风格分支：向量→特征图→逐层上采样
        style_feat = self.style_fc(style_vector)
        style_feat = style_feat.view(B, 64, self._spatial_base, self._spatial_base)
        style_feats = []
        for up in self.style_up:
            style_feat = up(style_feat)
            style_feats.append(style_feat)
        
        # 两分支在每个尺度融合（修复后尺寸完全对齐）
        fused = None
        for i, (c_feat, s_feat) in enumerate(zip(content_feats, style_feats)):
            merged = self.fusions[i](c_feat, s_feat)
            fused = merged
        
        # 最终输出
        output = self.output_conv(fused)
        return output


class FeatureFusionBlock(nn.Module):
    """
    特征融合模块 - 门控机制融合内容特征与风格特征
    
    使用可学习的门控系数，让网络自动决定每个空间位置上
    内容特征和风格特征的混合比例
    """
    
    def __init__(self, content_ch, style_ch=None):
        """
        Args:
            content_ch: 内容分支通道数
            style_ch:   风格分支通道数，None则等于content_ch
        """
        super().__init__()
        if style_ch is None:
            style_ch = content_ch
        out_ch = content_ch
        self.gate = nn.Sequential(
            nn.Conv2d(content_ch + style_ch, out_ch, 1, stride=1),
            nn.Sigmoid(),
        )
        # 风格特征通道数对齐
        self.style_proj = nn.Conv2d(style_ch, content_ch, 1) if style_ch != content_ch else nn.Identity()
        self.conv = nn.Sequential(
            nn.Conv2d(out_ch, out_ch, 3, stride=1, padding=1),
            nn.InstanceNorm2d(out_ch),
            nn.LeakyReLU(0.2, inplace=True),
        )
    
    def forward(self, content_feat, style_feat):
        """
        Args:
            content_feat: 内容分支特征 (B, C_c, H, W)
            style_feat: 风格分支特征 (B, C_s, H, W)
        Returns:
            融合特征 (B, C_c, H, W)
        """
        # 拼接 → 门控系数
        concat = torch.cat([content_feat, style_feat], dim=1)
        gate = self.gate(concat)  # (B, C_c, H, W)
        
        # 风格分支对齐到内容通道数
        style_aligned = self.style_proj(style_feat)
        
        # 门控融合
        fused = gate * content_feat + (1 - gate) * style_aligned
        fused = self.conv(fused)
        
        return fused


class Discriminator(nn.Module):
    """
    双分支判别器 - 分别判别真实性和风格一致性
    
    分支1：真/假判别（判断生成图片是否逼真）
    分支2：风格分类（判断图片是否符合目标风格）
    """
    
    def __init__(self, num_styles=12, in_channels=1, base_channels=64):
        super().__init__()
        
        # 共享特征提取层
        self.shared = nn.Sequential(
            nn.Conv2d(in_channels, base_channels, 4, stride=2, padding=1),
            nn.LeakyReLU(0.2, inplace=True),
            
            nn.Conv2d(base_channels, base_channels * 2, 4, stride=2, padding=1),
            nn.InstanceNorm2d(base_channels * 2),
            nn.LeakyReLU(0.2, inplace=True),
            
            nn.Conv2d(base_channels * 2, base_channels * 4, 4, stride=2, padding=1),
            nn.InstanceNorm2d(base_channels * 4),
            nn.LeakyReLU(0.2, inplace=True),
            
            nn.Conv2d(base_channels * 4, base_channels * 8, 4, stride=2, padding=1),
            nn.InstanceNorm2d(base_channels * 8),
            nn.LeakyReLU(0.2, inplace=True),
            
            nn.Conv2d(base_channels * 8, base_channels * 8, 4, stride=1, padding=1),
            nn.InstanceNorm2d(base_channels * 8),
            nn.LeakyReLU(0.2, inplace=True),
        )
        
        # 分支1：真/假判别
        self.adversarial = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(base_channels * 8, 1),
        )
        
        # 分支2：风格分类
        self.style_classifier = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(base_channels * 8, num_styles),
        )
    
    def forward(self, x):
        """
        Returns:
            adv_out: 真假判别得分 (B, 1)
            style_out: 风格分类logits (B, num_styles)
        """
        shared_feat = self.shared(x)
        adv_out = self.adversarial(shared_feat)
        style_out = self.style_classifier(shared_feat)
        return adv_out, style_out

"""
风格编码器 - StyleEncoder
将书法家风格映射到连续的低维隐空间，支持风格插值与混合
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class StyleEncoder(nn.Module):
    """
    风格编码器：从书法样本中提取风格特征向量
    
    输入：书法图片 (B, 1, H, W) - 灰度图
    输出：风格隐向量 (B, style_dim) - 低维连续表示
    """
    
    def __init__(self, style_dim=128, in_channels=1, base_channels=64):
        super().__init__()
        self.style_dim = style_dim
        
        # 下采样卷积层 - 逐步提取高层风格特征
        self.encoder = nn.Sequential(
            # Block 1: 256x256 -> 128x128
            nn.Conv2d(in_channels, base_channels, 4, stride=2, padding=1),
            nn.InstanceNorm2d(base_channels),
            nn.LeakyReLU(0.2, inplace=True),
            
            # Block 2: 128x128 -> 64x64
            nn.Conv2d(base_channels, base_channels * 2, 4, stride=2, padding=1),
            nn.InstanceNorm2d(base_channels * 2),
            nn.LeakyReLU(0.2, inplace=True),
            
            # Block 3: 64x64 -> 32x32
            nn.Conv2d(base_channels * 2, base_channels * 4, 4, stride=2, padding=1),
            nn.InstanceNorm2d(base_channels * 4),
            nn.LeakyReLU(0.2, inplace=True),
            
            # Block 4: 32x32 -> 16x16
            nn.Conv2d(base_channels * 4, base_channels * 8, 4, stride=2, padding=1),
            nn.InstanceNorm2d(base_channels * 8),
            nn.LeakyReLU(0.2, inplace=True),
            
            # Block 5: 16x16 -> 8x8
            nn.Conv2d(base_channels * 8, base_channels * 8, 4, stride=2, padding=1),
            nn.InstanceNorm2d(base_channels * 8),
            nn.LeakyReLU(0.2, inplace=True),
        )
        
        # 自注意力 - 捕获全局风格特征
        self.attention = SelfAttention(base_channels * 8)
        
        # 自适应池化 + 全连接映射到风格隐空间
        self.fc = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(base_channels * 8, style_dim * 2),
            nn.ReLU(inplace=True),
            nn.Linear(style_dim * 2, style_dim),
        )
    
    def forward(self, x):
        """
        Args:
            x: 书法图片 (B, 1, H, W)
        Returns:
            style_vector: 风格隐向量 (B, style_dim)
        """
        feat = self.encoder(x)
        feat = self.attention(feat)
        style_vector = self.fc(feat)
        # L2归一化，确保风格向量在单位超球面上
        style_vector = F.normalize(style_vector, dim=1)
        return style_vector
    
    def interpolate(self, style1, style2, alpha=0.5):
        """风格插值：在两个风格之间平滑过渡
        Args:
            style1, style2: 风格向量 (B, style_dim)
            alpha: 插值系数，0=纯style1, 1=纯style2
        Returns:
            混合风格向量
        """
        return (1 - alpha) * style1 + alpha * style2
    
    def mix(self, styles, weights=None):
        """多风格混合
        Args:
            styles: 风格向量列表 [style_dim, ...]
            weights: 各风格权重，None则等权
        """
        stacked = torch.stack(styles, dim=0)
        if weights is None:
            weights = torch.ones(len(styles), device=stacked.device) / len(styles)
        else:
            weights = torch.tensor(weights, device=stacked.device)
            weights = weights / weights.sum()
        mixed = (stacked * weights.view(-1, 1)).sum(dim=0)
        return F.normalize(mixed, dim=0)


class SelfAttention(nn.Module):
    """自注意力模块 - 增强全局风格特征提取"""
    
    def __init__(self, in_channels):
        super().__init__()
        self.query = nn.Conv2d(in_channels, in_channels // 8, 1)
        self.key = nn.Conv2d(in_channels, in_channels // 8, 1)
        self.value = nn.Conv2d(in_channels, in_channels, 1)
        self.gamma = nn.Parameter(torch.zeros(1))
    
    def forward(self, x):
        B, C, H, W = x.size()
        
        q = self.query(x).view(B, -1, H * W).permute(0, 2, 1)  # (B, HW, C//8)
        k = self.key(x).view(B, -1, H * W)  # (B, C//8, HW)
        v = self.value(x).view(B, -1, H * W)  # (B, C, HW)
        
        attention = F.softmax(torch.bmm(q, k), dim=-1)  # (B, HW, HW)
        out = torch.bmm(v, attention.permute(0, 2, 1))  # (B, C, HW)
        out = out.view(B, C, H, W)
        
        return self.gamma * out + x


class ContentEncoder(nn.Module):
    """
    内容编码器：从文本/骨架中提取字形结构特征（不含风格信息）
    
    输入：字形骨架图 (B, 1, H, W) - 二值骨架
    输出：内容特征图 (B, content_dim, H', W')
    """
    
    def __init__(self, content_dim=256, in_channels=1, base_channels=64):
        super().__init__()
        self.content_dim = content_dim
        
        self.encoder = nn.Sequential(
            nn.Conv2d(in_channels, base_channels, 4, stride=2, padding=1),
            nn.InstanceNorm2d(base_channels),
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
            
            nn.Conv2d(base_channels * 8, content_dim, 3, stride=1, padding=1),
            nn.InstanceNorm2d(content_dim),
            nn.LeakyReLU(0.2, inplace=True),
        )
    
    def forward(self, x):
        return self.encoder(x)

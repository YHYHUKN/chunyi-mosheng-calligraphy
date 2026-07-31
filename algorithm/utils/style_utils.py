"""
风格参数可解释化模块
将抽象的风格隐向量映射为传统书法术语，实现可解释的参数调节
"""
import torch
import torch.nn as nn
import numpy as np
from typing import Dict, Tuple


class StyleAttributePredictor(nn.Module):
    """
    风格属性预测器
    
    从风格隐向量预测可解释的书法属性：
    - 笔法粗细 (brush_weight)
    - 墨色浓淡 (ink_density)  
    - 结字疏密 (char_density)
    - 行笔速度 (stroke_speed)
    - 飞白程度 (flying_white)
    """
    
    ATTRIBUTES = ['brush_weight', 'ink_density', 'char_density',
                  'stroke_speed', 'flying_white']
    
    def __init__(self, style_dim=128, num_attributes=5):
        super().__init__()
        self.predictor = nn.Sequential(
            nn.Linear(style_dim, 64),
            nn.ReLU(inplace=True),
            nn.Linear(64, 32),
            nn.ReLU(inplace=True),
            nn.Linear(32, num_attributes),
            nn.Sigmoid(),  # 每个属性输出 [0, 1]
        )
    
    def forward(self, style_vector):
        """
        Args:
            style_vector: (B, style_dim)
        Returns:
            attributes: (B, num_attributes), 每个值在 [0, 1]
        """
        return self.predictor(style_vector)
    
    def predict_single(self, style_vector: torch.Tensor) -> Dict[str, float]:
        """预测单个风格向量的属性"""
        with torch.no_grad():
            attrs = self.predictor(style_vector.unsqueeze(0)).squeeze(0)
        return {name: attrs[i].item() for i, name in enumerate(self.ATTRIBUTES)}


class StyleInterpolator:
    """
    风格插值器 - 在隐空间中实现风格混合与过渡
    
    关键能力：
    1. 两个风格之间的平滑插值（如：颜体→柳体）
    2. 多风格加权混合
    3. 风格属性定向调整（如：加粗笔法、增加墨色）
    """
    
    def __init__(self, style_dim=128):
        self.style_dim = style_dim
        self.style_library: Dict[str, torch.Tensor] = {}
    
    def register_style(self, name: str, style_vector: torch.Tensor):
        """注册一个风格到库中"""
        self.style_library[name] = style_vector
    
    def interpolate(self, style1_name: str, style2_name: str, 
                    alpha: float = 0.5) -> torch.Tensor:
        """
        两个风格之间插值
        
        Args:
            alpha: 0=style1, 1=style2
        """
        s1 = self.style_library[style1_name]
        s2 = self.style_library[style2_name]
        return s1 * (1 - alpha) + s2 * alpha
    
    def mix_styles(self, style_names: list, weights: list = None) -> torch.Tensor:
        """多风格混合"""
        if weights is None:
            weights = [1.0 / len(style_names)] * len(style_names)
        
        assert len(style_names) == len(weights)
        total = sum(weights)
        weights = [w / total for w in weights]
        
        result = torch.zeros(self.style_dim)
        for name, w in zip(style_names, weights):
            result += w * self.style_library[name]
        
        return result
    
    def adjust_attribute(self, style_vector: torch.Tensor,
                         attribute_name: str,
                         delta: float) -> torch.Tensor:
        """
        定向调整风格属性
        
        通过在隐空间中沿属性方向移动来实现
        """
        # 这里简化为线性调整，实际可用属性向量学习
        adjusted = style_vector + delta * 0.1
        return adjusted
    
    def find_nearest_styles(self, style_vector: torch.Tensor, 
                            top_k: int = 3) -> list:
        """找到最接近的K个已注册风格"""
        distances = []
        for name, lib_vec in self.style_library.items():
            dist = torch.norm(style_vector - lib_vec).item()
            distances.append((name, dist))
        distances.sort(key=lambda x: x[1])
        return distances[:top_k]


class StrokeRenderer:
    """
    笔画渲染器 - 将GAN生成的单字合成完整作品
    
    功能：
    1. 按照竖排/横排布局排列单字
    2. 处理字间距、行间距
    3. 添加宣纸纹理
    4. 添加印章（可选）
    5. 渲染落款
    """
    
    def __init__(self):
        self.paper_texture = None
    
    def create_paper_texture(self, height: int, width: int) -> np.ndarray:
        """生成宣纸纹理"""
        texture = np.ones((height, width), dtype=np.uint8) * 250
        
        # 添加纤维纹理
        noise = np.random.normal(0, 5, (height, width)).astype(np.int16)
        texture = np.clip(texture.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        # 横向纤维
        for _ in range(height // 3):
            y = np.random.randint(0, height)
            x_start = np.random.randint(0, width)
            length = np.random.randint(50, 300)
            alpha = np.random.randint(3, 8)
            cv2.line(texture, (x_start, y), 
                    (min(x_start + length, width), y), 
                    (245 - alpha), 1)
        
        self.paper_texture = texture
        return texture
    
    def compose_work(self, 
                     char_images: list,
                     layout: str = 'vertical',
                     char_spacing: int = 20,
                     line_spacing: int = 30,
                     cols: int = 1) -> np.ndarray:
        """
        将单字图片合成完整书法作品
        
        Args:
            char_images: 单字图片列表 (每个 HxW 灰度图)
            layout: 'vertical' 或 'horizontal'
            char_spacing: 字间距（像素）
            line_spacing: 行间距（像素）
            cols: 列数（竖排时）
        """
        if not char_images:
            return None
        
        # 统一字号
        target_size = char_images[0].shape[0]
        resized_chars = []
        for img in char_images:
            if img.shape[0] != target_size:
                img = cv2.resize(img, (target_size, target_size))
            resized_chars.append(img)
        
        if layout == 'vertical':
            return self._compose_vertical(resized_chars, char_spacing, 
                                          line_spacing, cols)
        else:
            return self._compose_horizontal(resized_chars, char_spacing, 
                                             line_spacing)
    
    def _compose_vertical(self, chars, char_spacing, line_spacing, cols):
        """竖排合成（从右到左）"""
        chars_per_col = (len(chars) + cols - 1) // cols
        
        h = len(chars) * (chars[0].shape[0] + char_spacing) + line_spacing * 2
        w = cols * (chars[0].shape[1] + line_spacing) + line_spacing * 2
        
        canvas = np.ones((h, w), dtype=np.uint8) * 255
        
        for i, char_img in enumerate(chars):
            col = i // chars_per_col
            row = i % chars_per_col
            
            # 从右到左排列
            x = w - line_spacing - (col + 1) * (chars[0].shape[1] + line_spacing)
            y = line_spacing + row * (chars[0].shape[0] + char_spacing)
            
            # 叠加字符（处理透明）
            mask = char_img < 200
            canvas[y:y+char_img.shape[0], x:x+char_img.shape[1]][mask] = \
                char_img[mask]
        
        return canvas
    
    def _compose_horizontal(self, chars, char_spacing, line_spacing):
        """横排合成"""
        # 简单横排实现
        h = chars[0].shape[0] + line_spacing * 2
        w = len(chars) * (chars[0].shape[1] + char_spacing) + char_spacing
        
        canvas = np.ones((h, w), dtype=np.uint8) * 255
        
        x = char_spacing
        for char_img in chars:
            mask = char_img < 200
            y_offset = line_spacing
            canvas[y_offset:y_offset+char_img.shape[0], 
                   x:x+char_img.shape[1]][mask] = char_img[mask]
            x += char_img.shape[1] + char_spacing
        
        return canvas
    
    def add_seal(self, canvas: np.ndarray, 
                 position: str = 'bottom-right',
                 seal_size: int = 40) -> np.ndarray:
        """
        添加印章
        
        Args:
            position: 'bottom-right', 'top-left' 等
        """
        h, w = canvas.shape
        
        # 生成红色方形印章
        seal = np.ones((seal_size, seal_size), dtype=np.uint8) * 255
        border = 2
        seal[:border, :] = 0
        seal[-border:, :] = 0
        seal[:, :border] = 0
        seal[:, -border:] = 0
        
        # 印章内添加简单纹理
        inner = seal[border:-border, border:-border]
        noise = np.random.random((inner.shape[0], inner.shape[1])) > 0.6
        inner[noise] = 0
        
        # 叠加到画布
        if position == 'bottom-right':
            y = h - seal_size - 20
            x = w - seal_size - 20
        elif position == 'top-left':
            y = 20
            x = 20
        else:
            y = h - seal_size - 20
            x = w - seal_size - 20
        
        # 红色印章区域
        mask = seal < 200
        # 在灰度图上模拟红色印章
        canvas[y:y+seal_size, x:x+seal_size][mask] = 60  # 深灰模拟红色印章
        
        return canvas


# 需要cv2的一些引用
import cv2

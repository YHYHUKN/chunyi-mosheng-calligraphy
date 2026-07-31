"""
数据预处理工具 - 书法数据集处理、增强、骨架提取
支持多书法家、多书体的数据准备流程
"""
import os
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum


class ScriptType(Enum):
    """五大书体"""
    KAISHU = "楷书"
    XINGSHU = "行书"
    CAOSHU = "草书"
    LISHU = "隶书"
    ZHUANSHU = "篆书"


@dataclass
class CalligraphySample:
    """书法数据样本"""
    image: np.ndarray          # 原始图片 (H, W)
    skeleton: np.ndarray       # 字形骨架 (H, W), 二值图
    style_label: int           # 风格标签索引
    calligrapher: str          # 书法家名称
    script_type: ScriptType    # 书体类型
    char: str                  # 对应汉字
    quality_score: float       # 质量评分


class DataPreprocessor:
    """
    书法数据预处理器
    
    处理流程：
    1. 图片读取与标准化（灰度、尺寸归一化、去噪）
    2. 字符分割（整幅作品 → 单字切割）
    3. 骨架提取（细化算法提取字形骨架）
    4. 数据增强（旋转、扭曲、墨色变化等）
    5. 质量筛选（去除模糊、不完整样本）
    """
    
    # 标准尺寸
    TARGET_SIZE = 256
    
    def __init__(self, target_size=256):
        self.target_size = target_size
    
    def load_and_preprocess(self, image_path: str) -> Optional[np.ndarray]:
        """
        读取并预处理书法图片
        
        Args:
            image_path: 图片路径
        Returns:
            预处理后的灰度图 (target_size, target_size)
        """
        # 读取图片
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"[WARN] 无法读取图片: {image_path}")
            return None
        
        # 去噪
        img = cv2.GaussianBlur(img, (3, 3), 0)
        
        # 自适应二值化（处理不同背景）
        binary = cv2.adaptiveThreshold(
            img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 8
        )
        
        # 提取文字区域（去除白边）
        coords = cv2.findNonZero(binary)
        if coords is None:
            return None
        
        x, y, w, h = cv2.boundingRect(coords)
        padding = max(w, h) // 10
        x1 = max(0, x - padding)
        y1 = max(0, y - padding)
        x2 = min(img.shape[1], x + w + padding)
        y2 = min(img.shape[0], y + h + padding)
        
        cropped = img[y1:y2, x1:x2]
        
        # 等比例缩放到目标尺寸，保持笔画比例
        canvas = np.ones((self.target_size, self.target_size), dtype=np.uint8) * 255
        
        # 短边适配，居中放置
        scale = min(self.target_size * 0.85 / cropped.shape[0],
                    self.target_size * 0.85 / cropped.shape[1])
        new_w = int(cropped.shape[1] * scale)
        new_h = int(cropped.shape[0] * scale)
        
        if new_w > 0 and new_h > 0:
            resized = cv2.resize(cropped, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            offset_x = (self.target_size - new_w) // 2
            offset_y = (self.target_size - new_h) // 2
            canvas[offset_y:offset_y + new_h, offset_x:offset_x + new_w] = resized
        
        return canvas
    
    def extract_skeleton(self, image: np.ndarray) -> np.ndarray:
        """
        字形骨架提取
        
        使用Zhang-Suen细化算法提取笔画中心线，
        作为内容编码器的输入（不含风格信息）
        
        Args:
            image: 灰度图 (H, W)
        Returns:
            骨架二值图 (H, W), 255=骨架, 0=背景
        """
        # 二值化
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # 反转：笔画为白色
        binary_inv = cv2.bitwise_not(binary)
        
        # Zhang-Suen细化
        skeleton = cv2.ximgproc.thinning(binary_inv)
        
        # 膨胀1个像素确保骨架连续
        kernel = np.ones((3, 3), np.uint8)
        skeleton = cv2.dilate(skeleton, kernel, iterations=1)
        
        return skeleton
    
    def split_characters(self, image: np.ndarray, 
                         layout: str = 'vertical') -> List[np.ndarray]:
        """
        字符分割：将整幅书法作品分割为单字
        
        Args:
            image: 整幅作品灰度图
            layout: 'vertical'(竖排) 或 'horizontal'(横排)
        Returns:
            单字图片列表
        """
        # 二值化
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binary_inv = cv2.bitwise_not(binary)
        
        chars = []
        
        if layout == 'vertical':
            # 竖排：按列分割
            col_projection = np.sum(binary_inv, axis=0)
            col_ranges = self._find_ranges(col_projection)
            
            for x1, x2 in col_ranges:
                col_img = binary_inv[:, x1:x2]
                row_projection = np.sum(col_img, axis=1)
                row_ranges = self._find_ranges(row_projection)
                
                for y1, y2 in row_ranges:
                    char_img = image[y1:y2, x1:x2]
                    chars.append(char_img)
        else:
            # 横排：按行分割
            row_projection = np.sum(binary_inv, axis=1)
            row_ranges = self._find_ranges(row_projection)
            
            for y1, y2 in row_ranges:
                row_img = binary_inv[y1:y2, :]
                col_projection = np.sum(row_img, axis=0)
                col_ranges = self._find_ranges(col_projection)
                
                for x1, x2 in col_ranges:
                    char_img = image[y1:y2, x1:x2]
                    chars.append(char_img)
        
        return chars
    
    def _find_ranges(self, projection: np.ndarray, 
                     min_length: int = 5, min_sum: int = 100) -> List[Tuple[int, int]]:
        """找到投影中的连续区间"""
        threshold = max(projection.max() * 0.05, min_sum)
        in_range = projection > threshold
        
        ranges = []
        start = None
        for i, val in enumerate(in_range):
            if val and start is None:
                start = i
            elif not val and start is not None:
                if i - start >= min_length:
                    ranges.append((start, i))
                start = None
        
        if start is not None and len(projection) - start >= min_length:
            ranges.append((start, len(projection)))
        
        return ranges
    
    def augment(self, image: np.ndarray, 
                skeleton: np.ndarray,
                num_augmentations: int = 5) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        数据增强
        
        针对书法特性的增强：
        - 轻微旋转（模拟书写角度变化）
        - 弹性形变（模拟笔触自然抖动）
        - 墨色变化（模拟浓墨/淡墨/枯笔）
        - 模糊变化（模拟运笔速度）
        """
        augmented = []
        
        for _ in range(num_augmentations):
            # 随机旋转 [-5, 5] 度
            angle = np.random.uniform(-5, 5)
            h, w = image.shape
            M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
            aug_img = cv2.warpAffine(image, M, (w, h), borderValue=255)
            aug_skel = cv2.warpAffine(skeleton, M, (w, h), borderValue=0)
            
            # 随机弹性形变
            if np.random.random() > 0.5:
                aug_img, aug_skel = self._elastic_transform(aug_img, aug_skel)
            
            # 随机墨色变化
            if np.random.random() > 0.3:
                alpha = np.random.uniform(0.7, 1.3)
                aug_img = np.clip(aug_img * alpha, 0, 255).astype(np.uint8)
            
            # 随机模糊（模拟运笔速度变化）
            if np.random.random() > 0.5:
                k = np.random.choice([1, 3])
                aug_img = cv2.GaussianBlur(aug_img, (k, k), 0)
            
            augmented.append((aug_img, aug_skel))
        
        return augmented
    
    def _elastic_transform(self, image: np.ndarray, 
                           skeleton: np.ndarray,
                           alpha: float = 10,
                           sigma: float = 4) -> Tuple[np.ndarray, np.ndarray]:
        """弹性形变 - 模拟笔触自然抖动"""
        h, w = image.shape
        dx = cv2.GaussianBlur(np.random.uniform(-1, 1, (h, w)).astype(np.float32),
                              (0, 0), sigma) * alpha
        dy = cv2.GaussianBlur(np.random.uniform(-1, 1, (h, w)).astype(np.float32),
                              (0, 0), sigma) * alpha
        
        x, y = np.meshgrid(np.arange(w), np.arange(h))
        x = np.clip(x + dx, 0, w - 1).astype(np.float32)
        y = np.clip(y + dy, 0, h - 1).astype(np.float32)
        
        img_warped = cv2.remap(image, x, y, cv2.INTER_LINEAR, borderValue=255)
        skel_warped = cv2.remap(skeleton, x, y, cv2.INTER_NEAREST, borderValue=0)
        
        return img_warped, skel_warped
    
    def quality_check(self, image: np.ndarray, 
                      skeleton: np.ndarray) -> float:
        """
        质量检测 - 评估书法样本质量
        
        检查项：
        - 笔画完整性（骨架覆盖率）
        - 清晰度（拉普拉斯方差）
        - 对称性（可选）
        
        Returns:
            质量分数 [0, 1], 越高越好
        """
        score = 0.0
        
        # 1. 清晰度（拉普拉斯方差）
        laplacian_var = cv2.Laplacian(image, cv2.CV_64F).var()
        clarity = min(laplacian_var / 500, 1.0)
        score += clarity * 0.4
        
        # 2. 笔画密度（避免空白或过度密集）
        _, binary = cv2.threshold(image, 200, 255, cv2.THRESH_BINARY)
        ink_ratio = np.sum(binary == 0) / binary.size
        density_score = 1.0 - abs(ink_ratio - 0.15) * 5  # 理想墨迹占比约15%
        density_score = max(0, min(1, density_score))
        score += density_score * 0.3
        
        # 3. 骨架连通性
        skeleton_area = np.sum(skeleton > 0)
        total_area = skeleton.size
        skeleton_ratio = skeleton_area / total_area
        if 0.02 < skeleton_ratio < 0.15:
            score += 0.3
        else:
            score += max(0, 0.3 - abs(skeleton_ratio - 0.05) * 2)
        
        return min(score, 1.0)


class CalligraphyDataset:
    """
    书法数据集 - PyTorch Dataset
    
    支持加载多书法家、多书体的数据
    """
    
    def __init__(self, data_root: str, preprocessor: DataPreprocessor,
                 split: str = 'train', augment: bool = True):
        self.preprocessor = preprocessor
        self.augment = augment and (split == 'train')
        self.samples: List[CalligraphySample] = []
        self.style_map: Dict[str, int] = {}  # 书法家名 → 风格标签索引
        
        # 遍历数据目录
        data_path = Path(data_root)
        if not data_path.exists():
            print(f"[WARN] 数据目录不存在: {data_root}")
            return
        
        self._load_dataset(data_path)
        print(f"[INFO] 加载了 {len(self.samples)} 个书法样本")
    
    def _load_dataset(self, data_path: Path):
        """加载数据集 - 期望目录结构：data_path/书法家名/书体/*.jpg"""
        style_idx = 0
        
        for calligrapher_dir in sorted(data_path.iterdir()):
            if not calligrapher_dir.is_dir():
                continue
            
            calligrapher_name = calligrapher_dir.name
            if calligrapher_name not in self.style_map:
                self.style_map[calligrapher_name] = style_idx
                style_idx += 1
            
            for script_dir in calligrapher_dir.iterdir():
                if not script_dir.is_dir():
                    continue
                
                for img_file in script_dir.glob('*.jpg'):
                    sample = self._load_sample(
                        str(img_file), calligrapher_name,
                        self.style_map[calligrapher_name]
                    )
                    if sample is not None:
                        self.samples.append(sample)
                
                # 也支持png格式
                for img_file in script_dir.glob('*.png'):
                    sample = self._load_sample(
                        str(img_file), calligrapher_name,
                        self.style_map[calligrapher_name]
                    )
                    if sample is not None:
                        self.samples.append(sample)
    
    def _load_sample(self, path: str, calligrapher: str, 
                     style_label: int) -> Optional[CalligraphySample]:
        """加载单个样本"""
        img = self.preprocessor.load_and_preprocess(path)
        if img is None:
            return None
        
        skeleton = self.preprocessor.extract_skeleton(img)
        quality = self.preprocessor.quality_check(img, skeleton)
        
        if quality < 0.3:
            return None
        
        char = Path(path).stem[0] if Path(path).stem else '未'
        
        return CalligraphySample(
            image=img,
            skeleton=skeleton,
            style_label=style_label,
            calligrapher=calligrapher,
            script_type=ScriptType.KAISHU,  # 默认
            char=char,
            quality_score=quality,
        )
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        sample = self.samples[idx]
        
        # 归一化到 [-1, 1]
        image = sample.image.astype(np.float32) / 127.5 - 1.0
        skeleton = (sample.skeleton.astype(np.float32) / 127.5 - 1.0)
        
        # CHW格式
        image = image[np.newaxis, :, :]  # (1, H, W)
        skeleton = skeleton[np.newaxis, :, :]
        
        return {
            'image': image,
            'skeleton': skeleton,
            'style_label': sample.style_label,
            'calligrapher': sample.calligrapher,
            'char': sample.char,
        }

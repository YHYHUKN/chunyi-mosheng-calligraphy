"""
FastAPI后端服务 - AI书法创作系统API
提供书法生成、风格管理、作品管理等功能
"""
import os
import sys
import json
import base64
import time
from pathlib import Path
from typing import Optional, List

# 添加项目根目录到路径（algorithm/server/app.py → 上溯3级 → 项目根）
_PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _PROJECT_DIR)
# 同时将 algorithm 目录加入路径（用于导入 models, utils 等）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# PyTorch imports
import torch
import torch.nn.functional as F
import numpy as np
import cv2


# ============ 数据模型 ============

class GenerateRequest(BaseModel):
    """书法生成请求"""
    text: str                          # 要生成的文本
    style_name: str = "米芾"             # 风格名称
    layout: str = "vertical"           # 布局：vertical/horizontal
    char_spacing: int = 50             # 字间距 0-100
    line_spacing: int = 50             # 行间距 0-100
    font_size: int = 64                # 字号 30-120
    paper_ratio: str = "square"        # 纸幅比例：portrait/square/landscape
    # 风格参数
    brush_weight: int = 50             # 笔法粗细 0-100
    ink_density: int = 50              # 墨色浓淡 0-100
    char_density: int = 50             # 结字疏密 0-100
    flying_white: int = 0              # 飞白效果 0-100

class StyleInfo(BaseModel):
    """风格信息"""
    name: str
    display_name: str
    script_type: str
    description: str
    era: str
    sample_preview: str  # base64编码的预览图

class GenerateResponse(BaseModel):
    """生成响应"""
    success: bool
    image_base64: str
    generation_time: float
    style_used: str


# ============ FastAPI应用 ============

app = FastAPI(
    title="春意墨生 - AI书法创作系统",
    description="基于GAN与风格解耦技术的AI书法创作API",
    version="1.0.0"
)

# CORS跨域配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ 模型管理 ============

class ModelManager:
    """
    模型管理器 - 单例模式管理模型加载与推理
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.style_encoder = None
        self.content_encoder = None
        self.generator = None
        self.models_loaded = False
        
        # 风格库
        self.style_library = {}
        self._init_style_library()
        
        # 骨架缓存
        self.skeleton_cache = {}

        # 训练时的风格映射（模型加载后填充）
        self.train_style_map = {}
        
        # 字库缓存（方案A：字库匹配优先）
        self.char_library = {}  # {风格名: {字: 图片路径}}
        self._init_char_library()
        
        self._initialized = True
        print(f"[ModelManager] 初始化完成，设备: {self.device}")
    
    def _init_char_library(self):
        """初始化字库 - 扫描 Calli-Tongji 字库目录"""
        # 风格名映射：系统风格名 → 字库目录名
        style_to_dir = {
            "米芾": "米芾-行",
            "赵孟頫": "赵孟頫-楷",
            "褚遂良": "褚遂良-楷",
            "乙瑛碑": "吴让之-隶",
            "邓石如": "邓石如-篆",
            "怀素": "怀素-草",
        }
        
        lib_base = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            '书法字库', 'Calli-Tongji', 'Calli-Tongji'
        )
        
        if not os.path.isdir(lib_base):
            print("[ModelManager] 字库目录不存在，跳过字库初始化")
            return
        
        for style_name, dir_name in style_to_dir.items():
            style_dir = os.path.join(lib_base, dir_name)
            if os.path.isdir(style_dir):
                char_map = {}
                for f in os.listdir(style_dir):
                    if f.endswith('.png'):
                        char_name = f.replace('.png', '')
                        char_map[char_name] = os.path.join(style_dir, f)
                self.char_library[style_name] = char_map
                print(f"[ModelManager] 字库加载 '{style_name}': {len(char_map)}字")
    
    def _init_style_library(self):
        """初始化预置风格库"""
        styles = {
            "米芾":   {"display": "米芾行书", "script": "行书", "era": "宋代",
                       "desc": "沉着痛快，八面出锋，风樯阵马"},
            "赵孟頫": {"display": "赵体楷书", "script": "楷书", "era": "元代",
                       "desc": "圆润秀美，流畅自然，遒媚姿媚"},
            "褚遂良": {"display": "褚体楷书", "script": "楷书", "era": "唐代",
                       "desc": "清朗秀劲，疏瘦劲健，灵动飘逸"},
            "乙瑛碑": {"display": "吴让之隶书", "script": "隶书", "era": "清代",
                       "desc": "婉畅飘逸，圆浑沉着，遒劲古拙"},
            "邓石如": {"display": "邓派篆书", "script": "篆书", "era": "清代",
                       "desc": "圆转匀称，刚健婀娜，篆法精绝"},
            "怀素":   {"display": "怀素草书", "script": "草书", "era": "唐代",
                       "desc": "狂放飘逸，如骤雨旋风，挥毫泼墨"},
        }
        self.style_library = styles
    
    def load_models(self, checkpoint_dir: str):
        """加载训练好的模型"""
        try:
            from models.style_encoder import StyleEncoder, ContentEncoder
            from models.generator import DualBranchGenerator

            # 尝试从 style_map.json 读取配置
            config_path = os.path.join(checkpoint_dir, 'final', 'style_map.json')
            style_dim, content_dim, image_size = 128, 256, 128
            style_map = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                style_dim = meta.get('style_dim', 128)
                content_dim = meta.get('content_dim', 256)
                image_size = meta.get('image_size', 128)
                style_map = meta.get('style_map', {})

            self.style_encoder = StyleEncoder(style_dim=style_dim).to(self.device)
            self.content_encoder = ContentEncoder(content_dim=content_dim).to(self.device)
            self.generator = DualBranchGenerator(
                content_dim=content_dim, style_dim=style_dim,
                image_size=image_size
            ).to(self.device)

            # 查找 checkpoint（优先 mifu，再 zhao_fast，再 best，再 final）
            checkpoint_path = None
            candidates = [
                os.path.join(checkpoint_dir, 'final', 'mifu_ep030.pth'),
                os.path.join(checkpoint_dir, 'final', 'zhao_fast_ep010.pth'),
                os.path.join(checkpoint_dir, 'final', 'checkpoint_epoch_060.pth'),
            ]
            # 也找任何 _best.pth
            for f in sorted(os.listdir(checkpoint_dir)):
                if f.endswith('_best.pth'):
                    candidates.append(os.path.join(checkpoint_dir, f))
            # 最新 epoch 的 checkpoint
            for f in sorted(os.listdir(checkpoint_dir)):
                if f.endswith('.pth') and not f.endswith('_best.pth'):
                    candidates.append(os.path.join(checkpoint_dir, f))

            for cp in candidates:
                if os.path.exists(cp):
                    checkpoint_path = cp
                    break

            print(f"[ModelManager] 尝试加载: {checkpoint_path}", flush=True)

            if checkpoint_path:
                checkpoint = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
                self.style_encoder.load_state_dict(checkpoint['style_encoder'])
                self.content_encoder.load_state_dict(checkpoint['content_encoder'])
                self.generator.load_state_dict(checkpoint['generator'])

                # 从 checkpoint config 读取 image_size
                ckpt_config = checkpoint.get('config', {})
                self.image_size = ckpt_config.get('image_size', 128)
                # 使用 checkpoint 中的 style_map
                ckpt_style_map = checkpoint.get('style_map', {})
                if ckpt_style_map:
                    self.train_style_map = ckpt_style_map

                self.style_encoder.eval()
                self.content_encoder.eval()
                self.generator.eval()

                # 保存 style_map 供推理时用（优先用 checkpoint 中的）
                if not hasattr(self, 'train_style_map') or not self.train_style_map:
                    self.train_style_map = style_map
                self.models_loaded = True
                print(f"[ModelManager] 模型加载成功: {checkpoint_path}")
            else:
                print(f"[ModelManager] 无检查点，使用模拟生成模式")
        except Exception as e:
            print(f"[ModelManager] 模型加载失败: {e}，使用模拟生成模式")
            import traceback; traceback.print_exc()
            # 强制刷新 stdout
            import sys; sys.stdout.flush(); sys.stderr.flush()
    
    def generate(self, request: GenerateRequest) -> tuple:
        """
        生成书法作品
        
        策略（方案A）：
        1. 字库匹配：输入的字在字库中有 → 直接返回高清字库图
        2. 字库没有的字 + 有模型 → 用GAN生成（目前效果不好）
        3. 全部没有 → 前端Canvas模拟渲染
        
        Returns:
            (image_base64, generation_time)
        """
        start_time = time.time()
        
        # === 方案A：字库匹配优先 ===
        chars = list(request.text)
        lib_chars = self._match_from_library(chars, request.style_name)
        
        if lib_chars:
            # 字库中有至少一个字，用字库图
            # 混合：字库有的用字库图，没有的用Canvas模拟
            image = self._compose_mixed(lib_chars, chars, request)
        elif self.models_loaded and self.generator is not None:
            # 字库完全没命中，尝试模型推理
            image = self._generate_real(request)
        else:
            # 完全没有，用Canvas模拟
            image = self._generate_simulated(request)
        
        gen_time = time.time() - start_time
        
        # 转base64
        _, buffer = cv2.imencode('.png', image)
        image_b64 = base64.b64encode(buffer).decode('utf-8')
        
        return image_b64, gen_time
    
    def _match_from_library(self, chars: list, style_name: str) -> dict:
        """
        从字库匹配字符
        Returns: {索引: numpy图片} 命中的字符
        """
        if style_name not in self.char_library:
            return {}
        
        lib = self.char_library[style_name]
        matched = {}
        
        for i, char in enumerate(chars):
            if char in lib:
                img_path = lib[char]
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is not None:
                    # 字库图片是256x256，居中裁切到合适大小
                    # 先找字迹边界
                    binary = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                                   cv2.THRESH_BINARY_INV, 11, 8)
                    coords = cv2.findNonZero(binary)
                    if coords is not None:
                        x, y, w, h = cv2.boundingRect(coords)
                        pad = max(w, h) // 6
                        x1 = max(0, x - pad); y1 = max(0, y - pad)
                        x2 = min(img.shape[1], x + w + pad); y2 = min(img.shape[0], y + h + pad)
                        cropped = img[y1:y2, x1:x2]
                        # 放大到256x256保持清晰
                        canvas = np.ones((256, 256), dtype=np.uint8) * 255
                        scale = min(240 / cropped.shape[0], 240 / cropped.shape[1])
                        nw = int(cropped.shape[1] * scale); nh = int(cropped.shape[0] * scale)
                        resized = cv2.resize(cropped, (nw, nh), interpolation=cv2.INTER_CUBIC)
                        ox = (256 - nw) // 2; oy = (256 - nh) // 2
                        canvas[oy:oy+nh, ox:ox+nw] = resized
                        matched[i] = canvas
        
        return matched
    
    def _compose_mixed(self, lib_chars: dict, all_chars: list, request: GenerateRequest) -> np.ndarray:
        """
        混合合成：字库有的用字库图，没有的用Canvas渲染
        """
        from utils.style_utils import StrokeRenderer
        renderer = StrokeRenderer()
        style_params = self._get_style_params(request.style_name, request)
        char_images = []
        
        for i, char in enumerate(all_chars):
            if i in lib_chars:
                # 字库命中 → 直接用高清图
                char_images.append(lib_chars[i])
            else:
                # 字库没有 → Canvas渲染
                char_images.append(self._render_single_char(char, 256, style_params, request))
        
        # 合成完整作品
        composed = renderer.compose_work(
            char_images,
            layout=request.layout,
            char_spacing=int(request.char_spacing * 0.4),
            line_spacing=int(request.line_spacing * 0.6),
        )
        
        # 添加宣纸纹理和印章
        if composed is not None:
            h, w = composed.shape
            paper = renderer.create_paper_texture(h, w)
            mask = composed < 200
            paper[mask] = composed[mask]
            composed = paper
            composed = renderer.add_seal(composed, 'bottom-right', 48)
        
        return composed if composed is not None else np.ones((512, 512), dtype=np.uint8) * 255
    
    def _generate_real(self, request: GenerateRequest) -> np.ndarray:
        """真实模型推理 - 用训练好的风格编码器提取风格，生成器生成"""
        chars = list(request.text)
        generated_images = []
        img_size = getattr(self, 'image_size', 128)  # 从checkpoint读取训练分辨率

        # 从该风格的训练数据中随机取一张作为风格参考
        style_img = self._get_style_reference(request.style_name, img_size)
        if style_img is None:
            print(f"[ModelManager] 找不到风格参考图 '{request.style_name}'，降级模拟")
            return self._generate_simulated(request)

        with torch.no_grad():
            # 提取风格向量
            style_tensor = torch.from_numpy(style_img).float().unsqueeze(0).unsqueeze(0)
            style_tensor = (style_tensor / 127.5 - 1.0).to(self.device)
            style_vec = self.style_encoder(style_tensor)

            for char in chars:
                # 用渲染方法生成骨架作为内容输入
                skeleton_arr = self._render_skeleton(char, img_size)
                skel_tensor = torch.from_numpy(skeleton_arr).float().unsqueeze(0).unsqueeze(0)
                skel_tensor = (skel_tensor / 127.5 - 1.0).to(self.device)

                # 编码 + 生成
                content_feat = self.content_encoder(skel_tensor)
                generated = self.generator(content_feat, style_vec)

                # 后处理
                img = generated.squeeze().cpu().numpy()
                img = ((img + 1) * 127.5).clip(0, 255).astype(np.uint8)
                # 放大到渲染尺寸
                if img.shape[0] < 256:
                    img = cv2.resize(img, (256, 256), interpolation=cv2.INTER_CUBIC)
                generated_images.append(img)

        # 合成完整作品
        return self._compose(generated_images, request)

    def _get_style_reference(self, style_name: str, size: int) -> np.ndarray | None:
        """从训练数据中随机取一张该风格的图片作为风格参考"""
        data_dir = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))), 'algorithm', 'data', style_name)
        if not os.path.isdir(data_dir):
            return None
        # 递归找 jpg/png
        import random
        imgs = list(Path(data_dir).rglob("*.jpg")) + list(Path(data_dir).rglob("*.png"))
        if not imgs:
            return None
        img_path = random.choice(imgs)
        # 预处理
        img = self._preprocess_for_model(str(img_path), size)
        return img

    def _preprocess_for_model(self, path: str, size: int) -> np.ndarray | None:
        """读取图片并预处理为灰度 size×size"""
        from PIL import Image as PILImage
        try:
            pil = PILImage.open(path).convert('L')
            img = np.array(pil)
            # 居中裁切+缩放
            binary = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                           cv2.THRESH_BINARY_INV, 11, 8)
            coords = cv2.findNonZero(binary)
            if coords is None:
                return None
            x, y, w, h = cv2.boundingRect(coords)
            pad = max(w, h) // 8
            x1 = max(0, x - pad); y1 = max(0, y - pad)
            x2 = min(img.shape[1], x + w + pad); y2 = min(img.shape[0], y + h + pad)
            cropped = img[y1:y2, x1:x2]
            canvas = np.ones((size, size), dtype=np.uint8) * 255
            scale = min(size * 0.85 / cropped.shape[0], size * 0.85 / cropped.shape[1])
            nw = int(cropped.shape[1] * scale); nh = int(cropped.shape[0] * scale)
            if nw < 4 or nh < 4:
                return None
            resized = cv2.resize(cropped, (nw, nh), interpolation=cv2.INTER_CUBIC)
            ox = (size - nw) // 2; oy = (size - nh) // 2
            canvas[oy:oy+nh, ox:ox+nw] = resized
            return canvas
        except Exception:
            return None

    def _render_skeleton(self, char: str, size: int) -> np.ndarray:
        """用字体渲染一个字的骨架图（作为 ContentEncoder 的输入）"""
        from PIL import Image as PILImage, ImageDraw, ImageFont
        font_path = self._find_calligraphy_font('米芾')  # 用楷体做骨架
        font_size = int(size * 0.7)
        try:
            font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()

        pil = PILImage.new('L', (size, size), 255)
        draw = ImageDraw.Draw(pil)
        bbox = draw.textbbox((0, 0), char, font=font)
        tw = bbox[2] - bbox[0]; th = bbox[3] - bbox[1]
        x = (size - tw) // 2 - bbox[0]; y = (size - th) // 2 - bbox[1]
        draw.text((x, y), char, fill=0, font=font)
        return np.array(pil, dtype=np.uint8)
    
    def _generate_simulated(self, request: GenerateRequest) -> np.ndarray:
        """
        模拟生成 - 在没有训练模型时使用
        生成带有书法风格的文字图片
        """
        from utils.style_utils import StrokeRenderer
        
        chars = list(request.text)
        renderer = StrokeRenderer()
        char_images = []
        
        # 根据风格调整生成参数
        style_params = self._get_style_params(request.style_name, request)
        
        for char in chars:
            # 生成单个字的书法效果
            char_size = 256
            img = self._render_single_char(
                char, char_size, style_params, request
            )
            char_images.append(img)
        
        # 合成完整作品
        composed = renderer.compose_work(
            char_images,
            layout=request.layout,
            char_spacing=int(request.char_spacing * 0.4),
            line_spacing=int(request.line_spacing * 0.6),
        )
        
        # 添加宣纸纹理
        if composed is not None:
            h, w = composed.shape
            paper = renderer.create_paper_texture(h, w)
            mask = composed < 200
            paper[mask] = composed[mask]
            composed = paper
            
            # 添加印章
            composed = renderer.add_seal(composed, 'bottom-right', 48)
        
        return composed if composed is not None else np.ones((512, 512), dtype=np.uint8) * 255
    
    def _render_single_char(self, char: str, size: int, 
                           style_params: dict,
                           request: GenerateRequest) -> np.ndarray:
        """
        渲染单个字符 - 使用书法字体 + 多层后处理模拟毛笔字效果
        
        关键技巧：
        1. 根据风格选择书法字体（楷体/行楷/隶书等）
        2. 多层渲染叠加模拟墨色浓淡
        3. 形态学操作模拟笔触粗细变化
        4. 方向性飞白条纹模拟枯笔
        5. 边缘腐蚀模拟毛笔不规则接触
        """
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
        
        # ---- 1. 根据风格选择字体 ----
        font_path = self._find_calligraphy_font(request.style_name)
        font_size = int(size * 0.78)
        
        try:
            font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
        except Exception:
            font = ImageFont.load_default()
        
        # ---- 2. 渲染基础文字（稍大，后续做笔触收缩）----
        canvas_size = size + 20  # 留出笔触扩散空间
        pil_img = Image.new('L', (canvas_size, canvas_size), 255)
        draw = ImageDraw.Draw(pil_img)
        
        # 居中绘制
        bbox = draw.textbbox((0, 0), char, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (canvas_size - text_w) // 2 - bbox[0]
        y = (canvas_size - text_h) // 2 - bbox[1]
        
        # 基础墨色（深黑到深灰）
        base_ink = int(15 + (1 - style_params.get('ink_variation', 0.3)) * 25)
        draw.text((x, y), char, fill=base_ink, font=font)
        
        # ---- 3. 多层叠加模拟墨色浓淡变化 ----
        # 第一层：原始字迹
        # 第二层：略微偏移、稍淡，模拟笔画的墨色浓淡层次
        ink_var = style_params.get('ink_variation', 0.3)
        if ink_var > 0.1:
            offset = max(1, int(ink_var * 2))
            second_ink = min(255, base_ink + int(ink_var * 40))
            draw.text((x + offset, y + offset), char, fill=second_ink, font=font)
        
        # ---- 4. PIL图像处理模拟毛笔质感 ----
        # 轻微模糊模拟墨水洇散（毛笔笔尖分叉效果）
        blur_radius = style_params.get('roughness', 0.2) * 1.5
        if blur_radius > 0.3:
            pil_img = pil_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        
        # 裁切回标准尺寸
        crop_offset = (canvas_size - size) // 2
        pil_img = pil_img.crop((crop_offset, crop_offset, 
                                crop_offset + size, crop_offset + size))
        
        # PIL → OpenCV
        canvas = np.array(pil_img, dtype=np.uint8)
        
        # ---- 5. 模拟墨色不均匀（颗粒感）----
        if ink_var > 0.1:
            # 生成与笔画区域相关的墨色噪声
            noise = np.random.normal(0, ink_var * 15, (size, size)).astype(np.int16)
            stroke_mask = canvas < 200
            canvas_i16 = canvas.astype(np.int16)
            canvas_i16[stroke_mask] += noise[stroke_mask]
            canvas = np.clip(canvas_i16, 0, 255).astype(np.uint8)
        
        # ---- 6. 方向性飞白效果 ----
        fw = style_params.get('flying_white', 0.0)
        if fw > 0.01:
            canvas = self._apply_flying_white(canvas, fw)
        
        # ---- 7. 毛笔边缘不规则腐蚀 ----
        roughness = style_params.get('roughness', 0.2)
        if roughness > 0.05:
            canvas = self._apply_brush_edge(canvas, roughness)
        
        # ---- 8. 起笔收笔的笔锋效果 ----
        canvas = self._apply_stroke_ends(canvas, style_params)
        
        return canvas
    
    def _apply_flying_white(self, canvas: np.ndarray, intensity: float) -> np.ndarray:
        """
        方向性飞白效果 - 模拟毛笔快速拖拽时的条纹状留白
        
        核心思路：生成水平方向的条纹噪声，只在笔画区域内生效
        """
        h, w = canvas.shape
        stroke_mask = canvas < 200
        
        if not np.any(stroke_mask):
            return canvas
        
        result = canvas.copy()
        
        # 水平方向条纹噪声（模拟毛笔行笔方向）
        stripe_width = np.random.randint(1, 4)
        num_stripes = int(intensity * h * 0.8)
        
        for _ in range(num_stripes):
            y = np.random.randint(0, h)
            # 条纹宽度随强度变化
            sw = np.random.randint(1, max(2, int(intensity * 5) + 1))
            x_start = np.random.randint(0, w // 2)
            length = np.random.randint(w // 3, w)
            x_end = min(x_start + length, w)
            
            # 在笔画区域内制造留白条纹
            stripe_region = result[y:y+sw, x_start:x_end]
            stripe_mask = stroke_mask[y:y+sw, x_start:x_end]
            
            # 部分擦除（不是完全擦除，模拟飞白的部分留白）
            erase_prob = intensity * 0.7
            erase_noise = np.random.random(stripe_region.shape) < erase_prob
            final_mask = stripe_mask & erase_noise
            
            # 飞白区域变为浅灰色而非纯白，模拟残留墨迹
            result[final_mask] = np.clip(
                result[final_mask].astype(np.int16) + 
                np.random.randint(100, 200, size=np.sum(final_mask)),
                0, 255
            ).astype(np.uint8)
        
        return result
    
    def _apply_brush_edge(self, canvas: np.ndarray, roughness: float) -> np.ndarray:
        """
        毛笔边缘不规则腐蚀 - 模拟毛笔笔毫接触纸面的不规则性
        
        使用随机形态学操作实现笔画边缘的毛糙感
        """
        # 生成随机形态学核（非对称，模拟毛笔笔毫分布）
        kernel_size = max(3, int(roughness * 7))
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        # 随机二值核（模拟不规则笔毫）
        random_kernel = np.random.random((kernel_size, kernel_size))
        random_kernel = (random_kernel < 0.6).astype(np.uint8)
        # 确保中心有值
        center = kernel_size // 2
        random_kernel[center-1:center+2, center-1:center+2] = 1
        
        # 腐蚀操作（侵蚀笔画边缘）
        eroded = cv2.erode(canvas, random_kernel, iterations=1)
        
        # 轻微膨胀（恢复大部分笔画，但边缘变毛糙）
        dilated = cv2.dilate(eroded, random_kernel, iterations=1)
        
        # 混合原图和处理后的图（roughness控制混合比例）
        blended = cv2.addWeighted(canvas, 1.0 - roughness * 0.5, 
                                   dilated, roughness * 0.5, 0)
        
        return blended
    
    def _apply_stroke_ends(self, canvas: np.ndarray, 
                           style_params: dict) -> np.ndarray:
        """
        起笔收笔笔锋效果 - 模拟毛笔起笔时的按压和收笔时的提拉
        
        通过在笔画边缘的特定位置进行渐变处理
        """
        h, w = canvas.shape
        stroke_mask = canvas < 200
        
        if not np.any(stroke_mask):
            return canvas
        
        result = canvas.copy()
        stroke_width = style_params.get('stroke_width', 2.0)
        
        # 找到笔画的边界区域
        # 使用距离变换找到笔画边缘
        dist_transform = cv2.distanceTransform(
            (255 - canvas), cv2.DIST_L2, 5
        )
        
        # 边缘区域：距离小于阈值
        edge_threshold = max(2, int(stroke_width * 1.2))
        edge_mask = (dist_transform > 0) & (dist_transform < edge_threshold)
        
        # 在边缘区域添加微妙的墨色变化（模拟笔锋）
        if np.any(edge_mask):
            # 笔锋渐变：边缘处墨色略浅
            edge_darkening = np.ones_like(result, dtype=np.float32)
            # 距离越近边缘，墨色越淡（模拟笔锋收束）
            edge_darkening[edge_mask] = 0.7 + 0.3 * (
                dist_transform[edge_mask] / edge_threshold
            )
            
            # 只在笔画区域应用
            ink_area = result < 200
            apply_mask = ink_area & edge_mask
            
            result_float = result.astype(np.float32)
            result_float[apply_mask] *= edge_darkening[apply_mask]
            result = np.clip(result_float, 0, 255).astype(np.uint8)
        
        return result
    
    def _get_style_params(self, style_name: str, request: GenerateRequest) -> dict:
        """根据风格名称和请求参数生成渲染参数"""
        base = {
            'stroke_width': 2.5,
            'ink_variation': 0.3,
            'flying_white': 0.0,
            'roughness': 0.25,
        }
        
        # 不同风格的默认参数
        style_defaults = {
            # 行书：沉着痛快，八面出锋
            "米芾":   {'stroke_width': 2.8, 'ink_variation': 0.5, 'roughness': 0.3, 'flying_white': 0.15},
            # 楷书：圆润秀美
            "赵孟頫": {'stroke_width': 2.6, 'ink_variation': 0.35, 'roughness': 0.18},
            # 楷书：清朗秀劲
            "褚遂良": {'stroke_width': 2.3, 'ink_variation': 0.3, 'roughness': 0.15},
            # 隶书：古朴厚重
            "乙瑛碑": {'stroke_width': 3.5, 'ink_variation': 0.25, 'roughness': 0.35},
            # 篆书：圆转匀称
            "邓石如": {'stroke_width': 2.0, 'ink_variation': 0.2, 'roughness': 0.08},
            # 草书：狂放飘逸
            "怀素":   {'stroke_width': 2.5, 'ink_variation': 0.7, 'roughness': 0.45, 'flying_white': 0.25},
        }
        
        if style_name in style_defaults:
            base.update(style_defaults[style_name])
        
        # 用户参数覆盖
        base['stroke_width'] *= (request.brush_weight / 50)
        base['ink_variation'] = min(1.0, base['ink_variation'] * (request.ink_density / 50))
        base['flying_white'] = request.flying_white / 100
        
        return base
    
    def _find_calligraphy_font(self, style_name: str = "赵孟頫") -> Optional[str]:
        """
        根据书法风格选择最合适的中文字体
        
        风格 → 字体映射：
        - 颜真卿/柳公权/欧阳询（楷书）→ 华文楷体 STKAITI.TTF
        - 赵孟頫/王羲之（行楷/行书）→ 华文行楷 STXINGKA.TTF
        - 苏轼（行书，更潇洒）→ 华文行楷 STXINGKA.TTF
        """
        if sys.platform != 'win32':
            return self._find_chinese_font()
        
        font_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
        
        # 风格到字体的映射
        style_font_map = {
            "米芾":   "STXINGKA.TTF",   # 行书 → 行楷体
            "赵孟頫": "STKAITI.TTF",    # 楷书 → 楷体
            "褚遂良": "STKAITI.TTF",    # 楷书 → 楷体
            "乙瑛碑": "STLITI.TTF",     # 隶书 → 隶书体
            "邓石如": "STZHONGS.TTF",   # 篆书 → 中宋（近似）
            "怀素":   "STXINGKA.TTF",   # 草书 → 行楷体
        }
        
        # 优先使用映射的字体
        target_font = style_font_map.get(style_name, "STKAITI.TTF")
        fp = os.path.join(font_dir, target_font)
        if os.path.exists(fp):
            return fp
        
        # 降级：尝试其他书法字体
        fallback_fonts = [
            "STKAITI.TTF",    # 华文楷体
            "STXINGKA.TTF",   # 华文行楷
            "STLITI.TTF",     # 华文隶书
            "STZHONGS.TTF",   # 华文中宋
            "STFANGSO.TTF",   # 华文仿宋
            "simhei.ttf",     # 黑体
        ]
        for fn in fallback_fonts:
            fp = os.path.join(font_dir, fn)
            if os.path.exists(fp):
                return fp
        
        return None
    
    def _find_chinese_font(self) -> Optional[str]:
        """查找系统中文字体（通用备选）"""
        if sys.platform == 'win32':
            font_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
            font_names = ['simhei.ttf', 'simsun.ttc', 'msyh.ttc', 'msyhbd.ttc',
                         'STKAITI.TTF', 'STXINGKA.TTF', 'SIMLI.TTF', 'SIMFANG.TTF']
            
            for fn in font_names:
                fp = os.path.join(font_dir, fn)
                if os.path.exists(fp):
                    return fp
        
        return None
    
    def _get_skeleton(self, char: str) -> torch.Tensor:
        """获取字符骨架"""
        if char in self.skeleton_cache:
            return self.skeleton_cache[char]
        
        # 生成空白骨架占位
        skeleton = torch.zeros(1, 1, 256, 256, device=self.device)
        return skeleton
    
    def _get_style_vector(self, style_name: str) -> torch.Tensor:
        """获取风格向量"""
        # 从预计算的风格库获取
        style_vec = torch.randn(1, 128, device=self.device)
        return F.normalize(style_vec, dim=1)
    
    def _compose(self, char_images: list, request: GenerateRequest) -> np.ndarray:
        """合成完整作品"""
        from utils.style_utils import StrokeRenderer
        renderer = StrokeRenderer()
        return renderer.compose_work(
            char_images, layout=request.layout,
            char_spacing=int(request.char_spacing * 0.4),
            line_spacing=int(request.line_spacing * 0.6),
        )


# ============ 全局模型管理器 ============

model_manager = ModelManager()


# ============ API路由 ============

@app.get("/")
async def root():
    """返回前端页面"""
    return FileResponse(os.path.join(_PROJECT_DIR, "index.html"))


@app.get("/api/styles")
async def get_styles():
    """获取所有可用风格"""
    styles = []
    for name, info in model_manager.style_library.items():
        styles.append({
            "name": name,
            "display_name": info['display'],
            "script_type": info['script'],
            "era": info['era'],
            "description": info['desc'],
        })
    return {"styles": styles}


@app.post("/api/generate")
async def generate_calligraphy(request: GenerateRequest):
    """
    生成书法作品
    
    接收文本、风格、布局参数，返回生成的书法图片
    """
    try:
        image_b64, gen_time = model_manager.generate(request)
        return GenerateResponse(
            success=True,
            image_base64=image_b64,
            generation_time=gen_time,
            style_used=request.style_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload_style")
async def upload_custom_style(
    file: UploadFile = File(...),
    style_name: str = Form(...)
):
    """
    上传自定义风格
    
    上传书法样本，系统自动提取风格特征
    """
    try:
        # 保存上传的样本
        upload_dir = Path("data/custom_styles")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / f"{style_name}_{int(time.time())}.png"
        content = await file.read()
        
        with open(file_path, 'wb') as f:
            f.write(content)
        
        # 提取风格特征（如果有模型）
        if model_manager.models_loaded and model_manager.style_encoder:
            img = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_GRAYSCALE)
            if img is not None:
                # 预处理并提取风格
                img_resized = cv2.resize(img, (256, 256))
                img_tensor = torch.from_numpy(img_resized).float().unsqueeze(0).unsqueeze(0)
                img_tensor = (img_tensor - 127.5) / 127.5
                
                with torch.no_grad():
                    style_vec = model_manager.style_encoder(img_tensor.to(model_manager.device))
                
                # 注册新风格
                model_manager.style_library[style_name] = {
                    'display': f'自定义-{style_name}',
                    'script': '自定义',
                    'era': '当代',
                    'desc': '用户上传的自定义风格',
                }
        
        return {
            "success": True,
            "style_name": style_name,
            "message": f"风格 '{style_name}' 上传成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """系统健康检查"""
    return {
        "status": "healthy",
        "models_loaded": model_manager.models_loaded,
        "device": str(model_manager.device),
        "available_styles": list(model_manager.style_library.keys()),
    }


# ============ 静态文件服务 ============

# 挂载静态资源目录 - 使用项目根目录
PROJECT_ROOT = _PROJECT_DIR
assets_dir = os.path.join(PROJECT_ROOT, 'assets')
print(f"[静态文件] 项目根目录: {PROJECT_ROOT}")
print(f"[静态文件] 资源目录: {assets_dir}")
print(f"[静态文件] 资源目录存在: {os.path.exists(assets_dir)}")

if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    print("[静态文件] /assets 挂载成功")
else:
    print(f"[警告] 静态资源目录不存在: {assets_dir}")


# ============ 启动入口 ============

if __name__ == '__main__':
    print("=" * 50)
    print("  春意墨生 - AI书法创作系统")
    print("  API服务启动中...")
    print("=" * 50)
    
    # 尝试加载模型
    checkpoint_dir = os.path.join(PROJECT_ROOT, 'checkpoints')
    if os.path.exists(checkpoint_dir):
        model_manager.load_models(checkpoint_dir)
    
    # 启动服务
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info"
    )

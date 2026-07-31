# -*- coding: utf-8 -*-
"""
用字体渲染生成高质量书法训练数据
- 白底黑字、标准单字、尺寸统一
- 支持多种书法字体（华文楷体、华文行楷等）
- 自动加毛笔效果（飞白、边缘毛糙、笔锋）

用法: python algorithm/data/generate_synthetic.py
"""
import os, sys, io, time
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import random

DATA_DIR = Path(__file__).parent
TARGET_SIZE = 256  # 高分辨率

# 常用汉字（覆盖3000+常用字）
CHARS = (
    "天地人和风花雪月山水云龙凤鹤松竹梅兰菊荷柳桃李杏杨"
    "春夏秋冬东西南北金木火土日月星辰江河海湖溪泉潭瀑"
    "仁义礼智信忠孝廉耻勇毅刚正和平安宁静远深高明通达"
    "文章诗词书画墨笔砚纸色青红白黑紫碧苍翠丹朱金玉"
    "上下左右前后大小多少长短宽窄远近高低深浅轻重缓急"
    "一二三四五六七八九十百千万亿零"
    "王侯将相国城门道路桥船车马鸟兽鱼虫"
    "福禄寿喜吉祥如意瑞泰康宁富贵荣华"
    "道德经书礼乐春秋永平年中正大光明元亨利贞乾坤"
    "心性情怀志意思念感悟知道理法术势"
    "清浊浓淡干湿粗细刚柔方圆曲直"
    "动静行止起落收放开合张弛进退"
    "飞舞飘洒挥洒涂抹勾勒点画"
    "生老病死苦乐悲欢离合"
    "字字体书信文学史艺术哲学宗教政治经济社会文化教育科学"
    "父母兄弟姊妹夫妻子女家族亲朋友好师长同学邻居"
    "北京上海广州深圳天津重庆成都武汉南京杭州西安苏州"
    "龙头凤尾虎豹鹰犬牛羊猪鸡鹤燕雀梅兰菊竹荷松柏"
    "琴棋书画诗词歌赋曲乐舞剑弓箭枪刀剑斧钺"
    "锅碗瓢盆桌椅板凳门窗墙壁柱梁瓦砖石砂泥"
    "红橙黄绿蓝靛紫黑白灰金银铜铁锡"
    "江河湖海溪泉瀑布池潭沼泽港湾海峡群岛"
    "雷雨雪霜露冰雾霞虹风云雷电阴晴朗"
    "晨午暮夜黎明黄昏除夕元旦春节清明端午中秋重阳"
    "衣帽鞋袜裙袍巾带扣针线布丝绸棉麻"
    "酸甜苦辣咸淡香臭腥膻滋味鲜美醇厚浓郁清淡"
    "真假善恶美丑明暗新旧快慢高低强弱软硬轻重"
    "天地玄黄宇宙洪荒日月盈昃辰宿列张寒来暑往秋收冬藏"
    "闰余成岁律吕调阳云腾致雨露结为霜金生丽水玉出昆冈"
    "剑号巨阙珠称夜光果珍李柰菜重芥姜海咸河淡鳞潜羽翔"
    "龙师火帝鸟官人皇始制文字乃服衣裳推位让国有虞陶唐"
    "吊民伐罪周发殷汤坐朝问道垂拱平章爱育黎首臣伏戎羌"
    "遐迩壹体率宾归王鸣凤在竹白驹食场化被草木赖及万方"
    "盖此身发四大五常恭惟鞠养岂敢毁伤女慕贞洁男效才良"
    "知过必改得能莫忘罔谈彼短靡恃己长信使可覆器欲难量"
    "墨悲丝染诗赞羔羊景行维贤克念作圣德建名立形端表正"
    "空谷传声虚堂习听祸因恶积福缘善庆尺璧非宝寸阴是竞"
    "资父事君曰严与敬孝当竭力忠则尽命临深履薄夙兴温凊"
    "似兰斯馨如松之盛川流不息渊澄取映容止若思言辞安定"
    "笃初诚美慎终宜令荣业所基籍甚无竟学优登仕摄职从政"
    "存以甘棠去而益咏乐殊贵贱礼别尊卑上和下睦夫唱妇随"
    "孔怀兄弟同气连枝交友投分切磨箴规仁慈隐恻造次弗离"
    "节义廉退颠沛匪亏聆音察理鉴貌辨色贻厥嘉猷勉其祗植"
    "省躬讥诫宠增抗极殆辱近耻林皋幸即两疏见机解组谁逼"
    "索居闲处沉默寂寥求古寻论散虑逍遥欣奏累遣戚谢欢招"
    "渠荷的历园莽抽条枇杷晚翠梧桐蚤凋陈根委翳落叶飘摇"
    "游鲲独运凌摩绛霄耽读玩市寓目囊箱易輶攸畏属耳垣墙"
    "具膳餐饭适口充肠饱饫烹宰饥厌糟糠亲戚故旧老少异粮"
    "妾御绩纺侍巾帷房纨扇圆洁银烛炜煌昼眠夕寐蓝笋象床"
    "弦歌酒宴接杯举觞矫手顿足悦豫且康嫡后嗣续祭祀烝尝"
    "稽颡再拜悚惧恐惶笺牒简要顾答审详骸垢想浴执热愿凉"
    "驴骡犊特骇跃超骧诛斩贼盗捕获叛亡布射辽丸嵇琴阮啸"
    "恬笔伦纸钧巧任钓释纷利俗并皆佳妙毛施淑姿工颦妍笑"
    "年矢每催曦晖朗曜璇玑悬斡晦魄环照指薪修祜永绥吉劭"
    "矩步引领俯仰廊庙束带矜庄徘徊瞻眺孤陋寡闻愚蒙等诮"
    "谓语助者焉哉乎也"
)


def find_font(style_name: str) -> str | None:
    """查找系统中可用的书法字体"""
    import subprocess
    # Windows 字体目录
    font_dir = Path("C:/Windows/Fonts")
    
    # 风格到字体文件名映射
    font_map = {
        "楷书": ["simkai.ttf", "STKAITI.TTF", "stkaiti.ttf", "kaiu.ttf"],
        "行书": ["STXINGKA.TTF", "stxingka.ttf", "simfang.ttf", "FZSTK.TTF"],
        "隶书": ["SIMLI.TTF", "simli.ttf", "STLITI.TTF", "stliti.ttf"],
        "篆书": ["STZHONGS.TTF", "stzhongs.ttf", "SIMSUN.TTF", "simsun.ttc"],
        "草书": ["simkai.ttf", "STKAITI.TTF", "stkaiti.ttf"],  # 草书用楷体近似
    }
    
    candidates = font_map.get(style_name, font_map["楷书"])
    for fname in candidates:
        # 搜索字体文件
        for p in font_dir.rglob(fname.lower()):
            return str(p)
        for p in font_dir.rglob(fname.upper()):
            return str(p)
        # 精确匹配
        exact = font_dir / fname
        if exact.exists():
            return str(exact)
    
    # 回退：尝试用 fc-list 或列举
    print(f"  [WARN] 未找到 '{style_name}' 字体，尝试回退...")
    for p in font_dir.glob("*.ttf"):
        name_lower = p.stem.lower()
        if any(k in name_lower for k in ["kai", "xing", "li", "zhong"]):
            print(f"  [INFO] 使用回退字体: {p.name}")
            return str(p)
    
    # 最终回退
    return str(font_dir / "simkai.ttf") if (font_dir / "simkai.ttf").exists() else None


def render_char(char: str, font: ImageFont.FreeTypeFont, size: int = 256) -> Image.Image:
    """渲染单个汉字（白底黑字）"""
    canvas = Image.new("L", (size, size), 255)
    draw = ImageDraw.Draw(canvas)
    
    # 计算文字位置（居中）
    bbox = draw.textbbox((0, 0), char, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (size - tw) // 2 - bbox[0]
    y = (size - th) // 2 - bbox[1]
    
    draw.text((x, y), char, fill=0, font=font)
    return canvas


def add_ink_variation(img: Image.Image, intensity: float = 0.3) -> Image.Image:
    """添加墨色浓淡变化（模拟毛笔墨迹深浅不一）"""
    arr = np.array(img).astype(np.float32)
    
    # 创建不均匀的墨色纹理
    h, w = arr.shape
    # 多尺度噪声混合
    noise = np.zeros_like(arr)
    for scale in [8, 16, 32, 64]:
        small = np.random.randn(h // scale + 1, w // scale + 1) * scale * 0.5
        # 双线性插值放大
        from PIL import Image as PILImage
        noise_small = PILImage.fromarray(small.astype(np.float32))
        noise_up = noise_small.resize((w, h), PILImage.BILINEAR)
        noise += np.array(noise_up)
    
    noise = (noise - noise.mean()) / (noise.std() + 1e-6) * 20 * intensity
    
    # 只在笔画区域添加变化
    mask = arr < 200  # 笔画区域
    arr[mask] = arr[mask] + noise[mask]
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    
    return Image.fromarray(arr)


def add_flying_white(img: Image.Image, probability: float = 0.3) -> Image.Image:
    """添加飞白效果（毛笔快速拖拽的枯笔留白）"""
    if random.random() > probability:
        return img
    
    arr = np.array(img)
    h, w = arr.shape
    mask = arr < 200  # 笔画区域
    
    if mask.sum() < 50:
        return img
    
    # 找到笔画的主方向（水平或垂直）
    row_density = mask.sum(axis=1)
    col_density = mask.sum(axis=0)
    
    if col_density.max() > row_density.max():
        # 水平笔画多 → 水平飞白
        num_lines = random.randint(3, 12)
        for _ in range(num_lines):
            y = random.randint(0, h - 1)
            thickness = random.randint(1, 3)
            length = random.randint(w // 4, w)
            start_x = random.randint(0, w - length)
            alpha = random.uniform(0.3, 0.8)
            
            for dy in range(thickness):
                yy = min(y + dy, h - 1)
                for xx in range(start_x, start_x + length):
                    if mask[yy, xx]:
                        arr[yy, xx] = min(255, int(arr[yy, xx] + 255 * alpha))
    else:
        # 垂直笔画多 → 垂直飞白
        num_lines = random.randint(3, 12)
        for _ in range(num_lines):
            x = random.randint(0, w - 1)
            thickness = random.randint(1, 3)
            length = random.randint(h // 4, h)
            start_y = random.randint(0, h - length)
            alpha = random.uniform(0.3, 0.8)
            
            for dx in range(thickness):
                xx = min(x + dx, w - 1)
                for yy in range(start_y, start_y + length):
                    if mask[yy, xx]:
                        arr[yy, xx] = min(255, int(arr[yy, xx] + 255 * alpha))
    
    return Image.fromarray(arr)


def add_brush_edge(img: Image.Image, strength: float = 0.5) -> Image.Image:
    """添加毛笔边缘毛糙效果"""
    # 轻微模糊
    img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 0.8)))
    
    # 随机添加小噪点到笔画边缘
    arr = np.array(img)
    h, w = arr.shape
    
    # 检测边缘
    from PIL import Image as PILImage
    gray = PILImage.fromarray(arr)
    edge = gray.filter(ImageFilter.FIND_EDGES)
    edge_arr = np.array(edge)
    
    # 边缘区域加噪
    edge_mask = edge_arr > 30
    noise = np.random.randint(-15, 15, (h, w)).astype(np.int16)
    
    arr_f = arr.astype(np.int16)
    arr_f[edge_mask] = np.clip(arr_f[edge_mask] + (noise[edge_mask] * strength).astype(np.int16), 0, 255)
    
    return Image.fromarray(arr_f.astype(np.uint8))


def add_stroke_ends(img: Image.Image) -> Image.Image:
    """添加起笔收笔的笔锋效果（不依赖 scipy）"""
    arr = np.array(img).astype(np.float32)
    h, w = arr.shape
    
    # 简单距离近似：多次腐蚀
    binary = (arr < 128).astype(np.uint8)
    if binary.sum() < 10:
        return img
    
    # 用模糊近似距离场
    from PIL import Image as PILImage
    pil = PILImage.fromarray(binary.astype(np.uint8) * 255)
    blurred = pil.filter(ImageFilter.GaussianBlur(radius=2))
    dist_approx = np.array(blurred).astype(np.float32) / 255.0
    
    max_dist = dist_approx.max()
    if max_dist < 0.1:
        return img
    
    # 渐变：边缘变淡
    fade = np.clip(dist_approx / max_dist * 1.5, 0, 1)
    result = arr * fade
    result = np.clip(result, 0, 255).astype(np.uint8)
    
    return Image.fromarray(result)


def augment_image(img: Image.Image, level: str = "medium") -> Image.Image:
    """数据增强"""
    arr = np.array(img)
    h, w = arr.shape
    
    if level == "heavy":
        # 重度增强
        ops = ["rotate", "perspective", "elastic", "scale"]
    else:
        ops = ["rotate", "scale"]
    
    random.shuffle(ops)
    
    for op in ops[:2]:
        if op == "rotate":
            angle = random.uniform(-6, 6)
            img = img.rotate(angle, fillcolor=255, expand=False)
        elif op == "scale":
            scale = random.uniform(0.85, 0.98)
            new_w = int(w * scale)
            new_h = int(h * scale)
            img_small = img.resize((new_w, new_h), Image.LANCZOS)
            canvas = Image.new("L", (w, h), 255)
            ox = (w - new_w) // 2
            oy = (h - new_h) // 2
            canvas.paste(img_small, (ox, oy))
            img = canvas
        elif op == "elastic":
            # 简单弹性形变
            from PIL import Image as PILImage
            dx_map = PILImage.fromarray(np.random.randint(-3, 3, (h, w)).astype(np.float32))
            dy_map = PILImage.fromarray(np.random.randint(-3, 3, (h, w)).astype(np.float32))
            img = img.transform((w, h), Image.AFFINE,
                               (1, random.uniform(-0.02, 0.02), random.uniform(-2, 2),
                                random.uniform(-0.02, 0.02), 1, random.uniform(-2, 2)),
                               fillcolor=255)
        elif op == "perspective":
            img = img.transform((w, h), Image.PERSPECTIVE,
                               (random.uniform(-0.02, 0.02), random.uniform(-0.02, 0.02),
                                random.uniform(-0.02, 0.02), random.uniform(-0.02, 0.02),
                                random.uniform(-0.02, 0.02), random.uniform(-0.02, 0.02),
                                random.uniform(-0.02, 0.02), random.uniform(-0.02, 0.02)),
                               fillcolor=255)
    
    # 随机亮度
    if random.random() > 0.5:
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(random.uniform(0.8, 1.0))
    
    # 随机对比度
    if random.random() > 0.5:
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(random.uniform(0.9, 1.2))
    
    return img


def generate_training_data(
    style_name: str,
    script_name: str,
    font_path: str,
    num_chars: int = 500,
    aug_per_char: int = 4,
    target_size: int = 128,
):
    """生成一组训练数据"""
    output_dir = DATA_DIR / style_name / script_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 清空旧文件
    for f in output_dir.glob("*.jpg"):
        f.unlink()
    
    print(f"  字体: {font_path}")
    font = ImageFont.truetype(font_path, int(target_size * 0.75))
    
    # 选取汉字
    char_list = list(CHARS)
    random.shuffle(char_list)
    if len(char_list) > num_chars:
        char_list = char_list[:num_chars]
    
    count = 0
    for i, char in enumerate(char_list):
        # 渲染基础字
        base = render_char(char, font, target_size)
        
        # 保存原始字
        base.save(output_dir / f"raw_{i:04d}.jpg", quality=95)
        count += 1
        
        # 生成增强版本
        for j in range(aug_per_char):
            aug = base.copy()
            
            # 随机组合毛笔效果
            aug = add_ink_variation(aug, random.uniform(0.2, 0.6))
            aug = add_brush_edge(aug, random.uniform(0.3, 0.8))
            if random.random() > 0.5:
                aug = add_flying_white(aug, probability=0.4)
            aug = augment_image(aug, level="medium" if j < aug_per_char // 2 else "heavy")
            
            aug.save(output_dir / f"aug_{i:04d}_{j:02d}.jpg", quality=95)
            count += 1
        
        if (i + 1) % 50 == 0:
            print(f"    已生成 {i+1}/{len(char_list)} 字, 总计 {count} 张")
    
    print(f"  完成: {count} 张图片 ({len(char_list)} 原始 + {count - len(char_list)} 增强)")
    return count


def main():
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    print("=" * 60)
    print("  书法训练数据生成 - 字体渲染 + 毛笔效果")
    print("=" * 60)

    # 6 种风格配置
    STYLES = [
        ("米芾",   "行书", "楷书"),   # 行书用行楷字体近似
        ("赵孟頫", "楷书", "楷书"),
        ("褚遂良", "楷书", "楷书"),
        ("乙瑛碑", "隶书", "隶书"),
        ("邓石如", "篆书", "篆书"),
        ("怀素",   "草书", "楷书"),   # 草书用楷体近似
    ]

    total = 0
    for style_name, script_name, font_style in STYLES:
        print(f"\n{'─' * 50}")
        print(f"[{style_name}] {script_name}")
        
        font_path = find_font(font_style)
        if font_path is None:
            print(f"  [ERROR] 找不到字体，跳过")
            continue
        
        count = generate_training_data(
            style_name=style_name,
            script_name=script_name,
            font_path=font_path,
            num_chars=60,          # 少量高质量字
            aug_per_char=3,        # 适度增强
            target_size=128,
        )
        total += count
    
    print(f"\n{'=' * 60}")
    print(f"  全部完成! 共 {total} 张训练图片")
    print(f"{'=' * 60}")

    # 质量抽检
    print("\n质量抽检:")
    for style_name, _, _ in STYLES:
        style_dir = DATA_DIR / style_name
        if not style_dir.exists():
            continue
        for sub in style_dir.iterdir():
            if not sub.is_dir():
                continue
            imgs = list(sub.glob("*.jpg"))
            if not imgs:
                continue
            # 抽样3张
            samples = random.sample(imgs, min(3, len(imgs)))
            print(f"\n  {style_name}/{sub.name} ({len(imgs)}张):")
            for f in samples:
                im = np.array(Image.open(f).convert("L"))
                bright = (im > 200).sum() / im.size
                dark = (im < 60).sum() / im.size
                print(f"    {f.name}: 白{bright:.0%} 黑{dark:.0%}")


if __name__ == "__main__":
    main()

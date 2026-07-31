// slide-02.js — 风格编码器 + 内容编码器
const pptxgen = require("pptxgenjs");

const slideConfig = { type: 'content', index: 2, title: '风格编码器 & 内容编码器' };

function createSlide(pres, theme) {
  const slide = pres.addSlide();
  slide.background = { color: "F8F6F2" };

  // 顶部装饰条
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.08,
    fill: { color: "780000" }, line: { color: "780000" }
  });

  // 左侧蓝色竖条
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: 0.18, w: 0.07, h: 0.55,
    fill: { color: "003049" }, line: { color: "003049" }
  });

  slide.addText("算法设计", {
    x: 0.58, y: 0.15, w: 5, h: 0.45,
    fontSize: 28, fontFace: "Microsoft YaHei",
    color: "003049", bold: true, align: "left", valign: "middle", margin: 0
  });
  slide.addText("风格编码器 & 内容编码器", {
    x: 0.58, y: 0.58, w: 6, h: 0.28,
    fontSize: 14, fontFace: "Microsoft YaHei",
    color: "669bbc", bold: false, align: "left", margin: 0
  });
  slide.addText("南京信息工程大学", {
    x: 7, y: 0.2, w: 2.8, h: 0.35,
    fontSize: 11, fontFace: "Microsoft YaHei",
    color: "780000", bold: false, align: "right", margin: 0
  });

  // ===== 左侧：风格编码器 =====
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.35, y: 1.0, w: 4.4, h: 4.3,
    fill: { color: "FFFFFF" }, line: { color: "E0D9CF", pt: 1 }, rectRadius: 0.1
  });

  // 左侧标题栏
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.35, y: 1.0, w: 4.4, h: 0.45,
    fill: { color: "003049" }, line: { color: "003049" }, rectRadius: 0.1
  });
  slide.addText("StyleEncoder  风格编码器", {
    x: 0.45, y: 1.0, w: 4.2, h: 0.45,
    fontSize: 13, fontFace: "Microsoft YaHei",
    color: "FFFFFF", bold: true, align: "left", valign: "middle", margin: 0
  });

  // 输入输出标签
  slide.addText("输入: 书法灰度图  (B, 1, H, W)", {
    x: 0.5, y: 1.52, w: 4.1, h: 0.28,
    fontSize: 10, fontFace: "Microsoft YaHei",
    color: "003049", bold: false, align: "left", margin: 0
  });
  slide.addText("输出: 风格隐向量  (B, 128)  — L2 归一化", {
    x: 0.5, y: 1.8, w: 4.1, h: 0.28,
    fontSize: 10, fontFace: "Microsoft YaHei",
    color: "780000", bold: false, align: "left", margin: 0
  });

  // 网络结构步骤
  const styleSteps = [
    { label: "5层卷积下采样", desc: "Conv → InstanceNorm → LeakyReLU  ×5\n256→128→64→32→16→8" },
    { label: "自注意力模块", desc: "SelfAttention (SAGAN风格)\n增强全局风格特征提取" },
    { label: "全局平均池化", desc: "AdaptiveAvgPool2d(1)\n聚合空间特征" },
    { label: "全连接层", desc: "FC: 512→256→ReLU→128\n+ L2 归一化输出" },
  ];
  styleSteps.forEach((s, i) => {
    const y = 2.15 + i * 0.58;
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.5, y: y, w: 0.9, h: 0.42,
      fill: { color: "003049" }, line: { color: "003049" }, rectRadius: 0.05
    });
    slide.addText(`0${i + 1}`, {
      x: 0.5, y: y, w: 0.9, h: 0.42,
      fontSize: 14, fontFace: "Arial",
      color: "FFFFFF", bold: true, align: "center", valign: "middle"
    });
    slide.addText(s.label, {
      x: 1.52, y: y, w: 3.1, h: 0.22,
      fontSize: 10.5, fontFace: "Microsoft YaHei",
      color: "003049", bold: true, align: "left", margin: 0
    });
    slide.addText(s.desc, {
      x: 1.52, y: y + 0.2, w: 3.1, h: 0.28,
      fontSize: 8.5, fontFace: "Microsoft YaHei",
      color: "555555", bold: false, align: "left", margin: 0
    });
  });

  // 风格混合能力提示
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 4.5, w: 4.15, h: 0.62,
    fill: { color: "fdf0d5" }, line: { color: "e09f3e", pt: 1 }, rectRadius: 0.08
  });
  slide.addText("✦  支持风格插值：interpolate(s1, s2, α)\n✦  支持多风格混合：mix(styles, weights)", {
    x: 0.62, y: 4.5, w: 3.95, h: 0.62,
    fontSize: 9, fontFace: "Microsoft YaHei",
    color: "780000", bold: false, align: "left", valign: "middle", margin: 0
  });

  // ===== 右侧：内容编码器 =====
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.25, y: 1.0, w: 4.4, h: 4.3,
    fill: { color: "FFFFFF" }, line: { color: "E0D9CF", pt: 1 }, rectRadius: 0.1
  });

  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.25, y: 1.0, w: 4.4, h: 0.45,
    fill: { color: "c1121f" }, line: { color: "c1121f" }, rectRadius: 0.1
  });
  slide.addText("ContentEncoder  内容编码器", {
    x: 5.35, y: 1.0, w: 4.2, h: 0.45,
    fontSize: 13, fontFace: "Microsoft YaHei",
    color: "FFFFFF", bold: true, align: "left", valign: "middle", margin: 0
  });

  slide.addText("输入: 字形骨架图  (B, 1, H, W)", {
    x: 5.38, y: 1.52, w: 4.1, h: 0.28,
    fontSize: 10, fontFace: "Microsoft YaHei",
    color: "003049", bold: false, align: "left", margin: 0
  });
  slide.addText("输出: 内容特征图  (B, 256, H', W')", {
    x: 5.38, y: 1.8, w: 4.1, h: 0.28,
    fontSize: 10, fontFace: "Microsoft YaHei",
    color: "780000", bold: false, align: "left", margin: 0
  });

  const contentSteps = [
    { label: "4层卷积下采样", desc: "Conv → InstanceNorm → LeakyReLU  ×4\n保留结构空间信息" },
    { label: "特征精炼层", desc: "Conv→IN→LeakyReLU（保持空间尺寸）\n256通道语义特征" },
    { label: "骨架预处理", desc: "Zhang-Suen 细化算法\n提取纯笔画骨架（二值图）" },
  ];
  contentSteps.forEach((s, i) => {
    const y = 2.15 + i * 0.62;
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 5.4, y: y, w: 0.9, h: 0.42,
      fill: { color: "c1121f" }, line: { color: "c1121f" }, rectRadius: 0.05
    });
    slide.addText(`0${i + 1}`, {
      x: 5.4, y: y, w: 0.9, h: 0.42,
      fontSize: 14, fontFace: "Arial",
      color: "FFFFFF", bold: true, align: "center", valign: "middle"
    });
    slide.addText(s.label, {
      x: 6.42, y: y, w: 3.1, h: 0.22,
      fontSize: 10.5, fontFace: "Microsoft YaHei",
      color: "003049", bold: true, align: "left", margin: 0
    });
    slide.addText(s.desc, {
      x: 6.42, y: y + 0.2, w: 3.1, h: 0.28,
      fontSize: 8.5, fontFace: "Microsoft YaHei",
      color: "555555", bold: false, align: "left", margin: 0
    });
  });

  // SelfAttention 说明卡（右侧下方）
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.38, y: 4.0, w: 4.15, h: 1.15,
    fill: { color: "EEF3F7" }, line: { color: "669bbc", pt: 1 }, rectRadius: 0.08
  });
  slide.addText("自注意力模块 (SelfAttention)", {
    x: 5.5, y: 4.04, w: 3.9, h: 0.3,
    fontSize: 10.5, fontFace: "Microsoft YaHei",
    color: "003049", bold: true, align: "left", margin: 0
  });
  slide.addText("Q, K = Conv1×1(C→C/8)  |  V = Conv1×1(C→C)\nAttn = Softmax(Q·Kᵀ)\nOutput = γ × V·Attn + x   (γ可学习, 初始为0)", {
    x: 5.5, y: 4.35, w: 3.95, h: 0.75,
    fontSize: 9, fontFace: "Consolas",
    color: "003049", bold: false, align: "left", valign: "top", margin: 0
  });

  // 页码
  slide.addShape(pres.shapes.OVAL, {
    x: 9.3, y: 5.1, w: 0.4, h: 0.4,
    fill: { color: "780000" }
  });
  slide.addText("2", {
    x: 9.3, y: 5.1, w: 0.4, h: 0.4,
    fontSize: 12, fontFace: "Arial",
    color: "FFFFFF", bold: true, align: "center", valign: "middle"
  });

  return slide;
}

if (require.main === module) {
  const pres = new pptxgen();
  pres.layout = 'LAYOUT_16x9';
  const theme = { primary: "780000", secondary: "c1121f", accent: "003049", light: "669bbc", bg: "F8F6F2" };
  createSlide(pres, theme);
  pres.writeFile({ fileName: "slides/slide-02-preview.pptx" });
}

module.exports = { createSlide, slideConfig };

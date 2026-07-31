// slide-03.js — 双分支生成器（Generator）
const pptxgen = require("pptxgenjs");

const slideConfig = { type: 'content', index: 3, title: '双分支生成器' };

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
  slide.addText("双分支生成器 — Generator", {
    x: 0.58, y: 0.58, w: 7, h: 0.28,
    fontSize: 14, fontFace: "Microsoft YaHei",
    color: "669bbc", bold: false, align: "left", margin: 0
  });
  slide.addText("南京信息工程大学", {
    x: 7, y: 0.2, w: 2.8, h: 0.35,
    fontSize: 11, fontFace: "Microsoft YaHei",
    color: "780000", bold: false, align: "right", margin: 0
  });

  // ===== 核心创新点 =====
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.35, y: 0.98, w: 9.3, h: 0.52,
    fill: { color: "780000" }, line: { color: "780000" }, rectRadius: 0.08
  });
  slide.addText("核心创新：双分支架构  —  内容分支（Structure）保持笔画结构 × 风格分支（Style）注入书法风格", {
    x: 0.5, y: 0.98, w: 9.1, h: 0.52,
    fontSize: 11.5, fontFace: "Microsoft YaHei",
    color: "FFFFFF", bold: true, align: "center", valign: "middle", margin: 0
  });

  // ===== 整体架构大卡 =====
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.35, y: 1.58, w: 9.3, h: 3.4,
    fill: { color: "FFFFFF" }, line: { color: "E0D9CF", pt: 1 }, rectRadius: 0.1
  });

  // — 左侧：内容分支 —
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.55, y: 1.72, w: 3.6, h: 1.18,
    fill: { color: "EEF3F7" }, line: { color: "669bbc", pt: 1.5 }, rectRadius: 0.08
  });
  slide.addText("内容分支  Content Branch", {
    x: 0.65, y: 1.76, w: 3.4, h: 0.32,
    fontSize: 11.5, fontFace: "Microsoft YaHei",
    color: "003049", bold: true, align: "left", margin: 0
  });
  slide.addText("输入: ContentEncoder 特征图  (B, 256, H, W)\n4层上采样 + InstanceNorm\n→ 64×64×64 → 128×128×64 → 256×256×32", {
    x: 0.65, y: 2.1, w: 3.45, h: 0.7,
    fontSize: 9.5, fontFace: "Microsoft YaHei",
    color: "555555", bold: false, align: "left", valign: "top", margin: 0
  });

  // 中间连接 + AdaIN
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 4.28, y: 2.1, w: 0.38, h: 0.08,
    fill: { color: "780000" }, line: { color: "780000" }
  });
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 4.68, y: 1.72, w: 0.72, h: 0.85,
    fill: { color: "FFF0F0" }, line: { color: "c1121f", pt: 1.5 }, rectRadius: 0.06
  });
  slide.addText("AdaIN\n注入", {
    x: 4.68, y: 1.72, w: 0.72, h: 0.85,
    fontSize: 9.5, fontFace: "Microsoft YaHei",
    color: "780000", bold: true, align: "center", valign: "middle", margin: 0
  });

  // — 右侧：风格分支 —
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.52, y: 1.72, w: 3.95, h: 1.18,
    fill: { color: "fdf0d5" }, line: { color: "e09f3e", pt: 1.5 }, rectRadius: 0.08
  });
  slide.addText("风格分支  Style Branch", {
    x: 5.62, y: 1.76, w: 3.75, h: 0.32,
    fontSize: 11.5, fontFace: "Microsoft YaHei",
    color: "780000", bold: true, align: "left", margin: 0
  });
  slide.addText("输入: StyleEncoder 向量  (B, 128)\nFC → Broadcast → 空间调制\n调制内容分支每层特征", {
    x: 5.62, y: 2.1, w: 3.75, h: 0.7,
    fontSize: 9.5, fontFace: "Microsoft YaHei",
    color: "555555", bold: false, align: "left", valign: "top", margin: 0
  });

  // 连接线
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 9.46, y: 2.1, w: 0.06, h: 0.08,
    fill: { color: "780000" }, line: { color: "780000" }
  });

  // — AdaIN 详解（核心公式区）—
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.55, y: 3.0, w: 4.25, h: 1.85,
    fill: { color: "FFFFFF" }, line: { color: "780000", pt: 2 }, rectRadius: 0.1
  });
  slide.addText("AdaIN（自适应实例归一化）", {
    x: 0.65, y: 3.04, w: 4.0, h: 0.35,
    fontSize: 12, fontFace: "Microsoft YaHei",
    color: "780000", bold: true, align: "left", margin: 0
  });
  slide.addText("AdaIN(x, y) = y_s × (x − μ(x)) / σ(x) + y_b\n\n其中:\n  y_s = FC(style) → 缩放因子 (Scale)\n  y_b = FC(style) → 偏置因子 (Bias)\n\n→ 将风格向量 y 的均值/方差迁移到内容特征 x", {
    x: 0.65, y: 3.4, w: 4.1, h: 1.4,
    fontSize: 9.5, fontFace: "Consolas",
    color: "003049", bold: false, align: "left", valign: "top", margin: 0
  });

  // — 双线性门控融合 —
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.0, y: 3.0, w: 4.47, h: 1.85,
    fill: { color: "F5F3EE" }, line: { color: "003049", pt: 2 }, rectRadius: 0.1
  });
  slide.addText("门控特征融合  Gated Fusion", {
    x: 5.1, y: 3.04, w: 4.25, h: 0.35,
    fontSize: 12, fontFace: "Microsoft YaHei",
    color: "003049", bold: true, align: "left", margin: 0
  });
  slide.addText("Output = g · G + (1 − g) · x\n\n  G   = Conv(Concat(style_feat, content_feat))\n  g   = σ(Conv(Concat(style_feat, content_feat)))\n      ∈ [0,1] — 学习到的软门控权重\n\n融合风格细节与内容结构的双重信息", {
    x: 5.1, y: 3.4, w: 4.3, h: 1.4,
    fontSize: 9.5, fontFace: "Consolas",
    color: "003049", bold: false, align: "left", valign: "top", margin: 0
  });

  // 输出箭头
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 4.62, y: 4.95, w: 0.78, h: 0.07,
    fill: { color: "780000" }, line: { color: "780000" }
  });
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.4, y: 4.82, w: 3.85, h: 0.5,
    fill: { color: "780000" }, line: { color: "780000" }, rectRadius: 0.08
  });
  slide.addText("输出: 书法生成图  (B, 1, 256, 256)", {
    x: 5.4, y: 4.82, w: 3.85, h: 0.5,
    fontSize: 12, fontFace: "Microsoft YaHei",
    color: "FFFFFF", bold: true, align: "center", valign: "middle", margin: 0
  });

  // 页码
  slide.addShape(pres.shapes.OVAL, {
    x: 9.3, y: 5.1, w: 0.4, h: 0.4,
    fill: { color: "780000" }
  });
  slide.addText("3", {
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
  pres.writeFile({ fileName: "slides/slide-03-preview.pptx" });
}

module.exports = { createSlide, slideConfig };

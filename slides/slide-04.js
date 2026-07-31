// slide-04.js — 判别器 & 注意力机制
const pptxgen = require("pptxgenjs");

const slideConfig = { type: 'content', index: 4, title: '判别器 & 注意力机制' };

function createSlide(pres, theme) {
  const slide = pres.addSlide();
  slide.background = { color: "F8F6F2" };

  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.08,
    fill: { color: "780000" }, line: { color: "780000" }
  });
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.4, y: 0.18, w: 0.07, h: 0.55,
    fill: { color: "003049" }, line: { color: "003049" }
  });
  slide.addText("算法设计", {
    x: 0.58, y: 0.15, w: 5, h: 0.45,
    fontSize: 28, fontFace: "Microsoft YaHei",
    color: "003049", bold: true, align: "left", valign: "middle", margin: 0
  });
  slide.addText("判别器 & 自注意力机制", {
    x: 0.58, y: 0.58, w: 7, h: 0.28,
    fontSize: 14, fontFace: "Microsoft YaHei",
    color: "669bbc", bold: false, align: "left", margin: 0
  });
  slide.addText("南京信息工程大学", {
    x: 7, y: 0.2, w: 2.8, h: 0.35,
    fontSize: 11, fontFace: "Microsoft YaHei",
    color: "780000", bold: false, align: "right", margin: 0
  });

  // ===== 左卡：PatchGAN 判别器 =====
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.35, y: 0.98, w: 4.4, h: 4.32,
    fill: { color: "FFFFFF" }, line: { color: "E0D9CF", pt: 1 }, rectRadius: 0.1
  });

  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.35, y: 0.98, w: 4.4, h: 0.45,
    fill: { color: "003049" }, line: { color: "003049" }, rectRadius: 0.1
  });
  slide.addText("PatchGAN 判别器", {
    x: 0.48, y: 0.98, w: 4.15, h: 0.45,
    fontSize: 13, fontFace: "Microsoft YaHei",
    color: "FFFFFF", bold: true, align: "left", valign: "middle", margin: 0
  });

  // 输入输出
  slide.addText("输入: 书法图像对 (真实/生成)", {
    x: 0.5, y: 1.52, w: 4.1, h: 0.26,
    fontSize: 10, fontFace: "Microsoft YaHei",
    color: "003049", bold: false, align: "left", margin: 0
  });
  slide.addText("输出: Patch级矩阵 (B, 1, H/64, W/64)", {
    x: 0.5, y: 1.78, w: 4.1, h: 0.26,
    fontSize: 10, fontFace: "Microsoft YaHei",
    color: "780000", bold: false, align: "left", margin: 0
  });

  // 判别器结构
  const discSteps = [
    { label: "输入拼接", desc: "Concat(源图像, 目标图像)\n→ 强制判别器学习内容对应关系" },
    { label: "6层卷积下采样", desc: "C64→C128→C256→C512→C512→C1\n逐步提取细粒度纹理差异" },
    { label: "LeakyReLU + Dropout", desc: "α=0.2, rate=0.3\n防止判别器过强（mode collapse）" },
    { label: "Spectral Normalization", desc: "约束 W 的谱范数为1\n稳定GAN训练" },
  ];
  discSteps.forEach((s, i) => {
    const y = 2.1 + i * 0.63;
    slide.addShape(pres.shapes.OVAL, {
      x: 0.5, y: y, w: 0.36, h: 0.36,
      fill: { color: "003049" }, line: { color: "003049" }
    });
    slide.addText(`${i + 1}`, {
      x: 0.5, y: y, w: 0.36, h: 0.36,
      fontSize: 11, fontFace: "Arial",
      color: "FFFFFF", bold: true, align: "center", valign: "middle"
    });
    slide.addText(s.label, {
      x: 0.98, y: y, w: 3.65, h: 0.22,
      fontSize: 10.5, fontFace: "Microsoft YaHei",
      color: "003049", bold: true, align: "left", margin: 0
    });
    slide.addText(s.desc, {
      x: 0.98, y: y + 0.2, w: 3.65, h: 0.35,
      fontSize: 9, fontFace: "Microsoft YaHei",
      color: "555555", bold: false, align: "left", margin: 0
    });
  });

  // Patch优势
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.5, y: 4.52, w: 4.15, h: 0.65,
    fill: { color: "EEF3F7" }, line: { color: "669bbc", pt: 1 }, rectRadius: 0.08
  });
  slide.addText("PatchGAN优势：逐块判别 → 关注局部纹理细节（笔画粗细、墨色浓淡）", {
    x: 0.62, y: 4.52, w: 3.95, h: 0.65,
    fontSize: 9.5, fontFace: "Microsoft YaHei",
    color: "003049", bold: false, align: "left", valign: "middle", margin: 0
  });

  // ===== 右卡：自注意力模块 =====
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.25, y: 0.98, w: 4.4, h: 4.32,
    fill: { color: "FFFFFF" }, line: { color: "E0D9CF", pt: 1 }, rectRadius: 0.1
  });

  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.25, y: 0.98, w: 4.4, h: 0.45,
    fill: { color: "c1121f" }, line: { color: "c1121f" }, rectRadius: 0.1
  });
  slide.addText("Self-Attention (SAGAN)", {
    x: 5.38, y: 0.98, w: 4.15, h: 0.45,
    fontSize: 13, fontFace: "Microsoft YaHei",
    color: "FFFFFF", bold: true, align: "left", valign: "middle", margin: 0
  });

  slide.addText("作用：为生成器提供全局感受野", {
    x: 5.4, y: 1.52, w: 4.1, h: 0.26,
    fontSize: 10, fontFace: "Microsoft YaHei",
    color: "003049", bold: false, align: "left", margin: 0
  });
  slide.addText("→ 捕捉远距离笔画间的风格关联", {
    x: 5.4, y: 1.78, w: 4.1, h: 0.26,
    fontSize: 10, fontFace: "Microsoft YaHei",
    color: "780000", bold: false, align: "left", margin: 0
  });

  // 注意力公式
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.4, y: 2.12, w: 4.1, h: 1.85,
    fill: { color: "FFF0F0" }, line: { color: "c1121f", pt: 1.5 }, rectRadius: 0.08
  });
  slide.addText("计算流程", {
    x: 5.52, y: 2.18, w: 3.85, h: 0.28,
    fontSize: 11, fontFace: "Microsoft YaHei",
    color: "780000", bold: true, align: "left", margin: 0
  });
  slide.addText("① Query:  Q = Conv(x)  → (B, C/8, H, W)\n② Key:     K = Conv(x)  → (B, C/8, H, W)\n③ Value:   V = Conv(x)  → (B, C,    H, W)\n④ 注意力:  A = Softmax(Q ⊙ Kᵀ)  ∈ (B, HW, HW)\n⑤ 输出:     O = γ·(V ⊙ A) + x     (γ可学习, 初始0)", {
    x: 5.52, y: 2.48, w: 3.92, h: 1.4,
    fontSize: 9.5, fontFace: "Consolas",
    color: "003049", bold: false, align: "left", valign: "top", margin: 0
  });

  // 为什么用注意力
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 5.4, y: 4.06, w: 4.1, h: 1.1,
    fill: { color: "fdf0d5" }, line: { color: "e09f3e", pt: 1 }, rectRadius: 0.08
  });
  slide.addText("为什么需要注意力？", {
    x: 5.52, y: 4.1, w: 3.85, h: 0.3,
    fontSize: 10.5, fontFace: "Microsoft YaHei",
    color: "780000", bold: true, align: "left", margin: 0
  });
  slide.addText("卷积只能捕捉局部邻域信息\n书法风格 = 远距离笔画的整体协调性\n自注意力 → 建模任意两点间的风格相关性", {
    x: 5.52, y: 4.4, w: 3.9, h: 0.72,
    fontSize: 9.5, fontFace: "Microsoft YaHei",
    color: "555555", bold: false, align: "left", valign: "top", margin: 0
  });

  // 页码
  slide.addShape(pres.shapes.OVAL, {
    x: 9.3, y: 5.1, w: 0.4, h: 0.4,
    fill: { color: "780000" }
  });
  slide.addText("4", {
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
  pres.writeFile({ fileName: "slides/slide-04-preview.pptx" });
}

module.exports = { createSlide, slideConfig };

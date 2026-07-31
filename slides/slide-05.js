// slide-05.js — 综合损失函数
const pptxgen = require("pptxgenjs");

const slideConfig = { type: 'content', index: 5, title: '综合损失函数' };

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
  slide.addText("综合损失函数", {
    x: 0.58, y: 0.58, w: 7, h: 0.28,
    fontSize: 14, fontFace: "Microsoft YaHei",
    color: "669bbc", bold: false, align: "left", margin: 0
  });
  slide.addText("南京信息工程大学", {
    x: 7, y: 0.2, w: 2.8, h: 0.35,
    fontSize: 11, fontFace: "Microsoft YaHei",
    color: "780000", bold: false, align: "right", margin: 0
  });

  // ===== 总损失公式 =====
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.35, y: 0.98, w: 9.3, h: 0.62,
    fill: { color: "780000" }, line: { color: "780000" }, rectRadius: 0.08
  });
  slide.addText("总损失函数    L_total = λ₁·L_adv + λ₂·L_perc + λ₃·L_style + λ₄·L_content + λ₅·L_cls", {
    x: 0.5, y: 0.98, w: 9.1, h: 0.62,
    fontSize: 13, fontFace: "Consolas",
    color: "FFFFFF", bold: true, align: "center", valign: "middle", margin: 0
  });

  // ===== 五个损失卡 =====
  const losses = [
    {
      name: "L_adv  对抗损失",
      color: "c1121f", bg: "FFF0F0",
      formula: "L_adv = −E[log D(x, G(c,s))]\n\nMinimax博弈:\n  min_G max_D E[log D(real)]\n          + E[log(1−D(G(c,s)))]",
      role: "驱动生成器欺骗判别器",
      x: 0.35, w: 1.75
    },
    {
      name: "L_perc  感知损失",
      color: "003049", bg: "EEF3F7",
      formula: "VGG19 预训练权重视为特征提取器\n\nL_perc = Σ||VGG(y) − VGG(G)||₁",
      role: "保证生成图像的视觉真实性",
      x: 2.18, w: 1.75
    },
    {
      name: "L_style  风格损失",
      color: "780000", bg: "fdf0d5",
      formula: "Gram矩阵: Gᵢⱼ = Fᵢ·Fⱼ\n\nL_style = Σ||G(VGG(y)) − G(VGG(G)))||₁",
      role: "迁移书法家的笔触纹理特征",
      x: 4.01, w: 1.75
    },
    {
      name: "L_content  内容损失",
      color: "003049", bg: "F5F3EE",
      formula: "L_content = ||Content(G) − Content(y)||₁\n\nContent = Encoder输出的\n        深层语义特征图",
      role: "保持字形结构和可辨识度",
      x: 5.84, w: 1.75
    },
    {
      name: "L_cls  风格分类",
      color: "780000", bg: "EEF3F7",
      formula: "辅助分类器:\n  判断生成图像的书法风格\n  → 增强生成器对风格的感知",
      role: "确保生成书法属于目标风格",
      x: 7.67, w: 1.98
    },
  ];

  losses.forEach(l => {
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: l.x, y: 1.7, w: l.w, h: 2.65,
      fill: { color: l.bg }, line: { color: l.color, pt: 1.5 }, rectRadius: 0.08
    });
    // 标题
    slide.addText(l.name, {
      x: l.x + 0.08, y: 1.74, w: l.w - 0.16, h: 0.3,
      fontSize: 10.5, fontFace: "Microsoft YaHei",
      color: l.color, bold: true, align: "left", margin: 0
    });
    // 分隔线
    slide.addShape(pres.shapes.RECTANGLE, {
      x: l.x + 0.08, y: 2.06, w: l.w - 0.16, h: 0.025,
      fill: { color: l.color }, line: { color: l.color }
    });
    // 公式
    slide.addText(l.formula, {
      x: l.x + 0.08, y: 2.1, w: l.w - 0.16, h: 1.4,
      fontSize: 8.5, fontFace: "Consolas",
      color: "003049", bold: false, align: "left", valign: "top", margin: 0
    });
    // 作用
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: l.x + 0.06, y: 3.6, w: l.w - 0.12, h: 0.65,
      fill: { color: l.color }, line: { color: l.color }, rectRadius: 0.06
    });
    slide.addText(l.role, {
      x: l.x + 0.1, y: 3.6, w: l.w - 0.2, h: 0.65,
      fontSize: 9, fontFace: "Microsoft YaHei",
      color: "FFFFFF", bold: false, align: "center", valign: "middle", margin: 0
    });
  });

  // ===== VGG19 权重修复说明 =====
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.35, y: 4.45, w: 9.3, h: 0.7,
    fill: { color: "FFFFFF" }, line: { color: "780000", pt: 2 }, rectRadius: 0.08
  });
  slide.addText("⚠ 关键细节", {
    x: 0.48, y: 4.48, w: 1.2, h: 0.3,
    fontSize: 10.5, fontFace: "Microsoft YaHei",
    color: "780000", bold: true, align: "left", margin: 0
  });
  slide.addText("VGG19 感知损失必须加载 ImageNet 预训练权重（不要设置 pretrained=False，否则随机初始化权重会导致感知损失失效）", {
    x: 0.48, y: 4.78, w: 9.0, h: 0.32,
    fontSize: 10, fontFace: "Microsoft YaHei",
    color: "003049", bold: false, align: "left", margin: 0
  });

  // 页码
  slide.addShape(pres.shapes.OVAL, {
    x: 9.3, y: 5.1, w: 0.4, h: 0.4,
    fill: { color: "780000" }
  });
  slide.addText("5", {
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
  pres.writeFile({ fileName: "slides/slide-05-preview.pptx" });
}

module.exports = { createSlide, slideConfig };

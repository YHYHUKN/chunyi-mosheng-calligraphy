// slide-01.js — 算法设计总体架构
const pptxgen = require("pptxgenjs");

const slideConfig = { type: 'content', index: 1, title: '算法设计 — 总体架构' };

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

  // 标题
  slide.addText("算法设计", {
    x: 0.58, y: 0.15, w: 5, h: 0.45,
    fontSize: 28, fontFace: "Microsoft YaHei",
    color: "003049", bold: true, align: "left", valign: "middle", margin: 0
  });

  // 副标题
  slide.addText("总体架构概览", {
    x: 0.58, y: 0.58, w: 5, h: 0.28,
    fontSize: 14, fontFace: "Microsoft YaHei",
    color: "669bbc", bold: false, align: "left", margin: 0
  });

  // 右侧校名
  slide.addText("南京信息工程大学", {
    x: 7, y: 0.2, w: 2.8, h: 0.35,
    fontSize: 11, fontFace: "Microsoft YaHei",
    color: "780000", bold: false, align: "right", margin: 0
  });

  // ——— 架构流程图 ———
  // 整体背景卡
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x: 0.35, y: 1.02, w: 9.3, h: 4.1,
    fill: { color: "FFFFFF" }, line: { color: "E0D9CF", pt: 1 }, rectRadius: 0.1
  });

  // 流程：输入 → 预处理 → 编码器 → 生成器 → 输出
  // 节点参数: [x, y, w, h, 标签, 颜色, 文字颜色]
  const nodes = [
    { x: 0.55, y: 1.22, w: 1.55, h: 0.72, label: "字形输入\n书法图像", fill: "fdf0d5", text: "003049" },
    { x: 2.3, y: 1.22, w: 1.6, h: 0.72, label: "数据预处理\n骨架提取", fill: "fdf0d5", text: "003049" },
    { x: 4.1, y: 1.22, w: 1.6, h: 0.72, label: "风格编码器\nStyleEncoder", fill: "003049", text: "FFFFFF" },
    { x: 5.9, y: 1.22, w: 1.6, h: 0.72, label: "内容编码器\nContentEncoder", fill: "003049", text: "FFFFFF" },
    { x: 7.7, y: 1.22, w: 1.5, h: 0.72, label: "双分支生成器\nGenerator", fill: "c1121f", text: "FFFFFF" },
  ];

  nodes.forEach(n => {
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: n.x, y: n.y, w: n.w, h: n.h,
      fill: { color: n.fill }, line: { color: "C0BAB0", pt: 1 }, rectRadius: 0.1
    });
    slide.addText(n.label, {
      x: n.x, y: n.y, w: n.w, h: n.h,
      fontSize: 9.5, fontFace: "Microsoft YaHei",
      color: n.text, bold: false, align: "center", valign: "middle", margin: 0
    });
  });

  // 箭头（用细矩形模拟）
  const arrows = [
    { x: 2.12, y: 1.52, w: 0.2, h: 0.06 },
    { x: 3.93, y: 1.52, w: 0.2, h: 0.06 },
    { x: 5.73, y: 1.52, w: 0.2, h: 0.06 },
    { x: 7.53, y: 1.52, w: 0.2, h: 0.06 },
  ];
  arrows.forEach(a => {
    slide.addShape(pres.shapes.RECTANGLE, {
      x: a.x, y: a.y, w: a.w, h: a.h,
      fill: { color: "780000" }, line: { color: "780000" }
    });
  });

  // 分隔横线
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 2.16, w: 9.1, h: 0.03,
    fill: { color: "E0D9CF" }, line: { color: "E0D9CF" }
  });

  // ——— 下方四个关键模块说明卡 ———
  const modules = [
    {
      title: "① 数据预处理",
      desc: "Zhang-Suen 细化\n提取笔画骨架\n图像增强 ×N",
      x: 0.5, color: "fdf0d5", tc: "003049", bc: "003049"
    },
    {
      title: "② 风格编码器",
      desc: "5层卷积下采样\n+ 自注意力机制\n→ 128维风格向量",
      x: 2.9, color: "EEF3F7", tc: "003049", bc: "003049"
    },
    {
      title: "③ 双分支生成器",
      desc: "内容分支 + 风格分支\nAdaIN 风格注入\n门控特征融合",
      x: 5.28, color: "FFF0F0", tc: "780000", bc: "780000"
    },
    {
      title: "④ 综合损失函数",
      desc: "对抗损失 + 感知损失\n+ 风格损失 + 内容损失\n+ 风格分类损失",
      x: 7.65, color: "F5F3EE", tc: "003049", bc: "003049"
    },
  ];

  modules.forEach(m => {
    slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: m.x, y: 2.28, w: 2.25, h: 2.7,
      fill: { color: m.color }, line: { color: "C0BAB0", pt: 1 }, rectRadius: 0.1
    });
    slide.addText(m.title, {
      x: m.x + 0.1, y: 2.33, w: 2.05, h: 0.38,
      fontSize: 11, fontFace: "Microsoft YaHei",
      color: m.bc, bold: true, align: "left", margin: 0
    });
    slide.addShape(pres.shapes.RECTANGLE, {
      x: m.x + 0.1, y: 2.72, w: 2.0, h: 0.025,
      fill: { color: "C0BAB0" }, line: { color: "C0BAB0" }
    });
    slide.addText(m.desc, {
      x: m.x + 0.1, y: 2.76, w: 2.05, h: 2.1,
      fontSize: 10, fontFace: "Microsoft YaHei",
      color: m.tc, bold: false, align: "left", valign: "top", margin: 0
    });
  });

  // 页码
  slide.addShape(pres.shapes.OVAL, {
    x: 9.3, y: 5.1, w: 0.4, h: 0.4,
    fill: { color: "780000" }
  });
  slide.addText("1", {
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
  pres.writeFile({ fileName: "slides/slide-01-preview.pptx" });
}

module.exports = { createSlide, slideConfig };

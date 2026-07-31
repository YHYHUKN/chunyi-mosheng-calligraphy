// compile.js — 编译所有幻灯片为一份 PPT
const pptxgen = require("pptxgenjs");

const slide01 = require("./slide-01.js");
const slide02 = require("./slide-02.js");
const slide03 = require("./slide-03.js");
const slide04 = require("./slide-04.js");
const slide05 = require("./slide-05.js");

const pres = new pptxgen();
pres.layout = 'LAYOUT_16x9';
pres.title = '书法风格迁移算法设计';
pres.author = '杨辉';
pres.company = '南京信息工程大学';

const theme = {
  primary: "780000",    // 深红
  secondary: "c1121f",  // 亮红
  accent: "003049",     // 深蓝
  light: "669bbc",      // 浅蓝
  bg: "F8F6F2"          // 米白背景
};

const slides = [slide01, slide02, slide03, slide04, slide05];
slides.forEach(mod => mod.createSlide(pres, theme));

pres.writeFile({ fileName: "算法设计-幻灯片.pptx" })
  .then(() => console.log("✅ 编译完成: 算法设计-幻灯片.pptx"))
  .catch(err => console.error("❌ 编译失败:", err));

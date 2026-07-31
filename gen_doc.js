const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, AlignmentType,
       HeadingLevel, BorderStyle, WidthType, ShadingType, VerticalAlign,
       TableOfContents, PageNumber, Footer, Header } = require('docx');

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "宋体", size: 24 } },
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 32, bold: true, font: "黑体" },
        paragraph: { spacing: { before: 480, after: 240 }, outlineLevel: 0 }
      },
      {
        id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 28, bold: true, font: "黑体" },
        paragraph: { spacing: { before: 360, after: 180 }, outlineLevel: 1 }
      },
      {
        id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 26, bold: true, font: "黑体" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 2 }
      },
      {
        id: "BodyText", name: "Body Text",
        run: { size: 24, font: "宋体" },
        paragraph: { spacing: { line: 360, after: 120 } }
      },
      {
        id: "Code", name: "Code",
        run: { size: 20, font: "Consolas", color: "333333" },
        paragraph: { spacing: { before: 120, after: 120 }, indent: { left: 360 } }
      }
    ]
  },
  sections: [{
    properties: {
      page: { size: { width: 11906, height: 16838 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
    },
    children: [

      // ===== 封面 =====
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 2400, after: 400 },
        children: [new TextRun({ text: "春意墨生", size: 52, bold: true, font: "华文中宋" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 200 },
        children: [new TextRun({ text: "AI书法创作系统", size: 40, bold: true, font: "华文中宋" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 600 },
        children: [new TextRun({ text: "使用说明", size: 36, bold: true, font: "华文中宋" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 1200, after: 120 },
        children: [new TextRun({ text: "版本：1.0", size: 24, font: "宋体" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "2026年5月", size: 24, font: "宋体" })]
      }),
      new Paragraph({ pageBreakBefore: true }),

      // ===== 目录 =====
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("目  录")]
      }),
      new TableOfContents("目录", { hyperlink: true, headingStyleRange: "1-3" }),
      new Paragraph({ pageBreakBefore: true }),

      // ===== 第一章 =====
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("一、系统简介")]
      }),
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("1.1 系统概述")]
      }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun("「春意墨生」是基于深度学习（GAN）与风格解耦技术的AI书法创作系统。系统融合计算机视觉与传统书法艺术，支持米芾、赵孟頫、褚遂良、乙瑛碑、邓石如、怀素六种经典风格，覆盖行书、楷书、隶书、篆书、草书五大书体。")]
      }),
      new Paragraph({ spacing: { after: 120 } }),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("1.2 技术栈")]
      }),
      new Table({
        width: { size: 9072, type: WidthType.DXA },
        columnWidths: [2268, 6804],
        rows: [
          new TableRow({
            children: [
              new TableCell({ shading: { fill: "4472C4", type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER,
                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "层次", bold: true, color: "FFFFFF", font: "黑体" })] })] }),
              new TableCell({ shading: { fill: "4472C4", type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER,
                children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "技术", bold: true, color: "FFFFFF", font: "黑体" })] })] }),
            ]
          }),
          ...[
            ["深度学习框架", "PyTorch (CUDA)"],
            ["后端服务", "FastAPI + Uvicorn"],
            ["前端", "纯 HTML / CSS / JavaScript（无框架）"],
            ["图像处理", "OpenCV、Pillow"],
            ["GPU", "NVIDIA RTX 3050 4GB（推荐）"],
          ].map(([a, b]) => new TableRow({
            children: [
              new TableCell({ children: [new Paragraph({ style: "BodyText", children: [new TextRun({ text: a, font: "宋体" })] })] }),
              new TableCell({ children: [new Paragraph({ style: "BodyText", children: [new TextRun({ text: b, font: "宋体" })] })] }),
            ]
          }))
        ]
      }),
      new Paragraph({ spacing: { after: 200 } }),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("1.3 系统架构")]
      }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun({ text: "系统采用双分支风格解耦GAN，核心架构如下：", font: "宋体" })]
      }),
      new Paragraph({
        style: "Code",
        children: [new TextRun("StyleEncoder  →  风格隐向量 (B, 128)\nContentEncoder →  内容特征图 (B, 256, 8, 8)\n       ↓                              ↓\nDualBranchGenerator ← 特征融合（AdaIN + 门控）\n       ↓\nDiscriminator  →  真假判别 + 风格分类")]
      }),
      new Paragraph({ pageBreakBefore: true }),

      // ===== 第二章 =====
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("二、环境配置")]
      }),
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("2.1 系统要求")]
      }),
      new Table({
        width: { size: 9072, type: WidthType.DXA },
        columnWidths: [2268, 6804],
        rows: [
          new TableRow({ children: [
            new TableCell({ shading: { fill: "4472C4", type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER,
              children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "项目", bold: true, color: "FFFFFF", font: "黑体" })] })] }),
            new TableCell({ shading: { fill: "4472C4", type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER,
              children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "要求", bold: true, color: "FFFFFF", font: "黑体" })] })] }),
          ]}),
          ...[
            ["操作系统", "Windows 10 / 11"],
            ["Python", "3.8 - 3.12"],
            ["GPU", "NVIDIA RTX 3050 4GB+（可选）"],
            ["显存", "建议8GB+（GPU模式）"],
            ["硬盘", "至少5GB可用空间"],
          ].map(([a, b]) => new TableRow({ children: [
            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: a, font: "宋体" })] })] }),
            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: b, font: "宋体" })] })] }),
          ]}))
        ]
      }),
      new Paragraph({ spacing: { after: 200 } }),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("2.2 依赖安装")]
      }),
      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun("方式一：自动安装（推荐）")]
      }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun({ text: "双击运行根目录下的 ", font: "宋体" }), new TextRun({ text: "install_cuda_pytorch.bat", font: "Consolas", size: 20 }), new TextRun({ text: "，脚本会自动安装：", font: "宋体" })]
      }),
      new Paragraph({ style: "Code", children: [new TextRun("CUDA 12.x 驱动\nPyTorch (CUDA版)\nOpenCV\nFastAPI + Uvicorn")] }),

      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun("方式二：手动安装")]
      }),
      new Paragraph({ style: "Code", children: [new TextRun(
        "# 安装PyTorch（GPU版）\npip install torch torchvision --index-url https://download.pytorch.org/whl/cu121\n\n# 安装其他依赖\npip install fastapi uvicorn python-multipart opencv-python Pillow numpy"
      )] }),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("2.3 环境验证")]
      }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun({ text: "运行 ", font: "宋体" }), new TextRun({ text: "check_env.py", font: "Consolas", size: 20 }), new TextRun({ text: " 检查环境是否就绪：", font: "宋体" })]
      }),
      new Paragraph({ style: "Code", children: [new TextRun("python check_env.py")] }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun({ text: "正常输出应显示：", font: "宋体" })]
      }),
      new Paragraph({ style: "Code", children: [new TextRun(
        "✅ Python: 3.x.x\n✅ PyTorch: 2.x.x (CUDA可用/仅CPU)\n✅ OpenCV: 4.x.x\n✅ FastAPI: 已安装"
      )] }),
      new Paragraph({ pageBreakBefore: true }),

      // ===== 第三章 =====
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("三、启动系统")]
      }),
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("3.1 启动后端服务")]
      }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun({ text: "在命令行执行以下命令启动后端API服务：", font: "宋体" })]
      }),
      new Paragraph({ style: "Code", children: [new TextRun(
        "cd D:\\书法春\npython algorithm\\server\\app.py"
      )] }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun({ text: "服务启动成功后会显示：", font: "宋体" })]
      }),
      new Paragraph({ style: "Code", children: [new TextRun(
        "INFO:     Uvicorn running on http://0.0.0.0:8000\n[ModelManager] 初始化完成，设备: cuda"
      )] }),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("3.2 访问前端")]
      }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun({ text: "服务启动后，打开浏览器访问：", font: "宋体" })]
      }),
      new Paragraph({ style: "Code", children: [new TextRun("http://localhost:8000")] }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun({ text: "或直接双击打开项目目录中的 ", font: "宋体" }), new TextRun({ text: "index.html", font: "Consolas", size: 20 }), new TextRun({ text: " 文件（离线模式，使用Canvas模拟渲染）。", font: "宋体" })]
      }),
      new Paragraph({ pageBreakBefore: true }),

      // ===== 第四章 =====
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("四、功能使用说明")]
      }),
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("4.1 创作书法作品")]
      }),
      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun("第一步：输入文本")]
      }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun({ text: "在左侧文本框中输入要创作的书法内容，支持：", font: "宋体" })]
      }),
      new Paragraph({ style: "BodyText", children: [new TextRun("• 单字（如：「龙」）")] }),
      new Paragraph({ style: "BodyText", children: [new TextRun("• 词语（如：「上善若水」）")] }),
      new Paragraph({ style: "BodyText", children: [new TextRun("• 诗句（如：「春眠不觉晓」）")] }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun({ text: "点击「诗句」或「经典」按钮可快速填充示例文本。", font: "宋体" })]
      }),

      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun("第二步：选择布局")]
      }),
      new Table({
        width: { size: 9072, type: WidthType.DXA },
        columnWidths: [2268, 6804],
        rows: [
          new TableRow({ children: [
            new TableCell({ shading: { fill: "E9EEF7", type: ShadingType.CLEAR },
              children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "参数", bold: true, font: "黑体" })] })] }),
            new TableCell({ shading: { fill: "E9EEF7", type: ShadingType.CLEAR },
              children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "说明", bold: true, font: "黑体" })] })] }),
          ]}),
          ...[
            ["竖排/横排", "控制文字排列方向"],
            ["字间距", "拖动滑块调整（0-100）"],
            ["行间距", "拖动滑块调整（0-100）"],
            ["字号大小", "拖动滑块调整（30-120px）"],
            ["纸幅比例", "竖幅 / 方幅 / 横幅"],
          ].map(([a, b]) => new TableRow({ children: [
            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: a, font: "宋体" })] })] }),
            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: b, font: "宋体" })] })] }),
          ]}))
        ]
      }),
      new Paragraph({ spacing: { after: 200 } }),

      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun("第三步：选择风格")]
      }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun({ text: "系统支持两种风格选择模式：「经典书家」和「五大书体」。", font: "宋体" })]
      }),

      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun("第四步：调整风格参数")]
      }),
      new Table({
        width: { size: 9072, type: WidthType.DXA },
        columnWidths: [2268, 2268, 4536],
        rows: [
          new TableRow({ children: [
            new TableCell({ shading: { fill: "4472C4", type: ShadingType.CLEAR },
              children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "参数", bold: true, color: "FFFFFF", font: "黑体" })] })] }),
            new TableCell({ shading: { fill: "4472C4", type: ShadingType.CLEAR },
              children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "范围", bold: true, color: "FFFFFF", font: "黑体" })] })] }),
            new TableCell({ shading: { fill: "4472C4", type: ShadingType.CLEAR },
              children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "效果", bold: true, color: "FFFFFF", font: "黑体" })] })] }),
          ]}),
          ...[
            ["笔法粗细", "0-100", "控制笔画粗细"],
            ["墨色浓淡", "0-100", "控制墨色深浅"],
            ["结字疏密", "0-100", "控制字体紧凑程度"],
            ["飞白效果", "0-100", "添加飞白笔触效果"],
          ].map(([a, b, c]) => new TableRow({ children: [
            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: a, font: "宋体" })] })] }),
            new TableCell({ alignment: AlignmentType.CENTER,
              children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: b, font: "宋体" })] })] }),
            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: c, font: "宋体" })] })] }),
          ]}))
        ]
      }),
      new Paragraph({ spacing: { after: 200 } }),

      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun("第五步：生成与下载")]
      }),
      new Paragraph({ style: "BodyText", children: [new TextRun("1. 点击「生成书法」按钮，等待生成完成")] }),
      new Paragraph({ style: "BodyText", children: [new TextRun("2. 点击「下载作品」保存PNG格式图片")] }),

      new Paragraph({ pageBreakBefore: true }),

      // ===== 第五章 =====
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("五、支持的书法风格")]
      }),
      new Table({
        width: { size: 9072, type: WidthType.DXA },
        columnWidths: [1814, 1814, 1814, 3628],
        rows: [
          new TableRow({ children: [
            new TableCell({ shading: { fill: "4472C4", type: ShadingType.CLEAR },
              children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "书法家", bold: true, color: "FFFFFF", font: "黑体" })] })] }),
            new TableCell({ shading: { fill: "4472C4", type: ShadingType.CLEAR },
              children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "书体", bold: true, color: "FFFFFF", font: "黑体" })] })] }),
            new TableCell({ shading: { fill: "4472C4", type: ShadingType.CLEAR },
              children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "朝代", bold: true, color: "FFFFFF", font: "黑体" })] })] }),
            new TableCell({ shading: { fill: "4472C4", type: ShadingType.CLEAR },
              children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "风格特点", bold: true, color: "FFFFFF", font: "黑体" })] })] }),
          ]}),
          ...[
            ["米芾", "行书", "宋代", "沉着痛快，八面出锋，风樯阵马"],
            ["赵孟頫", "楷书", "元代", "圆润秀美，流畅自然，遒媚姿媚"],
            ["褚遂良", "楷书", "唐代", "清朗秀劲，疏瘦劲健，灵动飘逸"],
            ["乙瑛碑", "隶书", "汉代", "婉畅飘逸，圆浑沉着，遒劲古拙"],
            ["邓石如", "篆书", "清代", "圆转匀称，刚健婀娜，篆法精绝"],
            ["怀素", "草书", "唐代", "狂放飘逸，如骤雨旋风，挥毫泼墨"],
          ].map(([a, b, c, d]) => new TableRow({ children: [
            new TableCell({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: a, font: "宋体", bold: true })] })] }),
            new TableCell({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: b, font: "宋体" })] })] }),
            new TableCell({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: c, font: "宋体" })] })] }),
            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: d, font: "宋体" })] })] }),
          ]}))
        ]
      }),
      new Paragraph({ pageBreakBefore: true }),

      // ===== 第六章 =====
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("六、模型训练")]
      }),
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("6.1 完整训练（6风格）")]
      }),
      new Paragraph({ style: "Code", children: [new TextRun("python algorithm/train/run_train.py")] }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun({ text: "配置参数：训练分辨率128×128，批大小4-8，训练60 epoch，GPU训练速度约143秒/epoch。", font: "宋体" })]
      }),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("6.2 单风格快速训练")]
      }),
      new Paragraph({ style: "Code", children: [new TextRun("python algorithm/train/train_mifu.py")] }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun({ text: "仅训练米芾单一风格，30 epoch，约3小时完成。", font: "宋体" })]
      }),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("6.3 继续训练")]
      }),
      new Paragraph({ style: "BodyText", children: [new TextRun({ text: "从已有checkpoint继续训练（降低学习率微调）：", font: "宋体" })] }),
      new Paragraph({ style: "Code", children: [new TextRun("python algorithm/train/continue_train.py")] }),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("6.4 训练数据")]
      }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun({ text: "训练数据位于 ", font: "宋体" }), new TextRun({ text: "algorithm/data/", font: "Consolas", size: 20 }), new TextRun({ text: " 目录，包含6个风格目录：", font: "宋体" })]
      }),
      new Paragraph({ style: "BodyText", children: [new TextRun("• 米芾/ — 米芾行书训练样本")] }),
      new Paragraph({ style: "BodyText", children: [new TextRun("• 赵孟頫/ — 赵孟頫楷书训练样本")] }),
      new Paragraph({ style: "BodyText", children: [new TextRun("• 褚遂良/ — 褚遂良楷书训练样本")] }),
      new Paragraph({ style: "BodyText", children: [new TextRun("• 乙瑛碑/ — 乙瑛碑隶书训练样本")] }),
      new Paragraph({ style: "BodyText", children: [new TextRun("• 邓石如/ — 邓石如篆书训练样本")] }),
      new Paragraph({ style: "BodyText", children: [new TextRun("• 怀素/ — 怀素草书训练样本")] }),

      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun("6.5 模型检查点")]
      }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun({ text: "训练完成后，模型自动保存在 ", font: "宋体" }), new TextRun({ text: "checkpoints/", font: "Consolas", size: 20 }), new TextRun({ text: " 目录。", font: "宋体" })]
      }),
      new Paragraph({ pageBreakBefore: true }),

      // ===== 第七章 =====
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("七、生成策略说明")]
      }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun({ text: "系统采用三级降级生成策略，确保每次都能输出结果：", font: "宋体" })]
      }),
      new Paragraph({ spacing: { after: 120 } }),

      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun("第一级：字库匹配优先")]
      }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun({ text: "扫描 Calli-Tongji 字库，若输入字符在字库中存在，直接返回高清字库图片（256×256）。字库覆盖率约70-80%。", font: "宋体" })]
      }),

      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun("第二级：GAN模型推理")]
      }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun({ text: "当字库未完全命中时，加载训练好的StyleEncoder + ContentEncoder + DualBranchGenerator进行AI推理生成。需要GPU显存充足。", font: "宋体" })]
      }),

      new Paragraph({
        heading: HeadingLevel.HEADING_3,
        children: [new TextRun("第三级：Canvas模拟渲染")]
      }),
      new Paragraph({
        style: "BodyText",
        children: [new TextRun({ text: "当GAN模型未加载或输出空白时，自动降级到前端Canvas渲染（系统字体 + 8步后处理），生成速度约1-3秒/次。", font: "宋体" })]
      }),
      new Paragraph({ pageBreakBefore: true }),

      // ===== 第八章 =====
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("八、常见问题")]
      }),
      ...[
        {
          q: "Q1：启动报错「ModuleNotFoundError: No module named 'fastapi'」",
          a: "解决方案：手动安装依赖包：\n  pip install fastapi uvicorn python-multipart"
        },
        {
          q: "Q2：模型加载失败怎么办？",
          a: "正常现象！系统设计了三级降级策略，即使GAN模型未加载，系统仍可正常使用Canvas模式生成书法作品。"
        },
        {
          q: "Q3：生成速度慢如何加速？",
          a: "• GPU模式：约5-10秒/次生成\n• CPU模式：约30-60秒/次生成\n• Canvas模式：约1-3秒/次生成\n如需加速，请确保已安装CUDA版PyTorch。"
        },
        {
          q: "Q4：字库没有某字怎么办？",
          a: "系统使用Calli-Tongji字库，常见汉字覆盖率约70-80%。字库中没有的字会自动使用Canvas模拟渲染补充。"
        },
        {
          q: "Q5：生成的图片如何使用？",
          a: "下载的PNG图片可以直接打印输出、制作书法作品、用于PPT/文档配图，或分享到社交媒体。"
        },
      ].map(({ q, a }) => [
        new Paragraph({
          spacing: { before: 240, after: 80 },
          children: [new TextRun({ text: q, bold: true, font: "黑体", size: 24 })]
        }),
        new Paragraph({
          style: "BodyText",
          children: [new TextRun({ text: a, font: "宋体" })]
        }),
      ]).flat(),

      new Paragraph({ pageBreakBefore: true }),

      // ===== 第九章 =====
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("九、快捷命令速查")]
      }),
      new Table({
        width: { size: 4536, type: WidthType.DXA },
        columnWidths: [2268, 2268],
        rows: [
          new TableRow({ children: [
            new TableCell({ shading: { fill: "4472C4", type: ShadingType.CLEAR },
              children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "命令", bold: true, color: "FFFFFF", font: "黑体" })] })] }),
            new TableCell({ shading: { fill: "4472C4", type: ShadingType.CLEAR },
              children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "说明", bold: true, color: "FFFFFF", font: "黑体" })] })] }),
          ]}),
          ...[
            ["python check_env.py", "检查环境配置"],
            ["python algorithm/server/app.py", "启动后端服务"],
            ["python algorithm/train/run_train.py", "开始训练（6风格）"],
            ["python algorithm/train/train_mifu.py", "米芾单风格训练"],
          ].map(([a, b]) => new TableRow({ children: [
            new TableCell({ children: [new Paragraph({ style: "Code", children: [new TextRun({ text: a, size: 18 })] })] }),
            new TableCell({ children: [new Paragraph({ children: [new TextRun({ text: b, font: "宋体" })] })] }),
          ]}))
        ]
      }),
      new Paragraph({ spacing: { after: 400 } }),

      // ===== 结尾 =====
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 600, after: 200 },
        children: [new TextRun({ text: "—— 春意墨生 ——", size: 28, bold: true, font: "华文中宋" })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "让AI唤醒千年笔墨", size: 24, font: "华文中宋", color: "888888" })]
      }),
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("D:/书法春/春意墨生AI书法创作系统_使用说明.docx", buffer);
  console.log("✅ 文档生成成功：D:/书法春/春意墨生AI书法创作系统_使用说明.docx");
});

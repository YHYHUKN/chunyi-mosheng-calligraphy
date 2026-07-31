# 春意墨生 AI 书法创作系统 · Chunyi Mosheng — AI Calligraphy Creation System

> 基于深度学习（GAN）与风格解耦技术的 AI 书法创作系统，支持米芾、赵孟頫、褚遂良、乙瑛碑、邓石如、怀素六种经典书法风格。
>
> An AI-powered calligraphy creation system built on deep learning (GAN) and style-disentanglement. It supports six classic calligraphy styles: Mi Fu, Zhao Mengfu, Chu Suiliang, Yi Ying Bei, Deng Shiru, and Huaisu.

---

## 目录 · Table of Contents

- [项目简介 · Overview](#项目简介--overview)
- [核心特性 · Features](#核心特性--features)
- [技术栈 · Tech Stack](#技术栈--tech-stack)
- [模型架构 · Model Architecture](#模型架构--model-architecture)
- [支持的书法风格 · Supported Styles](#支持的书法风格--supported-styles)
- [项目结构 · Project Structure](#项目结构--project-structure)
- [快速开始 · Getting Started](#快速开始--getting-started)
- [后端 API · Backend API](#后端-api--backend-api)
- [模型训练 · Training](#模型训练--training)
- [说明 · Notes](#说明--notes)

---

## 项目简介 · Overview

**中文**：春意墨生融合计算机视觉与传统书法艺术，采用「双分支风格解耦 GAN」将字形结构与笔法墨法进行解耦，从而实现对书法作品的风格化生成与可控调节（笔法粗细、墨色浓淡、结字疏密、飞白效果）。系统包含纯前端创作界面与 FastAPI 后端推理服务，并内置三级生成降级策略以保证可用性。

**English**: *Chunyi Mosheng* bridges computer vision and traditional calligraphy. A **dual-branch style-disentangled GAN** separates glyph structure from brush/ink style, enabling stylized generation and controllable adjustments (brush weight, ink density, character density, flying-white effect). The system ships a vanilla-JS frontend and a FastAPI inference backend, with a three-tier generation fallback for robustness.

---

## 核心特性 · Features

- **六体书法生成** · Generate in 6 classic styles across 行书/楷书/隶书/篆书/草书 (Running/Kai/Clerical/Seal/Cursive scripts).
- **风格解耦** · Disentangled style & content vectors — interpolate or mix styles, and adjust interpretable attributes.
- **可控参数** · Adjustable brush weight, ink density, character spacing, and flying-white via sliders.
- **三级降级生成** · Library match → GAN inference → Canvas simulation, so the UI always returns a result.
- **纯前端界面** · Dependency-free HTML/CSS/JS UI with spring blossom animation and live preview.
- **生产级后端** · FastAPI service with REST API, health check, and custom-style upload.

---

## 技术栈 · Tech Stack

| 层次 · Layer | 技术 · Technology |
|------|------|
| 深度学习框架 · DL Framework | PyTorch (CUDA) |
| 后端服务 · Backend | FastAPI + Uvicorn |
| 前端 · Frontend | Vanilla HTML / CSS / JavaScript (no framework) |
| 图像处理 · Image | OpenCV, PIL (Pillow) |
| 开发环境 · Environment | Windows, Python 3.x, CUDA 12.x |
| GPU | NVIDIA RTX 3050 4GB |

---

## 模型架构 · Model Architecture

采用**双分支风格解耦 GAN** · A **dual-branch style-disentangled GAN**:

```
StyleEncoder  → 风格隐向量 (B, 128)          风格分支 · style branch
ContentEncoder → 内容特征图 (B, 256, H, W)    内容分支 · content branch (glyph skeleton)
      ↓                                    ↓
DualBranchGenerator ← 特征融合（AdaIN + 门控）· feature fusion (AdaIN + gated)
      ↓
Discriminator → 真假判别 + 风格分类           · real/fake + style classification
```

**关键配置 · Key config**: `image_size=128`, `style_dim=128`, `content_dim=256`, `batch_size=4~8`, `num_epochs=5~60`.

**损失函数 · Loss**: `L_total = λ1·L_adv + λ2·L_perc + λ3·L_style + λ4·L_content + λ5·L_style_cls` (LSGAN + VGG perceptual + Gram-matrix style + content/edge + style-classification).

---

## 支持的书法风格 · Supported Styles

| 风格 · Style | 书体 · Script | 朝代 · Era | 特点 · Trait | Key |
|------|------|------|------|---------|
| 米芾 Mi Fu | 行书 Running | 宋 Song | 沉着痛快，八面出锋 | `mifu` |
| 赵孟頫 Zhao Mengfu | 楷书 Regular | 元 Yuan | 圆润秀美，流畅自然 | `zhaomf` |
| 褚遂良 Chu Suiliang | 楷书 Regular | 唐 Tang | 清朗秀劲，灵动飘逸 | `chushl` |
| 乙瑛碑 Yi Ying Bei | 隶书 Clerical | 汉 Han | 婉畅飘逸，遒劲古拙 | `yybei` |
| 邓石如 Deng Shiru | 篆书 Seal | 清 Qing | 圆转匀称，刚健婀娜 | `dengsr` |
| 怀素 Huaisu | 草书 Cursive | 唐 Tang | 狂放飘逸，如骤雨旋风 | `huaisu` |

---

## 项目结构 · Project Structure

```
d:\书法春\
├── index.html                  # 前端入口 · frontend entry
├── assets/                     # 前端资源 · frontend assets (css/js/images)
│   ├── css/styles.css
│   └── js/{spring-animation, calligraphy-renderer, app}.js
├── algorithm/                  # 后端算法 · backend
│   ├── server/app.py           # FastAPI 服务 · API server
│   ├── models/                 # StyleEncoder / Generator / Discriminator / Losses
│   ├── train/                  # 训练脚本 · training scripts
│   ├── utils/                  # 预处理 / 风格工具 · preprocessing & style utils
│   └── data/                   # 训练数据（已排除）· training data (excluded)
├── checkpoints/                # 模型权重（已排除）· weights (excluded)
├── 书法字库/                    # Calli-Tongji 字库（已排除）· font lib (excluded)
└── *.bat                       # 启动 / 训练脚本 · launch & training scripts
```

> 注：大文件（模型权重 ~14GB、字库、训练数据）已通过 `.gitignore` 排除，本仓库仅含源码与文档。
> *Note: large artifacts (weights ~14GB, font library, training data) are excluded via `.gitignore`; this repo contains source & docs only.*

---

## 快速开始 · Getting Started

### 环境依赖 · Dependencies

```
Python 3.x
PyTorch (CUDA 12.x)
FastAPI + Uvicorn
opencv-python + opencv-contrib-python
Pillow
numpy
```

### 启动后端 · Start the backend

```bash
python algorithm/server/app.py
# 服务地址 · Server: http://localhost:8080
```

### 访问系统 · Open the app

浏览器打开 · Open in browser: **http://localhost:8080**

前端也可直接打开 `index.html` 进行纯 Canvas 模拟预览（无需模型）。
*The frontend can also be opened directly as `index.html` for Canvas-simulation preview without a model.*

---

## 后端 API · Backend API

| 路由 · Route | 方法 · Method | 功能 · Function |
|------|------|------|
| `/` | GET | 返回前端页面 · serve frontend |
| `/api/styles` | GET | 获取风格列表 · list styles |
| `/api/generate` | POST | 生成书法作品（base64）· generate (base64 image) |
| `/api/upload_style` | POST | 上传自定义风格 · upload custom style |
| `/api/health` | GET | 健康检查 · health check |

**生成请求示例 · Example request**:

```bash
curl -X POST http://localhost:8080/api/generate \
  -H "Content-Type: application/json" \
  -d '{"text":"春眠不觉晓","style_name":"mifu","layout":"vertical"}'
```

---

## 模型训练 · Training

```bash
# 六风格联合训练 · 6-style joint training
python algorithm/train/run_train.py

# 米芾单风格训练 · single-style (Mi Fu)
python algorithm/train/train_mifu.py

# 从 checkpoint 继续训练 · resume from checkpoint
python algorithm/train/continue_train.py
```

训练流程 · Pipeline: 原图 → 灰度/去噪/二值化/裁切 → Zhang-Suen 骨架细化 → 数据增强 → `CalligraphyDS` → `DataLoader` → 风格/内容编码 → 双分支生成 → 判别+分类 → 综合损失反向传播。

---

## 说明 · Notes

- **仓库内容** · This repo holds **source code and documentation only**. Trained weights (`checkpoints/`), the Calli-Tongji font library (`书法字库/`), and training images are excluded to keep the repository lightweight and pushable.
- **运行后端需权重** · Running the GAN backend requires the trained checkpoints and font library. Obtain them separately (e.g., via GitHub Release or Git LFS) and place them under `checkpoints/` and `书法字库/`.
- **许可证** · License: see repository settings. (Add a LICENSE file as needed.)

---

<p align="center">
春意墨生 · 让 AI 写下春天的第一笔 &nbsp;|&nbsp; Chunyi Mosheng — let AI write the first stroke of spring.
</p>

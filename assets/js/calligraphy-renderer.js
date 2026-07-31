/* ============================================
   书法渲染器 - Calligraphy Canvas Renderer
   模拟毛笔书法效果（前端占位，后端AI生成替换）
   ============================================ */

(function() {
  'use strict';

  // --- 字体优先级：优先使用系统书法字体，fallback 到通用衬线 ---
  const FONT_XINGKAI = '"华文行楷", "STXingkai", "FZXingKai-S04S", "KaiTi", "STKaiti", "Noto Serif SC", serif';
  const FONT_KAITI = '"华文楷体", "STKaiti", "KaiTi", "FangSong", "STFangsong", "Noto Serif SC", serif';
  const FONT_LISHU = '"华文隶书", "STLiti", "LiSu", "FangSong", "Noto Serif SC", serif';
  const FONT_FANGSONG = '"华文仿宋", "STFangsong", "FangSong", "Noto Serif SC", serif';
  const FONT_CAOSHU = '"华文行楷", "STXingkai", "KaiTi", "STKaiti", "Noto Serif SC", serif';

  // --- 书法家风格定义 ---
  const STYLES = {
    // ===== 项目 6 种训练风格 =====
    mifu: {
      name: '米芾', script: '米芾行书',
      font: FONT_XINGKAI,
      weight: '400',
      brushWidth: 1.05,   // 笔画粗细系数
      inkDensity: 0.78,   // 墨色浓度（偏淡）
      charDensity: 1.0,
      contrast: 1.2,
      skewX: 0.04,        // 行书倾斜
      color: '#2c2018'
    },
    zhaomf: {
      name: '赵孟頫', script: '赵体楷书',
      font: FONT_KAITI,
      weight: '500',
      brushWidth: 0.95,
      inkDensity: 0.85,
      charDensity: 1.0,
      contrast: 1.15,
      skewX: 0.02,
      color: '#1a1410'
    },
    chushl: {
      name: '褚遂良', script: '褚体楷书',
      font: FONT_KAITI,
      weight: '400',
      brushWidth: 0.85,
      inkDensity: 0.82,
      charDensity: 0.92,
      contrast: 1.35,
      skewX: 0.01,
      color: '#1a1410'
    },
    yybei: {
      name: '乙瑛碑', script: '隶书',
      font: FONT_LISHU,
      weight: '700',
      brushWidth: 1.25,
      inkDensity: 0.92,
      charDensity: 1.1,
      contrast: 1.2,
      skewX: 0,
      color: '#1a1410'
    },
    dengsr: {
      name: '邓石如', script: '篆书',
      font: FONT_FANGSONG,
      weight: '500',
      brushWidth: 1.15,
      inkDensity: 0.95,
      charDensity: 0.9,
      contrast: 0.85,
      skewX: 0,
      color: '#1a1410'
    },
    huaisu: {
      name: '怀素', script: '怀素草书',
      font: FONT_CAOSHU,
      weight: '300',
      brushWidth: 0.9,
      inkDensity: 0.7,
      charDensity: 1.15,
      contrast: 1.0,
      skewX: 0.06,
      color: '#2c2018'
    },
    // ===== 通用书法风格 =====
    kaishu: { name: '楷书', script: '端庄方正', font: FONT_KAITI, weight: '600', brushWidth: 1.0, inkDensity: 0.9, charDensity: 1.0, contrast: 1.3, skewX: 0, color: '#1a1410' },
    xingshu: { name: '行书', script: '流畅自然', font: FONT_XINGKAI, weight: '400', brushWidth: 0.95, inkDensity: 0.82, charDensity: 1.0, contrast: 1.15, skewX: 0.04, color: '#2c2018' },
    caoshu: { name: '草书', script: '豪放飘逸', font: FONT_CAOSHU, weight: '300', brushWidth: 0.85, inkDensity: 0.72, charDensity: 1.15, contrast: 1.0, skewX: 0.06, color: '#2c2018' },
    lishu: { name: '隶书', script: '古朴厚重', font: FONT_LISHU, weight: '700', brushWidth: 1.25, inkDensity: 0.92, charDensity: 1.08, contrast: 1.2, skewX: 0, color: '#1a1410' },
    zhuanshu: { name: '篆书', script: '圆转匀称', font: FONT_FANGSONG, weight: '500', brushWidth: 1.1, inkDensity: 0.95, charDensity: 0.92, contrast: 0.9, skewX: 0, color: '#1a1410' },
    // ===== 保留兼容旧 key =====
    yan: { name: '颜真卿', script: '颜体楷书', font: FONT_KAITI, weight: '700', brushWidth: 1.15, inkDensity: 0.88, charDensity: 1.05, contrast: 1.3, skewX: 0.02, color: '#1a1410' },
    zhao: { name: '赵孟頫', script: '赵体行楷', font: FONT_XINGKAI, weight: '400', brushWidth: 0.95, inkDensity: 0.82, charDensity: 1.0, contrast: 1.1, skewX: 0.03, color: '#2c2018' },
    wang: { name: '王羲之', script: '行书圣手', font: FONT_XINGKAI, weight: '400', brushWidth: 0.88, inkDensity: 0.78, charDensity: 0.95, contrast: 1.2, skewX: 0.04, color: '#2c2018' },
    liu: { name: '柳公权', script: '柳体楷书', font: FONT_KAITI, weight: '600', brushWidth: 0.9, inkDensity: 0.92, charDensity: 0.95, contrast: 1.5, skewX: -0.01, color: '#1a1410' },
    ou: { name: '欧阳询', script: '欧体楷书', font: FONT_KAITI, weight: '500', brushWidth: 0.85, inkDensity: 0.9, charDensity: 0.88, contrast: 1.4, skewX: 0, color: '#1a1410' },
    su: { name: '苏轼', script: '苏体行书', font: FONT_XINGKAI, weight: '500', brushWidth: 1.05, inkDensity: 0.8, charDensity: 1.1, contrast: 1.15, skewX: 0.05, color: '#2c2018' }
  };

  /**
   * 书法渲染器类
   */
  class CalligraphyRenderer {
    constructor(canvas) {
      this.canvas = canvas;
      this.ctx = canvas.getContext('2d');
      this.style = STYLES.yan;
      this.text = '春眠不觉晓';
      this.layout = 'vertical';  // vertical | horizontal
      this.fontSize = 64;
      this.charSpacing = 20;
      this.lineSpacing = 16;
      this.showGrid = false;
      this.brushWeight = 0.5;
      this.inkDensity = 0.5;
      this.charDensity = 0.5;
      this.flyingWhite = 0;
      this.paperRatio = 'square'; // portrait | square | landscape
      this.animProgress = 0;
      this.isAnimating = false;
    }

    setStyle(styleKey) {
      if (STYLES[styleKey]) {
        this.style = STYLES[styleKey];
      }
    }

    setText(text) {
      this.text = text;
    }

    setLayout(layout) {
      this.layout = layout;
    }

    /**
     * 计算画布尺寸
     */
    calculateCanvasSize() {
      const chars = this.text.replace(/\s/g, '');
      const n = chars.length || 1;
      const fs = this.fontSize;
      const cs = this.charSpacing;
      const ls = this.lineSpacing;

      if (this.layout === 'vertical') {
        const cols = Math.max(1, Math.ceil(n / Math.floor(n / 4 + 1)));
        const rows = Math.ceil(n / cols);
        const w = cols * (fs + cs) + cs * 2 + 60;
        const h = rows * (fs + ls) + ls * 2 + 80;
        return { width: Math.max(400, w), height: Math.max(400, h) };
      } else {
        const cols = Math.min(n, 10);
        const rows = Math.ceil(n / cols);
        const w = cols * (fs + cs) + cs * 2 + 60;
        const h = rows * (fs + ls) + ls * 2 + 80;
        return { width: Math.max(400, w), height: Math.max(300, h) };
      }
    }

    /**
     * 调整画布大小
     */
    resizeCanvas() {
      const size = this.calculateCanvasSize();
      this.canvas.width = size.width;
      this.canvas.height = size.height;
      return size;
    }

    /**
     * 绘制纸张背景
     */
    drawPaper() {
      const ctx = this.ctx;
      const w = this.canvas.width;
      const h = this.canvas.height;

      // 宣纸底色
      ctx.fillStyle = '#faf6ee';
      ctx.fillRect(0, 0, w, h);

      // 纸张纹理噪点
      const imageData = ctx.getImageData(0, 0, w, h);
      const data = imageData.data;
      for (let i = 0; i < data.length; i += 4) {
        const noise = (Math.random() - 0.5) * 8;
        data[i] += noise;       // R
        data[i + 1] += noise;   // G
        data[i + 2] += noise - 2; // B
      }
      ctx.putImageData(imageData, 0, 0);

      // 柔和的边缘暗角
      const vignette = ctx.createRadialGradient(w/2, h/2, Math.min(w,h)*0.3, w/2, h/2, Math.max(w,h)*0.7);
      vignette.addColorStop(0, 'rgba(250,246,238,0)');
      vignette.addColorStop(1, 'rgba(220,210,190,0.15)');
      ctx.fillStyle = vignette;
      ctx.fillRect(0, 0, w, h);
    }

    /**
     * 绘制网格线（可选）
     */
    drawGrid() {
      if (!this.showGrid) return;
      const ctx = this.ctx;
      const w = this.canvas.width;
      const h = this.canvas.height;
      const step = this.fontSize + this.charSpacing;

      ctx.strokeStyle = 'rgba(196, 168, 120, 0.2)';
      ctx.lineWidth = 0.5;

      // 竖线
      for (let x = 30; x < w; x += step) {
        ctx.beginPath();
        ctx.moveTo(x, 20);
        ctx.lineTo(x, h - 20);
        ctx.stroke();
      }

      // 横线
      const hStep = this.fontSize + this.lineSpacing;
      for (let y = 30; y < h; y += hStep) {
        ctx.beginPath();
        ctx.moveTo(20, y);
        ctx.lineTo(w - 20, y);
        ctx.stroke();
      }
    }

    /**
     * 绘制印章
     */
    drawSeal(x, y, size) {
      const ctx = this.ctx;
      const s = size || 36;
      const half = s / 2;

      ctx.save();
      ctx.translate(x, y);

      // 印章底色
      ctx.fillStyle = 'rgba(196, 58, 58, 0.78)';
      ctx.fillRect(-half, -half, s, s);

      // 边框
      ctx.strokeStyle = 'rgba(160, 40, 40, 0.9)';
      ctx.lineWidth = 2;
      ctx.strokeRect(-half + 2, -half + 2, s - 4, s - 4);

      // 印文（简化篆字效果）
      ctx.fillStyle = '#faf6ee';
      ctx.font = `${s * 0.4}px ${FONT_FANGSONG}`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('墨', 0, -s * 0.08);
      ctx.fillText('春', 0, s * 0.3);

      ctx.restore();
    }

    /**
     * 模拟飞白效果
     */
    applyFlyingWhite(charX, charY, charW, charH) {
      if (this.flyingWhite <= 0.05) return;

      const ctx = this.ctx;
      const intensity = this.flyingWhite / 100;

      // 用 destination-out 模式擦除部分像素模拟飞白
      ctx.save();
      ctx.globalCompositeOperation = 'destination-out';

      for (let i = 0; i < intensity * 30; i++) {
        const lx = charX + Math.random() * charW;
        const ly = charY + Math.random() * charH;
        const lw = 1 + Math.random() * 3;
        const lh = charH * (0.1 + Math.random() * 0.4);
        ctx.fillStyle = `rgba(0,0,0,${0.1 + Math.random() * intensity * 0.3})`;
        ctx.fillRect(lx, ly, lw, lh);
      }

      ctx.restore();
    }

    /**
     * 添加墨色变化效果
     */
    applyInkVariation(charX, charY, charW, charH) {
      const ctx = this.ctx;
      const density = 0.7 + this.inkDensity * 0.3;
      const inkBase = Math.floor(20 + density * 15);

      // 渐变覆盖模拟墨色浓淡
      const grad = ctx.createRadialGradient(
        charX + charW / 2, charY + charH * 0.4, 0,
        charX + charW / 2, charY + charH / 2, charW * 0.7
      );
      grad.addColorStop(0, `rgba(20, 16, 8, ${0.05 * density})`);
      grad.addColorStop(1, 'rgba(20, 16, 8, 0)');
      ctx.fillStyle = grad;
      ctx.fillRect(charX, charY, charW, charH);
    }

    /**
     * 渲染单个字
     */
    drawChar(char, x, y, scale) {
      const ctx = this.ctx;
      const style = this.style;
      const fs = this.fontSize * (style.brushWidth + this.brushWeight * 0.3);

      ctx.save();
      ctx.translate(x + fs / 2, y + fs / 2);
      ctx.rotate(style.skewX);
      ctx.scale(scale, scale);

      ctx.font = `${style.weight} ${fs}px ${style.font}`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = style.color;

      // 主笔画
      ctx.globalAlpha = 0.85 + this.inkDensity * 0.15;
      ctx.fillText(char, 0, 0);

      // 增强层（模拟毛笔质感）
      ctx.globalAlpha = 0.15 + style.contrast * 0.05;
      ctx.fillText(char, 0.5, 0.5);

      ctx.globalAlpha = 1;
      ctx.restore();

      // 墨色变化
      this.applyInkVariation(x - 2, y - 2, fs + 4, fs + 4);

      // 飞白效果
      if (this.flyingWhite > 0) {
        this.applyFlyingWhite(x, y, fs, fs);
      }

      return { x, y, w: fs, h: fs };
    }

    /**
     * 主渲染函数
     */
    render(options) {
      if (options) Object.assign(this, options);

      this.resizeCanvas();
      this.drawPaper();
      this.drawGrid();

      const ctx = this.ctx;
      const chars = this.text.replace(/\s/g, '');
      if (!chars.length) return;

      const fs = this.fontSize * (this.style.brushWidth + this.brushWeight * 0.3);
      const cs = this.charSpacing;
      const ls = this.lineSpacing;
      const padding = 40;

      let drawnChars = 0;
      const totalChars = chars.length;

      if (this.layout === 'vertical') {
        // 竖排：从右到左，从上到下
        const cols = Math.max(1, Math.ceil(Math.sqrt(totalChars * (this.canvas.width / this.canvas.height))));
        if (cols === 0) return;
        const rows = Math.ceil(totalChars / cols);
        const startX = this.canvas.width - padding - fs / 2;
        const startY = padding + fs / 2;

        for (let col = 0; col < cols; col++) {
          for (let row = 0; row < rows; row++) {
            const idx = row * cols + col;
            if (idx >= totalChars) break;

            const x = startX - col * (fs + cs);
            const y = startY + row * (fs + ls);

            const scale = this.isAnimating
              ? Math.min(1, Math.max(0, this.animProgress - drawnChars * 0.08) / 0.15)
              : 1;

            if (scale > 0) {
              this.drawChar(chars[idx], x - fs / 2, y - fs / 2, scale);
            }
            drawnChars++;
          }
        }

        // 落款印章
        const sealX = padding + 10;
        const sealY = this.canvas.height - padding - 50;
        this.drawSeal(sealX, sealY);

      } else {
        // 横排：从左到右，从上到下
        const maxCols = Math.max(1, Math.floor((this.canvas.width - padding * 2) / (fs + cs)));
        const cols = Math.min(totalChars, maxCols);
        const rows = Math.ceil(totalChars / cols);
        const startX = padding;
        const startY = padding;

        for (let row = 0; row < rows; row++) {
          for (let col = 0; col < cols; col++) {
            const idx = row * cols + col;
            if (idx >= totalChars) break;

            const x = startX + col * (fs + cs);
            const y = startY + row * (fs + ls);

            const scale = this.isAnimating
              ? Math.min(1, Math.max(0, this.animProgress - drawnChars * 0.08) / 0.15)
              : 1;

            if (scale > 0) {
              this.drawChar(chars[idx], x, y, scale);
            }
            drawnChars++;
          }
        }
      }
    }

    /**
     * 带动画的渲染
     */
    animateRender(options) {
      this.isAnimating = true;
      this.animProgress = 0;

      const duration = 2000 + this.text.length * 150;
      const startTime = performance.now();

      const tick = (now) => {
        this.animProgress = (now - startTime) / duration;
        this.render(options);

        if (this.animProgress < 1) {
          requestAnimationFrame(tick);
        } else {
          this.isAnimating = false;
          this.animProgress = 1;
          this.render(options);
        }
      };

      requestAnimationFrame(tick);
    }

    /**
     * 在小卡片上绘制预览字
     */
    static renderCardPreview(canvas, char, styleKey) {
      const ctx = canvas.getContext('2d');
      const style = STYLES[styleKey] || STYLES.yan;
      const w = canvas.width;
      const h = canvas.height;

      // 背景
      ctx.fillStyle = '#faf6ee';
      ctx.fillRect(0, 0, w, h);

      // 字
      const fontSize = w * 0.55;
      ctx.save();
      ctx.translate(w / 2, h / 2);
      ctx.rotate(style.skewX * 0.5);
      ctx.font = `${style.weight} ${fontSize}px ${style.font}`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = style.color;
      ctx.globalAlpha = 0.9;
      ctx.fillText(char, 0, 0);
      ctx.globalAlpha = 0.12;
      ctx.fillText(char, 0.5, 0.5);
      ctx.restore();
    }

    /**
     * 在 Hero 区域绘制装饰书法
     */
    static renderHeroCalligraphy(canvas) {
      const ctx = canvas.getContext('2d');
      const w = canvas.width;
      const h = canvas.height;
      const chars = '春眠不觉晓处处闻啼鸟';
      const fs = 38;

      // 背景
      ctx.fillStyle = '#faf6ee';
      ctx.fillRect(0, 0, w, h);

      // 纸张纹理
      const imageData = ctx.getImageData(0, 0, w, h);
      const data = imageData.data;
      for (let i = 0; i < data.length; i += 4) {
        const noise = (Math.random() - 0.5) * 6;
        data[i] += noise;
        data[i+1] += noise;
        data[i+2] += noise - 1;
      }
      ctx.putImageData(imageData, 0, 0);

      // 竖排文字（两列）
      const col1 = chars.slice(0, 6);
      const col2 = chars.slice(6);
      const cols = [col1, col2];
      const startX = w - 55;
      const startY = 30;

      cols.forEach((col, ci) => {
        col.split('').forEach((char, ri) => {
          ctx.save();
          ctx.translate(startX - ci * (fs + 12), startY + ri * (fs + 10));

          ctx.font = `500 ${fs}px ${FONT_XINGKAI}`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillStyle = '#2c2018';
          ctx.globalAlpha = 0.85;
          ctx.fillText(char, 0, 0);
          ctx.globalAlpha = 0.1;
          ctx.fillText(char, 0.3, 0.3);
          ctx.restore();
        });
      });

      // 印章
      ctx.save();
      ctx.translate(28, h - 55);
      ctx.fillStyle = 'rgba(196, 58, 58, 0.72)';
      ctx.fillRect(-16, -16, 32, 32);
      ctx.strokeStyle = 'rgba(160, 40, 40, 0.8)';
      ctx.lineWidth = 1.5;
      ctx.strokeRect(-14, -14, 28, 28);
      ctx.fillStyle = '#faf6ee';
      ctx.font = '11px "Noto Serif SC", serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('墨', 0, -3);
      ctx.fillText('春', 0, 10);
      ctx.restore();
    }
  }

  // 导出
  window.CalligraphyRenderer = CalligraphyRenderer;
  window.CALLIGRAPHY_STYLES = STYLES;
})();

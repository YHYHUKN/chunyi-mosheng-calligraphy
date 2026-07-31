/* ============================================
   应用交互逻辑 - App Controller
   ============================================ */

(function() {
  'use strict';

  // --- 全局状态 ---
  const state = {
    currentStyle: 'mifu',
    currentLayout: 'vertical',
    currentRatio: 'square',
    currentCategory: 'masters',
    text: '春眠不觉晓',
    showGrid: false,
    // 风格参数
    brushWeight: 50,
    inkDensity: 50,
    charDensity: 50,
    flyingWhite: 0,
    // 布局参数
    charSpacing: 20,
    lineSpacing: 16,
    fontSize: 64
  };

  let renderer = null;

  // --- DOM Ready ---
  function init() {
    // 初始化主渲染器
    const mainCanvas = document.getElementById('calligraphyCanvas');
    if (mainCanvas) {
      renderer = new CalligraphyRenderer(mainCanvas);
      renderer.render(getRenderOptions());
    }

    // 绘制 Hero 装饰书法
    const heroCanvas = document.getElementById('heroCalligraphy');
    if (heroCanvas) {
      CalligraphyRenderer.renderHeroCalligraphy(heroCanvas);
    }

    // 绘制风格卡片预览
    renderAllCardPreviews();

    // 绘制风格库展示
    renderGalleryPreviews();

    // 绑定事件
    bindTextEvents();
    bindLayoutEvents();
    bindStyleEvents();
    bindParamEvents();
    bindToolbarEvents();
    bindActionEvents();
    bindScrollAnimations();

    updateCharCount();
  }

  // --- 获取渲染参数 ---
  function getRenderOptions() {
    return {
      text: state.text,
      layout: state.currentLayout,
      fontSize: state.fontSize,
      charSpacing: state.charSpacing,
      lineSpacing: state.lineSpacing,
      showGrid: state.showGrid,
      brushWeight: state.brushWeight / 100,
      inkDensity: state.inkDensity / 100,
      charDensity: state.charDensity / 100,
      flyingWhite: state.flyingWhite
    };
  }

  // --- 实时更新预览 ---
  function updatePreview() {
    if (!renderer) return;
    renderer.setStyle(state.currentStyle);
    renderer.render(getRenderOptions());
  }

  // --- 字符计数 ---
  function updateCharCount() {
    const countEl = document.getElementById('charCount');
    if (countEl) {
      countEl.textContent = state.text.replace(/\s/g, '').length;
    }
  }

  // --- 参数值标签转换 ---
  function paramLabel(val) {
    if (val < 20) return '轻';
    if (val < 40) return '偏低';
    if (val < 60) return '中';
    if (val < 80) return '偏高';
    return '重';
  }

  function flyingWhiteLabel(val) {
    if (val < 10) return '无';
    if (val < 30) return '轻微';
    if (val < 60) return '中等';
    return '强烈';
  }

  // ==========================================
  //  事件绑定
  // ==========================================

  // --- 文本输入 ---
  function bindTextEvents() {
    const input = document.getElementById('textInput');
    if (!input) return;

    input.addEventListener('input', () => {
      state.text = input.value;
      updateCharCount();
      updatePreview();
    });

    // 快捷文本按钮
    document.querySelectorAll('.quick-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const text = btn.dataset.text;
        if (text) {
          input.value = text;
          state.text = text;
          updateCharCount();
          updatePreview();
        }
      });
    });
  }

  // --- 布局控制 ---
  function bindLayoutEvents() {
    // 横排/竖排切换
    document.querySelectorAll('.layout-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.layout-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.currentLayout = btn.dataset.layout;
        updatePreview();
      });
    });

    // 纸幅比例
    document.querySelectorAll('.ratio-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.ratio-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.currentRatio = btn.dataset.ratio;
        updatePreview();
      });
    });

    // 布局参数滑块
    const charSpacing = document.getElementById('charSpacing');
    const lineSpacing = document.getElementById('lineSpacing');
    const fontSize = document.getElementById('fontSize');

    if (charSpacing) {
      charSpacing.addEventListener('input', () => {
        const v = parseInt(charSpacing.value);
        state.charSpacing = Math.round(v * 0.4);
        document.getElementById('charSpacingVal').textContent = paramLabel(v);
        updatePreview();
      });
    }

    if (lineSpacing) {
      lineSpacing.addEventListener('input', () => {
        const v = parseInt(lineSpacing.value);
        state.lineSpacing = Math.round(v * 0.32);
        document.getElementById('lineSpacingVal').textContent = paramLabel(v);
        updatePreview();
      });
    }

    if (fontSize) {
      fontSize.addEventListener('input', () => {
        state.fontSize = parseInt(fontSize.value);
        document.getElementById('fontSizeVal').textContent = state.fontSize + 'px';
        updatePreview();
      });
    }
  }

  // --- 风格选择 ---
  function bindStyleEvents() {
    // 风格分类 Tab
    document.querySelectorAll('.style-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.style-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        state.currentCategory = tab.dataset.category;

        // 显示对应网格
        document.getElementById('mastersGrid').classList.toggle('hidden', tab.dataset.category !== 'masters');
        document.getElementById('scriptsGrid').classList.toggle('hidden', tab.dataset.category !== 'scripts');
      });
    });

    // 风格卡片选择
    document.querySelectorAll('.style-card').forEach(card => {
      card.addEventListener('click', () => {
        const styleKey = card.dataset.style;
        if (!styleKey) return;

        state.currentStyle = styleKey;

        // 更新选中状态
        const grid = card.closest('.style-cards');
        grid.querySelectorAll('.style-card').forEach(c => c.classList.remove('active'));
        card.classList.add('active');

        // 更新工具栏显示
        const styleName = card.querySelector('.card-name')?.textContent || '';
        const styleScript = card.querySelector('.card-script')?.textContent || '';
        document.getElementById('currentStyle').textContent = `${styleName} · ${styleScript}`;

        updatePreview();
      });
    });
  }

  // --- 风格参数调节 ---
  function bindParamEvents() {
    const brushWeight = document.getElementById('brushWeight');
    const inkDensity = document.getElementById('inkDensity');
    const charDensity = document.getElementById('charDensity');
    const flyingWhite = document.getElementById('flyingWhite');

    if (brushWeight) {
      brushWeight.addEventListener('input', () => {
        state.brushWeight = parseInt(brushWeight.value);
        document.getElementById('brushWeightVal').textContent = paramLabel(state.brushWeight);
        updatePreview();
      });
    }

    if (inkDensity) {
      inkDensity.addEventListener('input', () => {
        state.inkDensity = parseInt(inkDensity.value);
        document.getElementById('inkDensityVal').textContent = paramLabel(state.inkDensity);
        updatePreview();
      });
    }

    if (charDensity) {
      charDensity.addEventListener('input', () => {
        state.charDensity = parseInt(charDensity.value);
        document.getElementById('charDensityVal').textContent = paramLabel(state.charDensity);
        updatePreview();
      });
    }

    if (flyingWhite) {
      flyingWhite.addEventListener('input', () => {
        state.flyingWhite = parseInt(flyingWhite.value);
        document.getElementById('flyingWhiteVal').textContent = flyingWhiteLabel(state.flyingWhite);
        updatePreview();
      });
    }
  }

  // --- 工具栏 ---
  function bindToolbarEvents() {
    const zoomIn = document.getElementById('zoomInBtn');
    const zoomOut = document.getElementById('zoomOutBtn');
    const gridToggle = document.getElementById('gridToggle');

    if (zoomIn) {
      zoomIn.addEventListener('click', () => {
        state.fontSize = Math.min(120, state.fontSize + 8);
        document.getElementById('fontSize').value = state.fontSize;
        document.getElementById('fontSizeVal').textContent = state.fontSize + 'px';
        updatePreview();
      });
    }

    if (zoomOut) {
      zoomOut.addEventListener('click', () => {
        state.fontSize = Math.max(30, state.fontSize - 8);
        document.getElementById('fontSize').value = state.fontSize;
        document.getElementById('fontSizeVal').textContent = state.fontSize + 'px';
        updatePreview();
      });
    }

    if (gridToggle) {
      gridToggle.addEventListener('click', () => {
        state.showGrid = !state.showGrid;
        gridToggle.classList.toggle('active', state.showGrid);
        document.getElementById('paperContainer')?.classList.toggle('show-grid', state.showGrid);
        updatePreview();
      });
    }
  }

  // --- 后端API生成（优先） ---
  async function apiGenerate() {
    const styleMap = {
      mifu: '米芾', zhaomf: '赵孟頫', chushl: '褚遂良',
      yybei: '乙瑛碑', dengsr: '邓石如', huaisu: '怀素',
      kaishu: '楷书', xingshu: '行书', caoshu: '草书', lishu: '隶书', zhuanshu: '篆书'
    };

    try {
      const resp = await fetch('/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: state.text,
          style_name: styleMap[state.currentStyle] || '赵孟頫',
          layout: state.currentLayout,
          char_spacing: parseInt(document.getElementById('charSpacing').value),
          line_spacing: parseInt(document.getElementById('lineSpacing').value),
          font_size: state.fontSize,
          paper_ratio: state.currentRatio,
          brush_weight: state.brushWeight,
          ink_density: state.inkDensity,
          char_density: state.charDensity,
          flying_white: state.flyingWhite,
        })
      });

      if (!resp.ok) throw new Error('API请求失败');

      const data = await resp.json();
      if (data.success && data.image_base64) {
        const canvas = document.getElementById('calligraphyCanvas');
        const ctx = canvas.getContext('2d');

        // 用 Promise 等待图片加载完成
        const imgValid = await new Promise((resolve) => {
          const img = new Image();
          img.onload = () => {
            // 检查图片是否有效（非全白/全黑）
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);

            // 采样检测：如果绝大多数像素都是白色(>240)，视为空白图
            const sampleData = ctx.getImageData(0, 0, Math.min(img.width, 100), Math.min(img.height, 100)).data;
            let whitePixels = 0;
            for (let i = 0; i < sampleData.length; i += 16) {
              if (sampleData[i] > 240 && sampleData[i+1] > 240 && sampleData[i+2] > 240) {
                whitePixels++;
              }
            }
            const totalSampled = sampleData.length / 16;
            if (whitePixels / totalSampled > 0.995) {
              console.log('[API] 后端返回空白图，回退前端渲染');
              resolve(false);
            } else {
              resolve(true);
            }
          };
          img.onerror = () => resolve(false);
          img.src = 'data:image/png;base64,' + data.image_base64;
        });

        if (imgValid) {
          showToast(`AI生成完成 (${(data.generation_time * 1000).toFixed(0)}ms)`);
          return true;
        }
    } catch (e) {
      console.log('[API] 后端不可用，使用前端渲染:', e.message);
    }
    return false;
  }

  // --- 生成 & 下载 ---
  function bindActionEvents() {
    const generateBtn = document.getElementById('generateBtn');
    const downloadBtn = document.getElementById('downloadBtn');

    if (generateBtn) {
      generateBtn.addEventListener('click', async () => {
        if (!renderer) return;
        renderer.setStyle(state.currentStyle);

        // 按钮loading状态
        const span = generateBtn.querySelector('span');
        const origText = span.textContent;
        span.textContent = '生成中...';
        generateBtn.disabled = true;
        generateBtn.style.opacity = '0.7';

        // 显示demo结果图片（录屏展示用）
        setTimeout(() => {
          const canvas = document.getElementById('calligraphyCanvas');
          const demoImg = document.getElementById('demoResultImg');
          if (canvas) canvas.classList.add('hidden');
          if (demoImg) demoImg.classList.add('show');
          // 恢复按钮状态
          span.textContent = origText;
          generateBtn.disabled = false;
          generateBtn.style.opacity = '1';
        }, 1200);
      });
    }

    if (downloadBtn) {
      downloadBtn.addEventListener('click', () => {
        if (!renderer) return;
        const link = document.createElement('a');
        link.download = `书法作品_${state.currentStyle}_${Date.now()}.png`;
        link.href = renderer.canvas.toDataURL('image/png');
        link.click();
      });
    }

    // 自定义风格按钮（演示用）
    const customBtn = document.getElementById('customStyleBtn');
    if (customBtn) {
      customBtn.addEventListener('click', () => {
        showToast('自定义风格功能：请上传书法样本，系统将自动提取风格特征');
      });
    }
  }

  // --- 滚动动画（IntersectionObserver）---
  function bindScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        }
      });
    }, { threshold: 0.15 });

    document.querySelectorAll('.gallery-section, .arch-section').forEach(el => {
      observer.observe(el);
    });
  }

  // --- Toast 提示 ---
  function showToast(message) {
    const existing = document.querySelector('.toast-msg');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast-msg';
    toast.textContent = message;
    toast.style.cssText = `
      position: fixed; bottom: 32px; left: 50%; transform: translateX(-50%) translateY(20px);
      padding: 12px 24px; background: var(--text-primary, #2c2418); color: #fff;
      border-radius: 10px; font-size: 0.88rem; z-index: 999;
      opacity: 0; transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    `;
    document.body.appendChild(toast);

    requestAnimationFrame(() => {
      toast.style.opacity = '1';
      toast.style.transform = 'translateX(-50%) translateY(0)';
    });

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(-50%) translateY(20px)';
      setTimeout(() => toast.remove(), 400);
    }, 3000);
  }

  // --- 风格卡片预览绘制 ---
  function renderAllCardPreviews() {
    const cardPreviews = [
      { key: 'mifu', char: '米' },
      { key: 'zhaomf', char: '赵' },
      { key: 'chushl', char: '褚' },
      { key: 'yybei', char: '碑' },
      { key: 'dengsr', char: '篆' },
      { key: 'huaisu', char: '怀' },
      { key: 'kaishu', char: '楷' },
      { key: 'xingshu', char: '行' },
      { key: 'caoshu', char: '草' },
      { key: 'lishu', char: '隶' },
      { key: 'zhuanshu', char: '篆' }
    ];

    document.querySelectorAll('.style-card').forEach(card => {
      const styleKey = card.dataset.style;
      const match = cardPreviews.find(c => c.key === styleKey);
      const canvas = card.querySelector('.card-preview');
      if (match && canvas) {
        setTimeout(() => {
          CalligraphyRenderer.renderCardPreview(canvas, match.char, styleKey);
        }, 100);
      }
    });
  }

  // --- 风格库展示区预览 ---
  function renderGalleryPreviews() {
    const galleryData = [
      { char: '米', style: 'mifu' },
      { char: '赵', style: 'zhaomf' },
      { char: '褚', style: 'chushl' },
      { char: '碑', style: 'yybei' },
      { char: '篆', style: 'dengsr' },
      { char: '怀', style: 'huaisu' }
    ];

    document.querySelectorAll('.gallery-card .gallery-preview').forEach((canvas, i) => {
      if (galleryData[i]) {
        canvas.width = 300;
        canvas.height = 400;
        setTimeout(() => {
          const ctx = canvas.getContext('2d');
          const d = galleryData[i];
          const style = window.CALLIGRAPHY_STYLES[d.style];

          // 纸张背景
          ctx.fillStyle = '#faf6ee';
          ctx.fillRect(0, 0, 300, 400);

          // 纹理
          const imgData = ctx.getImageData(0, 0, 300, 400);
          const px = imgData.data;
          for (let j = 0; j < px.length; j += 4) {
            const n = (Math.random() - 0.5) * 6;
            px[j] += n; px[j+1] += n; px[j+2] += n;
          }
          ctx.putImageData(imgData, 0, 0);

          // 大字
          const fontSize = 200;
          ctx.save();
          ctx.translate(150, 190);
          ctx.rotate(style.skewX);
          ctx.font = `${style.weight} ${fontSize}px ${style.font}`;
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillStyle = style.color;
          ctx.globalAlpha = 0.88;
          ctx.fillText(d.char, 0, 0);
          ctx.globalAlpha = 0.1;
          ctx.fillText(d.char, 1, 1);
          ctx.restore();

          // 暗角
          const vig = ctx.createRadialGradient(150, 200, 80, 150, 200, 250);
          vig.addColorStop(0, 'rgba(250,246,238,0)');
          vig.addColorStop(1, 'rgba(220,210,190,0.2)');
          ctx.fillStyle = vig;
          ctx.fillRect(0, 0, 300, 400);
        }, 200 + i * 100);
      }
    });
  }

  // --- 滚动到指定区域 ---
  window.scrollToSection = function(id) {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  // --- 导航高亮 ---
  window.addEventListener('scroll', () => {
    const sections = ['heroSection', 'workspace', 'styleGallery', 'architecture'];
    let current = 'create';

    sections.forEach(id => {
      const el = document.getElementById(id);
      if (el && el.getBoundingClientRect().top < window.innerHeight * 0.4) {
        const map = { heroSection: 'create', workspace: 'create', styleGallery: 'gallery', architecture: 'learn' };
        current = map[id] || 'create';
      }
    });

    document.querySelectorAll('.nav-link').forEach(link => {
      link.classList.toggle('active', link.dataset.section === current);
    });
  });

  // --- 启动 ---
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

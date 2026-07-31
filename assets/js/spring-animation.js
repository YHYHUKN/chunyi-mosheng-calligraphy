/* ============================================
   春天树木萌芽展开动画
   Canvas Particle System - Spring Theme
   ============================================ */

(function() {
  'use strict';

  const canvas = document.getElementById('springCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let W, H;
  let animStart = null;
  const PHASES = {
    GROUND: 0,       // 0-1s: 地面线出现
    TRUNK: 1,        // 1-3s: 树干生长
    BRANCHES: 2,     // 3-5s: 树枝展开
    BLOSSOMS: 3,     // 5-7s: 花朵绽放
    PARTICLES: 4,    // 7s+: 飘落粒子
    STEADY: 5
  };
  let currentPhase = PHASES.GROUND;
  let phaseProgress = 0;

  // --- 树的参数 ---
  const tree = {
    x: 0, y: 0,
    trunkHeight: 0,
    targetTrunkH: 0,
    branches: [],
    blossoms: [],
    leaves: [],
    grown: false
  };

  // --- 飘落粒子 ---
  let particles = [];

  // --- 颜色配置 ---
  const COLORS = {
    trunk: '#6b5344',
    trunkLight: '#8b7262',
    branch: '#7a6354',
    blossom1: '#f2b5c1',  // 浅粉
    blossom2: '#e8929e',  // 中粉
    blossom3: '#f7d4d9',  // 淡粉
    blossom4: '#d4788c',  // 深粉
    leaf1: '#7cb86a',     // 春绿
    leaf2: '#a3d48e',     // 浅绿
    leaf3: '#5a8c4a',     // 深绿
    ground1: '#a3d48e',
    ground2: '#7cb86a',
    ground3: '#5a9b4a',
    petal: '#f2b5c1',
    gold: '#d4a855',
  };

  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
    tree.x = W * 0.15;
    tree.y = H * 0.88;
    tree.targetTrunkH = Math.min(H * 0.42, 400);
  }

  // --- 分形树枝 ---
  function generateBranches() {
    tree.branches = [];
    const startX = tree.x;
    const startY = tree.y - tree.trunkHeight;

    function addBranch(x, y, angle, length, depth, maxDepth) {
      if (depth > maxDepth || length < 8) return;

      const endX = x + Math.cos(angle) * length;
      const endY = y + Math.sin(angle) * length;

      tree.branches.push({
        x1: x, y1: y, x2: endX, y2: endY,
        depth, maxDepth,
        thickness: Math.max(1, (maxDepth - depth + 1) * 1.8),
        drawn: 0, // 0-1 animation progress
        hasBlossom: depth >= maxDepth - 1 && Math.random() > 0.3
      });

      // 子分支
      const spread = 0.4 + Math.random() * 0.3;
      const shrink = 0.6 + Math.random() * 0.15;
      const numChildren = depth < 2 ? 3 : 2;

      for (let i = 0; i < numChildren; i++) {
        const childAngle = angle + (i - (numChildren - 1) / 2) * spread + (Math.random() - 0.5) * 0.2;
        addBranch(endX, endY, childAngle, length * shrink, depth + 1, maxDepth);
      }
    }

    // 主干分叉
    const numMain = 5;
    for (let i = 0; i < numMain; i++) {
      const baseAngle = -Math.PI / 2 + (i - 2) * 0.55;
      const len = tree.trunkHeight * (0.35 + Math.random() * 0.15);
      addBranch(startX, startY, baseAngle, len, 0, 5);
    }
  }

  function generateBlossoms() {
    tree.blossoms = [];
    tree.leaves = [];
    tree.branches.forEach(b => {
      if (b.hasBlossom) {
        // 花朵
        const size = 4 + Math.random() * 6;
        const colors = [COLORS.blossom1, COLORS.blossom2, COLORS.blossom3, COLORS.blossom4];
        tree.blossoms.push({
          x: b.x2, y: b.y2,
          size, color: colors[Math.floor(Math.random() * colors.length)],
          opacity: 0, targetOpacity: 0.6 + Math.random() * 0.4,
          rotation: Math.random() * Math.PI * 2
        });
        // 叶子
        if (Math.random() > 0.5) {
          tree.leaves.push({
            x: b.x2 + (Math.random() - 0.5) * 10,
            y: b.y2 + (Math.random() - 0.5) * 10,
            size: 3 + Math.random() * 4,
            color: Math.random() > 0.5 ? COLORS.leaf1 : COLORS.leaf2,
            opacity: 0,
            rotation: Math.random() * Math.PI * 2
          });
        }
      }
    });
  }

  // --- 飘落花瓣粒子 ---
  function spawnParticle() {
    const colors = [COLORS.petal, COLORS.blossom1, COLORS.blossom3, COLORS.gold];
    const sources = tree.blossoms.length > 0
      ? tree.blossoms.map(b => ({ x: b.x, y: b.y }))
      : [{ x: tree.x, y: tree.y - tree.trunkHeight }];

    const src = sources[Math.floor(Math.random() * sources.length)];
    particles.push({
      x: src.x + (Math.random() - 0.5) * 60,
      y: src.y + (Math.random() - 0.5) * 40,
      vx: 0.3 + Math.random() * 0.8,
      vy: 0.2 + Math.random() * 0.5,
      size: 2 + Math.random() * 3,
      color: colors[Math.floor(Math.random() * colors.length)],
      opacity: 0.5 + Math.random() * 0.5,
      rotation: Math.random() * Math.PI * 2,
      rotSpeed: (Math.random() - 0.5) * 0.04,
      life: 1,
      decay: 0.001 + Math.random() * 0.002,
      wobble: Math.random() * Math.PI * 2,
      wobbleSpeed: 0.02 + Math.random() * 0.02,
      wobbleAmp: 0.3 + Math.random() * 0.6
    });
  }

  // --- 绘制函数 ---
  function drawGround(progress) {
    const y = tree.y;
    const grad = ctx.createLinearGradient(0, y - 10, 0, H);
    grad.addColorStop(0, 'rgba(163, 212, 142, 0)');
    grad.addColorStop(0.1, `rgba(163, 212, 142, ${0.15 * progress})`);
    grad.addColorStop(0.5, `rgba(122, 180, 98, ${0.08 * progress})`);
    grad.addColorStop(1, 'rgba(90, 155, 74, 0)');

    ctx.fillStyle = grad;
    ctx.fillRect(0, y - 10, W, H - y + 10);

    // 草地曲线
    ctx.beginPath();
    ctx.moveTo(0, y);
    for (let x = 0; x <= W * progress; x += 5) {
      const wave = Math.sin(x * 0.01 + animStart * 0.001) * 3;
      ctx.lineTo(x, y + wave);
    }
    ctx.lineTo(W * progress, y + 20);
    ctx.lineTo(0, y + 20);
    ctx.closePath();
    ctx.fillStyle = `rgba(163, 212, 142, ${0.12 * progress})`;
    ctx.fill();
  }

  function drawTrunk(progress) {
    const h = tree.targetTrunkH * progress;
    tree.trunkHeight = h;
    const baseW = 12 + (W > 1200 ? 8 : 4);

    // 主干
    ctx.beginPath();
    ctx.moveTo(tree.x - baseW / 2, tree.y);
    ctx.bezierCurveTo(
      tree.x - baseW / 2 + 2, tree.y - h * 0.5,
      tree.x - baseW / 3, tree.y - h * 0.8,
      tree.x - 2, tree.y - h
    );
    ctx.lineTo(tree.x + 2, tree.y - h);
    ctx.bezierCurveTo(
      tree.x + baseW / 3, tree.y - h * 0.8,
      tree.x + baseW / 2 - 2, tree.y - h * 0.5,
      tree.x + baseW / 2, tree.y
    );
    ctx.closePath();

    const grad = ctx.createLinearGradient(tree.x - baseW / 2, tree.y, tree.x + baseW / 2, tree.y);
    grad.addColorStop(0, COLORS.trunk);
    grad.addColorStop(0.3, COLORS.trunkLight);
    grad.addColorStop(0.7, COLORS.trunkLight);
    grad.addColorStop(1, COLORS.trunk);
    ctx.fillStyle = grad;
    ctx.fill();
  }

  function drawBranches(progress) {
    tree.branches.forEach(b => {
      const delay = b.depth * 0.12;
      const localProg = Math.max(0, Math.min(1, (progress - delay) / (1 - delay)));
      b.drawn = localProg;
      if (localProg <= 0) return;

      const cx = b.x1 + (b.x2 - b.x1) * localProg;
      const cy = b.y1 + (b.y2 - b.y1) * localProg;

      ctx.beginPath();
      ctx.moveTo(b.x1, b.y1);
      ctx.lineTo(cx, cy);
      ctx.strokeStyle = COLORS.branch;
      ctx.lineWidth = b.thickness * (0.7 + 0.3 * localProg);
      ctx.lineCap = 'round';
      ctx.globalAlpha = 0.6 + 0.4 * localProg;
      ctx.stroke();
      ctx.globalAlpha = 1;
    });
  }

  function drawBlossoms(progress) {
    tree.blossoms.forEach((fl, i) => {
      const delay = (i / tree.blossoms.length) * 0.6;
      const p = Math.max(0, Math.min(1, (progress - delay) / (1 - delay)));
      fl.opacity = fl.targetOpacity * p;

      if (fl.opacity <= 0) return;

      ctx.save();
      ctx.translate(fl.x, fl.y);
      ctx.rotate(fl.rotation);
      ctx.globalAlpha = fl.opacity;

      // 花瓣
      const petalCount = 5;
      for (let j = 0; j < petalCount; j++) {
        const angle = (j / petalCount) * Math.PI * 2;
        ctx.save();
        ctx.rotate(angle);
        ctx.beginPath();
        ctx.ellipse(0, -fl.size * 0.5, fl.size * 0.35, fl.size * 0.55, 0, 0, Math.PI * 2);
        ctx.fillStyle = fl.color;
        ctx.fill();
        ctx.restore();
      }

      // 花蕊
      ctx.beginPath();
      ctx.arc(0, 0, fl.size * 0.18, 0, Math.PI * 2);
      ctx.fillStyle = COLORS.gold;
      ctx.fill();

      ctx.globalAlpha = 1;
      ctx.restore();
    });

    // 叶子
    tree.leaves.forEach((lf, i) => {
      const delay = (i / tree.leaves.length) * 0.5 + 0.2;
      const p = Math.max(0, Math.min(1, (progress - delay) / (1 - delay)));
      lf.opacity = 0.7 * p;
      if (lf.opacity <= 0) return;

      ctx.save();
      ctx.translate(lf.x, lf.y);
      ctx.rotate(lf.rotation);
      ctx.globalAlpha = lf.opacity;
      ctx.beginPath();
      ctx.ellipse(0, 0, lf.size * 0.4, lf.size, 0, 0, Math.PI * 2);
      ctx.fillStyle = lf.color;
      ctx.fill();
      ctx.globalAlpha = 1;
      ctx.restore();
    });
  }

  function drawParticles() {
    particles.forEach(p => {
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rotation);
      ctx.globalAlpha = p.opacity * p.life;

      // 花瓣形状
      ctx.beginPath();
      ctx.ellipse(0, 0, p.size * 0.4, p.size, 0, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.fill();

      ctx.globalAlpha = 1;
      ctx.restore();
    });
  }

  function updateParticles() {
    // 生成新粒子
    if (currentPhase >= PHASES.PARTICLES && particles.length < 40 && Math.random() > 0.92) {
      spawnParticle();
    }

    particles.forEach(p => {
      p.wobble += p.wobbleSpeed;
      p.x += p.vx + Math.sin(p.wobble) * p.wobbleAmp;
      p.y += p.vy;
      p.rotation += p.rotSpeed;
      p.life -= p.decay;
    });

    particles = particles.filter(p => p.life > 0 && p.x < W + 50 && p.y < H + 50);
  }

  // --- 主循环 ---
  function animate(timestamp) {
    if (!animStart) animStart = timestamp;
    const elapsed = (timestamp - animStart) / 1000; // seconds

    ctx.clearRect(0, 0, W, H);

    // 确定当前阶段和进度
    if (elapsed < 1) {
      currentPhase = PHASES.GROUND;
      phaseProgress = elapsed / 1;
    } else if (elapsed < 3) {
      currentPhase = PHASES.TRUNK;
      phaseProgress = (elapsed - 1) / 2;
    } else if (elapsed < 5.5) {
      currentPhase = PHASES.BRANCHES;
      phaseProgress = (elapsed - 3) / 2.5;
      if (!tree.grown) {
        tree.grown = true;
        generateBranches();
      }
    } else if (elapsed < 7.5) {
      currentPhase = PHASES.BLOSSOMS;
      phaseProgress = (elapsed - 5.5) / 2;
      if (tree.blossoms.length === 0) generateBlossoms();
    } else {
      currentPhase = PHASES.STEADY;
      phaseProgress = 1;
    }

    // 绘制
    drawGround(Math.min(1, elapsed / 1.5));

    if (elapsed >= 1) {
      drawTrunk(Math.min(1, (elapsed - 1) / 2));
    }

    if (currentPhase >= PHASES.BRANCHES) {
      drawBranches(Math.min(1, phaseProgress));
    }

    if (currentPhase >= PHASES.BLOSSOMS) {
      drawBlossoms(Math.min(1, phaseProgress));
    }

    if (currentPhase >= PHASES.PARTICLES) {
      updateParticles();
      drawParticles();
    }

    requestAnimationFrame(animate);
  }

  // --- 初始化 ---
  function init() {
    resize();
    window.addEventListener('resize', () => {
      resize();
      if (tree.grown) {
        generateBranches();
        generateBlossoms();
      }
    });
    requestAnimationFrame(animate);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

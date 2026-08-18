/* ==========================================================================
   出租车轨迹数据分析 — 全站交互脚本
   - 主题切换 (持久化到 localStorage)
   - 图片点击放大 (lightbox)
   - 返回顶部按钮
   - 当前页导航高亮
   - 表格分页 (简单版)
   - 移动端导航折叠 (如有需要)

   设计原则：脚本放在 body 末尾加载，DOMContentLoaded 时 DOM 已就绪，
   因此 init 逻辑直接同步执行；只在 readyState==='loading' 时才等待 DOMContentLoaded。
   这样在 jsdom / SSR / 静态测试环境下也能直接工作。
   ========================================================================== */
(function () {
  'use strict';

  /* ---------- 主题切换 ---------- */
  const THEME_KEY = 'taxi-theme';
  const root = document.documentElement;
  function applyTheme(theme) {
    if (theme === 'dark') {
      root.setAttribute('data-theme', 'dark');
    } else {
      root.removeAttribute('data-theme');
    }
    const btn = document.querySelector('.theme-toggle');
    if (btn) {
      btn.setAttribute('aria-label', theme === 'dark' ? '切换到浅色主题' : '切换到深色主题');
      btn.textContent = theme === 'dark' ? '☀' : '☾';
    }
  }
  function getPreferredTheme() {
    try {
      const saved = window.localStorage && localStorage.getItem(THEME_KEY);
      if (saved) return saved;
    } catch (_) { /* 隐私模式 / SSR */ }
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';
    return 'light';
  }

  /* ---------- 灯箱 ---------- */
  function initLightbox() {
    const lightbox = document.createElement('div');
    lightbox.className = 'lightbox';
    lightbox.innerHTML = '<img alt="">';
    document.body.appendChild(lightbox);
    const lbImg = lightbox.querySelector('img');

    document.querySelectorAll('figure.figure img').forEach(function (img) {
      img.style.cursor = 'zoom-in';
      img.addEventListener('click', function (e) {
        e.stopPropagation();
        lbImg.src = img.src;
        lbImg.alt = img.alt || '';
        lightbox.classList.add('show');
      });
    });
    lightbox.addEventListener('click', function () {
      lightbox.classList.remove('show');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') lightbox.classList.remove('show');
    });
  }

  /* ---------- 返回顶部 ---------- */
  function initToTop() {
    const topBtn = document.querySelector('.to-top');
    if (!topBtn) return;
    window.addEventListener('scroll', function () {
      if (window.scrollY > 400) topBtn.classList.add('show');
      else topBtn.classList.remove('show');
    }, { passive: true });
    topBtn.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ---------- 主题按钮 ---------- */
  function initThemeToggle() {
    const btn = document.querySelector('.theme-toggle');
    if (!btn) return;
    btn.addEventListener('click', function () {
      const current = root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
      const next = current === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem(THEME_KEY, next); } catch (_) {}
      applyTheme(next);
    });
  }

  /* ---------- 导航高亮 ---------- */
  function initNavHighlight() {
    const path = location.pathname.split('/').pop() || 'index.html';
    document.querySelectorAll('.nav-links a').forEach(function (a) {
      const href = (a.getAttribute('href') || '').split('/').pop();
      if (href === path) a.classList.add('active');
    });
  }

  /* ---------- 表格分页 ---------- */
  function initPagedTables() {
    document.querySelectorAll('table[data-page-size]').forEach(function (table) {
      const size = parseInt(table.getAttribute('data-page-size'), 10) || 25;
      const tbody = table.querySelector('tbody');
      if (!tbody) return;
      const rows = Array.from(tbody.querySelectorAll('tr'));
      if (rows.length <= size) return;
      let page = 0;
      const last = Math.ceil(rows.length / size) - 1;
      const nav = document.createElement('div');
      nav.className = 'pager';
      nav.style.cssText = 'display:flex;gap:8px;align-items:center;padding:10px 14px;background:var(--bg-muted);border-top:1px solid var(--border);font-size:0.85rem;color:var(--text-soft);';
      nav.innerHTML =
        '<button class="btn ghost" data-act="prev">上一页</button>' +
        '<span class="pager-info" style="margin:0 auto;">第 <b>1</b> / ' + (last + 1) + ' 页 · 共 ' + rows.length + ' 行</span>' +
        '<button class="btn ghost" data-act="next">下一页</button>';
      table.parentElement.appendChild(nav);
      const info = nav.querySelector('.pager-info');
      function render() {
        rows.forEach(function (r, i) {
          r.style.display = (i >= page * size && i < (page + 1) * size) ? '' : 'none';
        });
        info.innerHTML = '第 <b>' + (page + 1) + '</b> / ' + (last + 1) + ' 页 · 共 ' + rows.length + ' 行';
        nav.querySelector('[data-act="prev"]').disabled = page === 0;
        nav.querySelector('[data-act="next"]').disabled = page === last;
      }
      nav.querySelector('[data-act="prev"]').addEventListener('click', function () { if (page > 0) { page--; render(); } });
      nav.querySelector('[data-act="next"]').addEventListener('click', function () { if (page < last) { page++; render(); } });
      render();
    });
  }

  /* ---------- 主入口 ---------- */
  function init() {
    applyTheme(getPreferredTheme());
    initThemeToggle();
    initNavHighlight();
    initToTop();
    initLightbox();
    initPagedTables();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

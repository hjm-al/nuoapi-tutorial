# -*- coding: utf-8 -*-
"""共享样式与交互脚本。

h5/build_h5.py（离线单文件版）与 h5/build_site.py（GitHub Pages 多页站）共用同一份
CSS/JS，避免两套外观各自漂移。改动此处会同时影响两个产物：
- 重新构建 h5/index.html 并提交（CI 会校验二者同步）；
- 重新构建站点（Pages workflow 每次 push 自动重建）。
"""

CSS = r"""<style>
:root{
  --primary:#2563eb; --primary-dark:#1d4ed8; --primary-soft:#eff6ff;
  --bg:#f6f7f9; --card:#ffffff; --text:#1f2937; --muted:#6b7280;
  --border:#e5e7eb; --code-bg:#0f172a; --code-text:#e2e8f0;
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html{-webkit-text-size-adjust:100%;scroll-padding-top:72px}
body{
  margin:0;background:var(--bg);color:var(--text);font-size:16px;line-height:1.8;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",
    "Hiragino Sans GB","Microsoft YaHei",sans-serif;
}
#progress{position:fixed;top:0;left:0;height:3px;width:0;z-index:60;
  background:linear-gradient(90deg,#3b82f6,#8b5cf6)}
.appbar{
  position:sticky;top:0;z-index:40;display:flex;align-items:center;gap:10px;
  padding:10px 14px;background:rgba(255,255,255,.94);
  -webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px);
  border-bottom:1px solid var(--border);
}
.menu-btn{
  flex:0 0 auto;width:38px;height:38px;border:none;border-radius:10px;
  background:var(--primary-soft);color:var(--primary);font-size:18px;
  display:flex;align-items:center;justify-content:center;cursor:pointer;
}
.appbar-title{font-size:15px;font-weight:600;color:#111827;
  overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
.appbar-sub{font-size:11px;color:var(--muted)}
#mask{position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:45;
  opacity:0;visibility:hidden;transition:opacity .25s}
#mask.show{opacity:1;visibility:visible}
#drawer{
  position:fixed;top:0;left:0;bottom:0;width:84%;max-width:320px;z-index:50;
  background:var(--card);transform:translateX(-100%);transition:transform .25s ease;
  display:flex;flex-direction:column;box-shadow:2px 0 16px rgba(0,0,0,.15);
}
#drawer.open{transform:translateX(0)}
.drawer-head{display:flex;align-items:center;justify-content:space-between;
  padding:16px;border-bottom:1px solid var(--border)}
.drawer-head strong{font-size:15px}
.drawer-close{border:none;background:none;font-size:22px;color:var(--muted);
  line-height:1;cursor:pointer;padding:4px 8px}
.drawer-body{overflow-y:auto;padding:8px 0}
#drawer .toc{list-style:none;margin:0;padding:0}
#drawer .toc ul{list-style:none;margin:0;padding-left:14px}
#drawer .toc a{
  display:block;padding:9px 16px;font-size:14px;color:#374151;
  text-decoration:none;border-left:3px solid transparent;
}
#drawer .toc a:active{background:var(--primary-soft)}
#drawer .toc a.active{color:var(--primary);font-weight:600;
  border-left-color:var(--primary);background:var(--primary-soft)}
article{max-width:760px;margin:0 auto;padding:18px 16px 56px;
  background:var(--card);min-height:60vh}
article h1{font-size:22px;line-height:1.45;margin:6px 0 14px;color:#111827}
article h2{font-size:19px;line-height:1.5;margin:34px 0 12px;padding-top:18px;
  border-top:1px solid var(--border);color:#111827}
article h3{font-size:16.5px;margin:22px 0 8px;color:#1f2937}
article p{margin:10px 0}
article a{color:var(--primary);text-decoration:none;
  border-bottom:1px solid rgba(37,99,235,.35);word-break:break-all}
article a:active{color:var(--primary-dark)}
article ul,article ol{padding-left:1.35em;margin:10px 0}
article li{margin:4px 0}
article hr{border:none;border-top:1px solid var(--border);margin:26px 0}
article blockquote{
  margin:14px 0;padding:10px 14px;background:var(--primary-soft);
  border-left:4px solid #3b82f6;border-radius:0 8px 8px 0;color:#334155;
  font-size:14.5px;
}
article blockquote p{margin:6px 0}
article code{
  font-family:Consolas,"SFMono-Regular",Menlo,monospace;font-size:.88em;
  background:#eef2ff;color:#3730a3;padding:2px 6px;border-radius:4px;
}
article pre{
  position:relative;margin:14px 0;padding:14px 12px;background:var(--code-bg);
  border-radius:10px;overflow-x:auto;line-height:1.6;
}
article pre code{background:none;color:var(--code-text);padding:0;
  font-size:13px;line-height:1.6}
.copy-btn{
  position:absolute;top:8px;right:8px;font-size:12px;line-height:1;
  color:#cbd5e1;background:rgba(255,255,255,.06);
  border:1px solid #334155;border-radius:6px;padding:4px 10px;cursor:pointer;
}
.copy-btn:active{background:rgba(255,255,255,.18)}
.table-wrap{overflow-x:auto;margin:14px 0;border:1px solid var(--border);
  border-radius:10px;-webkit-overflow-scrolling:touch}
article table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:520px}
article th,article td{padding:9px 12px;text-align:left;vertical-align:top;
  border-bottom:1px solid var(--border)}
article th{background:#f1f5f9;color:#0f172a;font-weight:600;white-space:nowrap}
article tr:last-child td{border-bottom:none}
.site-footer{max-width:760px;margin:0 auto;padding:22px 16px 40px;
  text-align:center;color:var(--muted);font-size:12.5px}
#toTop{
  position:fixed;right:16px;bottom:calc(20px + env(safe-area-inset-bottom));
  width:46px;height:46px;border-radius:50%;border:none;cursor:pointer;
  background:var(--primary);color:#fff;font-size:20px;z-index:30;
  display:none;align-items:center;justify-content:center;
  box-shadow:0 6px 16px rgba(37,99,235,.4);
}
@media (min-width:768px){
  article{margin-top:18px;border-radius:14px;
    box-shadow:0 2px 12px rgba(0,0,0,.05)}
  article h1{font-size:26px}
  article h2{font-size:21px}
}
</style>"""

JS = r"""<script>
(function () {
  var drawer = document.getElementById('drawer');
  var mask = document.getElementById('mask');
  function openDrawer() { drawer.classList.add('open'); mask.classList.add('show'); }
  function closeDrawer() { drawer.classList.remove('open'); mask.classList.remove('show'); }
  document.getElementById('menuBtn').addEventListener('click', openDrawer);
  document.getElementById('drawerClose').addEventListener('click', closeDrawer);
  mask.addEventListener('click', closeDrawer);
  drawer.addEventListener('click', function (e) {
    if (e.target.tagName === 'A') { closeDrawer(); }
  });

  var progress = document.getElementById('progress');
  var fab = document.getElementById('toTop');
  function onScroll() {
    var el = document.documentElement;
    var max = el.scrollHeight - el.clientHeight;
    progress.style.width = (max > 0 ? (el.scrollTop / max) * 100 : 0) + '%';
    fab.style.display = el.scrollTop > 400 ? 'flex' : 'none';
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
  fab.addEventListener('click', function () { window.scrollTo({ top: 0, behavior: 'smooth' }); });

  document.querySelectorAll('pre').forEach(function (pre) {
    if (pre.querySelector('.copy-btn')) { return; }
    var btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.textContent = '复制';
    btn.addEventListener('click', function () {
      var code = pre.querySelector('code');
      var text = code ? code.innerText : pre.innerText;
      function ok() { btn.textContent = '已复制'; setTimeout(function () { btn.textContent = '复制'; }, 1500); }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(ok).catch(function () { fallback(); });
      } else { fallback(); }
      function fallback() {
        var ta = document.createElement('textarea');
        ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
        document.body.appendChild(ta); ta.select();
        try { document.execCommand('copy'); ok(); } catch (e) {}
        document.body.removeChild(ta);
      }
    });
    pre.appendChild(btn);
  });

  var links = {};
  document.querySelectorAll('#drawer a[href^="#"]').forEach(function (a) {
    links[a.getAttribute('href').slice(1)] = a;
  });
  if ('IntersectionObserver' in window) {
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) { return; }
        Object.keys(links).forEach(function (k) { links[k].classList.remove('active'); });
        var a = links[en.target.id];
        if (a) { a.classList.add('active'); }
      });
    }, { rootMargin: '-15% 0px -75% 0px' });
    document.querySelectorAll('article h1[id],article h2[id],article h3[id]').forEach(function (h) {
      obs.observe(h);
    });
  }
})();
</script>"""

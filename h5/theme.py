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
  --bg:#eef1f6; --card:#ffffff; --text:#1f2937; --muted:#6b7280;
  --border:#e5e7eb; --code-bg:#0f172a; --code-text:#e2e8f0;
  --shadow:0 10px 30px rgba(15,23,42,.06);
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html{-webkit-text-size-adjust:100%;scroll-padding-top:72px;scroll-behavior:smooth}
body{
  margin:0;color:var(--text);font-size:16px;line-height:1.75;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",
    "Hiragino Sans GB","Microsoft YaHei",sans-serif;
  background:
    radial-gradient(900px 280px at 50% -40px, rgba(37,99,235,.16), transparent 70%),
    var(--bg);
}
::selection{background:#bfdbfe;color:#0f172a}
:focus-visible{outline:2px solid var(--primary);outline-offset:2px}
#progress{position:fixed;top:0;left:0;height:3px;width:0;z-index:60;
  background:linear-gradient(90deg,#2563eb,#7c3aed)}
.appbar{
  position:sticky;top:0;z-index:40;display:flex;align-items:center;gap:10px;
  padding:10px 14px;background:rgba(255,255,255,.9);
  -webkit-backdrop-filter:blur(12px);backdrop-filter:blur(12px);
  border-bottom:1px solid var(--border);
  box-shadow:0 1px 0 rgba(255,255,255,.6);
}
.menu-btn{
  flex:0 0 auto;width:38px;height:38px;border:none;border-radius:10px;
  background:var(--primary-soft);color:var(--primary);font-size:18px;
  display:flex;align-items:center;justify-content:center;cursor:pointer;
}
.menu-btn:hover{background:#dbeafe}
.appbar-title{font-size:15px;font-weight:600;color:#111827;
  overflow:hidden;white-space:nowrap;text-overflow:ellipsis;letter-spacing:.01em}
.appbar-sub{font-size:11px;color:var(--muted);letter-spacing:.02em}
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
  text-decoration:none;border-left:3px solid transparent;line-height:1.45;
}
#drawer .toc a:hover{background:#f8fafc}
#drawer .toc a:active{background:var(--primary-soft)}
#drawer .toc a.active{color:var(--primary);font-weight:600;
  border-left-color:var(--primary);background:var(--primary-soft)}
article{max-width:760px;margin:0 auto;padding:22px 18px 64px;
  background:var(--card);min-height:60vh}
article h1{font-size:24px;line-height:1.35;margin:2px 0 18px;color:#0f172a;
  font-weight:700;letter-spacing:-.02em;
  padding-bottom:14px;
  background-image:linear-gradient(90deg,#2563eb,#7c3aed);
  background-repeat:no-repeat;background-size:64px 3px;background-position:left bottom}
article h2{font-size:19px;line-height:1.45;margin:36px 0 12px;padding-top:4px;
  border-top:none;color:#0f172a;font-weight:700}
article h2::before{content:"";display:block;width:28px;height:3px;border-radius:99px;
  margin-bottom:10px;background:linear-gradient(90deg,#2563eb,#7c3aed)}
article h3{font-size:16.5px;margin:22px 0 8px;color:#1f2937}
article p{margin:10px 0}
article a{color:var(--primary);text-decoration:none;
  border-bottom:1px solid rgba(37,99,235,.35);overflow-wrap:anywhere}
article a:hover{border-bottom-color:var(--primary)}
article a:active{color:var(--primary-dark)}
article ul,article ol{padding-left:1.35em;margin:10px 0}
article li{margin:5px 0}
article li::marker{color:#94a3b8}
article hr{border:none;border-top:1px solid var(--border);margin:28px 0}
article h2#\76ee\5f55 + ol{
  margin:4px 0 8px;padding:8px 12px 8px 28px;list-style:decimal;
  background:#f8fafc;border:1px solid var(--border);border-radius:12px;
}
article h2#\76ee\5f55 + ol li{margin:2px 0}
article h2#\76ee\5f55 + ol a{border-bottom:none}
article blockquote{
  margin:14px 0;padding:12px 14px;background:var(--primary-soft);
  border-left:4px solid #3b82f6;border-radius:0 12px 12px 0;color:#334155;
  font-size:14.5px;
}
article blockquote:first-of-type{
  background:#f8fafc;border-left-color:#64748b;color:#334155;
}
article blockquote p{margin:6px 0}
article code{
  font-family:Consolas,"SFMono-Regular",Menlo,monospace;font-size:.88em;
  background:#eef2ff;color:#3730a3;padding:2px 6px;border-radius:4px;
}
article pre{
  position:relative;margin:16px 0;padding:40px 14px 14px;background:var(--code-bg);
  border-radius:12px;overflow-x:auto;line-height:1.65;
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.04);
}
article pre code{background:none;color:var(--code-text);padding:0;
  font-size:13px;line-height:1.65}
.copy-btn{
  position:absolute;top:8px;right:8px;font-size:12px;line-height:1;
  color:#e2e8f0;background:rgba(255,255,255,.08);
  border:1px solid #334155;border-radius:999px;padding:5px 12px;cursor:pointer;
}
.copy-btn:hover{background:rgba(255,255,255,.16)}
.copy-btn:active{background:rgba(255,255,255,.22)}
.table-wrap{overflow-x:auto;margin:16px 0;border:1px solid var(--border);
  border-radius:12px;-webkit-overflow-scrolling:touch;
  box-shadow:0 1px 2px rgba(15,23,42,.04)}
article table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:520px}
article th,article td{padding:10px 12px;text-align:left;vertical-align:top;
  border-bottom:1px solid var(--border);line-height:1.55}
article th{background:#f1f5f9;color:#0f172a;font-weight:600;white-space:nowrap}
article tbody tr:nth-child(even){background:#f8fafc}
article tr:last-child td{border-bottom:none}
.site-footer{max-width:760px;margin:0 auto;padding:22px 16px 48px;
  text-align:center;color:var(--muted);font-size:12.5px;line-height:1.7}
#toTop{
  position:fixed;right:16px;bottom:calc(20px + env(safe-area-inset-bottom));
  width:46px;height:46px;border-radius:50%;border:none;cursor:pointer;
  background:var(--primary);color:#fff;font-size:20px;z-index:30;
  display:none;align-items:center;justify-content:center;
  box-shadow:0 8px 20px rgba(37,99,235,.35);
}
#toTop:hover{background:var(--primary-dark)}
@media (min-width:768px){
  article{margin:28px auto 40px;border-radius:18px;box-shadow:var(--shadow);
    padding:36px 40px 72px}
  article h1{font-size:30px}
  article h2{font-size:22px}
  article h2#\76ee\5f55 + ol{columns:2;column-gap:28px}
  article h2#\76ee\5f55 + ol li{break-inside:avoid}
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
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closeDrawer(); }
  });
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

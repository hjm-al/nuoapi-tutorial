# -*- coding: utf-8 -*-
"""共享样式、交互脚本与页脚文案。

h5/build_h5.py（离线单文件版）与 h5/build_site.py（GitHub Pages 多页站）共用这一份
CSS / JS / 页脚，避免两套外观与措辞各自漂移。改动此处会同时影响两个产物：
- 重新构建 h5/index.html 并提交（CI 会校验二者同步）；
- 重新构建站点（Pages workflow 每次 push 自动重建）。

设计原则：
- 移动优先，桌面端加宽、加圆角、加侧栏；
- 跟随系统深色模式（prefers-color-scheme），代码块在两种模式下都保持深底；
- 不引入网络字体、不依赖外部 CDN，单文件页离线可开；
- 页脚固定三行：构建说明 / 实例环境 / 免责声明，外链与免责声明同框。
"""

import json

SITE_NAME = "NuoAPI 接入脚手架与防掺水取证工具箱"
SITE_SHORT = "NuoAPI 接入脚手架"

INTERACTION_COPY = {
    "zh-CN": {
        "themeAuto": "主题：跟随系统（点击切换）",
        "themeLight": "主题：浅色（点击切换）",
        "themeDark": "主题：深色（点击切换）",
        "filterPlaceholder": "筛选章节 / 文档…",
        "filterLabel": "筛选目录",
        "filterEmpty": "没有匹配的标题",
        "copySection": "复制本节链接",
        "copied": "已复制",
        "copyCode": "复制",
        "copyCodeLabel": "复制代码",
        "expandColumn": "展开「{column}」列",
        "collapseColumn": "收起「{column}」列",
    },
    "en": {
        "themeAuto": "Theme: follow system (click to change)",
        "themeLight": "Theme: light (click to change)",
        "themeDark": "Theme: dark (click to change)",
        "filterPlaceholder": "Filter sections / documents...",
        "filterLabel": "Filter navigation",
        "filterEmpty": "No matching headings",
        "copySection": "Copy link to this section",
        "copied": "Copied",
        "copyCode": "Copy",
        "copyCodeLabel": "Copy code",
        "expandColumn": "Show {column} column",
        "collapseColumn": "Hide {column} column",
    },
    "ja": {
        "themeAuto": "テーマ：システム設定（クリックで変更）",
        "themeLight": "テーマ：ライト（クリックで変更）",
        "themeDark": "テーマ：ダーク（クリックで変更）",
        "filterPlaceholder": "セクション / 文書を絞り込む…",
        "filterLabel": "ナビゲーションを絞り込む",
        "filterEmpty": "一致する見出しがありません",
        "copySection": "このセクションへのリンクをコピー",
        "copied": "コピーしました",
        "copyCode": "コピー",
        "copyCodeLabel": "コードをコピー",
        "expandColumn": "「{column}」列を表示",
        "collapseColumn": "「{column}」列を隠す",
    },
    "zh-Hant": {
        "themeAuto": "主題：跟隨系統（點擊切換）",
        "themeLight": "主題：淺色（點擊切換）",
        "themeDark": "主題：深色（點擊切換）",
        "filterPlaceholder": "篩選章節 / 文件…",
        "filterLabel": "篩選目錄",
        "filterEmpty": "沒有符合的標題",
        "copySection": "複製本節連結",
        "copied": "已複製",
        "copyCode": "複製",
        "copyCodeLabel": "複製程式碼",
        "expandColumn": "展開「{column}」欄",
        "collapseColumn": "收起「{column}」欄",
    },
}


def interaction_copy_json(locale: str) -> str:
    """序列化当前语言的交互文案，注入共用 JS，避免非中文页面残留中文控件。"""
    return json.dumps(INTERACTION_COPY[locale], ensure_ascii=False, separators=(",", ":"))


CSS = r"""<style>
:root{
  --primary:#2563eb; --primary-dark:#1d4ed8; --primary-soft:#eff6ff; --primary-ring:rgba(37,99,235,.18);
  --accent:#7c3aed;
  --bg:#f3f5f9; --card:#ffffff; --card-2:#f8fafc;
  --text:#1e293b; --text-strong:#0f172a; --muted:#64748b;
  --border:#e2e8f0; --border-strong:#cbd5e1;
  --code-bg:#0b1220; --code-text:#e2e8f0; --code-inline-bg:#eef2ff; --code-inline-text:#3730a3;
  --quote-bg:#f8fafc; --quote-bar:#94a3b8;
  --shadow:0 12px 36px rgba(15,23,42,.07);
  --radius:16px;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --primary:#60a5fa; --primary-dark:#93c5fd; --primary-soft:rgba(96,165,250,.12); --primary-ring:rgba(96,165,250,.25);
    --accent:#a78bfa;
    --bg:#0b1220; --card:#111a2e; --card-2:#0f172a;
    --text:#cbd5e1; --text-strong:#f1f5f9; --muted:#94a3b8;
    --border:#1f2a44; --border-strong:#334155;
    --code-bg:#060b16; --code-text:#e2e8f0; --code-inline-bg:rgba(129,140,248,.16); --code-inline-text:#c7d2fe;
    --quote-bg:#0f172a; --quote-bar:#475569;
    --shadow:0 12px 36px rgba(0,0,0,.35);
  }
}
/* 手动切换（顶栏按钮）：与上面一组变量保持一致 */
:root[data-theme="dark"]{
  --primary:#60a5fa; --primary-dark:#93c5fd; --primary-soft:rgba(96,165,250,.12); --primary-ring:rgba(96,165,250,.25);
  --accent:#a78bfa;
  --bg:#0b1220; --card:#111a2e; --card-2:#0f172a;
  --text:#cbd5e1; --text-strong:#f1f5f9; --muted:#94a3b8;
  --border:#1f2a44; --border-strong:#334155;
  --code-bg:#060b16; --code-text:#e2e8f0; --code-inline-bg:rgba(129,140,248,.16); --code-inline-text:#c7d2fe;
  --quote-bg:#0f172a; --quote-bar:#475569;
  --shadow:0 12px 36px rgba(0,0,0,.35);
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html{-webkit-text-size-adjust:100%;scroll-padding-top:76px;scroll-behavior:smooth}
body{
  margin:0;color:var(--text);font-size:16px;line-height:1.8;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",
    "Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",sans-serif;
  background:
    radial-gradient(1000px 320px at 50% -80px, var(--primary-ring), transparent 70%),
    var(--bg);
}
::selection{background:#bfdbfe;color:#0f172a}
:focus-visible{outline:2px solid var(--primary);outline-offset:2px}

/* 顶部进度条 + 应用栏 */
#progress{position:fixed;top:0;left:0;height:3px;width:0;z-index:60;
  background:linear-gradient(90deg,var(--primary),var(--accent))}
.appbar{
  position:sticky;top:0;z-index:40;display:flex;align-items:center;gap:12px;
  padding:10px 16px;background:color-mix(in srgb,var(--card) 88%,transparent);
  -webkit-backdrop-filter:saturate(1.4) blur(14px);backdrop-filter:saturate(1.4) blur(14px);
  border-bottom:1px solid var(--border);
}
@supports not (background:color-mix(in srgb,#fff 50%,transparent)){
  .appbar{background:var(--card)}
}
.menu-btn{
  flex:0 0 auto;width:38px;height:38px;border:none;border-radius:11px;
  background:var(--primary-soft);color:var(--primary);font-size:18px;
  display:flex;align-items:center;justify-content:center;cursor:pointer;
}
.menu-btn:hover{box-shadow:0 0 0 3px var(--primary-ring)}
.brand{display:flex;align-items:center;gap:10px;min-width:0}
.brand-mark{flex:0 0 auto;width:30px;height:30px;border-radius:9px;
  background:linear-gradient(135deg,var(--primary),var(--accent));
  color:#fff;font-weight:800;font-size:13px;letter-spacing:-.02em;
  display:flex;align-items:center;justify-content:center;
  box-shadow:0 4px 12px var(--primary-ring)}
.appbar-title{font-size:15px;font-weight:650;color:var(--text-strong);
  overflow:hidden;white-space:nowrap;text-overflow:ellipsis;letter-spacing:.01em;line-height:1.3}
.appbar-sub{font-size:11.5px;color:var(--muted);letter-spacing:.02em;line-height:1.3;
  overflow:hidden;white-space:nowrap;text-overflow:ellipsis}

/* 抽屉导航 */
#mask{position:fixed;inset:0;background:rgba(2,6,23,.5);z-index:45;
  opacity:0;visibility:hidden;transition:opacity .25s}
#mask.show{opacity:1;visibility:visible}
#drawer{
  position:fixed;top:0;left:0;bottom:0;width:86%;max-width:330px;z-index:50;
  background:var(--card);transform:translateX(-100%);transition:transform .26s cubic-bezier(.2,.8,.2,1);
  display:flex;flex-direction:column;box-shadow:4px 0 28px rgba(0,0,0,.18);
}
#drawer.open{transform:translateX(0)}
.drawer-head{display:flex;align-items:center;justify-content:space-between;
  padding:16px 18px;border-bottom:1px solid var(--border)}
.drawer-head strong{font-size:15px;color:var(--text-strong)}
.drawer-close{border:none;background:none;font-size:24px;color:var(--muted);
  line-height:1;cursor:pointer;padding:4px 8px;border-radius:8px}
.drawer-close:hover{background:var(--primary-soft);color:var(--primary)}
.drawer-body{overflow-y:auto;padding:6px 0 24px}
.drawer-section{margin:16px 18px 4px;font-size:11.5px;font-weight:700;
  letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
#drawer .toc{list-style:none;margin:0;padding:0}
#drawer .toc ul{list-style:none;margin:0;padding-left:14px}
#drawer .toc a{
  display:block;padding:9px 18px;font-size:14px;color:var(--text);
  text-decoration:none;border-left:3px solid transparent;line-height:1.45;
}
#drawer .toc a:hover{background:var(--card-2)}
#drawer .toc a.active,#drawer .toc a.current{color:var(--primary);font-weight:600;
  border-left-color:var(--primary);background:var(--primary-soft)}

/* 正文 */
article{max-width:760px;margin:0 auto;padding:26px 18px 64px;
  background:var(--card);min-height:60vh}
article h1{font-size:26px;line-height:1.3;margin:4px 0 20px;color:var(--text-strong);
  font-weight:800;letter-spacing:-.02em;padding-bottom:16px;
  background-image:linear-gradient(90deg,var(--primary),var(--accent));
  background-repeat:no-repeat;background-size:72px 4px;background-position:left bottom}
article h2{font-size:20px;line-height:1.4;margin:44px 0 14px;color:var(--text-strong);
  font-weight:750;letter-spacing:-.01em;position:relative;padding-left:14px}
article h2::before{content:"";position:absolute;left:0;top:.28em;bottom:.28em;width:4px;border-radius:99px;
  background:linear-gradient(180deg,var(--primary),var(--accent))}
article h3{font-size:16.5px;margin:26px 0 8px;color:var(--text-strong);font-weight:700}
article h4{font-size:15px;margin:20px 0 6px;color:var(--text-strong);font-weight:700}
article p{margin:10px 0}
article a{color:var(--primary);text-decoration:underline;text-decoration-color:var(--primary-ring);
  text-underline-offset:3px;text-decoration-thickness:1.5px;overflow-wrap:anywhere;transition:text-decoration-color .15s}
article a:hover{text-decoration-color:var(--primary)}
article a:active{color:var(--primary-dark)}
article strong{color:var(--text-strong)}
article ul,article ol{padding-left:1.4em;margin:10px 0}
article li{margin:6px 0}
article li::marker{color:var(--muted)}
article hr{border:none;border-top:1px solid var(--border);margin:32px 0}
article img{max-width:100%;height:auto;border-radius:10px}

/* 目录节（README 里的「目录」标题下紧跟的有序列表）*/
article h2#\76ee\5f55 + ol{
  margin:4px 0 8px;padding:10px 14px 10px 30px;list-style:decimal;
  background:var(--card-2);border:1px solid var(--border);border-radius:12px;
}
article h2#\76ee\5f55 + ol li{margin:2px 0}
article h2#\76ee\5f55 + ol a{text-decoration:none}
article h2#\76ee\5f55 + ol a:hover{text-decoration:underline}

/* 引用块：默认蓝色提示；文首第一块（免责声明/取证窗口）为中性灰 */
article blockquote{
  margin:16px 0;padding:12px 16px;background:var(--primary-soft);
  border-left:4px solid var(--primary);border-radius:0 12px 12px 0;color:var(--text);
  font-size:14.5px;
}
article blockquote:first-of-type{
  background:var(--quote-bg);border-left-color:var(--quote-bar);
  border:1px solid var(--border);border-left:4px solid var(--quote-bar);
  font-size:13.5px;line-height:1.7;color:var(--muted)}
article blockquote:first-of-type strong{color:var(--text)}
article blockquote p{margin:6px 0}
article blockquote ol,article blockquote ul{margin:6px 0}

/* 代码 */
article code{
  font-family:ui-monospace,"Cascadia Code",Consolas,"SFMono-Regular",Menlo,monospace;font-size:.86em;
  background:var(--code-inline-bg);color:var(--code-inline-text);padding:2px 6px;border-radius:6px;
}
article pre{
  position:relative;margin:18px 0;padding:42px 16px 16px;background:var(--code-bg);
  border-radius:14px;overflow-x:auto;line-height:1.65;color-scheme:dark;
  box-shadow:inset 0 0 0 1px rgba(255,255,255,.06),0 8px 24px rgba(2,6,23,.18);
}
article pre code{background:none;color:var(--code-text);padding:0;
  font-size:13px;line-height:1.65}
article pre::before{
  content:attr(data-lang);position:absolute;top:11px;left:14px;
  font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#94a3b8;
  font-family:ui-monospace,Consolas,Menlo,monospace}
.copy-btn{
  position:absolute;top:8px;right:8px;font-size:12px;line-height:1;
  color:#e2e8f0;background:rgba(255,255,255,.08);
  border:1px solid rgba(148,163,184,.35);border-radius:999px;padding:6px 12px;cursor:pointer;
  transition:background .15s}
.copy-btn:hover{background:rgba(255,255,255,.16)}
.copy-btn.done{background:rgba(34,197,94,.25);border-color:rgba(34,197,94,.5)}

/* 表格 */
.table-wrap{overflow-x:auto;margin:18px 0;border:1px solid var(--border);
  border-radius:12px;-webkit-overflow-scrolling:touch;background:var(--card)}
article table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:520px}
article th,article td{padding:10px 12px;text-align:left;vertical-align:top;
  border-bottom:1px solid var(--border);line-height:1.6}
article th{background:var(--card-2);color:var(--text-strong);font-weight:650;white-space:nowrap;
  position:sticky;top:0}
article tbody tr:hover{background:var(--primary-soft)}
article tr:last-child td{border-bottom:none}
/* 手机端：客户端大表只留「客户端（链到短页）/ 协议与 Base URL」两列，「关键点」点按钮再展开 */
.table-toggle{display:none;margin:0;padding:8px 12px;width:100%;border:none;border-bottom:1px solid var(--border);
  background:var(--card-2);color:var(--primary);font-size:13px;font-weight:600;cursor:pointer;text-align:left}
@media (max-width:767px){
  .table-wrap.compact .table-toggle{display:block}
  .table-wrap.compact table{min-width:0}
  .table-wrap.compact:not(.expanded) th:nth-child(3),
  .table-wrap.compact:not(.expanded) td:nth-child(3){display:none}
  .table-wrap.compact td:first-child{font-weight:600}
  .table-wrap.compact th,.table-wrap.compact td{padding:9px 10px;white-space:normal}
}

/* 页脚 */
.site-footer{max-width:760px;margin:0 auto;padding:8px 16px 56px;
  color:var(--muted);font-size:12.5px;line-height:1.75}
.site-footer .foot-card{border-top:1px solid var(--border);padding-top:18px;text-align:center}
.site-footer p{margin:4px 0}
.site-footer a{color:var(--muted);text-decoration:underline;text-underline-offset:3px;
  text-decoration-color:var(--border-strong)}
.site-footer a:hover{color:var(--primary)}
.site-footer .foot-label{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.06em;
  color:var(--muted);border:1px solid var(--border);border-radius:999px;padding:0 8px;margin-right:6px;
  vertical-align:middle;line-height:18px}

#toTop{
  position:fixed;right:16px;bottom:calc(20px + env(safe-area-inset-bottom));
  width:46px;height:46px;border-radius:50%;border:none;cursor:pointer;
  background:var(--primary);color:#fff;font-size:20px;z-index:30;
  display:none;align-items:center;justify-content:center;
  box-shadow:0 8px 20px var(--primary-ring);
}
#toTop:hover{background:var(--primary-dark)}
@media (min-width:768px){
  article{margin:28px auto 24px;border-radius:var(--radius);box-shadow:var(--shadow);
    padding:40px 44px 72px;border:1px solid var(--border)}
  article h1{font-size:32px}
  article h2{font-size:22px}
  article h2#\76ee\5f55 + ol{columns:2;column-gap:28px}
  article h2#\76ee\5f55 + ol li{break-inside:avoid}
}
@media print{
  .appbar,#drawer,#mask,#toTop,#progress,.copy-btn,.anchor,.table-toggle{display:none!important}
  article{box-shadow:none;border:none;max-width:none}
}

/* 顶栏右侧：主题切换 */
.appbar-actions{margin-left:auto;display:flex;gap:6px;flex:0 0 auto}
.icon-btn{width:36px;height:36px;border:1px solid var(--border);border-radius:10px;background:var(--card);
  color:var(--muted);cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:15px;line-height:1}
.icon-btn:hover{color:var(--primary);border-color:var(--primary)}
.icon-btn .i-dark{display:none}
:root[data-theme="dark"] .icon-btn .i-light{display:none}
:root[data-theme="dark"] .icon-btn .i-dark{display:inline}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]) .icon-btn .i-light{display:none}
  :root:not([data-theme="light"]) .icon-btn .i-dark{display:inline}
}

/* 标题锚点：悬停出现 #，点击复制本节链接 */
article h2,article h3{scroll-margin-top:76px}
.anchor{margin-left:.35em;font-weight:400;color:var(--muted);text-decoration:none;opacity:0;
  transition:opacity .15s;font-size:.85em}
h2:hover .anchor,h3:hover .anchor,.anchor:focus{opacity:1}
.anchor.copied{color:#16a34a;opacity:1}
@media (hover:none){.anchor{opacity:.45}}

/* 抽屉：过滤框 */
.drawer-filter{margin:10px 14px 2px}
.drawer-filter input{width:100%;padding:8px 12px;border:1px solid var(--border);border-radius:10px;
  background:var(--card-2);color:var(--text);font-size:14px;outline:none;-webkit-appearance:none}
.drawer-filter input:focus{border-color:var(--primary);box-shadow:0 0 0 3px var(--primary-ring)}
#drawer li.hide,#drawer .drawer-section.hide{display:none}
.drawer-empty{display:none;padding:14px 18px;color:var(--muted);font-size:13px}
.drawer-empty.show{display:block}

/* 正文外链小箭头 */
article a[target="_blank"]::after{content:"\2197";font-size:.72em;margin-left:2px;opacity:.6}

/* 宽表横滚时首列吸附 */
.table-wrap td:first-child,.table-wrap th:first-child{position:sticky;left:0;background:var(--card);z-index:1;
  box-shadow:inset -1px 0 0 var(--border)}
.table-wrap th:first-child{background:var(--card-2);z-index:2}
article tbody tr:hover td:first-child{background:var(--primary-soft)}

/* 单文件页：宽屏时右侧常驻目录 */
.page{max-width:1140px;margin:0 auto}
.page-side{display:none}
@media (min-width:1024px){
  .page{display:flex;gap:28px;align-items:flex-start;padding:0 16px}
  .page article{flex:1;min-width:0;max-width:none;margin-left:0;margin-right:0}
  .page-side{display:block;width:250px;flex:0 0 250px;position:sticky;top:72px;max-height:calc(100vh - 92px);
    overflow-y:auto;margin-top:28px;padding:12px 8px;background:var(--card);border:1px solid var(--border);
    border-radius:var(--radius);box-shadow:var(--shadow);font-size:13px}
  .page-side .side-title{font-size:11px;letter-spacing:.08em;text-transform:uppercase;font-weight:700;
    color:var(--muted);margin:4px 0 8px;padding:0 8px}
  .page-side ul{list-style:none;margin:0;padding:0}
  .page-side ul ul{padding-left:12px}
  .page-side a{display:block;padding:4px 8px;border-radius:6px;color:var(--text);text-decoration:none;line-height:1.45;
    overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .page-side a:hover{color:var(--primary);background:var(--card-2)}
  .page-side a.active{color:var(--primary);background:var(--primary-soft);font-weight:600}
}

@media (prefers-reduced-motion:reduce){
  html{scroll-behavior:auto}
  *,*::before,*::after{transition:none!important;animation:none!important}
}
</style>"""

JS = r"""<script>
(function () {
  var copy = __JS_I18N__;
  function tr(key, fallback) { return copy[key] || fallback; }
  // 主题：auto（跟系统）→ light → dark 循环；选择存本地，不发任何请求
  var root = document.documentElement;
  var themeBtn = document.getElementById('themeBtn');
  try {
    var saved = localStorage.getItem('theme');
    if (saved === 'light' || saved === 'dark') { root.setAttribute('data-theme', saved); }
  } catch (e) {}
  function themeLabel() {
    var t = root.getAttribute('data-theme') || 'auto';
    if (themeBtn) {
      themeBtn.title = {
        auto: tr('themeAuto', 'Theme: follow system (click to change)'),
        light: tr('themeLight', 'Theme: light (click to change)'),
        dark: tr('themeDark', 'Theme: dark (click to change)')
      }[t];
      themeBtn.setAttribute('aria-label', themeBtn.title);
    }
  }
  themeLabel();
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      var cur = root.getAttribute('data-theme') || 'auto';
      var next = cur === 'auto' ? 'light' : cur === 'light' ? 'dark' : 'auto';
      if (next === 'auto') { root.removeAttribute('data-theme'); } else { root.setAttribute('data-theme', next); }
      try { if (next === 'auto') { localStorage.removeItem('theme'); } else { localStorage.setItem('theme', next); } } catch (e) {}
      themeLabel();
    });
  }

  var drawer = document.getElementById('drawer');
  var mask = document.getElementById('mask');
  var menuBtn = document.getElementById('menuBtn');
  var lastFocus = null;
  function openDrawer() {
    lastFocus = document.activeElement;
    drawer.classList.add('open'); mask.classList.add('show');
    menuBtn.setAttribute('aria-expanded', 'true');
    var f = drawer.querySelector('.drawer-filter input') || drawer.querySelector('a');
    if (f) { setTimeout(function () { f.focus(); }, 260); }
  }
  function closeDrawer() {
    if (!drawer.classList.contains('open')) { return; }
    drawer.classList.remove('open'); mask.classList.remove('show');
    menuBtn.setAttribute('aria-expanded', 'false');
    if (lastFocus && lastFocus.focus) { lastFocus.focus(); }
  }
  menuBtn.setAttribute('aria-expanded', 'false');
  menuBtn.addEventListener('click', openDrawer);
  document.getElementById('drawerClose').addEventListener('click', closeDrawer);
  mask.addEventListener('click', closeDrawer);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closeDrawer(); return; }
    // Tab 不跑出抽屉
    if (e.key === 'Tab' && drawer.classList.contains('open')) {
      var vis = [].filter.call(drawer.querySelectorAll('button,input,a[href]'), function (el) { return el.offsetParent !== null; });
      if (!vis.length) { return; }
      var first = vis[0], last = vis[vis.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    }
  });
  drawer.addEventListener('click', function (e) {
    if (e.target.tagName === 'A') { closeDrawer(); }
  });

  // 抽屉过滤：按标题文字筛，子项命中时父项保留，空结果给提示
  var dbody = drawer.querySelector('.drawer-body');
  if (dbody && dbody.querySelectorAll('a').length > 8) {
    var wrap = document.createElement('div');
    wrap.className = 'drawer-filter';
    wrap.innerHTML = '<input type="search">';
    var input = wrap.querySelector('input');
    input.placeholder = tr('filterPlaceholder', 'Filter sections / documents...');
    input.setAttribute('aria-label', tr('filterLabel', 'Filter navigation'));
    dbody.insertBefore(wrap, dbody.firstChild);
    var empty = document.createElement('div');
    empty.className = 'drawer-empty';
    empty.textContent = tr('filterEmpty', 'No matching headings');
    dbody.appendChild(empty);
    var items = [].slice.call(dbody.querySelectorAll('li'));
    input.addEventListener('input', function () {
      var q = input.value.trim().toLowerCase();
      var any = false;
      // 先按自身文字判，再从后往前让有可见子项的父项露出来
      items.forEach(function (li) {
        var a = li.firstElementChild && li.firstElementChild.tagName === 'A' ? li.firstElementChild : null;
        var hit = !q || (a && a.textContent.toLowerCase().indexOf(q) !== -1);
        li.classList.toggle('hide', !hit);
        if (hit && q) { any = true; }
      });
      for (var i = items.length - 1; i >= 0; i--) {
        if (items[i].classList.contains('hide') && items[i].querySelector('li:not(.hide)')) { items[i].classList.remove('hide'); }
      }
      dbody.querySelectorAll('.drawer-section').forEach(function (sec) {
        var box = sec.parentElement;
        var has = !q || box.querySelector('li:not(.hide)');
        sec.classList.toggle('hide', !has);
      });
      empty.classList.toggle('show', !!q && !any);
    });
  }

  // 标题锚点：点 # 复制本节链接
  document.querySelectorAll('article h2[id],article h3[id]').forEach(function (h) {
    var a = document.createElement('a');
    a.className = 'anchor'; a.href = '#' + h.id; a.textContent = '#';
    a.setAttribute('aria-label', tr('copySection', 'Copy link to this section'));
    a.addEventListener('click', function (e) {
      if (!navigator.clipboard) { return; }
      e.preventDefault();
      var url = location.href.split('#')[0] + '#' + h.id;
      history.replaceState(null, '', '#' + h.id);
      navigator.clipboard.writeText(url).then(function () {
        a.classList.add('copied'); a.textContent = tr('copied', 'Copied');
        setTimeout(function () { a.classList.remove('copied'); a.textContent = '#'; }, 1200);
      });
    });
    h.appendChild(a);
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

  // 代码块：左上角语言标签 + 右上角复制按钮
  var LANG = { sh: 'bash', shell: 'bash', zsh: 'bash', ps1: 'powershell', pwsh: 'powershell',
    js: 'javascript', ts: 'typescript', py: 'python', yml: 'yaml', md: 'markdown', txt: 'text' };
  document.querySelectorAll('pre').forEach(function (pre) {
    if (pre.querySelector('.copy-btn')) { return; }
    var code = pre.querySelector('code');
    var m = code && /language-([\w+-]+)/.exec(code.className || '');
    var lang = m ? m[1].toLowerCase() : '';
    pre.setAttribute('data-lang', LANG[lang] || lang || 'code');
    var btn = document.createElement('button');
    btn.className = 'copy-btn';
    btn.type = 'button';
    btn.textContent = tr('copyCode', 'Copy');
    btn.setAttribute('aria-label', tr('copyCodeLabel', 'Copy code'));
    btn.addEventListener('click', function () {
      var text = code ? code.innerText : pre.innerText;
      function ok() {
        btn.textContent = tr('copied', 'Copied'); btn.classList.add('done');
        setTimeout(function () { btn.textContent = tr('copyCode', 'Copy'); btn.classList.remove('done'); }, 1500);
      }
      function fallback() {
        var ta = document.createElement('textarea');
        ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
        document.body.appendChild(ta); ta.select();
        try { document.execCommand('copy'); ok(); } catch (e) {}
        document.body.removeChild(ta);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(ok).catch(fallback);
      } else { fallback(); }
    });
    pre.appendChild(btn);
  });

  // 客户端大表：窄屏默认折叠第三列（关键点），按钮展开；桌面端不受影响
  var clientsHeading = document.getElementById('各客户端cli-接入要点');
  if (clientsHeading) {
    var node = clientsHeading.nextElementSibling;
    while (node && !(node.classList && node.classList.contains('table-wrap'))) { node = node.nextElementSibling; }
    if (node && node.querySelector('th:nth-child(3)')) {
      node.classList.add('compact');
      var tg = document.createElement('button');
      tg.type = 'button'; tg.className = 'table-toggle';
      var hidden = node.querySelector('th:nth-child(3)').textContent.trim();
      function label() {
        var template = node.classList.contains('expanded')
          ? tr('collapseColumn', 'Hide {column} column')
          : tr('expandColumn', 'Show {column} column');
        tg.textContent = template.replace('{column}', hidden);
      }
      label();
      tg.addEventListener('click', function () { node.classList.toggle('expanded'); label(); });
      node.insertBefore(tg, node.firstChild);
    }
  }

  // 滚动时高亮导航里对应的章节：取视口上沿以上最近的一个标题，比纯 IntersectionObserver 稳定
  var navLinks = {};
  document.querySelectorAll('#drawer a[href^="#"], .toc-box a[href^="#"], .page-side a[href^="#"]').forEach(function (a) {
    var id;
    try { id = decodeURIComponent(a.getAttribute('href').slice(1)); } catch (e) { id = a.getAttribute('href').slice(1); }
    (navLinks[id] = navLinks[id] || []).push(a);
  });
  var heads = [].slice.call(document.querySelectorAll('article h2[id],article h3[id]'));
  var activeId = null, ticking = false;
  function spy() {
    ticking = false;
    var y = window.scrollY + 90, cur = null;
    for (var i = 0; i < heads.length; i++) {
      if (heads[i].offsetTop <= y) { cur = heads[i].id; } else { break; }
    }
    if (cur === activeId) { return; }
    activeId = cur;
    Object.keys(navLinks).forEach(function (k) { navLinks[k].forEach(function (a) { a.classList.remove('active'); }); });
    (navLinks[cur] || []).forEach(function (a) {
      a.classList.add('active');
      var box = a.closest && a.closest('.page-side, .toc-box');
      if (box && (a.offsetTop < box.scrollTop || a.offsetTop > box.scrollTop + box.clientHeight - 40)) {
        box.scrollTop = a.offsetTop - box.clientHeight / 2;
      }
    });
  }
  if (heads.length) {
    window.addEventListener('scroll', function () {
      if (!ticking) { ticking = true; requestAnimationFrame(spy); }
    }, { passive: true });
    window.addEventListener('resize', spy);
    spy();
  }
})();
</script>"""


def footer_html(built_from: str, repo_url: str = "", locale: str = "zh-CN") -> str:
    """两套产物共用的页脚：构建说明 / 实例环境 / 免责声明三行。

    ``built_from`` 写明本页由哪份源文件构建；``repo_url`` 非空时追加仓库链接。
    实例链接与免责声明同框，是 AGENTS §1.1「转化」一行的落地：不弹窗、不留资。
    """
    copy = {
        "zh-CN": {
            "repo": "GitHub 仓库",
            "built": "本页由 {0} 自动构建 · 示例代码采用 MIT 许可证{1}",
            "fixture": "实例环境",
            "instance": "文中以 nuoapi.net 作为地址夹具；分组、倍率与可用性以 ",
            "console": "nuoapi.net",
            "live": " 控制台实时显示为准，带取证窗口日期的结论只代表该时间点的观察",
            "legal": "本仓库不提供、不代售任何 API 服务，不构成投资或购买建议；所提及商标归各自厂商所有",
        },
        "en": {
            "repo": "GitHub repository",
            "built": "Generated from {0} · examples are MIT licensed{1}",
            "fixture": "Instance",
            "instance": "This site uses nuoapi.net as an address fixture. Check ",
            "console": "nuoapi.net",
            "live": " for current groups, rates, and availability. Observations tagged with an evidence window apply only to that window.",
            "legal": "This repository does not provide or resell API access and is not an investment or purchase recommendation. Trademarks belong to their respective owners.",
        },
        "ja": {
            "repo": "GitHub リポジトリ",
            "built": "{0} から自動生成 · サンプルコードは MIT ライセンス{1}",
            "fixture": "接続先の例",
            "instance": "本文では nuoapi.net を接続先の例として使います。グループ、倍率、可用性は ",
            "console": "nuoapi.net",
            "live": " の管理画面にある最新表示を確認してください。証拠取得期間付きの記述はその期間だけを対象とします。",
            "legal": "本リポジトリは API サービスを提供・再販しません。投資や購入の推奨でもありません。各商標は各所有者に帰属します。",
        },
        "zh-Hant": {
            "repo": "GitHub 倉庫",
            "built": "本頁由 {0} 自動建置 · 範例程式採用 MIT 授權{1}",
            "fixture": "實例環境",
            "instance": "文中以 nuoapi.net 作為位址夾具；分組、倍率與可用性以 ",
            "console": "nuoapi.net",
            "live": " 控制台即時顯示為準，帶取證窗口日期的結論只代表該時間點的觀察",
            "legal": "本倉庫不提供、不代售任何 API 服務，不構成投資或購買建議；所提及商標歸各自廠商所有",
        },
    }
    text = copy.get(locale, copy["zh-CN"])
    repo = (
        ' · <a href="{0}" target="_blank" rel="noopener noreferrer">{1}</a>'.format(
            repo_url, text["repo"]
        )
        if repo_url
        else ""
    )
    return (
        '<footer class="site-footer"><div class="foot-card">\n'
        "  <p>{0}</p>\n"
        '  <p><span class="foot-label">{1}</span>{2}'
        '<a href="https://nuoapi.net" target="_blank" rel="noopener noreferrer">{3}</a>{4}</p>\n'
        "  <p>{5}</p>\n"
        "</div></footer>"
    ).format(
        text["built"].format(built_from, repo),
        text["fixture"],
        text["instance"],
        text["console"],
        text["live"],
        text["legal"],
    )

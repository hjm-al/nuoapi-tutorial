# -*- coding: utf-8 -*-
"""共享样式、交互脚本与页脚文案。

h5/build_h5.py（离线单文件版）与 h5/build_site.py（GitHub Pages 多页站）共用这一份
CSS / JS / 页脚，避免两套外观与措辞各自漂移。改动此处会同时影响两个产物：
- 重新构建 h5/index.html 并提交（CI 会校验二者同步）；
- 重新构建站点（Pages workflow 每次 push 自动重建）。

设计原则：
- 移动优先，桌面端加宽、使用纸面细线与侧栏；
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
  --paper:#f5f6f2; --surface:#fbfbf8; --surface-2:#eff1ec; --ink:#191b19; --ink-strong:#101210;
  --muted:#65706a; --line:#d7dcd6; --line-strong:#b8c0b9;
  --rust:#a64b2f; --rust-dark:#843a25; --rust-soft:#f3e7e1;
  --teal:#176f63; --teal-soft:#e7f1ee;
  --primary:var(--rust); --primary-dark:var(--rust-dark); --primary-soft:var(--rust-soft); --primary-ring:rgba(166,75,47,.18);
  --accent:var(--teal);
  --bg:var(--paper); --card:var(--surface); --card-2:var(--surface-2);
  --text:#343a35; --text-strong:var(--ink); --border:var(--line); --border-strong:var(--line-strong);
  --code-bg:#1b1f1d; --code-text:#eceee9; --code-inline-bg:#e8ebe5; --code-inline-text:#30463d;
  --quote-bg:#f0f2ed; --quote-bar:#aeb7b0;
  --shadow:none;
  --radius:6px;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --paper:#171a18; --surface:#1e221f; --surface-2:#242925; --ink:#eceee9; --ink-strong:#f6f7f4;
    --muted:#a5ada6; --line:#353c36; --line-strong:#505a52;
    --rust:#d17a5d; --rust-dark:#e59a80; --rust-soft:#34221c;
    --teal:#69b6aa; --teal-soft:#1c302b;
    --primary-ring:rgba(209,122,93,.24);
    --text:#d7dbd5; --code-bg:#101311; --code-text:#eef0ec; --code-inline-bg:#2b312c; --code-inline-text:#d7e4dd;
    --quote-bg:#202521; --quote-bar:#57615a;
  }
}
/* 手动切换（顶栏按钮）：与上面一组变量保持一致 */
:root[data-theme="dark"]{
  --paper:#171a18; --surface:#1e221f; --surface-2:#242925; --ink:#eceee9; --ink-strong:#f6f7f4;
  --muted:#a5ada6; --line:#353c36; --line-strong:#505a52;
  --rust:#d17a5d; --rust-dark:#e59a80; --rust-soft:#34221c;
  --teal:#69b6aa; --teal-soft:#1c302b;
  --primary-ring:rgba(209,122,93,.24);
  --text:#d7dbd5; --code-bg:#101311; --code-text:#eef0ec; --code-inline-bg:#2b312c; --code-inline-text:#d7e4dd;
  --quote-bg:#202521; --quote-bar:#57615a;
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html{-webkit-text-size-adjust:100%;scroll-padding-top:76px;scroll-behavior:smooth}
body{
  margin:0;color:var(--text);font-size:16px;line-height:1.8;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",
    "Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",sans-serif;
  background:var(--bg);
}
::selection{background:#bfdbfe;color:#0f172a}
:focus-visible{outline:2px solid var(--primary);outline-offset:2px}

/* 顶部进度条 + 应用栏 */
#progress{position:fixed;top:0;left:0;height:3px;width:0;z-index:60;
  background:var(--primary)}
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
  flex:0 0 auto;width:38px;height:38px;border:1px solid var(--border);border-radius:4px;
  background:var(--primary-soft);color:var(--primary);font-size:18px;
  display:flex;align-items:center;justify-content:center;cursor:pointer;
}
.menu-btn:hover{background:var(--surface-2);border-color:var(--line-strong)}
.brand{display:flex;align-items:center;gap:10px;min-width:0}
.brand-mark{flex:0 0 auto;width:30px;height:30px;border:1px solid var(--ink);border-radius:3px;
  background:transparent;
  color:var(--ink);font-weight:800;font-size:13px;letter-spacing:0;
  display:flex;align-items:center;justify-content:center;
}
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
  display:flex;flex-direction:column;border-right:1px solid var(--border);
}
#drawer.open{transform:translateX(0)}
.drawer-head{display:flex;align-items:center;justify-content:space-between;
  padding:16px 18px;border-bottom:1px solid var(--border)}
.drawer-head strong{font-size:15px;color:var(--text-strong)}
.drawer-close{border:none;background:none;font-size:24px;color:var(--muted);
  line-height:1;cursor:pointer;padding:4px 8px;border-radius:4px}
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
  background:none}
article h2{font-size:20px;line-height:1.4;margin:44px 0 14px;color:var(--text-strong);
  font-weight:750;letter-spacing:0;position:relative;padding-left:0}
article h2::before{display:none}
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
article img{max-width:100%;height:auto;border-radius:4px}

/* 目录节（README 里的「目录」标题下紧跟的有序列表）*/
article h2#\76ee\5f55 + ol{
  margin:4px 0 8px;padding:10px 14px 10px 30px;list-style:decimal;
  background:var(--card-2);border:1px solid var(--border);border-radius:6px;
}
article h2#\76ee\5f55 + ol li{margin:2px 0}
article h2#\76ee\5f55 + ol a{text-decoration:none}
article h2#\76ee\5f55 + ol a:hover{text-decoration:underline}

/* 引用块：默认蓝色提示；文首第一块（免责声明/取证窗口）为中性灰 */
article blockquote{
  margin:16px 0;padding:12px 16px;background:var(--quote-bg);
  border-left:2px solid var(--quote-bar);border-radius:0;color:var(--text);
  font-size:14.5px;
}
article blockquote:first-of-type{
  background:var(--quote-bg);border-left-color:var(--quote-bar);
  border:1px solid var(--border);border-left:2px solid var(--quote-bar);
  font-size:13.5px;line-height:1.7;color:var(--muted)}
article blockquote:first-of-type strong{color:var(--text)}
article blockquote p{margin:6px 0}
article blockquote ol,article blockquote ul{margin:6px 0}

/* 代码 */
article code{
  font-family:ui-monospace,"Cascadia Code",Consolas,"SFMono-Regular",Menlo,monospace;font-size:.86em;
  background:var(--code-inline-bg);color:var(--code-inline-text);padding:2px 6px;border-radius:3px;
}
article pre{
  position:relative;margin:18px 0;padding:42px 16px 16px;background:var(--code-bg);
  border:1px solid #303733;border-radius:6px;overflow-x:auto;line-height:1.65;color-scheme:dark;
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
  border:1px solid rgba(148,163,184,.35);border-radius:4px;padding:6px 12px;cursor:pointer;
  transition:background .15s}
.copy-btn:hover{background:rgba(255,255,255,.16)}
.copy-btn.done{background:rgba(34,197,94,.25);border-color:rgba(34,197,94,.5)}

/* 表格 */
.table-wrap{overflow-x:auto;margin:18px 0;border:1px solid var(--border);
  border-radius:6px;-webkit-overflow-scrolling:touch;background:var(--card)}
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
  color:var(--muted);border:1px solid var(--border);border-radius:3px;padding:0 8px;margin-right:6px;
  vertical-align:middle;line-height:18px}

#toTop{
  position:fixed;right:16px;bottom:calc(20px + env(safe-area-inset-bottom));
  width:46px;height:46px;border-radius:4px;border:1px solid var(--border-strong);cursor:pointer;
  background:var(--primary);color:#fff;font-size:20px;z-index:30;
  display:none;align-items:center;justify-content:center;
}
#toTop:hover{background:var(--primary-dark)}
@media (min-width:768px){
  article{margin:28px auto 24px;border-radius:0;
    padding:40px 44px 72px;border:1px solid var(--border)}
  article h1{font-size:32px}
  article h2{font-size:22px}
  article h2#\76ee\5f55 + ol{columns:2;column-gap:28px}
  article h2#\76ee\5f55 + ol li{break-inside:avoid}
}
@media print{
  .appbar,#drawer,#mask,#toTop,#progress,.copy-btn,.anchor,.table-toggle{display:none!important}
  article{border:none;max-width:none}
}

/* 顶栏右侧：主题切换 */
.appbar-actions{margin-left:auto;display:flex;gap:6px;flex:0 0 auto}
.icon-btn{width:36px;height:36px;border:1px solid var(--border);border-radius:4px;background:var(--card);
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
.drawer-filter input{width:100%;padding:8px 12px;border:1px solid var(--border);border-radius:4px;
  background:var(--card-2);color:var(--text);font-size:14px;outline:none;-webkit-appearance:none}
.drawer-filter input:focus{border-color:var(--primary)}
#drawer li.hide,#drawer .drawer-section.hide{display:none}
.drawer-empty{display:none;padding:14px 18px;color:var(--muted);font-size:13px}
.drawer-empty.show{display:block}

/* 正文外链小箭头 */
article a[target="_blank"]::after{content:"\2197";font-size:.72em;margin-left:2px;opacity:.6}

/* 宽表横滚时首列吸附 */
.table-wrap td:first-child,.table-wrap th:first-child{position:sticky;left:0;background:var(--card);z-index:1;
  border-right:1px solid var(--border)}
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
    border-radius:0;font-size:13px}
  .page-side .side-title{font-size:11px;letter-spacing:.08em;text-transform:uppercase;font-weight:700;
    color:var(--muted);margin:4px 0 8px;padding:0 8px}
  .page-side ul{list-style:none;margin:0;padding:0}
  .page-side ul ul{padding-left:12px}
  .page-side a{display:block;padding:4px 8px;border-radius:6px;color:var(--text);text-decoration:none;line-height:1.45;
    overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
  .page-side a:hover{color:var(--primary);background:var(--card-2)}
  .page-side a.active{color:var(--primary);background:var(--primary-soft);font-weight:600}
}

/* 技术手册视觉层：纸面、细线、编号与低密度强调色 */
body{
  background:var(--paper);
  color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",
    "Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC",sans-serif;
  line-height:1.78;
}
::selection{background:var(--rust-soft);color:var(--ink-strong)}
:focus-visible{outline:2px solid var(--rust);outline-offset:3px}
.appbar{
  gap:14px;padding:10px 18px;background:var(--paper);
  border-bottom:1px solid var(--line);
  -webkit-backdrop-filter:none;backdrop-filter:none;
}
#progress{height:2px;background:var(--rust)}
.menu-btn,.icon-btn,.drawer-close{
  border:1px solid var(--line);border-radius:4px;background:transparent;
  color:var(--ink);box-shadow:none;
}
.menu-btn:hover,.icon-btn:hover,.drawer-close:hover{
  border-color:var(--line-strong);color:var(--rust);background:var(--surface-2);
}
.brand{gap:11px}
.brand-mark{
  width:30px;height:30px;border:1px solid var(--ink);border-radius:3px;
  background:transparent;color:var(--ink);box-shadow:none;
  font-family:ui-monospace,"Cascadia Code",Consolas,monospace;
  font-size:13px;font-weight:700;letter-spacing:0;
}
.appbar-title{
  color:var(--ink-strong);font-size:14.5px;font-weight:650;letter-spacing:0;
}
.appbar-sub{
  color:var(--muted);font-size:11px;letter-spacing:.025em;
}
.appbar-actions{gap:8px;min-width:0}
.lang-switch a{
  min-width:31px;height:30px;padding:0 7px;border:1px solid var(--line);
  border-radius:4px;background:transparent;color:var(--muted);font-size:11px;
}
.lang-switch a:hover{border-color:var(--line-strong);color:var(--rust);background:var(--surface-2)}
.lang-switch a.current{border-color:var(--ink);background:transparent;color:var(--ink);font-weight:650}

#mask{background:rgba(12,15,13,.46)}
#drawer{
  background:var(--paper);border-right:1px solid var(--line);
  box-shadow:none;
}
.drawer-head{padding:16px 18px;border-bottom:1px solid var(--line)}
.drawer-head strong{font-size:14px;color:var(--ink)}
.drawer-language{border-bottom:1px solid var(--line)}
.drawer-language a{border:1px solid var(--line);border-radius:4px;color:var(--text)}
.drawer-language a.current{border-color:var(--ink);background:transparent;color:var(--ink)}
.drawer-section,.side-title,.toc-box strong{
  color:var(--muted);font-size:10.5px;font-weight:700;letter-spacing:.11em;
}
#drawer .toc a{
  border-left:0;padding:8px 18px;color:var(--text);
}
#drawer .toc a:hover{background:var(--surface-2);color:var(--rust)}
#drawer .toc a.active,#drawer .toc a.current{
  border-left:0;background:var(--surface-2);color:var(--rust);font-weight:650;
}
.drawer-filter input{
  border:1px solid var(--line);border-radius:4px;background:var(--surface);
  color:var(--ink);
}
.drawer-filter input:focus{border-color:var(--rust);box-shadow:none;outline:1px solid var(--rust)}

article{
  max-width:760px;min-width:0;padding:40px 24px 76px;margin:0 auto;
  background:transparent;border:0;border-radius:0;box-shadow:none;
}
article > *{min-width:0}
article h1{
  margin:0 0 24px;padding:0;background:none;color:var(--ink-strong);
  font-size:32px;line-height:1.25;font-weight:760;letter-spacing:0;
  overflow-wrap:anywhere;
}
article h2{
  margin:0 0 16px;padding:0;color:var(--ink-strong);
  font-size:24px;line-height:1.35;font-weight:700;letter-spacing:0;
}
article h2::before{display:none}
article h3{
  margin:28px 0 8px;color:var(--ink-strong);
  font-size:18px;line-height:1.45;font-weight:680;letter-spacing:0;
}
article h4{margin:22px 0 7px;color:var(--ink);font-size:15.5px;letter-spacing:0}
article p{margin:12px 0}
article a{
  color:var(--rust);text-decoration-color:rgba(166,75,47,.42);
  text-decoration-thickness:1px;text-underline-offset:3px;
  overflow-wrap:anywhere;
}
article a:hover{color:var(--rust-dark);text-decoration-color:currentColor}
article strong{color:var(--ink-strong)}
article ul,article ol{padding-left:1.35em}
article li{margin:7px 0}
article li::marker{color:var(--muted)}
article hr{border:0;border-top:1px solid var(--line);margin:36px 0}
article img{max-width:100%;height:auto;border-radius:4px}

.doc-section{
  padding:40px 0 10px;margin:0;min-width:0;
}
article > .doc-section + .doc-section{border-top:1px solid var(--line)}
.doc-section > :last-child{margin-bottom:0}
.doc-section:first-child{padding-top:4px}

article blockquote{
  margin:20px 0;padding:13px 16px;border:0;border-left:2px solid var(--line-strong);
  border-radius:0;background:var(--quote-bg);color:var(--text);font-size:14.5px;
}
article blockquote:first-of-type{
  border:0;border-left:2px solid var(--line-strong);color:var(--text);
  background:var(--quote-bg);font-size:14.5px;line-height:1.72;
}
article blockquote p{margin:6px 0}
article blockquote:first-of-type strong{color:var(--ink-strong)}

article code{
  border-radius:3px;background:var(--code-inline-bg);color:var(--code-inline-text);
  padding:.12em .35em;font-size:.86em;overflow-wrap:anywhere;
}
article pre{
  max-width:100%;margin:20px 0;padding:40px 16px 16px;border:1px solid #303733;
  border-radius:6px;background:var(--code-bg);box-shadow:none;
  overflow-x:auto;-webkit-overflow-scrolling:touch;
}
article pre code{overflow-wrap:normal;word-break:normal;white-space:pre}
article pre::before{color:#a9b3ac;font-size:10px;letter-spacing:.11em}
.copy-btn{
  top:8px;right:8px;padding:5px 10px;border:1px solid #4b554e;border-radius:3px;
  background:#262c28;color:#e2e7e1;font-size:11px;
}
.copy-btn:hover{background:#343b36}
.copy-btn.done{border-color:#4f8c78;background:#223b32}

.table-wrap{
  max-width:100%;margin:22px 0;border:1px solid var(--line);border-radius:6px;
  background:var(--surface);overflow-x:auto;overscroll-behavior-inline:contain;
}
article table{min-width:560px;font-size:13.5px}
article th,article td{padding:10px 12px;border-bottom:1px solid var(--line)}
article th{background:var(--surface-2);color:var(--ink-strong);font-weight:650;white-space:normal}
article tbody tr:hover{background:var(--surface-2)}
.table-wrap td:first-child,.table-wrap th:first-child{background:var(--surface)}
.table-wrap th:first-child{background:var(--surface-2)}
article tbody tr:hover td:first-child{background:var(--surface-2)}
.table-toggle{
  border:0;border-bottom:1px solid var(--line);border-radius:0;
  background:var(--surface-2);color:var(--rust);
}

.internal-toc{padding-top:36px}
.internal-toc > ol{
  margin:0;padding:18px 18px 18px 2.2em;border-top:1px solid var(--line);
  border-bottom:1px solid var(--line);background:transparent;border-radius:0;
  color:var(--text);
}
.internal-toc > ol a{color:var(--text);text-decoration:none}
.internal-toc > ol a:hover{color:var(--rust);text-decoration:underline}

.home-hero{padding:6px 0 34px;border-bottom:1px solid var(--line)}
article .home-hero h1{margin-bottom:20px}
.home-disclaimer{
  margin:0 0 24px;padding:11px 0;border-top:1px solid var(--line);
  border-bottom:1px solid var(--line);color:var(--muted);font-size:13px;line-height:1.7;
}
.home-disclaimer summary{
  cursor:pointer;color:var(--ink);font-weight:650;letter-spacing:.01em;
}
.home-disclaimer summary:hover{color:var(--rust)}
.home-disclaimer .legal-copy{padding:8px 0 1px 1.25em}
.home-disclaimer ol{margin:2px 0;padding-left:1.15em}
.home-disclaimer li{margin:5px 0}
.home-lede{
  max-width:720px;margin:0;color:var(--ink);font-size:20px;line-height:1.65;
  overflow-wrap:anywhere;
}
.home-lede strong{font-weight:680}
.home-hero + .doc-section{padding-top:34px}
.home-hero + .doc-section > ol{
  counter-reset:home-task;list-style:none;margin:24px 0;padding:0;
  border-top:1px solid var(--line);
}
.home-hero + .doc-section > ol > li{
  counter-increment:home-task;position:relative;display:block;min-width:0;
  margin:0;padding:16px 0 16px 64px;
  border-bottom:1px solid var(--line);
  overflow-wrap:anywhere;
}
.home-hero + .doc-section > ol > li::before{
  content:counter(home-task,decimal-leading-zero);position:absolute;left:0;top:16px;
  color:var(--rust);
  font-family:ui-monospace,"Cascadia Code",Consolas,monospace;
  font-size:12px;font-weight:700;line-height:1.9;letter-spacing:.04em;
}
.home-status{
  margin:0 0 12px;padding:13px 0 15px;border-top:1px solid var(--line);
  border-bottom:1px solid var(--line);color:var(--muted);font-size:12.5px;line-height:1.75;
}
.home-status p{
  display:flex;align-items:center;flex-wrap:wrap;gap:5px 8px;margin:5px 0;
  overflow-wrap:anywhere;
}
.home-status img{display:inline-block;width:auto;max-width:100%;height:20px;border-radius:0}
.home-status a{color:var(--muted);text-decoration-color:var(--line-strong)}
.home-status a:hover{color:var(--rust)}

body[data-page-kind="faq"] .faq-entry{
  display:grid;grid-template-columns:50px minmax(0,1fr);column-gap:20px;
  padding:28px 0;border-top:1px solid var(--line);
}
body[data-page-kind="faq"] .faq-entry::before{
  content:attr(data-entry);grid-column:1;grid-row:1 / span 20;
  color:var(--rust);font-family:ui-monospace,"Cascadia Code",Consolas,monospace;
  font-size:12px;font-weight:700;line-height:1.9;letter-spacing:.05em;
}
body[data-page-kind="faq"] .faq-entry > *{grid-column:2;min-width:0}
body[data-page-kind="faq"] .faq-entry > h2{
  margin:0 0 10px;font-size:20px;line-height:1.45;
}
body[data-page-kind="faq"] .faq-entry > h2 .anchor{margin-top:1px}
body[data-page-kind="faq"] .faq-entry:first-of-type{border-top:0;padding-top:20px}

body[data-page-kind="error"] .doc-section[data-role]{
  display:grid;grid-template-columns:104px minmax(0,1fr);column-gap:24px;
  padding:30px 0;border-top:1px solid var(--line);
}
body[data-page-kind="error"] .doc-section[data-role]::before{
  content:attr(data-section-index) " / " attr(data-role-label);
  grid-column:1;grid-row:1 / span 24;color:var(--muted);
  font-family:ui-monospace,"Cascadia Code",Consolas,monospace;
  font-size:10.5px;font-weight:700;line-height:1.7;letter-spacing:.055em;
  text-transform:uppercase;overflow-wrap:anywhere;
}
body[data-page-kind="error"] .doc-section[data-role] > *{
  grid-column:2;min-width:0;
}
body[data-page-kind="error"] .doc-section[data-role] > h2{
  margin:0 0 12px;font-size:22px;
}
body[data-page-kind="error"] .doc-section[data-role="symptom"]::before{color:var(--rust)}
body[data-page-kind="error"] .doc-section[data-role="fix"]::before{color:var(--ink)}
body[data-page-kind="error"] .doc-section[data-role="verify"]::before{color:var(--teal)}
body[data-page-kind="error"] .doc-section[data-role="verify"]{
  border-top-color:var(--teal);
}
body[data-page-kind="error"] .doc-section[data-role="related"],
body[data-page-kind="error"] .doc-section[data-role="detail"]{
  padding-top:24px;padding-bottom:24px;font-size:14.5px;
}
body[data-page-kind="error"] .doc-section[data-role="related"] > h2,
body[data-page-kind="error"] .doc-section[data-role="detail"] > h2{font-size:19px}

.crumb{
  max-width:760px;margin:20px auto 0;padding:0 24px;color:var(--muted);font-size:12px;
}
.crumb a:hover{color:var(--rust)}
.side-card{
  padding:0;border:0;border-radius:0;background:transparent;box-shadow:none;
}
.side-title{margin:6px 0 9px;padding:0}
.side-nav a,.toc-box a,.page-side a{
  border-radius:3px;color:var(--text);padding:5px 7px;
}
.side-nav a:hover,.toc-box a:hover,.page-side a:hover{
  background:var(--surface-2);color:var(--rust);
}
.side-nav a.current,.toc-box a.active,.page-side a.active{
  background:var(--surface-2);color:var(--rust);font-weight:650;
}
.side-group{
  margin-top:18px;padding-top:14px;border-top:1px solid var(--line);
}
.toc-box{
  margin:0 0 20px;padding:0 0 18px;border:0;border-bottom:1px solid var(--line);
}
.toc-box strong{margin-bottom:8px}
.page-side{
  font-size:13px;background:transparent;border:0;border-radius:0;box-shadow:none;
}
.pager{
  max-width:760px;gap:0;padding:0 24px 8px;border-top:1px solid var(--line);
  border-bottom:1px solid var(--line);
}
.pager a{
  padding:15px 0;border:0;border-radius:0;background:transparent;color:var(--text);
}
.pager a + a{border-left:0}
.pager a:hover{border-color:transparent;box-shadow:none;color:var(--rust)}
.pager a span{color:var(--muted);font-family:ui-monospace,"Cascadia Code",Consolas,monospace}
.pager a.next{text-align:right}
.site-footer{
  max-width:760px;padding:20px 24px 58px;color:var(--muted);font-size:12px;
}
.site-footer .foot-card{border-top:1px solid var(--line);padding-top:18px;text-align:left}
.site-footer .foot-label{
  border:0;border-radius:0;padding:0;color:var(--ink);font-size:10.5px;
  letter-spacing:.08em;text-transform:uppercase;
}
.site-footer a:hover{color:var(--rust)}
#toTop{
  width:40px;height:40px;border:1px solid var(--line-strong);border-radius:4px;
  background:var(--paper);color:var(--ink);box-shadow:none;
}
#toTop:hover{background:var(--surface-2);color:var(--rust)}
.anchor{color:var(--muted)}
.anchor.copied{color:var(--teal)}

@media (min-width:768px){
  article{padding:48px 32px 88px}
  article h1{font-size:38px}
  article h2{font-size:25px}
  .home-lede{font-size:21px}
  .pager{grid-template-columns:1fr 1fr;gap:0}
  .pager a:first-child{padding-right:22px}
  .pager a.next{padding-left:22px;border-left:1px solid var(--line)}
}
@media (min-width:900px){
  .menu-btn{display:none}
  .layout{
    display:grid;grid-template-columns:260px minmax(0,760px);
    justify-content:center;gap:56px;max-width:1120px;padding:0 24px;
  }
  .side{
    display:block;position:sticky;top:72px;max-height:calc(100vh - 92px);
    overflow-y:auto;padding:34px 0 48px;
  }
  .layout article{width:100%;max-width:760px;margin:0;padding:46px 0 88px}
  .crumb{max-width:1120px;padding:0 24px}
  .pager{max-width:760px;padding-left:0;padding-right:0;margin-left:calc((100% - 760px) / 2)}
  .site-footer{max-width:760px;padding-left:0;padding-right:0;margin-left:calc((100% - 760px) / 2)}
}
@media (min-width:1000px){
  .page{
    display:grid;grid-template-columns:minmax(0,760px) 238px;
    justify-content:center;gap:52px;max-width:1090px;padding:0 24px;
  }
  .page article{width:100%;max-width:760px;margin:0;padding:46px 0 88px}
  .page-side{
    display:block;width:238px;position:sticky;top:72px;
    max-height:calc(100vh - 92px);overflow-y:auto;margin:46px 0 0;padding:0;
  }
}
@media (max-width:899px){
  .internal-toc{display:none}
  .appbar{padding:10px 14px}
  .appbar .lang-switch{display:none}
  .doc-section{padding:34px 0 8px}
  body[data-page-kind="faq"] .faq-entry{
    grid-template-columns:42px minmax(0,1fr);column-gap:14px;padding:24px 0;
  }
  body[data-page-kind="error"] .doc-section[data-role]{
    display:block;padding:28px 0;
  }
  body[data-page-kind="error"] .doc-section[data-role]::before{
    display:block;margin:0 0 9px;
  }
  body[data-page-kind="error"] .doc-section[data-role="verify"]{
    background:none;
  }
  .pager{grid-template-columns:1fr;gap:0}
  .pager a.next{border-left:0;border-top:1px solid var(--line);text-align:left}
}
@media (max-width:520px){
  html{scroll-padding-top:68px}
  .appbar{gap:10px;padding:9px 12px}
  .brand-mark{width:28px;height:28px}
  .appbar-title{font-size:13.5px}
  .appbar-sub{display:none}
  .appbar-actions{gap:5px}
  .icon-btn{width:34px;height:34px}
  article{padding:30px 16px 64px}
  article h1{font-size:29px;line-height:1.28}
  article h2{font-size:22px}
  article h3{font-size:17px}
  .home-hero{padding-bottom:28px}
  .home-lede{font-size:18px;line-height:1.65}
  .home-hero + .doc-section > ol > li{padding-left:48px}
  .home-status p{display:block}
  .home-status a{display:inline}
  body[data-page-kind="faq"] .faq-entry{
    grid-template-columns:34px minmax(0,1fr);column-gap:10px;
  }
  body[data-page-kind="faq"] .faq-entry > h2{font-size:18.5px}
  body[data-page-kind="error"] .doc-section[data-role] > h2{font-size:20px}
  .pager{padding-left:16px;padding-right:16px}
  .site-footer{padding-left:16px;padding-right:16px}
  article pre{font-size:12.5px}
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

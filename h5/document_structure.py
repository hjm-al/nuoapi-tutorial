# -*- coding: utf-8 -*-
"""Shared HTML structure transforms for the single-page and multi-page builds."""

from __future__ import annotations

import html
import re


HEADING = re.compile(r"<h2\b[^>]*>.*?</h2>", re.IGNORECASE | re.DOTALL)
TAG = re.compile(r"<[^>]+>")
LEADING_NUMBER = re.compile(r"^\s*(\d+)\.\s*")
DOC_SECTION = re.compile(
    r'<section\b[^>]*class="[^"]*\bdoc-section\b[^"]*"[^>]*>.*?</section>',
    re.IGNORECASE | re.DOTALL,
)

ROLE_LABELS = {
    "zh-CN": {
        "symptom": "症状",
        "fix": "配置 / 解法",
        "verify": "验证",
        "related": "相关",
        "detail": "详细说明",
    },
    "en": {
        "symptom": "Symptom",
        "fix": "Configuration",
        "verify": "Verification",
        "related": "Related",
        "detail": "Details",
    },
    "ja": {
        "symptom": "症状",
        "fix": "設定 / 対処",
        "verify": "確認",
        "related": "関連",
        "detail": "詳細",
    },
    "zh-Hant": {
        "symptom": "症狀",
        "fix": "設定 / 解法",
        "verify": "驗證",
        "related": "相關",
        "detail": "詳細說明",
    },
}


def heading_text(heading_html: str) -> str:
    """Return readable heading text without tags or entities."""
    return html.unescape(TAG.sub("", heading_html)).strip()


def section_role(title: str) -> str:
    """Map known error-page headings to a layout role.

    Matching uses all four site locales, but still falls back to ``detail``.
    The fallback is intentional: an unfamiliar translation must render even
    when its wording has no entry here.
    """
    title = title.strip().lower()
    if any(token in title for token in ("相关深页", "相關深頁", "関連ページ", "related")):
        return "related"
    if any(token in title for token in ("症状", "症狀", "symptom")):
        return "symptom"
    if any(
        token in title
        for token in (
            "验证步骤",
            "驗證步驟",
            "验证",
            "驗證",
            "verification",
            "確認",
            "重启",
            "重啟",
            "restart",
        )
    ):
        return "verify"
    if any(
        token in title
        for token in (
            "单一解法",
            "單一解法",
            "一份配置",
            "一つの設定",
            "單一設定",
            "one configuration",
        )
    ):
        return "fix"
    return "detail"


def is_page_toc(title: str) -> bool:
    """Identify the in-article Markdown TOC without relying on one locale."""
    normalized = re.sub(r"\s+", "", title).lower()
    return normalized in {"目录", "目錄", "contents", "目次", "tableofcontents"}


def _number_faq_heading(heading_html: str, fallback: int) -> tuple[str, str]:
    """Move a FAQ's leading number into a dedicated index column."""
    inner = re.match(r"(<h2\b[^>]*>)(.*?)(</h2>)", heading_html, re.I | re.S)
    if not inner:
        return heading_html, "{0:02d}".format(fallback)
    content = inner.group(2)
    number = LEADING_NUMBER.match(TAG.sub("", content))
    if not number:
        return heading_html, "{0:02d}".format(fallback)
    content = LEADING_NUMBER.sub("", content, count=1)
    return (
        inner.group(1) + content + inner.group(3),
        "{0:02d}".format(int(number.group(1))),
    )


def wrap_sections(html_text: str, kind: str, locale: str = "zh-CN") -> str:
    """Wrap every H2 and its following content in a semantic page section."""
    matches = list(HEADING.finditer(html_text))
    if not matches:
        return html_text

    parts = [html_text[: matches[0].start()]]
    role_labels = ROLE_LABELS.get(locale, ROLE_LABELS["zh-CN"])
    for index, match in enumerate(matches, start=1):
        end = matches[index].start() if index < len(matches) else len(html_text)
        block = html_text[match.start() : end]
        heading = match.group(0)
        title = heading_text(heading)
        classes = ["doc-section"]
        attributes = ['data-section-index="{0:02d}"'.format(index)]

        if is_page_toc(title):
            classes.append("internal-toc")
            attributes.append('data-landmark="toc"')

        if kind == "faq":
            heading, entry_number = _number_faq_heading(heading, index)
            block = heading + block[match.end() - match.start() :]
            classes.append("faq-entry")
            attributes.append('data-entry="{0}"'.format(entry_number))

        if kind == "error":
            role = section_role(title)
            classes.append("role-" + role)
            attributes.extend(
                [
                    'data-role="{0}"'.format(role),
                    'data-role-label="{0}"'.format(
                        html.escape(role_labels[role], quote=True)
                    ),
                ]
            )

        parts.append(
            '<section class="{0}" {1}>{2}</section>'.format(
                " ".join(classes), " ".join(attributes), block
            )
        )
    return "".join(parts)


def _compact_disclaimer(blockquote: str) -> str:
    """Turn the home legal notice into a compact, keyboard-accessible disclosure."""
    match = re.match(
        r"\s*<blockquote>\s*<p><strong>(.*?)</strong></p>(.*?)</blockquote>",
        blockquote,
        re.I | re.S,
    )
    if not match:
        return '<div class="home-disclaimer">{0}</div>'.format(blockquote)
    return (
        '<details class="home-disclaimer">'
        "<summary>{0}</summary>"
        '<div class="legal-copy">{1}</div>'
        "</details>"
    ).format(match.group(1), match.group(2))


def _looks_like_status(markup: str) -> bool:
    """Keep badge rows and auxiliary links out of the one-sentence lead."""
    lowered = markup.lower()
    if "<img" in lowered or "github.io" in lowered:
        return True
    language_links = sum(
        marker in markup for marker in ("简体中文", "English", "日本語", "繁體中文")
    )
    return language_links >= 2


def transform_home_content(html_text: str) -> str:
    """Put the existing home-page facts into the technical-manual hero order.

    No prose is rewritten. ``html_text`` is expected to have already passed
    through ``wrap_sections`` so every H2 is an independent block. The H1,
    legal notice, positioning sentence, dry-run plan, status links, and all
    remaining README sections are moved as intact fragments.
    """
    h1 = re.search(r"<h1\b[^>]*>.*?</h1>", html_text, re.I | re.S)
    if not h1:
        return html_text

    after_h1 = html_text[h1.end() :]
    first_section_match = re.search(
        r'<section\b[^>]*class="[^"]*\bdoc-section\b[^"]*"[^>]*>',
        after_h1,
        re.I,
    )
    lead = after_h1[: first_section_match.start()] if first_section_match else after_h1
    blocks = re.findall(
        r"<blockquote>.*?</blockquote>|<p\b[^>]*>.*?</p>",
        lead,
        re.I | re.S,
    )
    disclaimer = next(
        (block for block in blocks if block.lstrip().lower().startswith("<blockquote")),
        "",
    )
    paragraphs = [block for block in blocks if block != disclaimer]
    lede = ""
    status_blocks = []
    for block in paragraphs:
        if not lede and not _looks_like_status(block):
            lede = block
        elif _looks_like_status(block):
            status_blocks.append(block)

    remaining = after_h1[first_section_match.start() :] if first_section_match else ""
    plan_section = ""
    plan_match = next(
        (
            match
            for match in DOC_SECTION.finditer(remaining)
            if "--selftest" in match.group(0) and "model_verify.py" in match.group(0)
        ),
        None,
    )
    if plan_match:
        plan_section = plan_match.group(0)
        remaining = remaining[: plan_match.start()] + remaining[plan_match.end() :]

    hero = [h1.group(0)]
    if disclaimer:
        hero.append(_compact_disclaimer(disclaimer))
    if lede:
        hero.append('<p class="home-lede">{0}</p>'.format(lede[3:-4]))
    output = '<header class="home-hero">{0}</header>'.format("".join(hero))
    if plan_section:
        output += plan_section
    if status_blocks:
        output += (
            '<div class="home-status">{0}</div>'.format("".join(status_blocks))
        )
    return output + remaining

#!/usr/bin/env python3
"""Notify IndexNow about the URLs published by the GitHub Pages site.

The submitter intentionally uses only the Python standard library. The
IndexNow key is read from ``build_site.py`` so the deployment script and the
published key file cannot drift.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen


SCRIPT_DIR = Path(__file__).resolve().parent
SITEMAP_FILENAME = "sitemap.xml"
DEFAULT_SITEMAP = SCRIPT_DIR / "_site" / SITEMAP_FILENAME
INDEXNOW_ENDPOINT = "https://api.indexnow.org/indexnow"
MAX_ATTEMPTS = 3
REQUEST_TIMEOUT_SECONDS = 30


class SubmissionError(RuntimeError):
    """Raised when sitemap collection or IndexNow submission fails."""

    def __init__(
        self,
        message: str,
        *,
        url_count: int | None = None,
        http_status: int | None = None,
        attempts: int | None = None,
    ) -> None:
        super().__init__(message)
        self.url_count = url_count
        self.http_status = http_status
        self.attempts = attempts


@dataclass(frozen=True)
class SubmissionResult:
    site_url: str
    urls: tuple[str, ...]
    payload: dict[str, object]
    dry_run: bool
    http_status: int | None
    attempts: int


def _load_indexnow_key() -> str:
    source = (SCRIPT_DIR / "build_site.py").read_text(encoding="utf-8")
    tree = ast.parse(source, filename="build_site.py")
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == "INDEXNOW_KEY"
                   for target in targets):
            continue
        if node.value is None:
            break
        value = ast.literal_eval(node.value)
        if isinstance(value, str) and value:
            return value
        break
    raise RuntimeError("build_site.py does not define a usable INDEXNOW_KEY")


INDEXNOW_KEY = _load_indexnow_key()


def normalize_site_url(raw: str) -> str:
    """Return a strict HTTPS site root without query, fragment, or userinfo."""
    parsed = urlsplit(raw.strip())
    if parsed.scheme.lower() != "https":
        raise ValueError("site URL must use HTTPS")
    if not parsed.hostname:
        raise ValueError("site URL must include a host")
    if parsed.username or parsed.password:
        raise ValueError("site URL must not include user information")
    if parsed.query or parsed.fragment:
        raise ValueError("site URL must not include a query or fragment")
    path = parsed.path.rstrip("/")
    return urlunsplit(("https", parsed.netloc.lower(), path, "", ""))


def key_location(site_url: str) -> str:
    return "{0}/{1}.txt".format(site_url.rstrip("/"), INDEXNOW_KEY)


def is_allowed_url(raw_url: str, site_url: str) -> bool:
    """Keep only HTTPS URLs inside the configured host and path prefix."""
    try:
        candidate = urlsplit(raw_url.strip())
        site = urlsplit(site_url)
    except ValueError:
        return False
    if candidate.scheme.lower() != "https" or not candidate.hostname:
        return False
    if candidate.username or candidate.password:
        return False
    if candidate.fragment or candidate.netloc.lower() != site.netloc.lower():
        return False

    site_path = site.path.rstrip("/")
    if not site_path:
        return True
    return candidate.path == site_path or candidate.path.startswith(site_path + "/")


def dedupe_urls(raw_urls: Iterable[str], site_url: str) -> list[str]:
    """Filter, trim, and de-duplicate sitemap URLs while preserving order."""
    unique: dict[str, None] = {}
    for raw_url in raw_urls:
        candidate = raw_url.strip()
        if candidate and is_allowed_url(candidate, site_url):
            unique.setdefault(candidate, None)
    return list(unique)


def parse_sitemap(xml_text: str) -> list[str]:
    """Read all ``loc`` elements, including namespaced sitemap documents."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise SubmissionError("invalid sitemap XML: {0}".format(exc)) from exc
    urls = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] == "loc" and element.text:
            urls.append(element.text)
    return urls


def fetch_sitemap(
    site_url: str,
    opener: Callable[..., object] = urlopen,
) -> str:
    sitemap_url = site_url.rstrip("/") + "/" + SITEMAP_FILENAME
    request = Request(
        sitemap_url,
        headers={"User-Agent": "nuoapi-tutorial-indexnow/1.0"},
    )
    try:
        with opener(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset)
    except HTTPError as exc:
        raise SubmissionError(
            "could not read {0}: {1}".format(sitemap_url, exc),
            http_status=exc.code,
        ) from exc
    except (URLError, OSError, TimeoutError) as exc:
        raise SubmissionError("could not read {0}: {1}".format(sitemap_url, exc)) from exc


def build_payload(site_url: str, urls: Sequence[str]) -> dict[str, object]:
    site = urlsplit(site_url)
    return {
        "host": site.netloc,
        "key": INDEXNOW_KEY,
        "keyLocation": key_location(site_url),
        "urlList": list(urls),
    }


def post_json(
    payload: Mapping[str, object],
    opener: Callable[..., object] = urlopen,
) -> tuple[int, str]:
    body = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    request = Request(
        INDEXNOW_ENDPOINT,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": "nuoapi-tutorial-indexnow/1.0",
        },
    )
    with opener(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        status = int(response.status)
        response_body = response.read().decode("utf-8", errors="replace")
        return status, response_body


def submit_payload(
    payload: Mapping[str, object],
    requester: Callable[[Mapping[str, object]], tuple[int, str]] = post_json,
    sleeper: Callable[[float], None] = time.sleep,
    max_attempts: int = MAX_ATTEMPTS,
) -> tuple[int, str, int]:
    """Submit with bounded retries and return status, response body, attempts."""
    last_error = "unknown error"
    last_status = None
    url_count = len(payload.get("urlList", []))
    for attempt in range(1, max_attempts + 1):
        try:
            status, response_body = requester(payload)
            last_status = status
            if 200 <= status < 300:
                return status, response_body, attempt
            last_error = "HTTP {0}: {1}".format(status, response_body[:200])
        except Exception as exc:  # Retry network and response-shape failures.
            last_error = "{0}: {1}".format(type(exc).__name__, exc)
        if attempt < max_attempts:
            sleeper(float(2 ** (attempt - 1)))
    raise SubmissionError(
        "IndexNow submission failed after {0} attempts: {1}".format(
            max_attempts,
            last_error,
        ),
        url_count=url_count,
        http_status=last_status,
        attempts=max_attempts,
    )


def fetch_sitemap_with_retries(
    site_url: str,
    *,
    fetcher: Callable[[str], str] = fetch_sitemap,
    sleeper: Callable[[float], None] = time.sleep,
    max_attempts: int = MAX_ATTEMPTS,
) -> str:
    """Retry the public sitemap read while Pages finishes propagating."""
    last_error = "unknown error"
    last_status = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fetcher(site_url)
        except Exception as exc:
            last_error = "{0}: {1}".format(type(exc).__name__, exc)
            last_status = getattr(exc, "http_status", None)
            if last_status is None:
                last_status = getattr(exc, "code", None)
        if attempt < max_attempts:
            sleeper(float(attempt))
    raise SubmissionError(
        "could not read sitemap after {0} attempts: {1}".format(
            max_attempts,
            last_error,
        ),
        http_status=last_status,
        attempts=max_attempts,
    )


def run_submission(
    site_url: str,
    *,
    dry_run: bool = False,
    sitemap_path: Path | None = None,
    fetcher: Callable[[str], str] = fetch_sitemap,
    requester: Callable[[Mapping[str, object]], tuple[int, str]] = post_json,
    sleeper: Callable[[float], None] = time.sleep,
    max_attempts: int = MAX_ATTEMPTS,
) -> SubmissionResult:
    normalized = normalize_site_url(site_url)
    if dry_run:
        source = Path(sitemap_path) if sitemap_path else DEFAULT_SITEMAP
        if not source.exists():
            raise SubmissionError(
                "local sitemap not found: {0}; run the site build first".format(source)
            )
        sitemap_text = source.read_text(encoding="utf-8")
    else:
        sitemap_text = fetch_sitemap_with_retries(
            normalized,
            fetcher=fetcher,
            sleeper=sleeper,
            max_attempts=max_attempts,
        )

    urls = dedupe_urls(parse_sitemap(sitemap_text), normalized)
    if not urls:
        raise SubmissionError("sitemap contains no URLs for " + normalized)
    payload = build_payload(normalized, urls)

    if dry_run:
        return SubmissionResult(
            site_url=normalized,
            urls=tuple(urls),
            payload=payload,
            dry_run=True,
            http_status=None,
            attempts=0,
        )

    status, _response_body, attempts = submit_payload(
        payload,
        requester=requester,
        sleeper=sleeper,
        max_attempts=max_attempts,
    )
    return SubmissionResult(
        site_url=normalized,
        urls=tuple(urls),
        payload=payload,
        dry_run=False,
        http_status=status,
        attempts=attempts,
    )


def write_step_summary(lines: Sequence[str]) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as summary:
        summary.write("\n".join(lines).rstrip() + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Submit the published sitemap to IndexNow."
    )
    parser.add_argument("--site-url", required=True, help="HTTPS Pages site root")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="read h5/_site/sitemap.xml and do not send network requests",
    )
    parser.add_argument(
        "--sitemap",
        type=Path,
        help="local sitemap path for dry-run (default: h5/_site/sitemap.xml)",
    )
    args = parser.parse_args(argv)

    try:
        result = run_submission(
            args.site_url,
            dry_run=args.dry_run,
            sitemap_path=args.sitemap,
        )
    except (SubmissionError, ValueError) as exc:
        url_count = getattr(exc, "url_count", None)
        http_status = getattr(exc, "http_status", None)
        attempts = getattr(exc, "attempts", None)
        write_step_summary(
            [
                "### IndexNow",
                "",
                "- Submission failed: `{0}`".format(str(exc).replace("`", "'")),
                "- Eligible URLs: {0}".format(
                    url_count if url_count is not None else "not available"
                ),
                "- HTTP status: {0}".format(
                    http_status if http_status is not None else "not received"
                ),
                "- Attempts: {0}".format(
                    attempts if attempts is not None else "not started"
                ),
                "- The GitHub Pages deployment remains valid.",
            ]
        )
        print("ERROR: {0}".format(exc), file=sys.stderr)
        return 1

    if result.dry_run:
        write_step_summary(
            [
                "### IndexNow dry run",
                "",
                "- Eligible URLs: {0}".format(len(result.urls)),
                "- Network requests: 0",
            ]
        )
        print(
            "DRY RUN: {0} eligible URLs; no network requests sent".format(
                len(result.urls)
            )
        )
        return 0

    write_step_summary(
        [
            "### IndexNow",
            "",
            "- Eligible URLs: {0}".format(len(result.urls)),
            "- HTTP status: {0}".format(result.http_status),
            "- Attempts: {0}".format(result.attempts),
        ]
    )
    print(
        "IndexNow accepted {0} URLs with HTTP {1} after {2} attempt(s)".format(
            len(result.urls),
            result.http_status,
            result.attempts,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

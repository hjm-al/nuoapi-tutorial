# -*- coding: utf-8 -*-
"""IndexNow submitter contract tests. No real HTTP requests are made."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
H5 = ROOT / "h5"
sys.path.insert(0, str(H5))

import submit_indexnow  # noqa: E402


class FakeResponse:
    status = 202

    def __init__(self, body: bytes = b"") -> None:
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return self._body


class TestIndexNow(unittest.TestCase):
    def test_deduplicates_and_rejects_ineligible_urls(self):
        site = submit_indexnow.normalize_site_url(
            "https://example.github.io/nuoapi-tutorial/"
        )
        urls = submit_indexnow.dedupe_urls(
            [
                "https://example.github.io/nuoapi-tutorial/",
                "https://example.github.io/nuoapi-tutorial/a.html",
                "https://example.github.io/nuoapi-tutorial/a.html",
                "http://example.github.io/nuoapi-tutorial/b.html",
                "https://other.example/nuoapi-tutorial/c.html",
                "https://example.github.io/nuoapi-tutorial-other/d.html",
                "https://user:pass@example.github.io/nuoapi-tutorial/e.html",
            ],
            site,
        )
        self.assertEqual(
            urls,
            [
                "https://example.github.io/nuoapi-tutorial/",
                "https://example.github.io/nuoapi-tutorial/a.html",
            ],
        )

    def test_parse_sitemap_accepts_namespaced_locs(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.github.io/nuoapi-tutorial/</loc></url>
  <url><loc>https://example.github.io/nuoapi-tutorial/faq.html</loc></url>
</urlset>
"""
        self.assertEqual(
            submit_indexnow.parse_sitemap(xml),
            [
                "https://example.github.io/nuoapi-tutorial/",
                "https://example.github.io/nuoapi-tutorial/faq.html",
            ],
        )

    def test_payload_contains_required_indexnow_fields(self):
        site = submit_indexnow.normalize_site_url(
            "https://example.github.io/nuoapi-tutorial"
        )
        urls = [
            "https://example.github.io/nuoapi-tutorial/",
            "https://example.github.io/nuoapi-tutorial/faq.html",
        ]
        payload = submit_indexnow.build_payload(site, urls)
        self.assertEqual(payload["host"], "example.github.io")
        self.assertEqual(payload["key"], submit_indexnow.INDEXNOW_KEY)
        self.assertEqual(
            payload["keyLocation"],
            "https://example.github.io/nuoapi-tutorial/{0}.txt".format(
                submit_indexnow.INDEXNOW_KEY
            ),
        )
        self.assertEqual(payload["urlList"], urls)

    def test_post_json_sends_payload_to_indexnow(self):
        captured = {}

        def opener(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return FakeResponse()

        payload = {
            "host": "example.github.io",
            "key": "test-key",
            "keyLocation": "https://example.github.io/project/test-key.txt",
            "urlList": ["https://example.github.io/project/"],
        }
        status, body = submit_indexnow.post_json(payload, opener=opener)

        self.assertEqual(status, 202)
        self.assertEqual(body, "")
        request = captured["request"]
        self.assertEqual(request.full_url, submit_indexnow.INDEXNOW_ENDPOINT)
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(
            request.get_header("Content-type"),
            "application/json; charset=utf-8",
        )
        self.assertEqual(json.loads(request.data.decode("utf-8")), payload)

    def test_submission_retries_three_times_then_accepts_202(self):
        statuses = iter([503, 500, 202])
        sleeps = []

        def requester(_payload):
            return next(statuses), "response"

        status, _, attempts = submit_indexnow.submit_payload(
            {"urlList": []},
            requester=requester,
            sleeper=sleeps.append,
        )
        self.assertEqual(status, 202)
        self.assertEqual(attempts, 3)
        self.assertEqual(sleeps, [1.0, 2.0])

    def test_submission_fails_after_bounded_retries(self):
        calls = []
        payload = {
            "urlList": [
                "https://example.github.io/project/",
                "https://example.github.io/project/faq.html",
            ]
        }

        def requester(_payload):
            calls.append(1)
            return 500, "still unavailable"

        with self.assertRaises(submit_indexnow.SubmissionError) as raised:
            submit_indexnow.submit_payload(
                payload,
                requester=requester,
                sleeper=lambda _seconds: None,
            )
        self.assertEqual(len(calls), 3)
        self.assertEqual(raised.exception.url_count, 2)
        self.assertEqual(raised.exception.http_status, 500)
        self.assertEqual(raised.exception.attempts, 3)

    def test_sitemap_fetch_retries_before_submission(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.github.io/project/</loc></url>
</urlset>
"""
        fetch_calls = []
        sleeps = []

        def fetcher(_site_url):
            fetch_calls.append(1)
            if len(fetch_calls) < 3:
                raise OSError("sitemap not ready")
            return xml

        result = submit_indexnow.run_submission(
            "https://example.github.io/project",
            fetcher=fetcher,
            requester=lambda _payload: (202, "accepted"),
            sleeper=sleeps.append,
        )
        self.assertEqual(len(fetch_calls), 3)
        self.assertEqual(sleeps, [1.0, 2.0])
        self.assertEqual(result.http_status, 202)
        self.assertEqual(len(result.urls), 1)

    def test_sitemap_http_error_keeps_status_for_summary(self):
        def fetcher(_site_url):
            raise HTTPError(
                "https://example.github.io/project/sitemap.xml",
                503,
                "Service Unavailable",
                {},
                None,
            )

        with self.assertRaises(submit_indexnow.SubmissionError) as raised:
            submit_indexnow.run_submission(
                "https://example.github.io/project",
                fetcher=fetcher,
                requester=lambda _payload: (202, "accepted"),
                sleeper=lambda _seconds: None,
            )

        self.assertEqual(raised.exception.http_status, 503)
        self.assertEqual(raised.exception.attempts, 3)

    def test_failure_summary_includes_status_and_attempts(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary = Path(tmp) / "summary.md"
            with mock.patch.dict(
                os.environ,
                {"GITHUB_STEP_SUMMARY": str(summary)},
                clear=False,
            ):
                with mock.patch.object(
                    submit_indexnow,
                    "run_submission",
                    side_effect=submit_indexnow.SubmissionError(
                        "HTTP 503",
                        url_count=37,
                        http_status=503,
                        attempts=3,
                    ),
                ):
                    self.assertEqual(submit_indexnow.main([
                        "--site-url",
                        "https://example.github.io/project",
                    ]), 1)

            text = summary.read_text(encoding="utf-8")
            self.assertIn("Eligible URLs: 37", text)
            self.assertIn("HTTP status: 503", text)
            self.assertIn("Attempts: 3", text)

    def test_dry_run_reads_local_sitemap_without_network(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.github.io/nuoapi-tutorial/</loc></url>
  <url><loc>https://example.github.io/nuoapi-tutorial/faq.html</loc></url>
</urlset>
"""
        with tempfile.TemporaryDirectory() as tmp:
            sitemap = Path(tmp) / "sitemap.xml"
            sitemap.write_text(xml, encoding="utf-8")

            def no_network(*_args, **_kwargs):
                self.fail("dry-run attempted a network request")

            result = submit_indexnow.run_submission(
                "https://example.github.io/nuoapi-tutorial",
                dry_run=True,
                sitemap_path=sitemap,
                fetcher=no_network,
                requester=no_network,
            )

        self.assertTrue(result.dry_run)
        self.assertIsNone(result.http_status)
        self.assertEqual(result.attempts, 0)
        self.assertEqual(len(result.urls), 2)


if __name__ == "__main__":
    unittest.main()

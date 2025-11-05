import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = ROOT / "index.html"


class TestFextoLandingPage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = INDEX_HTML.read_text(encoding="utf-8")

    def test_has_canonical_link(self):
        self.assertIn(
            '<link rel="canonical" href="https://fexto.app/" />',
            self.html,
            "Expected canonical link for SEO not found.",
        )

    def test_has_structured_data(self):
        self.assertIn(
            '<script type="application/ld+json">',
            self.html,
            "Missing JSON-LD structured data block.",
        )

    def test_has_download_form(self):
        self.assertIn(
            'id="download-form"',
            self.html,
            "Downloader form with id 'download-form' is required.",
        )
        self.assertIn(
            'id="video-url"',
            self.html,
            "URL input field with id 'video-url' should exist.",
        )

    def test_has_platform_tabs(self):
        for platform in ("instagram", "youtube", "tiktok", "facebook", "twitter"):
            with self.subTest(platform=platform):
                self.assertIn(
                    f'data-platform="{platform}"',
                    self.html,
                    f"Platform tab for {platform} is missing.",
                )

    def test_has_results_card(self):
        self.assertIn(
            'id="result"',
            self.html,
            "Results card container should exist for displaying download links.",
        )
        self.assertIn(
            'id="copy-btn"',
            self.html,
            "Copy button should be present for mirror reuse.",
        )

    def test_has_hero_statistics(self):
        self.assertIn(
            '<dl class="hero-stats">',
            self.html,
            "Hero statistics definition list is missing.",
        )


if __name__ == "__main__":
    unittest.main()

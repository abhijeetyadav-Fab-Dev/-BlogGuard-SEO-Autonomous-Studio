import os
import unittest
import crawler
import audit_engine
import api_integrations
import export_helper

class TestBlogGuard(unittest.TestCase):
    def test_readability_calculations(self):
        text = "Search engine optimization is the process of improving the quality and quantity of website traffic."
        words = text.split()
        sentences = [text]
        read = crawler.calculate_readability(text, words, sentences)
        self.assertIn("flesch_reading_ease", read)
        self.assertIn("flesch_kincaid_grade", read)
        self.assertGreater(read["flesch_reading_ease"], 0)

    def test_mock_page_audit(self):
        mock_data = {
            "title": "Best Technical SEO Guide 2026",
            "meta_description": "Learn the best technical SEO practices to rank your website on Google search engine results in 2026.",
            "canonical_url": "https://example.com/guide",
            "url": "https://example.com/guide",
            "final_url": "https://example.com/guide",
            "status_code": 200,
            "engine": "Test",
            "robots": "index, follow",
            "author": "Dr. SEO Expert",
            "published_date": "2026-01-01",
            "headings": [
                {"tag": "h1", "level": 1, "text": "Best Technical SEO Guide 2026"},
                {"tag": "h2", "level": 2, "text": "Understanding Technical SEO"},
                {"tag": "h2", "level": 2, "text": "Core Web Vitals and PageSpeed"},
                {"tag": "h2", "level": 2, "text": "Conclusion and Key Takeaways"},
            ],
            "h1_list": ["Best Technical SEO Guide 2026"],
            "h2_list": ["Understanding Technical SEO", "Core Web Vitals and PageSpeed", "Conclusion and Key Takeaways"],
            "h3_list": [],
            "hierarchy_valid": True,
            "clean_text": "Best Technical SEO Guide 2026. Understanding technical SEO is crucial. According to research by Stanford.edu, page speed matters. In conclusion, technical SEO ensures indexability.",
            "words": ["Best", "Technical", "SEO", "Guide", "2026"] * 150, # 750 words
            "sentence_count": 40,
            "paragraph_count": 8,
            "reading_time_min": 3.5,
            "images": [{"src": "img.png", "alt": "Technical SEO architecture", "has_alt": True, "format": ".webp", "loading": "lazy"}],
            "images_without_alt": [],
            "links": [{"href": "https://example.com/other", "text": "Other", "is_internal": True, "is_nofollow": False, "is_citation": False}],
            "internal_links_count": 3,
            "external_links_count": 2,
            "nofollow_links_count": 0,
            "citation_links": [{"href": "https://stanford.edu/paper", "text": "Stanford", "is_citation": True}],
            "in_text_sources": 1,
            "opengraph": {"og:title": "Best Technical SEO Guide"},
            "twitter_cards": {},
            "schema_types": ["Article"],
            "readability": {"flesch_reading_ease": 65.0, "flesch_kincaid_grade": 8.0, "avg_sentence_length": 18.0, "complex_words": 20},
            "long_sentences": [],
            "suggested_keyword": "technical seo",
        }
        res = audit_engine.audit_page(mock_data, keyword="technical seo")
        self.assertGreaterEqual(res["overall_score"], 70)
        self.assertEqual(len(res["scores"]), 7)
        self.assertIn("Technical SEO", res["scores"])
        self.assertIn("Content & Readability", res["scores"])

        html_out = export_helper.generate_html_report(mock_data, res)
        self.assertIn("BlogGuard SEO Intelligence Report", html_out)
        self.assertIn("Best Technical SEO Guide 2026", html_out)

    def test_crawler_on_real_page(self):
        res = crawler.fetch_html("https://example.com", use_browser=False)
        self.assertEqual(res["status_code"], 200)
        data = crawler.parse_page_data(res)
        self.assertIn("Example Domain", data["title"])

if __name__ == "__main__":
    unittest.main()

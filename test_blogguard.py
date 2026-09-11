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
    def test_highlighted_html(self):
        text = "Organizations must utilize modern strategies to avoid mistakes. Furthermore, we recieved alot of feedback. The report was written by our team in order to provide clarity."
        html_res = audit_engine.generate_highlighted_html(
            text,
            keyword="strategies",
            hl_kw=True,
            hl_jg=True,
            hl_tp=True,
            hl_ls=True,
            hl_rd=True,
            hl_pv=True
        )
        self.assertIn("hl-kw", html_res)
        self.assertIn("hl-jargon", html_res)
        self.assertIn("hl-typo", html_res)
        self.assertIn("hl-redundant", html_res)
        self.assertIn("hl-passive", html_res)

    def test_grammar_clarity_alignment(self):
        # 1. Passive voice detection
        sentences = [
            "The SEO audit was performed by our team.",
            "Search engines reward active, engaging writing.",
            "New guidelines were published by Google."
        ]
        pv = audit_engine.detect_passive_voice(sentences)
        self.assertEqual(pv["count"], 2)
        self.assertAlmostEqual(pv["percentage"], 66.7, places=1)

        # 2. Redundancy detection
        sample_text = "In order to succeed, at this point in time we must make a decision for the purpose of growth."
        reds = audit_engine.detect_redundancies(sample_text)
        phrases = [r["phrase"] for r in reds]
        self.assertIn("in order to", phrases)
        self.assertIn("at this point in time", phrases)
        self.assertIn("for the purpose of", phrases)

        # 3. Content alignment test
        title = "10 Best SEO Practices For High Ranking"
        h1 = ["10 Best SEO Practices For High Ranking"]
        h2 = ["Practice 1: Keyword Research", "Practice 2: Backlinks", "Practice 3: Speed"]
        text = "This guide covers SEO practices and keyword research to improve rankings on search engines."
        align = audit_engine.check_content_alignment(title, h1, h2, text)
        self.assertIn("score", align)
        self.assertEqual(align["promise_type"], "listicle")
        self.assertEqual(align["promised_number"], 10)
        self.assertEqual(align["actual_h2_count"], 3)
        # Should flag mismatch between promised 10 and actual 3
        mismatch_found = any("promises 10 items" in obs for obs in align["observations"])
        self.assertTrue(mismatch_found)


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

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

    def test_crawler_error_handling(self):
        # Invalid / non-existent domain should gracefully return status >= 400 and error string, never crash
        res = crawler.fetch_html("https://invalid-non-existent-domain-test-xyz987.com", use_browser=False)
        self.assertGreaterEqual(res["status_code"], 400)
        self.assertTrue(bool(res.get("error")))
        self.assertEqual(res["html"], "")

    def test_mode2_battle_comparison_data_integrity(self):
        import pandas as pd
        # Simulate dual article audit
        p1 = {"title": "Post 1", "clean_text": "SEO tips for search engine ranking.", "words": ["seo"]*200, "sentence_count": 10, "paragraph_count": 2, "headings": [], "h1_list": ["Post 1"], "h2_list": ["Section A"], "h3_list": [], "images": [], "images_without_alt": [], "citation_links": [], "internal_links_count": 1, "in_text_sources": 0, "schema_types": [], "readability": {"flesch_reading_ease": 60.0, "flesch_kincaid_grade": 8.0, "avg_sentence_length": 15, "complex_words": 10}, "long_sentences": [], "url": "https://p1.com", "final_url": "https://p1.com", "status_code": 200, "load_time_sec": 0.5, "engine": "HTTP"}
        p2 = {"title": "Post 2", "clean_text": "Advanced guide to search engine ranking.", "words": ["seo"]*400, "sentence_count": 20, "paragraph_count": 4, "headings": [], "h1_list": ["Post 2"], "h2_list": ["Section X", "Section Y"], "h3_list": [], "images": [], "images_without_alt": [], "citation_links": [], "internal_links_count": 2, "in_text_sources": 0, "schema_types": [], "readability": {"flesch_reading_ease": 70.0, "flesch_kincaid_grade": 7.0, "avg_sentence_length": 12, "complex_words": 15}, "long_sentences": [], "url": "https://p2.com", "final_url": "https://p2.com", "status_code": 200, "load_time_sec": 0.4, "engine": "HTTP"}

        a1 = audit_engine.audit_page(p1, keyword="search engine")
        a2 = audit_engine.audit_page(p2, keyword="search engine")

        cmp_table = [
            {"Metric": "Overall SEO Score", "Your Post": f"{a1['overall_score']}/100", "Competitor": f"{a2['overall_score']}/100", "Winner": "You" if a1['overall_score'] >= a2['overall_score'] else "Competitor"},
            {"Metric": "Word Count", "Your Post": f"{a1['word_count']:,}", "Competitor": f"{a2['word_count']:,}", "Winner": "You" if a1['word_count'] >= a2['word_count'] else "Competitor"},
            {"Metric": "H2 Sections", "Your Post": a1['h2_count'], "Competitor": a2['h2_count'], "Winner": "You" if a1['h2_count'] >= a2['h2_count'] else "Competitor"},
        ]
        df = pd.DataFrame(cmp_table)
        self.assertEqual(len(df), 3)
        self.assertEqual(list(df.columns), ["Metric", "Your Post", "Competitor", "Winner"])

    def test_mode4_manual_draft_audit_and_highlight(self):
        draft_text = (
            "# Complete SEO Strategy\n\n"
            "In the modern era, seo is critical. Due to the fact that algorithms evolve, "
            "organizations must utilize structured content. The report was written by our team "
            "in order to explain best practices for search engines."
        )
        words = ["Complete", "SEO", "Strategy", "In", "the", "modern", "era"] * 20
        sentences = [
            "In the modern era, seo is critical.",
            "Due to the fact that algorithms evolve, organizations must utilize structured content.",
            "The report was written by our team in order to explain best practices for search engines."
        ]
        mock_data = {
            "title": "Complete SEO Strategy",
            "url": "Draft Article",
            "clean_text": draft_text,
            "words": words,
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": 2,
            "headings": [{"tag": "h1", "level": 1, "text": "Complete SEO Strategy"}],
            "h1_list": ["Complete SEO Strategy"],
            "h2_list": ["Strategy Overview"],
            "h3_list": [],
            "images": [],
            "images_without_alt": [],
            "citation_links": [],
            "internal_links_count": 0,
            "in_text_sources": 0,
            "schema_types": [],
            "readability": crawler.calculate_readability(draft_text, words, sentences),
            "long_sentences": [],
            "suggested_keyword": "seo",
            "final_url": "Draft Article",
            "status_code": 200,
            "load_time_sec": 0.0,
            "engine": "Manual Draft",
        }
        res = audit_engine.audit_page(mock_data, keyword="seo")
        self.assertGreater(res["overall_score"], 0)
        self.assertIn("scores", res)

        hl_html = audit_engine.generate_highlighted_html(
            draft_text,
            keyword="seo",
            hl_kw=True,
            hl_jg=True,
            hl_tp=True,
            hl_ls=True,
            hl_rd=True,
            hl_pv=True
        )
        self.assertIn("hl-kw", hl_html)
        self.assertIn("hl-redundant", hl_html)

if __name__ == "__main__":
    unittest.main()

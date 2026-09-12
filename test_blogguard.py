import os
import unittest
import crawler
import audit_engine
import api_integrations
import export_helper
import db_history

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

    def test_yoast_seo_evaluation_criteria(self):
        sample_page = {
            "title": "Complete SEO Strategy for High Rankings",
            "meta_description": "Learn the complete SEO strategy to dominate search engine results with our comprehensive 2026 guide.",
            "url": "https://example.com/blog/complete-seo-strategy",
            "clean_text": (
                "In order to rank, a complete seo strategy is essential for every business. "
                "Furthermore, understanding search engines helps you optimize effectively. "
                "However, algorithm updates require continuous monitoring. "
                "Therefore, keyword research and technical audits remain foundational. "
                "As a result, sites following these principles outperform their competition."
            ),
            "words": ["seo", "strategy", "complete"] * 120, # 360 words
            "h1_list": ["Complete SEO Strategy for High Rankings"],
            "h2_list": ["1. Complete SEO Strategy Foundations", "2. Technical Architecture", "3. Analytics"],
            "h3_list": [],
            "images": [{"src": "img.jpg", "alt": "complete seo strategy blueprint", "has_alt": True}],
            "internal_links_count": 2,
            "external_links_count": 1,
            "readability": {"flesch_reading_ease": 68.0},
        }

        yoast = audit_engine.evaluate_yoast_seo(sample_page, keyword="complete seo strategy")
        self.assertIn("seo", yoast)
        self.assertIn("readability", yoast)

        # Verify 14 SEO criteria
        self.assertEqual(yoast["seo"]["total"], 14)
        self.assertIn("score", yoast["seo"])
        self.assertIn("badge", yoast["seo"])

        # Verify 7 Readability criteria
        self.assertEqual(yoast["readability"]["total"], 7)
        self.assertIn("transition_words_pct", yoast["readability"]["metrics"])
        self.assertGreater(yoast["readability"]["metrics"]["transition_words_pct"], 0)

    def test_yoast_detect_seo(self):
        html_with_yoast = "<html><head><!-- This site is optimized with the Yoast SEO plugin v22.0 --><meta name='generator' content='Yoast SEO 22.0' /></head></html>"
        det = api_integrations.detect_yoast_seo("https://example.com", html_content=html_with_yoast)
        self.assertTrue(det["is_yoast"])
        self.assertGreater(len(det["evidence"]), 0)

        html_without_yoast = "<html><head><title>No Plugin</title></head></html>"
        det2 = api_integrations.detect_yoast_seo("", html_content=html_without_yoast)
        self.assertFalse(det2["is_yoast"])

    def test_yoast_api_endpoint_structure(self):
        # Test input validation of Yoast API functions
        empty_res = api_integrations.fetch_yoast_head("")
        self.assertFalse(empty_res["success"])

        posts_err = api_integrations.fetch_wp_yoast_posts("")
        self.assertFalse(posts_err["success"])

        sync_err = api_integrations.update_wp_yoast_meta("", "", "", "")
        self.assertFalse(sync_err["success"])

    def test_db_history_lifecycle(self):
        sample_page = {
            "title": "History Test Blog",
            "url": "https://test.com/history-test",
            "final_url": "https://test.com/history-test",
        }
        sample_audit = {
            "overall_score": 88,
            "keyword": "history test",
            "scores": {"Technical SEO": 90, "Content & Readability": 85},
            "word_count": 500,
            "reading_time_min": 2.5,
            "readability": {"flesch_reading_ease": 70.0, "flesch_kincaid_grade": 7.0},
            "issues": ["Issue 1"],
            "aeo": {"aeo_score": 84},
            "yoast": {"seo_verdict": "Good", "readability_verdict": "Good"},
        }
        snap_id = db_history.save_audit_snapshot(sample_page, sample_audit)
        self.assertIsNotNone(snap_id)
        self.assertGreater(snap_id, 0)

        history = db_history.get_audit_history(limit=10)
        self.assertGreater(len(history), 0)
        latest = history[0]
        self.assertEqual(latest["title"], "History Test Blog")
        self.assertEqual(latest["overall_score"], 88)

        # Check velocity
        velocity = db_history.get_url_velocity("https://test.com/history-test")
        self.assertGreaterEqual(velocity["total_audits"], 1)
        self.assertEqual(velocity["latest_score"], 88)

        # Delete snapshot
        deleted = db_history.delete_snapshot(snap_id)
        self.assertTrue(deleted)

    def test_aeo_readiness_scoring(self):
        sample_data = {
            "clean_text": "Search engine optimization is the art of ranking websites. In 2026, over 55% of search results feature AI overviews according to Gartner.com research.",
            "headings": [
                {"tag": "h2", "level": 2, "text": "What is Search Engine Optimization?"},
                {"tag": "h2", "level": 2, "text": "How Does Technical SEO Work?"}
            ],
            "citation_links": [{"href": "https://gartner.com/report", "text": "Gartner.com"}],
            "schema_types": ["Article", "FAQPage"],
        }
        aeo = audit_engine.evaluate_aeo_readiness(sample_data, keyword="search engine optimization")
        self.assertIn("aeo_score", aeo)
        self.assertGreaterEqual(aeo["aeo_score"], 0)
        self.assertLessEqual(aeo["aeo_score"], 100)
        self.assertIn("pillars", aeo)
        self.assertIn("Direct Answer Delivery", aeo["pillars"])
        self.assertIn("observations", aeo)

    def test_apply_safe_simplifications(self):
        messy_text = (
            "We must utilize this strategy in order to acheive growth. "
            "Furthermore, at this point in time we have alot of learnings. "
            "Leverage these learnings to move the needle."
        )
        patched = audit_engine.apply_safe_simplifications(messy_text)
        self.assertGreater(patched["total_replacements"], 0)
        self.assertIn("utilize", [r["original"] for r in patched["replacements"]])
        self.assertNotIn("acheive", patched["patched_text"])
        self.assertIn("achieve", patched["patched_text"])
        self.assertGreater(patched["words_saved"], 0)

    def test_competitor_semantic_gap(self):
        user_data = {
            "clean_text": "We provide cloud hosting and managed servers for modern web applications.",
            "headings": [{"tag": "h2", "level": 2, "text": "Cloud Hosting"}],
            "words": ["cloud", "hosting", "managed", "servers"] * 25,
            "images": [{"has_alt": True}],
            "citation_links": [],
        }
        competitors = [
            {
                "title": "Best Cloud Hosting & Dedicated Servers 2026",
                "clean_text": "Our cloud hosting platform delivers kubernetes clusters, serverless containers, database replication, and edge networking for enterprise organizations.",
                "headings": ["Kubernetes Clusters", "Edge Networking", "Database Replication"],
                "word_count": 800,
                "image_count": 5,
                "citation_count": 3,
            }
        ]
        gap = audit_engine.analyze_competitor_semantic_gap(user_data, competitors, target_keyword="cloud hosting")
        self.assertIn("target_keyword", gap)
        self.assertIn("top_competitor_terms", gap)
        self.assertIn("missing_terms", gap)
        missing_words = [m["term"] for m in gap["missing_terms"]]
        self.assertTrue("kubernetes" in missing_words or "networking" in missing_words or "replication" in missing_words)

    def test_autonomous_pipeline(self):
        sample_page = {
            "title": "Autonomous Pipeline SEO Test",
            "meta_description": "A complete guide to autonomous SEO testing and remediation.",
            "url": "https://test.com/auto-pipeline",
            "final_url": "https://test.com/auto-pipeline",
            "clean_text": "In order to optimize web pages, technical seo is critical. We must utilize best practices.",
            "words": ["technical", "seo", "optimize", "practices"] * 50,
            "headings": [{"tag": "h1", "level": 1, "text": "Autonomous Pipeline SEO Test"}],
            "h1_list": ["Autonomous Pipeline SEO Test"],
            "h2_list": ["SEO Practices"],
            "h3_list": [],
            "images": [],
            "images_without_alt": [],
            "citation_links": [],
            "internal_links_count": 1,
            "in_text_sources": 0,
            "schema_types": ["Article"],
            "readability": {"flesch_reading_ease": 65.0, "flesch_kincaid_grade": 7.0, "avg_sentence_length": 15, "complex_words": 10},
            "long_sentences": [],
            "suggested_keyword": "technical seo",
            "status_code": 200,
            "load_time_sec": 0.2,
            "engine": "Fast HTTP",
        }
        auto_res = audit_engine.run_autonomous_pipeline(sample_page, keyword="technical seo")
        self.assertIn("audit", auto_res)
        self.assertIn("patch", auto_res)
        self.assertIn("yoast", auto_res)
        self.assertIn("aeo", auto_res)
        self.assertGreater(auto_res["audit"]["overall_score"], 0)

    def test_cms_platform_detection(self):
        wp_html = "<html><head><meta name='generator' content='WordPress 6.4.2' /><link rel='https://api.w.org/' href='https://example.com/wp-json/' /></head></html>"
        cms = api_integrations.detect_cms_platform("https://example.com", html_content=wp_html)
        self.assertEqual(cms["platform"], "WordPress")
        self.assertGreaterEqual(cms["confidence"], 80)

        ghost_html = "<html><head><meta name='generator' content='Ghost 5.80' /></head></html>"
        cms_ghost = api_integrations.detect_cms_platform("https://example.com", html_content=ghost_html)
        self.assertEqual(cms_ghost["platform"], "Ghost")

    def test_sitemap_and_link_health(self):
        # Invalid / mock sitemap URL
        res = crawler.discover_and_parse_sitemap("invalid-url-1234567")
        self.assertFalse(res["success"])
        self.assertIn("error", res)

        # Mock links audit
        test_links = [
            {"href": "https://example.com", "text": "Example Domain", "is_internal": False},
            {"href": "http://insecure.example.com", "text": "Insecure Link", "is_internal": False},
        ]
        lh = crawler.audit_links_health(test_links, base_url="https://example.com", max_check=2)
        self.assertEqual(lh["total_checked"], 2)
        self.assertGreaterEqual(lh["mixed_content_count"], 1)

    def test_multi_llm_copilot_validation(self):
        # Missing key returns clean error, never unhandled exception
        res_ds = api_integrations.query_ai_copilot("test prompt", provider="deepseek", api_key="")
        self.assertIn("error", res_ds)

        res_gem = api_integrations.query_ai_copilot("test prompt", provider="gemini", api_key="")
        self.assertIn("error", res_gem)

        res_oa = api_integrations.query_ai_copilot("test prompt", provider="openai", api_key="")
        self.assertIn("error", res_oa)

if __name__ == "__main__":
    unittest.main()


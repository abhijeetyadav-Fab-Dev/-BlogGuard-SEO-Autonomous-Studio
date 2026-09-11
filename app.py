import os
import re
import json
import pandas as pd
import streamlit as st

import importlib
import crawler
import audit_engine
import api_integrations
import export_helper

# Force-reload local modules on every run so any long-running Streamlit process gets latest code
for _mod in [crawler, audit_engine, api_integrations, export_helper]:
    try:
        importlib.reload(_mod)
    except Exception:
        pass

# Page configuration
st.set_page_config(
    page_title="BlogGuard SEO - Autonomous Intelligence Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom styling for high-end feel
st.markdown("""
<style>
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 16px;
        font-weight: 700;
        font-size: 13px;
    }
    .badge-elite { background-color: #dcfce7; color: #15803d; }
    .badge-strong { background-color: #dbeafe; color: #1d4ed8; }
    .badge-moderate { background-color: #fef9c3; color: #a16207; }
    .badge-critical { background-color: #fee2e2; color: #b91c1c; }
    .serp-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 10px;
    }
    .blog-viewer-canvas {
        background: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        padding: 28px;
        font-size: 15.5px;
        line-height: 1.85;
        color: #1e293b;
        max-height: 680px;
        overflow-y: auto;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .hl-kw {
        background-color: #bbf7d0;
        color: #14532d;
        font-weight: 700;
        padding: 1px 6px;
        border-radius: 4px;
        border: 1px solid #86efac;
    }
    .hl-jargon {
        background-color: #f3e8ff;
        color: #6b21a8;
        font-weight: 600;
        padding: 1px 6px;
        border-radius: 4px;
        border-bottom: 2px solid #a855f7;
    }
    .hl-typo {
        background-color: #fee2e2;
        color: #991b1b;
        font-weight: 600;
        padding: 1px 6px;
        border-radius: 4px;
        text-decoration: underline wavy #ef4444;
    }
    .hl-long-sent {
        background-color: #fef9c3;
        border-left: 3.5px solid #ca8a04;
        padding: 2px 6px;
        border-radius: 3px;
        display: inline;
    }
    .fix-tag {
        font-size: 11px;
        font-weight: 700;
        color: #b91c1c;
        background: #ffffff;
        padding: 1px 5px;
        border-radius: 3px;
        border: 1px solid #fca5a5;
        margin-left: 3px;
    }
    .sim-tag {
        font-size: 11px;
        font-weight: 700;
        color: #7e22ce;
        background: #ffffff;
        padding: 1px 5px;
        border-radius: 3px;
        border: 1px solid #d8b4fe;
        margin-left: 3px;
    }
    .hl-redundant {
        background-color: #ffedd5;
        color: #9a3412;
        font-weight: 600;
        padding: 1px 6px;
        border-radius: 4px;
        border-bottom: 2px solid #f97316;
    }
    .hl-passive {
        background-color: #e0f2fe;
        border-left: 3.5px solid #0284c7;
        padding: 2px 6px;
        border-radius: 3px;
        display: inline;
    }
    .red-tag {
        font-size: 11px;
        font-weight: 700;
        color: #c2410c;
        background: #ffffff;
        padding: 1px 5px;
        border-radius: 3px;
        border: 1px solid #fdba74;
        margin-left: 3px;
    }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if "results" not in st.session_state:
    st.session_state.results = []
if "serp_cache" not in st.session_state:
    st.session_state.serp_cache = {}
if "pagespeed_cache" not in st.session_state:
    st.session_state.pagespeed_cache = {}
if "ai_audit_cache" not in st.session_state:
    st.session_state.ai_audit_cache = {}
if "deepseek_key" not in st.session_state:
    st.session_state.deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "")

# -----------------------------------------------------------------------------
# SIDEBAR: Control Tower & API Integrations
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluent/96/shield.png", width=64)
    st.title("BlogGuard SEO")
    st.caption("Autonomous Blog Architecture, Content & SERP Engine")
    st.divider()

    st.subheader("🎯 Audit Mode")
    audit_mode = st.radio(
        "Choose Mode:",
        [
            "🌐 Autonomous Live URL Audit",
            "⚔️ Competitor Battle Mode",
            "📑 Batch / Multi-URL Audit",
            "✍️ Manual Content Draft",
        ],
        label_visibility="collapsed"
    )

    st.divider()
    st.subheader("🔌 Connected Rivers (APIs)")

    # 1. SerpApi
    default_serp_key = os.environ.get("SERPAPI_KEY", "")
    has_serp = bool(default_serp_key)
    serp_status = "🟢 Active (System ENV)" if has_serp else "⚪ Needs Key"
    st.markdown(f"**Google SerpApi**: `{serp_status}`")
    serpapi_key = st.text_input(
        "SerpApi Key",
        value=default_serp_key,
        type="password",
        help="Provides live Google Top 10 rankings, competitor analysis, and People Also Ask questions."
    )
    enable_serp = st.checkbox("Run Live Google SERP Analysis", value=bool(serpapi_key))

    # 2. DeepSeek AI
    st.markdown("**DeepSeek AI Copilot**")
    deepseek_key = st.text_input(
        "DeepSeek API Key",
        value=st.session_state.deepseek_key,
        type="password",
        help="Powers the autonomous editorial critique, title/meta generator, and FAQ schema."
    )
    if deepseek_key:
        st.session_state.deepseek_key = deepseek_key

    deepseek_model = st.selectbox(
        "AI Model",
        ["deepseek-chat", "deepseek-reasoner"],
        help="deepseek-chat for speed, deepseek-reasoner (R1) for rigorous strategic reasoning."
    )

    # 3. Google PageSpeed
    st.markdown("**Google PageSpeed Insights**")
    enable_pagespeed = st.checkbox("Audit Core Web Vitals (Mobile)", value=False)
    pagespeed_key = st.text_input("Google PageSpeed Key (Optional)", type="password", help="Leave blank for public rate-limited quota.")

    # 4. Engine selector
    st.divider()
    browser_exe = crawler.get_browser_executable()
    default_engine = "Headless Browser (Chrome/Edge)" if browser_exe else "Fast HTTP"
    engine_choice = st.selectbox(
        "Crawl Engine",
        ["Auto / Headless Browser (JS Rendered)", "Fast High-Fidelity HTTP"],
        help="Headless browser executes client-side JavaScript (React, Next.js, hydration)."
    )
    use_browser = "Headless Browser" in engine_choice

st.title("🛡️ BlogGuard SEO Autonomous Studio")
st.caption("End-to-end autonomous blog evaluation powered by Headless Browser, Google SerpApi & DeepSeek AI.")

# -----------------------------------------------------------------------------
# MODE 1: Autonomous Live URL Audit
# -----------------------------------------------------------------------------
if audit_mode == "🌐 Autonomous Live URL Audit":
    st.subheader("🌐 Live URL Autonomous Inspection")
    col1, col2 = st.columns([3, 2])
    with col1:
        target_url = st.text_input("Blog Post URL", placeholder="https://example.com/blog/best-seo-tips")
    with col2:
        target_keyword = st.text_input("Primary Keyword (Leave empty for AI Auto-Discovery)", placeholder="e.g. best seo tips")

    run_btn = st.button("🚀 Run Autonomous Audit", type="primary", use_container_width=True)

    if run_btn:
        if not target_url.strip():
            st.error("Please provide a valid blog URL to audit.")
        else:
            with st.status("Running Autonomous Multi-Engine Audit...", expanded=True) as status:
                st.write("🌐 Launching browser engine and extracting rendered DOM...")
                fetch_res = crawler.fetch_html(target_url, use_browser=use_browser)
                
                if fetch_res["status_code"] >= 400 or not fetch_res["html"]:
                    st.error(f"Failed to fetch {target_url} (HTTP {fetch_res['status_code']})")
                else:
                    st.write(f"✅ Loaded page in {fetch_res['load_time_sec']}s using {fetch_res['engine']}")
                    st.write("🔍 Parsing DOM, Headings, Schema JSON-LD, Images, Links & Readability...")
                    page_data = crawler.parse_page_data(fetch_res)

                    keyword_to_use = target_keyword.strip() or page_data.get("suggested_keyword")
                    st.write(f"🎯 Evaluating 7 SEO Pillars for keyword: **{keyword_to_use}**...")
                    audit_res = audit_engine.audit_page(page_data, keyword=keyword_to_use)

                    # SerpApi if enabled
                    serp_res = None
                    if enable_serp and serpapi_key and keyword_to_use:
                        st.write(f"📊 Connecting to Google SerpApi for '{keyword_to_use}'...")
                        serp_res = api_integrations.fetch_serp_intelligence(keyword_to_use, api_key=serpapi_key)
                        if serp_res and serp_res.get("success"):
                            st.session_state.serp_cache[keyword_to_use] = serp_res

                    # PageSpeed if enabled
                    ps_res = None
                    if enable_pagespeed:
                        st.write("⚡ Fetching Google Core Web Vitals...")
                        ps_res = api_integrations.fetch_pagespeed_insights(target_url, api_key=pagespeed_key)
                        if ps_res and ps_res.get("success"):
                            st.session_state.pagespeed_cache[target_url] = ps_res

                    full_record = {
                        "type": "Single URL",
                        "url": target_url,
                        "title": page_data["title"],
                        "keyword": keyword_to_use,
                        "page_data": page_data,
                        "audit": audit_res,
                        "serp": serp_res,
                        "pagespeed": ps_res,
                    }
                    st.session_state.results.insert(0, full_record)
                    status.update(label=f"Audit complete! Score: {audit_res['overall_score']}/100 ({audit_res['status']})", state="complete")
                    st.rerun()

# -----------------------------------------------------------------------------
# MODE 2: Competitor Battle Mode
# -----------------------------------------------------------------------------
elif audit_mode == "⚔️ Competitor Battle Mode":
    st.subheader("⚔️ Head-to-Head Competitor Gap Matrix")
    st.write("Compare your blog post directly against a ranking competitor to spot exact topical and structural advantages.")
    col_a, col_b = st.columns(2)
    with col_a:
        your_url = st.text_input("Your Blog URL", placeholder="https://yoursite.com/blog/my-guide")
    with col_b:
        comp_url = st.text_input("Competitor Blog URL", placeholder="https://competitor.com/blog/their-guide")
    battle_keyword = st.text_input("Shared Target Keyword", placeholder="e.g. cloud security best practices")

    battle_btn = st.button("⚔️ Launch Head-to-Head Battle", type="primary", use_container_width=True)

    if battle_btn:
        if not your_url or not comp_url:
            st.error("Please enter both URLs to run the comparison.")
        else:
            with st.status("Auditing both articles in parallel...", expanded=True) as status:
                st.write("Fetching Your Post...")
                fetch_1 = crawler.fetch_html(your_url, use_browser=use_browser)
                data_1 = crawler.parse_page_data(fetch_1)
                audit_1 = audit_engine.audit_page(data_1, keyword=battle_keyword)

                st.write("Fetching Competitor Post...")
                fetch_2 = crawler.fetch_html(comp_url, use_browser=use_browser)
                data_2 = crawler.parse_page_data(fetch_2)
                audit_2 = audit_engine.audit_page(data_2, keyword=battle_keyword)

                st.session_state.battle_data = {
                    "your": {"data": data_1, "audit": audit_1},
                    "comp": {"data": data_2, "audit": audit_2},
                    "keyword": battle_keyword,
                }
                status.update(label="Battle comparison generated!", state="complete")

    if "battle_data" in st.session_state:
        b = st.session_state.battle_data
        y_a = b["your"]["audit"]
        c_a = b["comp"]["audit"]
        y_d = b["your"]["data"]
        c_d = b["comp"]["data"]

        st.divider()
        mcol1, mcol2, mcol3 = st.columns([2, 1, 2])
        with mcol1:
            st.metric("Your Score", f"{y_a['overall_score']}/100", f"{y_a['overall_score'] - c_a['overall_score']}")
            st.caption(f"**{y_d['title']}**")
        with mcol2:
            st.markdown("<h2 style='text-align: center; margin-top: 15px;'>VS</h2>", unsafe_allow_html=True)
        with mcol3:
            st.metric("Competitor Score", f"{c_a['overall_score']}/100")
            st.caption(f"**{c_d['title']}**")

        st.subheader("Comparison Matrix")
        cmp_table = [
            {"Metric": "Overall SEO Score", "Your Post": f"{y_a['overall_score']}/100", "Competitor": f"{c_a['overall_score']}/100", "Winner": "You" if y_a['overall_score'] >= c_a['overall_score'] else "Competitor"},
            {"Metric": "Word Count", "Your Post": f"{y_a['word_count']:,}", "Competitor": f"{c_a['word_count']:,}", "Winner": "You" if y_a['word_count'] >= c_a['word_count'] else "Competitor"},
            {"Metric": "H2 Sections", "Your Post": y_a['h2_count'], "Competitor": c_a['h2_count'], "Winner": "You" if y_a['h2_count'] >= c_a['h2_count'] else "Competitor"},
            {"Metric": "H3 Sub-sections", "Your Post": y_a['h3_count'], "Competitor": c_a['h3_count'], "Winner": "You" if y_a['h3_count'] >= c_a['h3_count'] else "Competitor"},
            {"Metric": "Reading Ease", "Your Post": y_a['readability']['flesch_reading_ease'], "Competitor": c_a['readability']['flesch_reading_ease'], "Winner": "You" if y_a['readability']['flesch_reading_ease'] >= c_a['readability']['flesch_reading_ease'] else "Competitor"},
            {"Metric": "Total Images", "Your Post": y_a['image_count'], "Competitor": c_a['image_count'], "Winner": "You" if y_a['image_count'] >= c_a['image_count'] else "Competitor"},
            {"Metric": "Missing Alt Text", "Your Post": y_a['missing_alt_count'], "Competitor": c_a['missing_alt_count'], "Winner": "You" if y_a['missing_alt_count'] <= c_a['missing_alt_count'] else "Competitor"},
            {"Metric": "Outbound Citations", "Your Post": y_a['citations_count'], "Competitor": c_a['citations_count'], "Winner": "You" if y_a['citations_count'] >= c_a['citations_count'] else "Competitor"},
            {"Metric": "Internal Links", "Your Post": y_a['internal_links_count'], "Competitor": c_a['internal_links_count'], "Winner": "You" if y_a['internal_links_count'] >= c_a['internal_links_count'] else "Competitor"},
        ]
        st.dataframe(pd.DataFrame(cmp_table), use_container_width=True, hide_index=True)

        st.subheader("Headings Gap Analysis")
        hcol1, hcol2 = st.columns(2)
        with hcol1:
            st.markdown("**Your H2 Headings:**")
            for h in y_d["h2_list"]:
                st.write(f"- {h}")
        with hcol2:
            st.markdown("**Competitor H2 Headings (Topics you might have missed):**")
            for h in c_d["h2_list"]:
                st.write(f"- {h}")

# -----------------------------------------------------------------------------
# MODE 3: Batch / Multi-URL Audit
# -----------------------------------------------------------------------------
elif audit_mode == "📑 Batch / Multi-URL Audit":
    st.subheader("📑 Batch URL Crawler & Site-Wide Audit")
    urls_input = st.text_area(
        "Enter URLs (one per line):",
        placeholder="https://example.com/blog-1\nhttps://example.com/blog-2\nhttps://example.com/blog-3",
        height=150
    )
    batch_btn = st.button("🚀 Run Batch Audit", type="primary", use_container_width=True)

    if batch_btn:
        urls = [u.strip() for u in urls_input.splitlines() if u.strip()]
        if not urls:
            st.error("Please enter at least one URL.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            for idx, u in enumerate(urls):
                status_text.text(f"Auditing ({idx+1}/{len(urls)}): {u}")
                fetch_res = crawler.fetch_html(u, use_browser=use_browser)
                if fetch_res["status_code"] < 400 and fetch_res["html"]:
                    p_data = crawler.parse_page_data(fetch_res)
                    a_res = audit_engine.audit_page(p_data)
                    st.session_state.results.insert(0, {
                        "type": "Batch",
                        "url": u,
                        "title": p_data["title"],
                        "keyword": a_res["keyword"],
                        "page_data": p_data,
                        "audit": a_res,
                        "serp": None,
                        "pagespeed": None,
                    })
                progress_bar.progress((idx + 1) / len(urls))
            status_text.success("Batch audit completed!")
            st.rerun()

# -----------------------------------------------------------------------------
# MODE 4: Manual Content Draft
# -----------------------------------------------------------------------------
elif audit_mode == "✍️ Manual Content Draft":
    st.subheader("✍️ Draft & Pre-Publish Manual Audit")
    d_col1, d_col2 = st.columns([3, 2])
    with d_col1:
        draft_title = st.text_input("Draft Title", placeholder="The Complete Guide to Technical SEO in 2026")
        draft_text = st.text_area("Blog Content (Paste raw text or Markdown)", height=300, placeholder="Paste your article draft here...")
    with d_col2:
        draft_kw = st.text_input("Focus Keyword", placeholder="technical seo guide")
        draft_author = st.text_input("Writer / Author", placeholder="Jane Doe")
        draft_btn = st.button("Audit Draft", type="primary", use_container_width=True)

    if draft_btn:
        if not draft_text.strip():
            st.error("Please provide article text to audit.")
        else:
            # Build mock page_data from draft
            words = re.findall(r"\b[\w'-]+\b", draft_text)
            sentences = [s.strip() for s in re.split(r"[.!?]+", draft_text) if s.strip()]
            h1_matches = re.findall(r"(?im)^#\s+(.+)$|<h1\b[^>]*>(.+?)</h1>", draft_text)
            h1_list = [m[0] or m[1] for m in h1_matches]
            h2_matches = re.findall(r"(?im)^##\s+(.+)$|<h2\b[^>]*>(.+?)</h2>", draft_text)
            h2_list = [m[0] or m[1] for m in h2_matches]

            mock_fetch = {
                "url": "draft://local",
                "final_url": "draft://local",
                "status_code": 200,
                "load_time_sec": 0.0,
                "engine": "Manual Draft",
                "html": draft_text,
            }
            mock_data = {
                "url": "Draft Article",
                "final_url": "Draft Article",
                "status_code": 200,
                "load_time_sec": 0.0,
                "engine": "Manual Draft",
                "title": draft_title or (h1_list[0] if h1_list else "Untitled Draft"),
                "meta_description": "",
                "canonical_url": "",
                "canonical_match": False,
                "robots": "",
                "author": draft_author or "Author",
                "published_date": "Draft",
                "headings": [{"tag": "h1", "level": 1, "text": h} for h in h1_list] + [{"tag": "h2", "level": 2, "text": h} for h in h2_list],
                "h1_list": h1_list,
                "h2_list": h2_list,
                "h3_list": [],
                "hierarchy_valid": True,
                "clean_text": draft_text,
                "words": words,
                "word_count": len(words),
                "sentence_count": len(sentences),
                "paragraph_count": len(re.split(r"\n\s*\n", draft_text)),
                "reading_time_min": round(len(words) / 200, 1),
                "images": [],
                "images_without_alt": [],
                "links": [],
                "internal_links_count": 0,
                "external_links_count": 0,
                "nofollow_links_count": 0,
                "citation_links": [],
                "in_text_sources": len(re.findall(r"(?i)according to|study shows|source:", draft_text)),
                "opengraph": {},
                "twitter_cards": {},
                "schema_types": [],
                "readability": crawler.calculate_readability(draft_text, words, sentences),
                "long_sentences": [{"sentence": s, "word_count": len(re.findall(r"\b\w+\b", s))} for s in sentences if len(re.findall(r"\b\w+\b", s)) > 28],
                "suggested_keyword": draft_kw,
            }
            a_res = audit_engine.audit_page(mock_data, keyword=draft_kw, writer=draft_author)
            st.session_state.results.insert(0, {
                "type": "Manual Draft",
                "url": "Draft Article",
                "title": mock_data["title"],
                "keyword": draft_kw,
                "page_data": mock_data,
                "audit": a_res,
                "serp": None,
                "pagespeed": None,
            })
            st.rerun()


# =============================================================================
# MAIN RESULTS & DASHBOARD
# =============================================================================
st.divider()

if not st.session_state.results:
    st.info("👋 Welcome to BlogGuard SEO! Select an audit mode above, enter a URL or keyword, and click Run to begin.")
else:
    st.subheader("📋 Audit Records & Session Dashboard")

    summary_rows = []
    for idx, r in enumerate(st.session_state.results):
        summary_rows.append({
            "Index": idx + 1,
            "Title": r["title"][:50] + ("..." if len(r["title"]) > 50 else ""),
            "Keyword": r["keyword"] or "Auto-detected",
            "Words": r["audit"]["word_count"],
            "Score": f"{r['audit']['overall_score']}/100",
            "Status": r["audit"]["status"],
            "URL": r["url"][:40] + "...",
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    selected_idx = st.selectbox(
        "Inspect Audit Report:",
        range(len(st.session_state.results)),
        format_func=lambda i: f"#{i+1}: {st.session_state.results[i]['title']} (Score: {st.session_state.results[i]['audit']['overall_score']})"
    )

    current = st.session_state.results[selected_idx]
    c_audit = current["audit"]
    c_data = current["page_data"]

    st.markdown(f"## 🛡️ {c_data['title']}")
    st.caption(f"**URL:** {c_data['url']} | **Focus Keyword:** `{c_audit['keyword']}` | **Engine:** `{c_data.get('engine', 'HTTP')}`")

    # -------------------------------------------------------------------------
    # Hero Metric Strip
    # -------------------------------------------------------------------------
    mcol1, mcol2, mcol3, mcol4, mcol5, mcol6 = st.columns(6)
    with mcol1:
        st.metric("Overall Score", f"{c_audit['overall_score']}/100")
    with mcol2:
        st.metric("Word Count", f"{c_audit['word_count']:,}")
    with mcol3:
        st.metric("Read Time", f"{c_audit['reading_time_min']} min")
    with mcol4:
        st.metric("Flesch Ease", f"{c_audit['readability']['flesch_reading_ease']}/100")
    with mcol5:
        st.metric("H1 / H2 Headings", f"{c_audit['h1_count']} / {c_audit['h2_count']}")
    with mcol6:
        st.metric("Outbound Citations", c_audit['citations_count'])

    # -------------------------------------------------------------------------
    # TABS SECTION: The 9 Power Centers
    # -------------------------------------------------------------------------
    tabs = st.tabs([
        "📊 360° Scorecard",
        "🚨 Actionable Issues",
        "🔍 Grammar, Clarity & Alignment",
        "🎨 In-Text Issue Highlighter",
        "🔍 Google SERP (SerpApi)",
        "🧠 DeepSeek AI Copilot",
        "⚡ Core Web Vitals",
        "📱 SERP & Social Preview",
        "📑 Content Hierarchy",
        "🖼️ Media & Links",
        "📝 Writer Checklist & Export"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: 360° Scorecard
    # -------------------------------------------------------------------------
    with tabs[0]:
        st.subheader("7-Pillar Performance Matrix")
        scores_dict = c_audit["scores"]
        sdf = pd.DataFrame({
            "Pillar": list(scores_dict.keys()),
            "Score": list(scores_dict.values()),
        })
        st.bar_chart(sdf.set_index("Pillar"), use_container_width=True)

        scols = st.columns(len(scores_dict))
        for idx, (pillar, val) in enumerate(scores_dict.items()):
            with scols[idx]:
                color = "green" if val >= 80 else ("orange" if val >= 60 else "red")
                st.markdown(f"**{pillar}**")
                st.markdown(f"<h3 style='color: {color}; margin-top: -8px;'>{val}/100</h3>", unsafe_allow_html=True)

        st.divider()
        st.markdown(f"### Overall Verdict: **:{c_audit['status_color']}[{c_audit['status']}]**")
        if c_audit["quick_wins"]:
            st.markdown("#### ✨ Detected Strengths:")
            for qw in c_audit["quick_wins"]:
                st.success(qw)

    # -------------------------------------------------------------------------
    # TAB 2: Actionable Issues
    # -------------------------------------------------------------------------
    with tabs[1]:
        st.subheader(f"Identified Optimization Opportunities ({len(c_audit['issues'])})")

        sev_filter = st.multiselect(
            "Filter by Severity:",
            ["critical", "warning", "info"],
            default=["critical", "warning", "info"]
        )

        filtered_issues = [i for i in c_audit["issues"] if i["severity"] in sev_filter]
        if not filtered_issues:
            st.success("No issues match the selected filter!")
        else:
            for iss in filtered_issues:
                sev = iss["severity"]
                if sev == "critical":
                    with st.expander(f"🔴 CRITICAL: {iss['title']} ({iss['pillar']})", expanded=True):
                        st.markdown(f"**Detail:** {iss['detail']}")
                        st.markdown(f"💡 **Action Required:** `{iss['fix']}`")
                elif sev == "warning":
                    with st.expander(f"🟡 WARNING: {iss['title']} ({iss['pillar']})"):
                        st.markdown(f"**Detail:** {iss['detail']}")
                        st.markdown(f"💡 **Recommended Fix:** `{iss['fix']}`")
                else:
                    with st.expander(f"🔵 INFO: {iss['title']} ({iss['pillar']})"):
                        st.markdown(f"**Detail:** {iss['detail']}")
                        st.markdown(f"💡 **Suggestion:** `{iss['fix']}`")

        # Spelling corrections
        if c_audit["corrections"]:
            st.divider()
            st.subheader("Spelling & Typography Cleanups")
            st.dataframe(pd.DataFrame(c_audit["corrections"]), use_container_width=True, hide_index=True)

        # Jargon & Complex Vocabulary Simplifier
        if c_audit.get("detected_jargon"):
            st.divider()
            st.subheader("📖 Complex Jargon & Vocabulary Simplifier")
            st.caption("Replacing these multi-syllable corporate/academic terms with plain conversational words will immediately boost your Flesch Reading Ease score:")
            st.dataframe(pd.DataFrame(c_audit["detected_jargon"]), use_container_width=True, hide_index=True)
            st.info("💡 **Tip:** Switch to the **'🎨 In-Text Issue Highlighter'** tab above to see these exact jargon words, run-on sentences, and typos highlighted live inside your article!")

    # -------------------------------------------------------------------------
    # TAB 3: Grammar, Clarity & Content-Information Alignment
    # -------------------------------------------------------------------------
    with tabs[2]:
        st.subheader("🔍 Grammar, Clarity & Content-Information Alignment")
        st.caption("Comprehensive analysis of linguistic precision, passive voice, wordy redundancies, reading clarity, and title-to-content promise delivery.")

        align = c_audit.get("content_alignment", {})
        passive = c_audit.get("passive_voice", {})
        red_list = c_audit.get("redundancies", [])
        clarity_score = c_audit.get("clarity_score", 0)

        # 4 Core Pillar Metrics
        gcol1, gcol2, gcol3, gcol4 = st.columns(4)
        with gcol1:
            align_score = align.get("score", 0)
            align_delta = "High Alignment" if align_score >= 80 else ("Moderate Drift" if align_score >= 60 else "Major Mismatch")
            st.metric("Headline Alignment", f"{align_score}/100", align_delta)
        with gcol2:
            clarity_delta = "Crisp & Clear" if clarity_score >= 80 else ("Acceptable" if clarity_score >= 60 else "Dense/Complex")
            st.metric("Clarity & Flow Index", f"{clarity_score}/100", clarity_delta)
        with gcol3:
            pv_pct = passive.get("percentage", 0.0)
            pv_delta = "Active Voice" if pv_pct <= 10 else ("Acceptable" if pv_pct <= 20 else "Too Passive")
            st.metric("Passive Voice", f"{pv_pct}%", f"{passive.get('count', 0)} sentences ({pv_delta})", delta_color="inverse" if pv_pct > 15 else "normal")
        with gcol4:
            total_red_count = sum(r.get("count", 0) for r in red_list)
            st.metric("Wordy Redundancies", f"{len(red_list)} phrases", f"{total_red_count} total occurrences")

        st.divider()

        # Section 1: Headline to Content Alignment & Promise Delivery
        st.markdown("### 🎯 Headline-to-Content Promise Fulfillment")
        st.caption("Evaluates whether the article actually delivers on what the title promises, verifying H1/H2 topic alignment and listicle/how-to structure.")

        obs = align.get("observations", [])
        if obs:
            for ob in obs:
                if ob.startswith("✅"):
                    st.success(ob)
                elif ob.startswith("⚠️"):
                    st.warning(ob)
                elif ob.startswith("❌"):
                    st.error(ob)
                else:
                    st.info(ob)
        else:
            st.info("Content structure matches title expectations.")

        st.divider()

        # Section 2: Passive Voice Analysis & Improvement
        st.markdown("### 🗣️ Passive Voice vs Active Voice")
        st.caption("Active voice makes your writing direct, authoritative, and engaging. Google and readers prefer clear subject-action constructions.")

        if passive.get("count", 0) == 0:
            st.success("🎉 Excellent! Zero passive voice constructions detected. Your writing is fully active and punchy.")
        else:
            if pv_pct > 15:
                st.warning(f"⚠️ {pv_pct}% of your sentences use passive voice (industry target: under 10%).")
            else:
                st.info(f"Passive voice is at {pv_pct}% ({passive.get('count', 0)} sentences), which is within acceptable limits.")

            with st.expander(f"Inspect Detected Passive Voice Sentences ({passive.get('count', 0)} found)", expanded=(pv_pct > 15)):
                for psent in passive.get("sentences", []):
                    st.markdown(f"- 🔵 *\"{psent}\"*")
                st.caption("💡 Switch to the **'🎨 In-Text Issue Highlighter'** tab to see these sentences highlighted in blue directly in the article body.")

        st.divider()

        # Section 3: Wordiness & Redundancy Trimmer
        st.markdown("### ✂️ Wordiness & Redundancy Trimmer")
        st.caption("Eliminate flab from your copy. Replacing filler words with concise alternatives strengthens your message and boosts readability.")

        if not red_list:
            st.success("🎉 Clean copy! No common redundant or wordy filler phrases detected.")
        else:
            table_rows = [
                {
                    "Redundant Phrase": r.get("phrase") or r.get("Redundant Phrase", ""),
                    "Occurrences": r.get("count") or r.get("Occurrences", 1),
                    "Concise Alternative": r.get("replacement") or r.get("Simpler Alternative", "")
                }
                for r in red_list
            ]
            st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
            st.caption("💡 Switch to the **'🎨 In-Text Issue Highlighter'** tab to see these phrases highlighted in orange with their one-click replacements.")

        st.divider()

        # Section 4: Deep AI Forensic Verification (Fact-checking, Logic & Contradictions)
        st.markdown("### 🛡️ AI Deep Forensic & Factual Alignment Scanner")
        st.caption("Harness DeepSeek AI to perform deep factual verification, uncover internal contradictions, audit grammar/syntax, and detect title drift.")

        ds_key = st.session_state.deepseek_key
        cache_key = f"{c_data['title']}-{deepseek_model}"

        if not ds_key:
            st.warning("Enter your DeepSeek API Key in the left sidebar to run deep AI fact and contradiction audits.")
        else:
            if st.button("🛡️ Run Deep Forensic & Factual Verification", key=f"btn_verify_{selected_idx}", use_container_width=True):
                with st.spinner("DeepSeek AI is forensically analyzing article facts, logic, grammar, and headline alignment..."):
                    v_res = api_integrations.verify_content_and_facts(c_data, api_key=ds_key, model=deepseek_model)
                    if v_res.get("success"):
                        st.session_state.ai_audit_cache[f"{cache_key}-verification"] = v_res
                    else:
                        st.error(v_res.get("error", "Verification failed"))

            if f"{cache_key}-verification" in st.session_state.ai_audit_cache:
                v_data = st.session_state.ai_audit_cache[f"{cache_key}-verification"]
                if v_data.get("reasoning"):
                    with st.expander("💭 View DeepSeek Reasoning Process (CoT)"):
                        st.write(v_data["reasoning"])
                st.markdown(v_data["content"])

    # -------------------------------------------------------------------------
    # TAB 4: In-Text Issue Highlighter
    # -------------------------------------------------------------------------
    with tabs[3]:
        st.subheader("🎨 Live In-Text Visual Issue Highlighter")
        st.caption("Inspect your full article with color-coded in-line highlights for run-on sentences, complex jargon, typos, redundancies, passive voice, and keyword density.")

        # Interactive Controls
        ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4, ctrl_col5, ctrl_col6 = st.columns(6)
        with ctrl_col1:
            hl_ls = st.checkbox("🟡 Run-On Sentences", value=True, key=f"hl_ls_{selected_idx}")
        with ctrl_col2:
            hl_jg = st.checkbox("🟣 Complex Jargon", value=True, key=f"hl_jg_{selected_idx}")
        with ctrl_col3:
            hl_tp = st.checkbox("🔴 Spelling & Typos", value=True, key=f"hl_tp_{selected_idx}")
        with ctrl_col4:
            hl_rd = st.checkbox("🟠 Redundancies", value=True, key=f"hl_rd_{selected_idx}")
        with ctrl_col5:
            hl_pv = st.checkbox("🔵 Passive Voice", value=True, key=f"hl_pv_{selected_idx}")
        with ctrl_col6:
            hl_kw = st.checkbox("🟢 Focus Keyword", value=True, key=f"hl_kw_{selected_idx}")

        # Metrics Strip
        long_count = len(c_data.get("long_sentences", []))
        jargon_count = sum(j["Occurrences"] for j in c_audit.get("detected_jargon", []))
        typo_count = len(c_audit.get("corrections", []))
        redundant_count = sum(r["count"] for r in c_audit.get("redundancies", []))
        passive_count = c_audit.get("passive_voice", {}).get("count", 0)
        kw_count = len(re.findall(rf"\b{re.escape(c_audit['keyword'])}\b", c_data["clean_text"], re.IGNORECASE)) if c_audit["keyword"] else 0

        st.markdown(
            f"""
            <div style="display: flex; gap: 12px; margin: 12px 0 18px 0; flex-wrap: wrap;">
                <span style="background: #fef08a; color: #854d0e; padding: 4px 12px; border-radius: 6px; font-size: 13px; font-weight: 600; border: 1px solid #fde047;">
                    🟡 {long_count} Run-On Sentence(s)
                </span>
                <span style="background: #f3e8ff; color: #6b21a8; padding: 4px 12px; border-radius: 6px; font-size: 13px; font-weight: 600; border: 1px solid #d8b4fe;">
                    🟣 {jargon_count} Jargon Term(s)
                </span>
                <span style="background: #fee2e2; color: #991b1b; padding: 4px 12px; border-radius: 6px; font-size: 13px; font-weight: 600; border: 1px solid #fca5a5;">
                    🔴 {typo_count} Spelling Correction(s)
                </span>
                <span style="background: #ffedd5; color: #c2410c; padding: 4px 12px; border-radius: 6px; font-size: 13px; font-weight: 600; border: 1px solid #fed7aa;">
                    🟠 {redundant_count} Redundant Phrase(s)
                </span>
                <span style="background: #dbeafe; color: #1e40af; padding: 4px 12px; border-radius: 6px; font-size: 13px; font-weight: 600; border: 1px solid #bfdbfe;">
                    🔵 {passive_count} Passive Sentence(s)
                </span>
                <span style="background: #dcfce7; color: #166534; padding: 4px 12px; border-radius: 6px; font-size: 13px; font-weight: 600; border: 1px solid #86efac;">
                    🟢 {kw_count} Keyword Mention(s)
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Render highlighted article canvas
        highlighted_body = audit_engine.generate_highlighted_html(
            c_data["clean_text"],
            keyword=c_audit["keyword"],
            hl_kw=hl_kw,
            hl_jg=hl_jg,
            hl_tp=hl_tp,
            hl_ls=hl_ls,
            hl_rd=hl_rd,
            hl_pv=hl_pv
        )

        st.markdown(f'<div class="blog-viewer-canvas">{highlighted_body}</div>', unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # TAB 5: Google SERP Intelligence (SerpApi)
    # -------------------------------------------------------------------------
    with tabs[4]:
        st.subheader("🔍 Google SERP Live Intelligence")
        kw = c_audit["keyword"]
        serp = current.get("serp") or st.session_state.serp_cache.get(kw)

        if not serp and serpapi_key and kw:
            if st.button("Fetch Live Google SERP for this Keyword"):
                with st.spinner(f"Pulling Google rankings for '{kw}'..."):
                    serp = api_integrations.fetch_serp_intelligence(kw, api_key=serpapi_key)
                    if serp and serp.get("success"):
                        current["serp"] = serp
                        st.session_state.serp_cache[kw] = serp
                        st.rerun()

        if serp and serp.get("success"):
            st.markdown(f"**Target Query:** `{serp['keyword']}` | **Total Search Results:** `{serp['total_results']}`")

            # People Also Ask
            paa = serp.get("people_also_ask", [])
            if paa:
                st.markdown("### ❓ Google 'People Also Ask' (Rich Snippet Opportunities)")
                st.caption("Add these questions directly into your blog as H2 or H3 sections to win Google Featured Snippets:")
                pcols = st.columns(2)
                for i, p in enumerate(paa[:6]):
                    with pcols[i % 2]:
                        with st.container(border=True):
                            st.markdown(f"**{p['question']}**")
                            st.caption(p.get("snippet", ""))

            # Competitor Rankings
            st.markdown("### 🏆 Top 10 Google Organic Competitors")
            comp_df = pd.DataFrame(serp["competitors"])
            st.dataframe(comp_df, use_container_width=True, hide_index=True)

            # Related searches
            if serp.get("related_searches"):
                st.markdown("### 🔗 Google Related Searches (LSI Keywords)")
                st.write(", ".join([f"`{q}`" for q in serp["related_searches"]]))
        else:
            if not serpapi_key:
                st.warning("SerpApi Key not detected. Add your SERPAPI_KEY in the sidebar to activate live Google Competitor & PAA intelligence.")
            else:
                st.info("Click 'Fetch Live Google SERP' above to run live competitive intelligence.")

    # -------------------------------------------------------------------------
    # TAB 6: DeepSeek AI Copilot
    # -------------------------------------------------------------------------
    with tabs[5]:
        st.subheader("🧠 DeepSeek AI Editorial Director")
        ds_key = st.session_state.deepseek_key

        if not ds_key:
            st.warning("Please enter your DeepSeek API Key in the left sidebar to unlock the AI Copilot.")
        else:
            ai_col1, ai_col2, ai_col3, ai_col4, ai_col5 = st.columns(5)
            with ai_col1:
                run_ai_audit_btn = st.button("⚡ Executive AI Audit", use_container_width=True)
            with ai_col2:
                run_ai_faq_btn = st.button("📋 Generate FAQ Schema", use_container_width=True)
            with ai_col3:
                run_ai_titles_btn = st.button("🎯 CTR Titles & Meta", use_container_width=True)
            with ai_col4:
                run_ai_read_btn = st.button("🪄 Readability Rewriter", use_container_width=True)
            with ai_col5:
                run_ai_verify_btn = st.button("🛡️ Content & Fact Audit", use_container_width=True)

            cache_key = f"{c_data['title']}-{deepseek_model}"

            if run_ai_audit_btn:
                with st.spinner(f"Querying DeepSeek ({deepseek_model})..."):
                    ai_res = api_integrations.generate_deepseek_audit(c_data, c_audit, api_key=ds_key, model=deepseek_model)
                    if ai_res.get("success"):
                        st.session_state.ai_audit_cache[f"{cache_key}-audit"] = ai_res
                    else:
                        st.error(ai_res.get("error"))

            if run_ai_faq_btn:
                with st.spinner(f"Generating JSON-LD Schema with DeepSeek ({deepseek_model})..."):
                    paa_q = current.get("serp", {}).get("people_also_ask", []) if current.get("serp") else []
                    faq_res = api_integrations.generate_ai_faq_schema(c_data, paa_q, api_key=ds_key, model=deepseek_model)
                    if faq_res.get("success"):
                        st.session_state.ai_audit_cache[f"{cache_key}-faq"] = faq_res
                    else:
                        st.error(faq_res.get("error"))

            if run_ai_titles_btn:
                with st.spinner("Generating CTR optimized titles..."):
                    t_prompt = f"Provide 5 high-converting, high-CTR SEO title tags and 3 compelling meta descriptions for an article titled '{c_data['title']}' targeting keyword '{c_audit['keyword']}'."
                    t_res = api_integrations.query_deepseek_copilot(t_prompt, api_key=ds_key, model=deepseek_model)
                    if t_res.get("success"):
                        st.session_state.ai_audit_cache[f"{cache_key}-titles"] = t_res
                    else:
                        st.error(t_res.get("error"))

            if run_ai_read_btn:
                with st.spinner("Generating conversational readability rewrite (Flesch 65–75)..."):
                    r_res = api_integrations.rewrite_for_readability(c_data, api_key=ds_key, model=deepseek_model)
                    if r_res.get("success"):
                        st.session_state.ai_audit_cache[f"{cache_key}-readability"] = r_res
                    else:
                        st.error(r_res.get("error"))

            if run_ai_verify_btn:
                with st.spinner("Forensically verifying content, facts, and alignment..."):
                    v_res = api_integrations.verify_content_and_facts(c_data, api_key=ds_key, model=deepseek_model)
                    if v_res.get("success"):
                        st.session_state.ai_audit_cache[f"{cache_key}-verification"] = v_res
                    else:
                        st.error(v_res.get("error"))

            # Display cached AI outputs
            if f"{cache_key}-audit" in st.session_state.ai_audit_cache:
                st.markdown("### 📋 DeepSeek Strategic Editorial Verdict")
                res = st.session_state.ai_audit_cache[f"{cache_key}-audit"]
                if res.get("reasoning"):
                    with st.expander("💭 View DeepSeek Reasoning Process (CoT)"):
                        st.write(res["reasoning"])
                st.markdown(res["content"])

            if f"{cache_key}-faq" in st.session_state.ai_audit_cache:
                st.markdown("### 📋 Generated JSON-LD FAQPage Schema")
                st.code(st.session_state.ai_audit_cache[f"{cache_key}-faq"]["content"], language="json")

            if f"{cache_key}-titles" in st.session_state.ai_audit_cache:
                st.markdown("### 🎯 High-CTR Titles & Meta Descriptions")
                st.markdown(st.session_state.ai_audit_cache[f"{cache_key}-titles"]["content"])

            if f"{cache_key}-readability" in st.session_state.ai_audit_cache:
                st.markdown("### 🪄 DeepSeek Conversational Readability Rewrite (Flesch 65–75)")
                res = st.session_state.ai_audit_cache[f"{cache_key}-readability"]
                if res.get("reasoning"):
                    with st.expander("💭 View DeepSeek Reasoning Process (CoT)"):
                        st.write(res["reasoning"])
                st.markdown(res["content"])

            if f"{cache_key}-verification" in st.session_state.ai_audit_cache:
                st.markdown("### 🛡️ Deep Forensic & Factual Alignment Report")
                res = st.session_state.ai_audit_cache[f"{cache_key}-verification"]
                if res.get("reasoning"):
                    with st.expander("💭 View DeepSeek Reasoning Process (CoT)"):
                        st.write(res["reasoning"])
                st.markdown(res["content"])

    # -------------------------------------------------------------------------
    # TAB 7: Core Web Vitals & PageSpeed
    # -------------------------------------------------------------------------
    with tabs[6]:
        st.subheader("⚡ Google Core Web Vitals & Mobile Performance")
        ps = current.get("pagespeed") or st.session_state.pagespeed_cache.get(c_data["url"])

        if not ps and c_data["url"].startswith("http"):
            if st.button("Run Google PageSpeed Insights Check"):
                with st.spinner("Analyzing Core Web Vitals via Google API..."):
                    ps = api_integrations.fetch_pagespeed_insights(c_data["url"], api_key=pagespeed_key)
                    if ps and ps.get("success"):
                        current["pagespeed"] = ps
                        st.session_state.pagespeed_cache[c_data["url"]] = ps
                        st.rerun()

        if ps and ps.get("success"):
            pcol1, pcol2, pcol3, pcol4, pcol5 = st.columns(5)
            with pcol1:
                st.metric("Performance", f"{ps['perf_score']}/100")
            with pcol2:
                st.metric("LCP", ps["lcp"])
            with pcol3:
                st.metric("CLS", ps["cls"])
            with pcol4:
                st.metric("FCP", ps["fcp"])
            with pcol5:
                st.metric("TBT", ps["tbt"])

            if ps.get("opportunities"):
                st.markdown("### 🛠️ Google Speed Opportunities:")
                for opp in ps["opportunities"]:
                    st.warning(f"**{opp['title']}** - Est. Savings: {opp.get('savings', '')}")
        else:
            st.info("Core Web Vitals check evaluates real-world mobile UX metrics (LCP, CLS, FCP) directly via Google's Lighthouse engine.")

    # -------------------------------------------------------------------------
    # TAB 8: SERP & Social Preview
    # -------------------------------------------------------------------------
    with tabs[7]:
        st.subheader("📱 Live SERP & Social Sharing Simulators")
        serp_title = c_data["title"][:60]
        serp_url = c_data["url"]
        serp_desc = c_data["meta_description"][:160] or "No meta description provided. Google will generate a dynamic snippet from page content."

        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #dfe1e5; border-radius: 8px; padding: 16px; max-width: 650px;">
            <div style="font-size: 14px; color: #202124;">{serp_url}</div>
            <div style="font-size: 20px; color: #1a0dab; text-decoration: none; cursor: pointer; line-height: 1.3; font-weight: 400; margin: 4px 0;">{serp_title}</div>
            <div style="font-size: 14px; color: #4d5156; line-height: 1.5;">{serp_desc}</div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.markdown("#### OpenGraph (Facebook / LinkedIn) Share Card")
        og_img = c_data["opengraph"].get("og:image") or "https://via.placeholder.com/600x315.png?text=No+OG:Image+Detected"
        st.markdown(f"""
        <div style="background: #ffffff; border: 1px solid #ced0d4; border-radius: 8px; max-width: 500px; overflow: hidden;">
            <img src="{og_img}" style="width: 100%; height: 250px; object-fit: cover;">
            <div style="padding: 12px; background: #f0f2f5;">
                <div style="font-size: 12px; color: #65676b; text-transform: uppercase;">{c_data['url']}</div>
                <div style="font-size: 16px; font-weight: 600; color: #050505; margin: 4px 0;">{c_data['opengraph'].get('og:title') or c_data['title']}</div>
                <div style="font-size: 13px; color: #65676b;">{c_data['opengraph'].get('og:description') or c_data['meta_description'][:100]}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # TAB 9: Content Hierarchy
    # -------------------------------------------------------------------------
    with tabs[8]:
        st.subheader("📑 Document Heading Hierarchy")
        st.write(f"Total Headings: **{len(c_data['headings'])}** (H1: {c_audit['h1_count']}, H2: {c_audit['h2_count']}, H3: {c_audit['h3_count']})")

        if not c_data["headings"]:
            st.warning("No HTML headings detected in this article!")
        else:
            for h in c_data["headings"]:
                indent = "&nbsp;" * ((h["level"] - 1) * 6)
                badge_bg = "#dbeafe" if h["level"] == 1 else ("#e0e7ff" if h["level"] == 2 else "#f1f5f9")
                st.markdown(f"{indent}<span style='background: {badge_bg}; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-weight: 700;'>H{h['level']}</span> **{h['text']}**", unsafe_allow_html=True)

        if c_data.get("long_sentences"):
            st.divider()
            st.subheader(f"⚠️ Run-On Sentences ({len(c_data['long_sentences'])})")
            st.caption("Sentences with more than 28 words should be broken into punchier units:")
            for ls in c_data["long_sentences"][:8]:
                st.write(f"- ({ls['word_count']} words): *\"{ls['sentence']}\"*")

    # -------------------------------------------------------------------------
    # TAB 10: Media & Links
    # -------------------------------------------------------------------------
    with tabs[9]:
        st.subheader("🖼️ Image Alt Text & Format Audit")
        if c_data["images"]:
            img_df = pd.DataFrame(c_data["images"])[["src", "alt", "has_alt", "format", "loading"]]
            st.dataframe(img_df, use_container_width=True, hide_index=True)
        else:
            st.info("No images detected on this page.")

        st.divider()
        st.subheader("🔗 Links & Authority References")
        lcol1, lcol2, lcol3 = st.columns(3)
        with lcol1:
            st.metric("Internal Links", c_audit["internal_links_count"])
        with lcol2:
            st.metric("External Links", c_audit["external_links_count"])
        with lcol3:
            st.metric("Outbound Authority Citations", c_audit["citations_count"])

        if c_data.get("citation_links"):
            st.markdown("#### 🎓 Recognized Authority Citations Found:")
            for cit in c_data["citation_links"]:
                st.write(f"- [{cit['text'] or cit['href']}]({cit['href']})")

    # -------------------------------------------------------------------------
    # TAB 11: Checklist & Export
    # -------------------------------------------------------------------------
    with tabs[10]:
        st.subheader("📝 Pre-Publish Editorial Sign-off")
        chk_items = [
            "Primary keyword present in Title, H1 and First 100 Words",
            "Meta description is 140-160 characters and includes a clear CTA",
            "Exactly one descriptive H1 tag present",
            "At least 3 descriptive H2 sections organize the content",
            "Flesch Reading Ease is conversational (60+)",
            "All images contain descriptive Alt text",
            "At least 2 outbound links to trusted, authoritative sources (.gov, .edu, journals)",
            "Internal contextual links added to related topic cluster articles",
            "Canonical tag and JSON-LD Article/FAQ schema validated",
            "Actionable Conclusion or Key Takeaways summary included",
        ]
        for i, item in enumerate(chk_items):
            st.checkbox(item, key=f"chk-{selected_idx}-{i}")

        st.divider()
        st.subheader("📥 Export Reports")
        dcol1, dcol2 = st.columns(2)

        with dcol1:
            csv_data = pd.DataFrame(summary_rows).to_csv(index=False)
            st.download_button(
                label="📊 Download Dashboard CSV",
                data=csv_data,
                file_name="blogguard_seo_dashboard.csv",
                mime="text/csv",
                use_container_width=True
            )

        with dcol2:
            html_report = export_helper.generate_html_report(c_data, c_audit, serp_data=current.get("serp"))
            st.download_button(
                label="📑 Download Executive HTML/PDF Report",
                data=html_report,
                file_name=f"blogguard_report_{c_data['title'][:20].replace(' ', '_')}.html",
                mime="text/html",
                use_container_width=True
            )

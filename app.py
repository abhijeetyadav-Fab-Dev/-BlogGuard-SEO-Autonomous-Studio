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
import db_history

# Force-reload local modules on every run so any long-running Streamlit process gets latest code
for _mod in [crawler, audit_engine, api_integrations, export_helper, db_history]:
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
if "audit_mode" not in st.session_state:
    st.session_state.audit_mode = "🌐 Autonomous Live URL Audit"

# -----------------------------------------------------------------------------
# SIDEBAR: Control Tower & API Integrations
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/fluent/96/shield.png", width=64)
    st.title("BlogGuard SEO")
    st.caption("Autonomous Blog Architecture, Content & SERP Engine")
    st.divider()

    st.subheader("🎯 Active Audit Mode")
    st.info(f"**{st.session_state.audit_mode}**")
    st.caption("Switch modes directly in the studio banner at the top of the main page.")

    if st.session_state.results:
        if st.button("🗑️ Clear Session Audits", use_container_width=True, help="Clear all currently stored audit results"):
            st.session_state.results = []
            if "battle_data" in st.session_state:
                del st.session_state["battle_data"]
            st.rerun()

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

    # 2. Multi-LLM AI Copilot Hub
    st.markdown("**🧠 Multi-LLM AI Copilot Hub**")
    ai_provider = st.selectbox(
        "AI Provider",
        ["🤖 DeepSeek", "⚡ Google Gemini", "🧠 OpenAI"],
        index=0,
        help="Switch seamlessly between DeepSeek, Google Gemini, and OpenAI."
    )
    selected_provider_slug = "gemini" if "Gemini" in ai_provider else ("openai" if "OpenAI" in ai_provider else "deepseek")

    if selected_provider_slug == "gemini":
        default_ai_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
        ai_key = st.text_input("Google Gemini API Key", value=st.session_state.get("gemini_key", default_ai_key), type="password", help="Powers Gemini 1.5 Flash / Pro reasoning.")
        st.session_state.gemini_key = ai_key
        ai_model = st.selectbox("Gemini Model", ["gemini-1.5-flash", "gemini-1.5-pro"])
    elif selected_provider_slug == "openai":
        default_ai_key = os.environ.get("OPENAI_API_KEY", "")
        ai_key = st.text_input("OpenAI API Key", value=st.session_state.get("openai_key", default_ai_key), type="password", help="Powers GPT-4o / GPT-4o-mini reasoning.")
        st.session_state.openai_key = ai_key
        ai_model = st.selectbox("OpenAI Model", ["gpt-4o-mini", "gpt-4o"])
    else:
        default_ai_key = os.environ.get("DEEPSEEK_API_KEY", "")
        ai_key = st.text_input("DeepSeek API Key", value=st.session_state.get("deepseek_key", default_ai_key), type="password", help="Powers DeepSeek R1 / V3 reasoning.")
        st.session_state.deepseek_key = ai_key
        ai_model = st.selectbox("DeepSeek Model", ["deepseek-chat", "deepseek-reasoner"])

    # 3. Google PageSpeed
    st.markdown("**Google PageSpeed Insights**")
    enable_pagespeed = st.checkbox("Audit Core Web Vitals (Mobile)", value=False)
    pagespeed_key = st.text_input("Google PageSpeed Key (Optional)", type="password", help="Leave blank for public rate-limited quota.")

    # 4. WordPress & Yoast SEO Suite
    st.markdown("**WordPress & Yoast SEO Suite**")
    wp_site_url = st.text_input(
        "WordPress Site URL",
        value=st.session_state.get("wp_site_url", "https://yoast.com"),
        placeholder="https://yourblog.com",
        help="Target WordPress installation running Yoast SEO REST API (v14.0+)."
    )
    st.session_state.wp_site_url = wp_site_url

    with st.expander("🔐 WordPress Credentials (Optional / 2-Way Sync)", expanded=False):
        wp_user = st.text_input("WP Username", value=st.session_state.get("wp_user", ""), placeholder="admin")
        wp_app_pass = st.text_input("Application Password", value=st.session_state.get("wp_app_pass", ""), type="password", help="Generated under WordPress Users > Profile > Application Passwords.")
        st.session_state.wp_user = wp_user
        st.session_state.wp_app_pass = wp_app_pass

    # 5. Engine selector
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

AUDIT_MODES = [
    "🌐 Autonomous Live URL Audit",
    "⚔️ Competitor Battle Mode",
    "📑 Batch / Multi-URL Audit",
    "✍️ Manual Content Draft",
]

st.markdown("#### 🎯 Choose Audit Engine Mode")
audit_mode = st.radio(
    "Audit Mode Selection",
    AUDIT_MODES,
    index=AUDIT_MODES.index(st.session_state.audit_mode) if st.session_state.audit_mode in AUDIT_MODES else 0,
    horizontal=True,
    key="audit_mode_selection_bar"
)
st.session_state.audit_mode = audit_mode
st.divider()

# -----------------------------------------------------------------------------
# MODE 1: Autonomous Live URL Audit
# -----------------------------------------------------------------------------
if audit_mode == "🌐 Autonomous Live URL Audit":
    st.subheader("🌐 Live URL Autonomous Inspection")
    st.caption("Audit any published article for technical structure, readability, wordiness, grammar, E-E-A-T, and SERP visibility.")

    if "mode1_url" not in st.session_state:
        st.session_state.mode1_url = ""
    if "mode1_kw" not in st.session_state:
        st.session_state.mode1_kw = ""

    demo_col1, demo_col2 = st.columns([3, 1])
    with demo_col2:
        if st.button("✨ Load Demo Article", use_container_width=True, help="Populate with a live accessible article for instant testing"):
            st.session_state.mode1_url = "https://en.wikipedia.org/wiki/Search_engine_optimization"
            st.session_state.mode1_kw = "search engine optimization"
            st.rerun()

    col1, col2 = st.columns([3, 2])
    with col1:
        target_url = st.text_input("Blog Post URL", value=st.session_state.mode1_url, placeholder="https://example.com/blog/best-seo-tips")
    with col2:
        target_keyword = st.text_input("Primary Keyword (Leave empty for AI Auto-Discovery)", value=st.session_state.mode1_kw, placeholder="e.g. best seo tips")

    run_btn = st.button("🚀 Run Autonomous Audit", type="primary", use_container_width=True)

    if run_btn:
        if not target_url.strip():
            st.error("Please provide a valid blog URL to audit.")
        else:
            with st.status("Running Autonomous Multi-Engine Audit...", expanded=True) as status:
                st.write("🌐 Launching browser engine and extracting rendered DOM...")
                fetch_res = crawler.fetch_html(target_url, use_browser=use_browser)

                if fetch_res.get("error") or fetch_res.get("status_code", 0) >= 400 or not fetch_res.get("html"):
                    err_detail = fetch_res.get("error") or f"HTTP {fetch_res.get('status_code')}"
                    status.update(label=f"Fetch failed: {err_detail}", state="error")
                    st.error(f"❌ Could not retrieve `{target_url}` ({err_detail}).")
                    if fetch_res.get("status_code") in (401, 403, 503):
                        st.warning("🛡️ **Cloud Bot Protection / WAF Detected:** This website blocked incoming requests from cloud hosting servers (Cloudflare/Akamai). You can audit this exact article without obstacles by copying its text into **✍️ Manual Content Draft** mode!")
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
                    try:
                        db_history.save_audit_snapshot(page_data, audit_res)
                    except Exception:
                        pass
                    status.update(label=f"Audit complete! Score: {audit_res['overall_score']}/100 ({audit_res['status']})", state="complete")
                    st.rerun()

# -----------------------------------------------------------------------------
# MODE 2: Competitor Battle Mode
# -----------------------------------------------------------------------------
elif audit_mode == "⚔️ Competitor Battle Mode":
    st.subheader("⚔️ Head-to-Head Competitor Gap Matrix")
    st.caption("Compare your blog post directly against a ranking competitor to spot exact topical, heading, and structural gaps.")

    if "battle_url_1" not in st.session_state:
        st.session_state.battle_url_1 = ""
    if "battle_url_2" not in st.session_state:
        st.session_state.battle_url_2 = ""
    if "battle_kw" not in st.session_state:
        st.session_state.battle_kw = ""

    b_demo_c1, b_demo_c2 = st.columns([3, 1])
    with b_demo_c2:
        if st.button("✨ Load Demo Battle", use_container_width=True, help="Load two sample URLs for instant battle testing"):
            st.session_state.battle_url_1 = "https://en.wikipedia.org/wiki/Search_engine_optimization"
            st.session_state.battle_url_2 = "https://en.wikipedia.org/wiki/Web_crawler"
            st.session_state.battle_kw = "search engine"
            st.rerun()

    col_a, col_b = st.columns(2)
    with col_a:
        your_url = st.text_input("Your Blog URL", value=st.session_state.battle_url_1, placeholder="https://yoursite.com/blog/my-guide")
    with col_b:
        comp_url = st.text_input("Competitor Blog URL", value=st.session_state.battle_url_2, placeholder="https://competitor.com/blog/their-guide")
    battle_keyword = st.text_input("Shared Target Keyword", value=st.session_state.battle_kw, placeholder="e.g. search engine")

    battle_btn = st.button("⚔️ Launch Head-to-Head Battle", type="primary", use_container_width=True)

    if battle_btn:
        if not your_url.strip() or not comp_url.strip():
            st.error("Please enter both URLs to run the comparison.")
        else:
            with st.status("Auditing both articles in parallel...", expanded=True) as status:
                st.write(f"🔄 Fetching Your Post: `{your_url}`...")
                fetch_1 = crawler.fetch_html(your_url, use_browser=use_browser)
                err_1 = fetch_1.get("error") or f"HTTP {fetch_1.get('status_code', 0)}"
                if fetch_1.get("error") or fetch_1.get("status_code", 0) >= 400 or not fetch_1.get("html"):
                    status.update(label=f"Failed to fetch Your URL: {err_1}", state="error")
                    st.error(f"❌ Could not crawl Your Blog URL: {err_1}")
                else:
                    data_1 = crawler.parse_page_data(fetch_1)
                    kw_1 = battle_keyword.strip() or data_1.get("suggested_keyword")
                    audit_1 = audit_engine.audit_page(data_1, keyword=kw_1)

                    st.write(f"🔄 Fetching Competitor Post: `{comp_url}`...")
                    fetch_2 = crawler.fetch_html(comp_url, use_browser=use_browser)
                    err_2 = fetch_2.get("error") or f"HTTP {fetch_2.get('status_code', 0)}"
                    if fetch_2.get("error") or fetch_2.get("status_code", 0) >= 400 or not fetch_2.get("html"):
                        status.update(label=f"Failed to fetch Competitor URL: {err_2}", state="error")
                        st.error(f"❌ Could not crawl Competitor Blog URL: {err_2}")
                    else:
                        data_2 = crawler.parse_page_data(fetch_2)
                        kw_2 = battle_keyword.strip() or data_2.get("suggested_keyword")
                        audit_2 = audit_engine.audit_page(data_2, keyword=kw_2)

                        st.session_state.battle_data = {
                            "your": {"data": data_1, "audit": audit_1},
                            "comp": {"data": data_2, "audit": audit_2},
                            "keyword": battle_keyword,
                        }

                        # Insert both records so user can inspect the full 11-tab scorecard for each!
                        st.session_state.results.insert(0, {
                            "type": "Competitor Battle",
                            "url": comp_url,
                            "title": f"⚔️ [Competitor] {data_2['title']}",
                            "keyword": kw_2,
                            "page_data": data_2,
                            "audit": audit_2,
                            "serp": None,
                            "pagespeed": None,
                        })
                        st.session_state.results.insert(0, {
                            "type": "Competitor Battle",
                            "url": your_url,
                            "title": f"⚔️ [Your Post] {data_1['title']}",
                            "keyword": kw_1,
                            "page_data": data_1,
                            "audit": audit_1,
                            "serp": None,
                            "pagespeed": None,
                        })
                        status.update(label="Battle comparison & full audits generated!", state="complete")
                        st.success("⚔️ Battle completed! Review the comparison matrix below and inspect each article in the 11-Tab Inspection Dashboard at the bottom.")

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
            if y_d.get("h2_list"):
                for h in y_d["h2_list"]:
                    st.write(f"- {h}")
            else:
                st.caption("No H2 headings detected.")
        with hcol2:
            st.markdown("**Competitor H2 Headings (Topics you might have missed):**")
            if c_d.get("h2_list"):
                for h in c_d["h2_list"]:
                    st.write(f"- {h}")
            else:
                st.caption("No H2 headings detected.")

# -----------------------------------------------------------------------------
# MODE 3: Batch / Multi-URL Audit
# -----------------------------------------------------------------------------
elif audit_mode == "📑 Batch / Multi-URL Audit":
    st.subheader("📑 Batch URL Crawler & Site-Wide Audit")
    st.caption("Audit multiple published URLs in one sequential pipeline to identify site-wide content health and ranking readiness.")

    if "batch_urls_input" not in st.session_state:
        st.session_state.batch_urls_input = ""

    b_demo_c1, b_demo_c2 = st.columns([3, 1])
    with b_demo_c2:
        if st.button("✨ Load Demo Batch URLs", use_container_width=True, help="Populate with 3 sample articles for quick batch testing"):
            st.session_state.batch_urls_input = (
                "https://en.wikipedia.org/wiki/Search_engine_optimization\n"
                "https://en.wikipedia.org/wiki/Web_crawler\n"
                "https://en.wikipedia.org/wiki/PageRank"
            )
            st.rerun()

    urls_input = st.text_area(
        "Enter URLs (one per line):",
        value=st.session_state.batch_urls_input,
        placeholder="https://example.com/blog-1\nhttps://example.com/blog-2\nhttps://example.com/blog-3",
        height=150
    )
    batch_btn = st.button("🚀 Run Batch Audit", type="primary", use_container_width=True)

    if batch_btn:
        urls = [u.strip() for u in urls_input.splitlines() if u.strip()]
        if not urls:
            st.error("Please enter at least one URL.")
        else:
            success_count = 0
            failed_items = []
            with st.status(f"Auditing {len(urls)} URLs in batch...", expanded=True) as status:
                progress_bar = st.progress(0)
                for idx, u in enumerate(urls):
                    st.write(f"🔄 ({idx+1}/{len(urls)}) Auditing: `{u}`")
                    fetch_res = crawler.fetch_html(u, use_browser=use_browser)
                    if not fetch_res.get("error") and fetch_res.get("status_code", 0) < 400 and fetch_res.get("html"):
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
                        try:
                            db_history.save_audit_snapshot(p_data, a_res)
                        except Exception:
                            pass
                        success_count += 1
                        st.write(f"✅ Success: **{p_data['title']}** (Score: {a_res['overall_score']}/100)")
                    else:
                        err_msg = fetch_res.get("error") or f"HTTP {fetch_res.get('status_code')}"
                        failed_items.append((u, err_msg))
                        st.write(f"⚠️ Failed: `{u}` ({err_msg})")
                    progress_bar.progress((idx + 1) / len(urls))

                final_label = f"Batch completed: {success_count} succeeded, {len(failed_items)} failed."
                status.update(label=final_label, state="complete" if success_count > 0 else "error")

            if success_count > 0:
                st.success(f"🎉 Successfully audited {success_count} article(s)! Select any article from the dashboard below to view its 11-tab scorecard.")
            if failed_items:
                with st.expander(f"⚠️ {len(failed_items)} URL(s) could not be crawled", expanded=True):
                    for u, err in failed_items:
                        st.markdown(f"- `{u}`: **{err}**")
                    st.info("💡 **Note:** Websites blocking automated cloud crawlers can be audited directly via **✍️ Manual Content Draft** mode.")

# -----------------------------------------------------------------------------
# MODE 4: Manual Content Draft
# -----------------------------------------------------------------------------
elif audit_mode == "✍️ Manual Content Draft":
    st.subheader("✍️ Draft & Pre-Publish Manual Audit")
    st.caption("Audit unpublished content drafts before publishing. Uncover run-on sentences, jargon, typos, wordy redundancies, E-E-A-T gaps, and headline alignment with 0 dependency on live web access.")

    SAMPLE_DRAFT_TITLE = "Mastering Modern Technical SEO for High-Impact Search Rankings"
    SAMPLE_DRAFT_KW = "technical seo"
    SAMPLE_DRAFT_AUTHOR = "Alex Taylor"
    SAMPLE_DRAFT_TEXT = """# Mastering Modern Technical SEO for High-Impact Search Rankings

In the modern digital ecosystem, technical seo is the absolute bedrock upon which all organic growth strategies must be meticulously constructed and continually optimized. Due to the fact that search engine algorithms are becoming extraordinarily sophisticated, understanding how crawlers index and interpret structured web architecture has become more paramount than ever before for marketing teams across the globe.

## Why Technical Architecture Determines Organic Visibility

In this day and age, search engines prioritize websites that demonstrate fast load velocity, impeccable mobile responsiveness, and clean semantic markup. A study was conducted by leading web engineers which verified that pages loading in under two seconds achieve significantly higher conversion rates and superior user retention.

According to Google search advocates, Core Web Vitals directly influence ranking signals. Furthermore, if your site architecture suffers from deep crawl depth or fragmented internal link paths, search bots will deplete their crawl budget before discovering your high-value commercial landing pages.

## Key Pillars of a Modern Technical SEO Audit

1. **Crawlability and Indexability**: Ensure your robots.txt does not inadvertently block critical CSS or JavaScript assets that render the page layout.
2. **Canonicalization**: Eliminate duplicate content risks across HTTP, HTTPS, trailing slashes, and parameterized query strings.
3. **Structured Data Markup**: Implement Article, FAQPage, and BreadcrumbList schemas to earn rich snippets on Google SERPs.

In order to optimize your technical seo performance, audit your XML sitemaps regularly, rectify broken 404 links, and maintain clean canonical tags. In the event that server latency spikes, implement edge caching and content delivery networks immediately.
"""

    if "draft_title_val" not in st.session_state:
        st.session_state.draft_title_val = ""
    if "draft_text_val" not in st.session_state:
        st.session_state.draft_text_val = ""
    if "draft_kw_val" not in st.session_state:
        st.session_state.draft_kw_val = ""
    if "draft_author_val" not in st.session_state:
        st.session_state.draft_author_val = ""

    d_demo_c1, d_demo_c2 = st.columns([3, 1])
    with d_demo_c2:
        if st.button("✨ Load Sample Draft", use_container_width=True, help="Load an article draft designed to test all audit metrics"):
            st.session_state.draft_title_val = SAMPLE_DRAFT_TITLE
            st.session_state.draft_text_val = SAMPLE_DRAFT_TEXT
            st.session_state.draft_kw_val = SAMPLE_DRAFT_KW
            st.session_state.draft_author_val = SAMPLE_DRAFT_AUTHOR
            st.rerun()

    d_col1, d_col2 = st.columns([3, 2])
    with d_col1:
        draft_title = st.text_input("Draft Title", value=st.session_state.draft_title_val, placeholder="The Complete Guide to Technical SEO in 2026")
        draft_text = st.text_area("Blog Content (Paste raw text or Markdown)", value=st.session_state.draft_text_val, height=300, placeholder="Paste your article draft here...")
    with d_col2:
        draft_kw = st.text_input("Focus Keyword", value=st.session_state.draft_kw_val, placeholder="technical seo")
        draft_author = st.text_input("Writer / Author", value=st.session_state.draft_author_val, placeholder="Alex Taylor")
        draft_btn = st.button("🚀 Audit Draft Content", type="primary", use_container_width=True)

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
            try:
                db_history.save_audit_snapshot(mock_data, a_res)
            except Exception:
                pass
            st.success("✅ Draft audited successfully! View the full scorecard below.")
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
            "Mode": r.get("type", "Audit"),
            "Title": r["title"][:45] + ("..." if len(r["title"]) > 45 else ""),
            "Keyword": r["keyword"] or "Auto-detected",
            "Words": r["audit"]["word_count"],
            "Score": f"{r['audit']['overall_score']}/100",
            "Status": r["audit"]["status"],
            "URL": r["url"][:35] + ("..." if len(r["url"]) > 35 else ""),
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    selected_idx = st.selectbox(
        "Inspect Audit Report:",
        range(len(st.session_state.results)),
        format_func=lambda i: f"#{i+1}: [{st.session_state.results[i].get('type', 'Audit')}] {st.session_state.results[i]['title']} (Score: {st.session_state.results[i]['audit']['overall_score']})"
    )

    current = st.session_state.results[selected_idx]
    c_audit = current["audit"]
    c_data = current["page_data"]

    st.markdown(f"## 🛡️ {c_data['title']}")
    st.caption(f"**URL:** {c_data['url']} | **Focus Keyword:** `{c_audit['keyword']}` | **Engine:** `{c_data.get('engine', 'HTTP')}`")

    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # Hero Metric Strip
    # -------------------------------------------------------------------------
    aeo_val = c_audit.get("aeo", {}).get("aeo_score", 0)
    mcol1, mcol2, mcol3, mcol4, mcol5, mcol6 = st.columns(6)
    with mcol1:
        st.metric("Overall Score", f"{c_audit['overall_score']}/100")
    with mcol2:
        st.metric("AEO Citation", f"{aeo_val}/100")
    with mcol3:
        st.metric("Word Count", f"{c_audit['word_count']:,}")
    with mcol4:
        st.metric("Read Time", f"{c_audit['reading_time_min']} min")
    with mcol5:
        st.metric("Flesch Ease", f"{c_audit['readability']['flesch_reading_ease']}/100")
    with mcol6:
        st.metric("Outbound Citations", c_audit['citations_count'])

    # -------------------------------------------------------------------------
    # Autonomous 1-Click Auto-Pilot Banner
    # -------------------------------------------------------------------------
    with st.container():
        auto_c1, auto_c2 = st.columns([3, 1])
        with auto_c1:
            st.markdown("### 🚀 Autonomous Closed-Loop Auto-Pilot")
            st.caption("Executes crawling, Google SERP, competitor semantic gap, AI strategic audit, FAQ schema generation, and safe auto-patching in a single pass.")
        with auto_c2:
            if st.button("⚡ Run Full Auto-Pilot", type="primary", use_container_width=True, key=f"auto_pilot_btn_{selected_idx}"):
                with st.spinner("Executing full autonomous pipeline..."):
                    target_to_audit = c_data["url"] if c_data.get("url") not in ("Draft Article", "Manual Draft / Offline") else c_data["clean_text"]
                    pipe_res = audit_engine.run_autonomous_pipeline(
                        target_to_audit,
                        keyword=c_audit["keyword"],
                        serpapi_key=serpapi_key if enable_serp else None,
                        ai_key=ai_key,
                        ai_provider=selected_provider_slug,
                        ai_model=ai_model,
                        save_history=True
                    )
                    st.success("🎉 Full Autonomous Pipeline completed! Check AEO Studio, Competitor Gap, and In-Text Fixer below.")
                    st.session_state[f"patch_{selected_idx}"] = pipe_res["safe_patch"]
                    if pipe_res.get("competitor_gap"):
                        st.session_state[f"comp_gap_{selected_idx}"] = pipe_res["competitor_gap"]
                    if pipe_res.get("ai_audit") and pipe_res["ai_audit"].get("success"):
                        st.session_state.ai_audit_cache[c_data["url"]] = pipe_res["ai_audit"]
                    st.rerun()

    # -------------------------------------------------------------------------
    # TABS SECTION: The 16 Power Centers
    # -------------------------------------------------------------------------
    tabs = st.tabs([
        "📊 360° Scorecard",
        "🚨 Actionable Issues",
        "🌐 AEO & AI Overview Studio",
        "📊 Competitor Semantic Gap",
        "🎨 In-Text Highlighter & 1-Click Fixer",
        "🔍 Grammar, Clarity & Alignment",
        "🚦 Yoast SEO & REST API Studio",
        "🕷️ Sitemap & Link Sentinel",
        "📈 Audit History & Velocity",
        "🔍 Google SERP (SerpApi)",
        "🧠 Multi-LLM AI Copilot",
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
    # TAB 3: AEO (Answer Engine Optimization) & GEO Citation Studio
    # -------------------------------------------------------------------------
    with tabs[2]:
        st.subheader("🌐 AEO & GEO (AI Search Engine Optimization) Studio")
        st.caption("Grades content readiness for citation in Google AI Overviews (SGE), Perplexity AI, ChatGPT Search, and Microsoft Copilot.")

        aeo = c_audit.get("aeo") or audit_engine.evaluate_aeo_readiness(c_data, keyword=c_audit.get("keyword"))
        aeo_score = aeo.get("aeo_score", 0)
        aeo_verdict = aeo.get("verdict", "N/A")

        acol1, acol2, acol3 = st.columns([1, 2, 1])
        with acol1:
            st.metric("AEO Citation Score", f"{aeo_score}/100")
        with acol2:
            st.markdown(f"#### {aeo_verdict}")
            st.caption("AI search engines synthesize direct answers from articles with high factual entity density, explicit source attribution, and structured formatting.")
        with acol3:
            st.metric("Quantitative Proof Points", f"{aeo.get('stats_count', 0)} detected")

        st.divider()
        st.markdown("### 🏛️ The 4 AEO / GEO Foundations")

        crit_cols = st.columns(4)
        for idx, crit in enumerate(aeo.get("criteria", [])):
            with crit_cols[idx % 4]:
                st.markdown(f"**{crit['pillar']}**")
                st.metric("Score", f"{crit['score']}/{crit['max']}")
                status_icon = "🟢" if crit["status"] == "good" else ("🟠" if crit["status"] == "ok" else "🔴")
                st.write(f"{status_icon} {crit['advice']}")

        st.divider()
        st.markdown("### 💡 Recommended AEO Enhancements to Rank in AI Summaries")
        st.markdown("""
        1. **Direct Answer Paragraphs**: Start each major H2 with a concise 30-40 word direct definition or answer before elaborating.
        2. **Quantified Findings**: Back assertions with percentages (e.g. `+34%`), benchmark numbers, dates, or study years.
        3. **Structured Quotations**: Use explicit source attribution markers (`"According to a study by..."`).
        4. **Key Takeaways Table**: Provide summary tables comparing options, pros/cons, or steps.
        """)

    # -------------------------------------------------------------------------
    # TAB 4: Competitor Semantic Gap & TF-IDF Heatmap
    # -------------------------------------------------------------------------
    with tabs[3]:
        st.subheader("📊 Competitor Semantic Gap & TF-IDF Heatmap")
        st.caption("Identifies high-frequency terms, missing H2 subtopics, and structural benchmarks from top Google ranking competitors.")

        serp_res = current.get("serp") or st.session_state.serp_cache.get(c_audit["keyword"])
        comp_gap_key = f"comp_gap_{selected_idx}"

        if comp_gap_key not in st.session_state:
            st.session_state[comp_gap_key] = None

        if not serp_res or not serp_res.get("competitors"):
            st.info("ℹ️ To run Competitor Semantic Gap analysis, Google SerpApi results are needed. Enable SerpApi in the sidebar and ensure a focus keyword is set.")
            if serpapi_key and st.button("🔍 Fetch Live Google SERP Competitors Now", key=f"fetch_serp_gap_{selected_idx}"):
                with st.spinner("Fetching Google rankings..."):
                    serp_res = api_integrations.fetch_serp_intelligence(c_audit["keyword"], api_key=serpapi_key)
                    if serp_res and serp_res.get("success"):
                        st.session_state.serp_cache[c_audit["keyword"]] = serp_res
                        current["serp"] = serp_res
                        st.rerun()
        else:
            competitors_list = serp_res.get("competitors", [])[:3]
            st.write(f"Top competitors identified for **'{c_audit['keyword']}'**:")
            for idx, comp in enumerate(competitors_list, 1):
                st.caption(f"#{comp.get('position', idx)} **{comp.get('title', '')}** — `{comp.get('displayed_link', '')}`")

            if st.session_state[comp_gap_key] is None:
                if st.button("⚡ Crawl Competitors & Generate Semantic Gap Matrix", type="primary", key=f"btn_calc_gap_{selected_idx}"):
                    with st.spinner("Analyzing competitor content and extracting semantic n-grams..."):
                        comp_profiles = api_integrations.fetch_competitor_content(competitors_list, max_comp=3)
                        gap_report = audit_engine.analyze_competitor_semantic_gap(c_data, comp_profiles)
                        st.session_state[comp_gap_key] = gap_report
                        st.rerun()
            else:
                gap_report = st.session_state[comp_gap_key]
                if gap_report.get("success"):
                    bm = gap_report.get("benchmarks", {})
                    bm_col1, bm_col2, bm_col3 = st.columns(3)
                    with bm_col1:
                        st.metric("Word Count Benchmark", f"{bm['word_count']['target']:,} vs {bm['word_count']['competitor_avg']:,}", bm['word_count']['status'])
                    with bm_col2:
                        st.metric("Images Benchmark", f"{bm['images']['target']} vs {bm['images']['competitor_avg']}", bm['images']['status'])
                    with bm_col3:
                        st.metric("Citations Benchmark", f"{bm['citations']['target']} vs {bm['citations']['competitor_avg']}", bm['citations']['status'])

                    st.divider()
                    gap_col1, gap_col2 = st.columns(2)
                    with gap_col1:
                        st.markdown("#### 🎯 Missing High-Impact Keywords")
                        st.caption("Used frequently by top 3 rankers, but absent from your post:")
                        missing_kw = gap_report.get("missing_keywords", [])
                        if missing_kw:
                            st.dataframe(pd.DataFrame(missing_kw), use_container_width=True, hide_index=True)
                        else:
                            st.success("🎉 Excellent! Your post covers all core semantic terms used by top competitors.")

                    with gap_col2:
                        st.markdown("#### 📑 Missing Subtopic Themes (Competitor H2s)")
                        st.caption("Subtopics covered by competitors that your post does not mention:")
                        missing_topics = gap_report.get("missing_subtopics", [])
                        if missing_topics:
                            for mt in missing_topics:
                                st.markdown(f"- 📌 **{mt}**")
                        else:
                            st.success("Your heading structure thoroughly covers competitor subtopics.")

                    if st.button("🔄 Re-crawl & Re-analyze Competitors", key=f"btn_recalc_gap_{selected_idx}"):
                        st.session_state[comp_gap_key] = None
                        st.rerun()

    # -------------------------------------------------------------------------
    # TAB 5: In-Text Highlighter & 1-Click Auto-Patcher
    # -------------------------------------------------------------------------
    with tabs[4]:
        st.subheader("🎨 Live In-Text Visual Issue Highlighter & 1-Click Auto-Patcher")
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

        st.divider()

        # --- 1-Click Safe Editorial Auto-Patcher ---
        st.markdown("### 🪄 1-Click Safe Editorial Auto-Patcher (Self-Remediation)")
        st.caption("Automatically patches verified typos, replaces wordy redundancies with punchy alternatives, and simplifies corporate jargon while preserving all original markdown headings, links, and intent.")

        patch_res = audit_engine.apply_safe_simplifications(c_data["clean_text"])
        total_p = patch_res.get("total_replacements", 0)

        p_col1, p_col2, p_col3, p_col4 = st.columns(4)
        with p_col1:
            st.metric("Safe Fixes Available", f"{total_p} patches")
        with p_col2:
            st.metric("Spelling Corrections", f"{len(patch_res.get('spelling_fixes', []))} words")
        with p_col3:
            st.metric("Redundancies Trimmed", f"{len(patch_res.get('redundancy_fixes', []))} phrases")
        with p_col4:
            st.metric("Words / Flab Saved", f"{patch_res.get('words_saved', 0)} words")

        if total_p > 0:
            with st.expander(f"🔍 Inspect All {total_p} Safe Editorial Patches", expanded=False):
                patch_df = pd.DataFrame(patch_res.get("replacements", []))
                if not patch_df.empty:
                    st.dataframe(patch_df, use_container_width=True, hide_index=True)

            diff_col1, diff_col2 = st.columns(2)
            with diff_col1:
                st.markdown("#### 📄 Original Text (Excerpt)")
                st.text_area("Original", value=c_data["clean_text"][:800] + ("..." if len(c_data["clean_text"]) > 800 else ""), height=220, disabled=True, key=f"orig_txt_{selected_idx}")
            with diff_col2:
                st.markdown("#### ✨ Patched & Cleaned Text (Excerpt)")
                st.text_area("Patched", value=patch_res["patched_text"][:800] + ("..." if len(patch_res["patched_text"]) > 800 else ""), height=220, disabled=True, key=f"patch_txt_{selected_idx}")

            st.download_button(
                label="📥 Download Patched & Cleaned Content (.md)",
                data=patch_res["patched_text"],
                file_name=f"cleaned_{c_data['title'][:20].replace(' ', '_')}.md",
                mime="text/markdown",
                use_container_width=True
            )
        else:
            st.success("🎉 No safe fixes needed! Your copy is free of common typos, wordiness, and corporate jargon.")

    # -------------------------------------------------------------------------
    # TAB 6: Grammar, Clarity & Content-Information Alignment
    # -------------------------------------------------------------------------
    with tabs[5]:
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
                st.caption("💡 Switch to the **'🎨 In-Text Highlighter & 1-Click Auto-Patcher'** tab to see these sentences highlighted in blue directly in the article body.")

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
            st.caption("💡 Switch to the **'🎨 In-Text Highlighter & 1-Click Auto-Patcher'** tab to see these phrases highlighted in orange with their one-click replacements.")

        st.divider()

        # Section 4: Deep AI Forensic Verification (Fact-checking, Logic & Contradictions)
        st.markdown("### 🛡️ AI Deep Forensic & Factual Alignment Scanner")
        st.caption("Harness Multi-LLM AI to perform deep factual verification, uncover internal contradictions, audit grammar/syntax, and detect title drift.")

        cache_key = f"{c_data['title']}-{ai_model}"

        if not ai_key:
            st.warning(f"Enter your {ai_provider} API Key in the left sidebar to run deep AI fact and contradiction audits.")
        else:
            if st.button(f"🛡️ Run Deep Forensic & Factual Verification ({ai_provider})", key=f"btn_verify_{selected_idx}", use_container_width=True):
                with st.spinner(f"{ai_provider} AI is forensically analyzing article facts, logic, grammar, and headline alignment..."):
                    v_res = api_integrations.verify_content_and_facts(c_data, api_key=ai_key, model=ai_model, provider=selected_provider_slug)
                    if v_res.get("success"):
                        st.session_state.ai_audit_cache[f"{cache_key}-verification"] = v_res
                    else:
                        st.error(v_res.get("error", "Verification failed"))

            if f"{cache_key}-verification" in st.session_state.ai_audit_cache:
                v_data = st.session_state.ai_audit_cache[f"{cache_key}-verification"]
                if v_data.get("reasoning"):
                    with st.expander(f"💭 View {ai_provider} Reasoning Process (CoT)"):
                        st.write(v_data["reasoning"])
                st.markdown(v_data["content"])

    # -------------------------------------------------------------------------
    # TAB 7: Yoast SEO & REST API Studio
    # -------------------------------------------------------------------------
    with tabs[6]:
        st.subheader("🚦 Yoast SEO Traffic Lights & REST API Studio")
        st.caption("Official 14 Focus Keyphrase Criteria, 7 Readability Criteria, and direct integration with WordPress Yoast REST API endpoints.")

        y_eval = c_audit.get("yoast") or audit_engine.evaluate_yoast_seo(c_data, keyword=c_audit.get("keyword"))
        y_seo = y_eval["seo"]
        y_read = y_eval["readability"]

        # Dual Traffic Light Banners
        ycol1, ycol2 = st.columns(2)
        with ycol1:
            with st.container(border=True):
                st.markdown(f"### SEO Traffic Light: **{y_seo['badge']}**")
                st.markdown(f"**Score:** `{y_seo['score']}/100` | **Passed:** `{y_seo['passed_count']}/{y_seo['total']}` | **OK:** `{y_seo['ok_count']}` | **Needs Fix:** `{y_seo['bad_count']}`")
                st.caption(f"Focus Keyphrase evaluated: `{y_eval['keyword'] or 'None (Auto-detected)'}`")

        with ycol2:
            with st.container(border=True):
                st.markdown(f"### Readability Traffic Light: **{y_read['badge']}**")
                st.markdown(f"**Score:** `{y_read['score']}/100` | **Passed:** `{y_read['passed_count']}/{y_read['total']}` | **OK:** `{y_read['ok_count']}` | **Needs Fix:** `{y_read['bad_count']}`")
                st.caption(f"Flesch: `{y_read['metrics']['flesch_score']:.1f}` | Passive: `{y_read['metrics']['passive_voice_pct']:.1f}%` | Transitions: `{y_read['metrics']['transition_words_pct']:.1f}%`")

        st.divider()

        # Inner Sub-Tabs
        y_subtabs = st.tabs([
            f"🎯 14 SEO Criteria ({y_seo['passed_count']}/{y_seo['total']} Passed)",
            f"📖 7 Readability Criteria ({y_read['passed_count']}/{y_read['total']} Passed)",
            "🔌 Live Yoast REST API Explorer (All Endpoints)",
            "📤 Sync to WordPress via Yoast API"
        ])

        # SUBTAB 1: 14 SEO Criteria
        with y_subtabs[0]:
            st.markdown("#### 🚦 Yoast Focus Keyphrase Assessment Matrix")
            s_filter = st.radio(
                "Filter Criteria:",
                ["All", "🟢 Good", "🟠 OK", "🔴 Needs Improvement"],
                horizontal=True,
                key=f"yoast_seo_filter_{selected_idx}"
            )
            filter_map = {"🟢 Good": "good", "🟠 OK": "ok", "🔴 Needs Improvement": "bad"}

            for item in y_seo["items"]:
                if s_filter != "All" and item["status"] != filter_map[s_filter]:
                    continue
                icon = "🟢" if item["status"] == "good" else ("🟠" if item["status"] == "ok" else "🔴")
                exp_title = f"{icon} {item['title']}"
                with st.expander(exp_title, expanded=(item["status"] == "bad")):
                    st.markdown(f"**Diagnostic Feedback:** {item['feedback']}")
                    st.markdown(f"💡 **Yoast Recommendation:** `{item['recommendation']}`")

        # SUBTAB 2: 7 Readability Criteria
        with y_subtabs[1]:
            st.markdown("#### 📖 Yoast Readability & Content Flow Matrix")
            r_filter = st.radio(
                "Filter Readability:",
                ["All", "🟢 Good", "🟠 OK", "🔴 Needs Improvement"],
                horizontal=True,
                key=f"yoast_read_filter_{selected_idx}"
            )
            for item in y_read["items"]:
                if r_filter != "All" and item["status"] != filter_map.get(r_filter, ""):
                    continue
                icon = "🟢" if item["status"] == "good" else ("🟠" if item["status"] == "ok" else "🔴")
                exp_title = f"{icon} {item['title']}"
                with st.expander(exp_title, expanded=(item["status"] == "bad")):
                    st.markdown(f"**Diagnostic Feedback:** {item['feedback']}")
                    st.markdown(f"💡 **Yoast Recommendation:** `{item['recommendation']}`")

        # SUBTAB 3: Live Yoast REST API Explorer
        with y_subtabs[2]:
            st.markdown("#### 🔌 Yoast SEO REST API Client & Endpoint Inspector")
            st.caption("Directly query and test live Yoast SEO endpoints on WordPress sites.")

            api_ep = st.selectbox(
                "Select Yoast API Endpoint:",
                [
                    "1. GET /wp-json/yoast/v1/get_head?url={url} (Retrieve Full Yoast SEO Metadata)",
                    "2. GET /wp-json/wp/v2/posts (WordPress REST API with embedded yoast_head_json)",
                    "3. GET /wp-json/yoast/v1/statistics (Site Indexing Statistics)",
                    "4. GET /wp-json/yoast/v1/settings (Plugin Configuration)",
                ],
                key=f"yoast_api_ep_select_{selected_idx}"
            )

            # Endpoint 1: get_head
            if api_ep.startswith("1."):
                st.markdown("**Endpoint:** `GET /wp-json/yoast/v1/get_head?url={target_url}`")
                st.caption("Fetches complete Yoast rendered `<head>` HTML and structured JSON metadata for any post on a WordPress site with Yoast SEO.")

                ghead_col1, ghead_col2 = st.columns([3, 1])
                with ghead_col1:
                    query_url = st.text_input(
                        "Target Blog Post URL to Query:",
                        value=c_data.get("url") if c_data.get("url", "").startswith("http") else "https://yoast.com/wordpress-seo/",
                        key=f"yoast_q_url_{selected_idx}"
                    )
                with ghead_col2:
                    test_demo_btn = st.button("✨ Demo: yoast.com", key=f"btn_demo_yoast_{selected_idx}", use_container_width=True)

                if test_demo_btn:
                    query_url = "https://yoast.com/wordpress-seo/"

                run_get_head = st.button("🚀 Query Yoast get_head Endpoint", type="primary", key=f"btn_run_ghead_{selected_idx}")

                if run_get_head or test_demo_btn:
                    with st.spinner("Connecting to WordPress Yoast REST API..."):
                        y_head_res = api_integrations.fetch_yoast_head(query_url)
                        st.session_state[f"cached_yoast_head_{selected_idx}"] = y_head_res

                if f"cached_yoast_head_{selected_idx}" in st.session_state:
                    res = st.session_state[f"cached_yoast_head_{selected_idx}"]
                    if res.get("success"):
                        st.success(f"✅ Received HTTP 200 from Yoast REST API endpoint: `{res['endpoint']}`")

                        # Summary Metrics
                        ym_c1, ym_c2, ym_c3, ym_c4 = st.columns(4)
                        with ym_c1:
                            st.metric("Yoast Title Length", f"{len(res['title'])} chars")
                        with ym_c2:
                            st.metric("Meta Desc Length", f"{len(res['description'])} chars")
                        with ym_c3:
                            st.metric("Robots Index", res.get("robots", {}).get("index", "default"))
                        with ym_c4:
                            st.metric("Schema Nodes", len(res.get("schema_graph", [])))

                        head_tabs = st.tabs(["📑 Structured Yoast JSON", "📱 OpenGraph & Twitter Cards", "🕸️ Schema @graph", "💻 Raw <head> HTML"])
                        with head_tabs[0]:
                            st.json(res["json"])
                        with head_tabs[1]:
                            og = res.get("og", {})
                            tw = res.get("twitter", {})
                            st.markdown("##### OpenGraph Card")
                            st.write(f"- **OG Title:** {og.get('title')}")
                            st.write(f"- **OG Description:** {og.get('description')}")
                            st.write(f"- **OG Type:** {og.get('type')}")
                            st.markdown("##### Twitter Card")
                            st.write(f"- **Twitter Title:** {tw.get('title')}")
                            st.write(f"- **Twitter Card:** {tw.get('card')}")
                        with head_tabs[2]:
                            if res.get("schema_graph"):
                                for node in res["schema_graph"]:
                                    node_type = node.get("@type", "Schema Node")
                                    with st.expander(f"📍 {node_type} ({node.get('@id', '')})"):
                                        st.json(node)
                            else:
                                st.info("No @graph schema nodes returned.")
                        with head_tabs[3]:
                            st.code(res["html"][:3000] + ("..." if len(res["html"]) > 3000 else ""), language="html")
                    else:
                        st.error(res.get("error"))

            # Endpoint 2: wp/v2/posts
            elif api_ep.startswith("2."):
                st.markdown("**Endpoint:** `GET /wp-json/wp/v2/posts`")
                st.caption("Fetches posts with embedded `yoast_head` and `yoast_head_json` fields.")

                wp_s_col1, wp_s_col2 = st.columns([3, 1])
                with wp_s_col1:
                    wp_site = st.text_input("WordPress Base URL:", value=st.session_state.get("wp_site_url", "https://yoast.com"), key=f"wp_p_site_{selected_idx}")
                with wp_s_col2:
                    wp_search_term = st.text_input("Search Keyword / Slug (Optional):", placeholder="e.g. seo", key=f"wp_s_term_{selected_idx}")

                if st.button("🚀 Fetch WP Posts via Yoast API", type="primary", key=f"btn_fetch_wp_p_{selected_idx}"):
                    with st.spinner("Fetching WordPress posts with Yoast data..."):
                        wp_posts_res = api_integrations.fetch_wp_yoast_posts(wp_site, search=wp_search_term, per_page=5)
                        if wp_posts_res.get("success"):
                            st.success(f"✅ Retrieved {wp_posts_res['count']} post(s) from `{wp_posts_res['endpoint']}`")
                            for p in wp_posts_res["posts"]:
                                with st.expander(f"📄 #{p['id']}: {p['title']} ({'🟢 Yoast Active' if p['has_yoast'] else '⚪ No Yoast'})"):
                                    st.write(f"- **Permalink:** [{p['link']}]({p['link']})")
                                    st.write(f"- **Yoast Title:** {p['yoast_title']}")
                                    st.write(f"- **Yoast Description:** {p['yoast_description']}")
                                    if p.get("yoast_head_json"):
                                        st.json(p["yoast_head_json"])
                        else:
                            st.error(wp_posts_res.get("error"))

            # Endpoint 3: statistics
            elif api_ep.startswith("3."):
                st.markdown("**Endpoint:** `GET /wp-json/yoast/v1/statistics`")
                st.caption("Retrieves site-wide indexing statistics. (Requires WordPress admin authorization).")
                stat_site = st.text_input("WordPress Base URL:", value=st.session_state.get("wp_site_url", "https://yoast.com"), key=f"stat_site_{selected_idx}")
                stat_user = st.text_input("WP Username:", value=st.session_state.get("wp_user", ""), key=f"stat_u_{selected_idx}")
                stat_pass = st.text_input("WP Application Password:", value=st.session_state.get("wp_app_pass", ""), type="password", key=f"stat_p_{selected_idx}")

                if st.button("🚀 Query Yoast Statistics", key=f"btn_stat_{selected_idx}"):
                    with st.spinner("Querying Yoast statistics..."):
                        s_res = api_integrations.fetch_yoast_statistics(stat_site, username=stat_user, app_password=stat_pass)
                        if s_res.get("success"):
                            st.success("✅ Statistics received:")
                            st.json(s_res["statistics"])
                        else:
                            st.warning(s_res.get("error"))

            # Endpoint 4: settings
            elif api_ep.startswith("4."):
                st.markdown("**Endpoint:** `GET /wp-json/yoast/v1/settings`")
                st.caption("Retrieves site-wide Yoast SEO configuration settings.")
                set_site = st.text_input("WordPress Base URL:", value=st.session_state.get("wp_site_url", "https://yoast.com"), key=f"set_site_{selected_idx}")
                set_user = st.text_input("WP Username:", value=st.session_state.get("wp_user", ""), key=f"set_u_{selected_idx}")
                set_pass = st.text_input("WP Application Password:", value=st.session_state.get("wp_app_pass", ""), type="password", key=f"set_p_{selected_idx}")

                if st.button("🚀 Query Yoast Settings", key=f"btn_set_{selected_idx}"):
                    with st.spinner("Querying Yoast settings..."):
                        set_res = api_integrations.fetch_yoast_settings(set_site, username=set_user, app_password=set_pass)
                        if set_res.get("success"):
                            st.success("✅ Settings received:")
                            st.json(set_res["settings"])
                        else:
                            st.warning(set_res.get("error"))

        # SUBTAB 4: Sync to WordPress
        with y_subtabs[3]:
            st.markdown("#### 📤 One-Click 2-Way Sync: Export Recommendations into Yoast SEO")
            st.caption("Publish your optimized Focus Keyphrase, Title tag, and Meta Description straight back into WordPress via WP REST API + Yoast metadata!")

            sync_col1, sync_col2 = st.columns(2)
            with sync_col1:
                sync_site = st.text_input("WordPress Site URL:", value=st.session_state.get("wp_site_url", "https://yourblog.com"), key=f"sync_site_{selected_idx}")
                sync_pid = st.text_input("WordPress Post ID:", placeholder="e.g. 1042", key=f"sync_pid_{selected_idx}")
                sync_user = st.text_input("WP Admin/Author Username:", value=st.session_state.get("wp_user", ""), key=f"sync_u_{selected_idx}")
                sync_pass = st.text_input("WP Application Password:", value=st.session_state.get("wp_app_pass", ""), type="password", key=f"sync_p_{selected_idx}")

            with sync_col2:
                st.markdown("**Payload Preview to Sync:**")
                sync_fkw = st.text_input("Yoast Focus Keyphrase (`_yoast_wpseo_focuskw`):", value=c_audit.get("keyword", ""), key=f"sync_kw_{selected_idx}")
                sync_title = st.text_input("Yoast SEO Title (`_yoast_wpseo_title`):", value=c_data.get("title", ""), key=f"sync_t_{selected_idx}")
                sync_desc = st.text_area("Yoast Meta Description (`_yoast_wpseo_metadesc`):", value=c_data.get("meta_description", ""), height=85, key=f"sync_d_{selected_idx}")

            if st.button("🚀 Push to WordPress Yoast SEO", type="primary", key=f"btn_push_wp_{selected_idx}", use_container_width=True):
                if not sync_site or not sync_pid or not sync_user or not sync_pass:
                    st.error("Please provide WordPress Site URL, Post ID, Username, and Application Password.")
                else:
                    with st.spinner("Pushing metadata to WordPress & Yoast..."):
                        up_res = api_integrations.update_wp_yoast_meta(
                            sync_site,
                            post_id=sync_pid,
                            username=sync_user,
                            app_password=sync_pass,
                            focus_kw=sync_fkw,
                            seo_title=sync_title,
                            meta_desc=sync_desc
                        )
                        if up_res.get("success"):
                            st.success(f"🎉 {up_res['message']}")
                            st.write(f"Updated Post URL: [{up_res['link']}]({up_res['link']})")
                        else:
                            st.error(up_res.get("error"))

    # -------------------------------------------------------------------------
    # TAB 8: Sitemap Discovery & Link Sentinel
    # -------------------------------------------------------------------------
    with tabs[7]:
        st.subheader("🕷️ Site-Wide XML Sitemap Discovery & Link Sentinel")
        st.caption("Deep sitemap parsing, recursive sitemap index resolution, concurrent broken link checks (404s, 301s, mixed HTTP content), and CMS platform discovery.")

        sm_col1, sm_col2 = st.columns([3, 1])
        with sm_col1:
            sitemap_target = st.text_input(
                "Target Domain or Sitemap URL",
                value=c_data.get("url", ""),
                placeholder="https://example.com/sitemap.xml or https://example.com",
                key=f"sm_target_{selected_idx}"
            )
        with sm_col2:
            max_sm_urls = st.number_input("Max URLs to fetch", min_value=10, max_value=500, value=100, step=25, key=f"sm_max_{selected_idx}")

        sm_cache_key = f"sitemap_{sitemap_target}"
        if st.button("🔎 Discover & Parse XML Sitemap", key=f"btn_sm_{selected_idx}", use_container_width=True):
            with st.spinner("Discovering and parsing XML sitemap..."):
                sm_res = crawler.discover_and_parse_sitemap(sitemap_target, max_urls=max_sm_urls)
                st.session_state[sm_cache_key] = sm_res

        if sm_cache_key in st.session_state:
            sm_res = st.session_state[sm_cache_key]
            if sm_res.get("success"):
                st.success(f"Discovered **{sm_res['total_found']}** URL(s) from sitemap: `{sm_res['sitemap_url']}`")
                if sm_res.get("sitemaps_indexed"):
                    with st.expander(f"Indexed Child Sitemaps ({len(sm_res['sitemaps_indexed'])})"):
                        for csm in sm_res["sitemaps_indexed"]:
                            st.write(f"- `{csm}`")

                sm_df = pd.DataFrame(sm_res["urls"])
                st.dataframe(sm_df, use_container_width=True, hide_index=True)
            else:
                st.error(sm_res.get("error", "Failed to discover XML sitemap"))

        st.divider()

        # Section 2: Concurrent Broken Link Sentinel
        st.markdown("### 🔗 Concurrent Dead Link Sentinel (404s, Redirects, Mixed Content)")
        st.caption("Concurrently verifies every outbound and internal link on this page to prevent SEO crawl waste, broken user journeys, and Google ranking penalties.")

        page_links = c_data.get("links", [])
        st.write(f"Total links on this page: **{len(page_links)}**")

        link_cache_key = f"link_health_{c_data.get('url')}"
        if st.button("🛡️ Audit Link Health for Current Page", key=f"btn_audit_links_{selected_idx}", use_container_width=True):
            with st.spinner(f"Auditing links concurrently (up to 30 URLs)..."):
                lh_res = crawler.audit_links_health(page_links, base_url=c_data.get("url"), max_check=30)
                st.session_state[link_cache_key] = lh_res

        if link_cache_key in st.session_state:
            lh = st.session_state[link_cache_key]
            lh_c1, lh_c2, lh_c3, lh_c4, lh_c5 = st.columns(5)
            with lh_c1:
                st.metric("Total Checked", lh.get("total_checked", 0))
            with lh_c2:
                st.metric("Healthy (200 OK)", lh.get("healthy_count", 0))
            with lh_c3:
                st.metric("Broken (404/Error)", lh.get("broken_count", 0), delta_color="inverse" if lh.get("broken_count", 0) > 0 else "normal")
            with lh_c4:
                st.metric("Redirects (301/302)", lh.get("redirect_count", 0))
            with lh_c5:
                st.metric("Mixed Content (HTTP)", lh.get("mixed_content_count", 0), delta_color="inverse" if lh.get("mixed_content_count", 0) > 0 else "normal")

            if lh.get("broken_links"):
                st.markdown("#### 🚨 Broken Links Detected:")
                b_df = pd.DataFrame(lh["broken_links"])
                st.dataframe(b_df, use_container_width=True, hide_index=True)

            if lh.get("redirects"):
                with st.expander(f"⚠️ Redirected Links ({len(lh['redirects'])})"):
                    st.dataframe(pd.DataFrame(lh["redirects"]), use_container_width=True, hide_index=True)

            if lh.get("mixed_content"):
                with st.expander(f"⚠️ Insecure HTTP Mixed Content Links ({len(lh['mixed_content'])})"):
                    st.dataframe(pd.DataFrame(lh["mixed_content"]), use_container_width=True, hide_index=True)

        st.divider()

        # Section 3: CMS & SEO Plugin Detector
        st.markdown("### 🏷️ CMS & SEO Plugin Architecture Detection")
        st.caption("Identifies the underlying content management platform and installed SEO plugins.")
        cms_cache_key = f"cms_detect_{c_data.get('url')}"

        if st.button("🔎 Detect CMS Platform & Active Plugins", key=f"btn_cms_{selected_idx}"):
            with st.spinner("Analyzing site generator, headers, and meta signatures..."):
                cms_info = api_integrations.detect_cms_platform(c_data.get("url"), html_content=c_data.get("raw_html", ""))
                st.session_state[cms_cache_key] = cms_info

        if cms_cache_key in st.session_state:
            cms_info = st.session_state[cms_cache_key]
            cc1, cc2, cc3 = st.columns(3)
            with cc1:
                st.metric("CMS Platform", cms_info.get("platform", "Unknown"))
            with cc2:
                st.metric("Confidence", f"{cms_info.get('confidence', 0)}%")
            with cc3:
                plugins = cms_info.get("seo_plugins", [])
                st.metric("SEO Plugins", ", ".join(plugins) if plugins else "None Detected")
            st.info(f"**Diagnostic Evidence:** {cms_info.get('evidence', 'No specific signatures identified')}")

    # -------------------------------------------------------------------------
    # TAB 9: Audit History & Score Velocity Progression
    # -------------------------------------------------------------------------
    with tabs[8]:
        st.subheader("📈 Historical SEO Velocity & Score Progression")
        st.caption("Persistent SQLite tracking (`blogguard_history.db`) records every audit iteration, score delta, and AEO velocity over time.")

        # Current URL velocity tracking
        curr_url = c_data.get("url", "")
        vel_data = db_history.get_url_velocity(curr_url)

        if vel_data.get("total_audits", 0) > 1:
            v1, v2, v3, v4 = st.columns(4)
            delta_score = vel_data.get("score_delta", 0)
            delta_str = f"+{delta_score}" if delta_score > 0 else f"{delta_score}"
            with v1:
                st.metric("Total Revisions Audited", vel_data.get("total_audits", 0))
            with v2:
                st.metric("Latest Score", f"{vel_data.get('latest_score', 0)}/100", f"{delta_str} pts vs baseline")
            with v3:
                st.metric("First Recorded Score", f"{vel_data.get('first_score', 0)}/100")
            with v4:
                st.metric("AEO Readiness Score", f"{vel_data.get('latest_aeo', 0)}/100")

            # Progression Chart
            st.markdown("#### 📊 Score Velocity Progression Over Time")
            history_rows = vel_data.get("history", [])
            if history_rows:
                chart_df = pd.DataFrame([
                    {
                        "Timestamp": h["timestamp"],
                        "Overall Score": h["overall_score"],
                        "AEO Score": h["aeo_score"] or 0,
                    }
                    for h in history_rows
                ])
                st.line_chart(chart_df.set_index("Timestamp"), use_container_width=True)
        else:
            st.info("ℹ️ Only 1 audit recorded for this URL so far. Run subsequent audits or re-audit after making edits to view score progression trends.")

        st.divider()

        # Complete Database Audit Log
        st.markdown("### 🗄️ All Historical Audits Database (`blogguard_history.db`)")
        all_snaps = db_history.get_audit_history(limit=50)

        if all_snaps:
            snap_df = pd.DataFrame([
                {
                    "ID": s["id"],
                    "Timestamp": s["timestamp"],
                    "URL": s["url"],
                    "Title": s["title"][:40] if s["title"] else "",
                    "Keyword": s["keyword"],
                    "Score": s["overall_score"],
                    "AEO": s["aeo_score"],
                    "Words": s["word_count"],
                    "Flesch": round(s["flesch_reading_ease"], 1) if s["flesch_reading_ease"] else 0,
                }
                for s in all_snaps
            ])
            st.dataframe(snap_df, use_container_width=True, hide_index=True)

            del_col1, del_col2 = st.columns([3, 1])
            with del_col2:
                if st.button("🗑️ Clear Entire History DB", key=f"btn_clear_hist_{selected_idx}", help="Reset the local SQLite audit history"):
                    db_history.clear_all_history()
                    st.success("Database cleared!")
                    st.rerun()
        else:
            st.write("No historical snapshots saved yet.")

    # -------------------------------------------------------------------------
    # TAB 10: Google SERP Intelligence (SerpApi)
    # -------------------------------------------------------------------------
    with tabs[9]:
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
    # TAB 11: Multi-LLM AI Copilot
    # -------------------------------------------------------------------------
    with tabs[10]:
        st.subheader(f"🧠 {ai_provider} AI Editorial Director")
        st.caption(f"Active AI Provider: **{ai_provider}** | Model: `{ai_model}`. Switch providers and models anytime in the left sidebar.")

        if not ai_key:
            st.warning(f"Please enter your {ai_provider} API Key in the left sidebar to unlock the AI Copilot.")
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

            cache_key = f"{c_data['title']}-{ai_model}"

            if run_ai_audit_btn:
                with st.spinner(f"Querying {ai_provider} ({ai_model})..."):
                    ai_res = api_integrations.generate_deepseek_audit(c_data, c_audit, api_key=ai_key, model=ai_model, provider=selected_provider_slug)
                    if ai_res.get("success"):
                        st.session_state.ai_audit_cache[f"{cache_key}-audit"] = ai_res
                    else:
                        st.error(ai_res.get("error"))

            if run_ai_faq_btn:
                with st.spinner(f"Generating JSON-LD Schema with {ai_provider} ({ai_model})..."):
                    paa_q = current.get("serp", {}).get("people_also_ask", []) if current.get("serp") else []
                    faq_res = api_integrations.generate_ai_faq_schema(c_data, paa_q, api_key=ai_key, model=ai_model, provider=selected_provider_slug)
                    if faq_res.get("success"):
                        st.session_state.ai_audit_cache[f"{cache_key}-faq"] = faq_res
                    else:
                        st.error(faq_res.get("error"))

            if run_ai_titles_btn:
                with st.spinner(f"Generating CTR optimized titles with {ai_provider}..."):
                    t_prompt = f"Provide 5 high-converting, high-CTR SEO title tags and 3 compelling meta descriptions for an article titled '{c_data['title']}' targeting keyword '{c_audit['keyword']}'."
                    t_res = api_integrations.query_ai_copilot(t_prompt, provider=selected_provider_slug, api_key=ai_key, model=ai_model)
                    if t_res.get("success"):
                        st.session_state.ai_audit_cache[f"{cache_key}-titles"] = t_res
                    else:
                        st.error(t_res.get("error"))

            if run_ai_read_btn:
                with st.spinner(f"Generating conversational readability rewrite with {ai_provider} (Flesch 65–75)..."):
                    r_res = api_integrations.rewrite_for_readability(c_data, api_key=ai_key, model=ai_model, provider=selected_provider_slug)
                    if r_res.get("success"):
                        st.session_state.ai_audit_cache[f"{cache_key}-readability"] = r_res
                    else:
                        st.error(r_res.get("error"))

            if run_ai_verify_btn:
                with st.spinner(f"Forensically verifying content, facts, and alignment with {ai_provider}..."):
                    v_res = api_integrations.verify_content_and_facts(c_data, api_key=ai_key, model=ai_model, provider=selected_provider_slug)
                    if v_res.get("success"):
                        st.session_state.ai_audit_cache[f"{cache_key}-verification"] = v_res
                    else:
                        st.error(v_res.get("error"))

            # Display cached AI outputs
            if f"{cache_key}-audit" in st.session_state.ai_audit_cache:
                st.markdown(f"### 📋 {ai_provider} Strategic Editorial Verdict")
                res = st.session_state.ai_audit_cache[f"{cache_key}-audit"]
                if res.get("reasoning"):
                    with st.expander(f"💭 View {ai_provider} Reasoning Process (CoT)"):
                        st.write(res["reasoning"])
                st.markdown(res["content"])

            if f"{cache_key}-faq" in st.session_state.ai_audit_cache:
                st.markdown("### 📋 Generated JSON-LD FAQPage Schema")
                st.code(st.session_state.ai_audit_cache[f"{cache_key}-faq"]["content"], language="json")

            if f"{cache_key}-titles" in st.session_state.ai_audit_cache:
                st.markdown("### 🎯 High-CTR Titles & Meta Descriptions")
                st.markdown(st.session_state.ai_audit_cache[f"{cache_key}-titles"]["content"])

            if f"{cache_key}-readability" in st.session_state.ai_audit_cache:
                st.markdown(f"### 🪄 {ai_provider} Conversational Readability Rewrite (Flesch 65–75)")
                res = st.session_state.ai_audit_cache[f"{cache_key}-readability"]
                if res.get("reasoning"):
                    with st.expander(f"💭 View {ai_provider} Reasoning Process (CoT)"):
                        st.write(res["reasoning"])
                st.markdown(res["content"])

            if f"{cache_key}-verification" in st.session_state.ai_audit_cache:
                st.markdown(f"### 🛡️ Deep Forensic & Factual Alignment Report ({ai_provider})")
                res = st.session_state.ai_audit_cache[f"{cache_key}-verification"]
                if res.get("reasoning"):
                    with st.expander(f"💭 View {ai_provider} Reasoning Process (CoT)"):
                        st.write(res["reasoning"])
                st.markdown(res["content"])

    # -------------------------------------------------------------------------
    # TAB 12: Core Web Vitals & PageSpeed
    # -------------------------------------------------------------------------
    with tabs[11]:
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
    # TAB 13: SERP & Social Preview
    # -------------------------------------------------------------------------
    with tabs[12]:
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
    # TAB 14: Content Hierarchy
    # -------------------------------------------------------------------------
    with tabs[13]:
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
    # TAB 15: Media & Links
    # -------------------------------------------------------------------------
    with tabs[14]:
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
    # TAB 16: Checklist & Export
    # -------------------------------------------------------------------------
    with tabs[15]:
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
            html_report = export_helper.generate_html_report(
                c_data,
                c_audit,
                serp_data=current.get("serp"),
                competitor_gap=c_audit.get("competitor_gap")
            )
            st.download_button(
                label="📑 Download Executive HTML/PDF Report",
                data=html_report,
                file_name=f"blogguard_report_{c_data['title'][:20].replace(' ', '_')}.html",
                mime="text/html",
                use_container_width=True
            )

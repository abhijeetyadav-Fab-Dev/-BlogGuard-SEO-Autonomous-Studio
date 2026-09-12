import html


def generate_html_report(article_data, audit_results, serp_data=None, competitor_gap=None):
    title = html.escape(article_data.get("title", "Untitled"))
    url = html.escape(article_data.get("url", "N/A"))
    keyword = html.escape(audit_results.get("keyword", "N/A"))
    writer = html.escape(audit_results.get("writer", "N/A"))
    score = audit_results.get("overall_score", 0)
    status = html.escape(audit_results.get("status", "N/A"))
    word_count = audit_results.get("word_count", 0)
    reading_time = audit_results.get("reading_time_min", 0)
    readability = audit_results.get("readability", {})
    reading_ease = readability.get("flesch_reading_ease", 0)
    grade = readability.get("flesch_kincaid_grade", 0)

    aeo = audit_results.get("aeo", {})
    aeo_score = aeo.get("aeo_score", 0)
    aeo_verdict = html.escape(aeo.get("verdict", "N/A"))

    yoast = audit_results.get("yoast", {})
    yoast_seo_badge = yoast.get("seo", {}).get("badge", "⚪")
    yoast_seo_verdict = yoast.get("seo", {}).get("verdict", "N/A")
    yoast_read_badge = yoast.get("readability", {}).get("badge", "⚪")
    yoast_read_verdict = yoast.get("readability", {}).get("verdict", "N/A")

    # Pillar scores rows
    scores_html = ""
    for pillar, pscore in audit_results.get("scores", {}).items():
        color = "#10b981" if pscore >= 80 else ("#f59e0b" if pscore >= 60 else "#ef4444")
        scores_html += f"""
        <div style="margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; font-weight: 600; font-size: 14px; margin-bottom: 4px;">
                <span>{html.escape(pillar)}</span>
                <span style="color: {color};">{pscore}/100</span>
            </div>
            <div style="background: #e2e8f0; border-radius: 6px; height: 8px; overflow: hidden;">
                <div style="background: {color}; width: {pscore}%; height: 100%;"></div>
            </div>
        </div>
        """

    # Issues
    issues_html = ""
    for issue in audit_results.get("issues", []):
        sev = issue.get("severity", "info")
        badge_bg = "#fee2e2" if sev == "critical" else ("#fef3c7" if sev == "warning" else "#e0f2fe")
        badge_color = "#991b1b" if sev == "critical" else ("#92400e" if sev == "warning" else "#075985")
        issues_html += f"""
        <div style="border-left: 4px solid {badge_color}; background: #f8fafc; padding: 12px 16px; margin-bottom: 12px; border-radius: 0 8px 8px 0;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
                <span style="background: {badge_bg}; color: {badge_color}; font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; text-transform: uppercase;">{sev}</span>
                <strong style="color: #1e293b; font-size: 15px;">{html.escape(issue.get('title', ''))}</strong>
            </div>
            <p style="margin: 4px 0; color: #475569; font-size: 13px;">{html.escape(issue.get('detail', ''))}</p>
            <div style="margin-top: 6px; font-size: 13px; color: #0284c7; font-weight: 500;">
                💡 <strong>Action:</strong> {html.escape(issue.get('fix', ''))}
            </div>
        </div>
        """

    # Competitor Benchmarks if available
    bench_html = ""
    if competitor_gap and competitor_gap.get("benchmarks"):
        bm = competitor_gap["benchmarks"]
        bench_html += f"""
        <h2 style="color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px; margin-top: 30px;">Competitor Semantic Gap Benchmark</h2>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 24px;">
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; text-align: center;">
                <div style="font-size: 12px; color: #64748b; font-weight: 600;">Word Count vs Competitors</div>
                <div style="font-size: 20px; font-weight: 700; color: #0f172a; margin: 4px 0;">{bm.get('word_count', {}).get('target', 0):,} vs {bm.get('word_count', {}).get('competitor_avg', 0):,}</div>
                <div style="font-size: 12px; font-weight: 600; color: #2563eb;">{bm.get('word_count', {}).get('status', '')}</div>
            </div>
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; text-align: center;">
                <div style="font-size: 12px; color: #64748b; font-weight: 600;">Images vs Competitors</div>
                <div style="font-size: 20px; font-weight: 700; color: #0f172a; margin: 4px 0;">{bm.get('images', {}).get('target', 0)} vs {bm.get('images', {}).get('competitor_avg', 0)}</div>
                <div style="font-size: 12px; font-weight: 600; color: #2563eb;">{bm.get('images', {}).get('status', '')}</div>
            </div>
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; text-align: center;">
                <div style="font-size: 12px; color: #64748b; font-weight: 600;">Citations vs Competitors</div>
                <div style="font-size: 20px; font-weight: 700; color: #0f172a; margin: 4px 0;">{bm.get('citations', {}).get('target', 0)} vs {bm.get('citations', {}).get('competitor_avg', 0)}</div>
                <div style="font-size: 12px; font-weight: 600; color: #2563eb;">{bm.get('citations', {}).get('status', '')}</div>
            </div>
        </div>
        """

    # Competitors SERP list
    comp_html = ""
    if serp_data and serp_data.get("competitors"):
        comp_html += "<h2 style='color: #0f172a; margin-top: 30px; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;'>Top Google SERP Competitors</h2>"
        for comp in serp_data.get("competitors", [])[:5]:
            comp_html += f"""
            <div style="padding: 10px 14px; background: #fff; border: 1px solid #e2e8f0; border-radius: 6px; margin-bottom: 8px;">
                <div style="font-weight: 600; font-size: 14px; color: #1d4ed8;">#{comp.get('position')} {html.escape(comp.get('title', ''))}</div>
                <div style="font-size: 12px; color: #059669; margin: 2px 0;">{html.escape(comp.get('displayed_link', ''))}</div>
                <div style="font-size: 13px; color: #4b5563;">{html.escape(comp.get('snippet', ''))}</div>
            </div>
            """

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>BlogGuard SEO Executive Audit - {title}</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; line-height: 1.5; color: #334155; background: #f1f5f9; margin: 0; padding: 30px; }}
    .container {{ max-width: 900px; margin: 0 auto; background: #fff; border-radius: 12px; padding: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }}
    .header {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 20px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: flex-start; }}
    .badge {{ padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 13px; }}
    .metric-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 30px; }}
    .metric-box {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; text-align: center; }}
    .metric-val {{ font-size: 22px; font-weight: 700; color: #0f172a; margin-top: 4px; }}
    .metric-lbl {{ font-size: 11px; color: #64748b; text-transform: uppercase; font-weight: 600; }}
    .status-ribbon {{ display: flex; gap: 12px; background: #f1f5f9; padding: 12px 16px; border-radius: 8px; margin-bottom: 24px; font-size: 13px; }}
    @media print {{
        body {{ padding: 0; background: #fff; }}
        .container {{ box-shadow: none; max-width: 100%; padding: 0; }}
    }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <div>
            <div style="font-size: 13px; font-weight: 700; color: #3b82f6; text-transform: uppercase; letter-spacing: 0.5px;">🛡️ BlogGuard SEO Intelligence Report</div>
            <h1 style="color: #0f172a; margin: 6px 0 8px 0; font-size: 26px;">{title}</h1>
            <div style="font-size: 13px; color: #64748b;">URL: {url} | Focus Keyword: <strong>{keyword}</strong> | Author: <strong>{writer}</strong></div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 38px; font-weight: 800; color: #2563eb;">{score}<span style="font-size: 20px; color: #94a3b8;">/100</span></div>
            <div style="font-size: 13px; font-weight: 600; color: #475569;">{status}</div>
        </div>
    </div>

    <div class="status-ribbon">
        <div><strong>🌐 AEO Citation Readiness:</strong> {aeo_score}/100 ({aeo_verdict})</div>
        <div><strong>🚦 Yoast SEO:</strong> {yoast_seo_badge} {yoast_seo_verdict}</div>
        <div><strong>📖 Yoast Readability:</strong> {yoast_read_badge} {yoast_read_verdict}</div>
    </div>

    <div class="metric-grid">
        <div class="metric-box">
            <div class="metric-lbl">Total Words</div>
            <div class="metric-val">{word_count:,}</div>
        </div>
        <div class="metric-box">
            <div class="metric-lbl">Reading Time</div>
            <div class="metric-val">{reading_time} min</div>
        </div>
        <div class="metric-box">
            <div class="metric-lbl">Reading Ease</div>
            <div class="metric-val">{reading_ease}</div>
        </div>
        <div class="metric-box">
            <div class="metric-lbl">Grade Level</div>
            <div class="metric-val">Grade {grade}</div>
        </div>
        <div class="metric-box">
            <div class="metric-lbl">AEO Citation</div>
            <div class="metric-val">{aeo_score}/100</div>
        </div>
    </div>

    <h2 style="color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">7-Pillar SEO Performance Matrix</h2>
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 30px;">
        {scores_html}
    </div>

    {bench_html}

    <h2 style="color: #0f172a; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">Prioritized Action Items ({len(audit_results.get('issues', []))})</h2>
    <div>
        {issues_html if issues_html else "<p style='color: #10b981; font-weight: 600;'>No critical issues detected!</p>"}
    </div>

    {comp_html}

    <div style="margin-top: 40px; padding-top: 16px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8; text-align: center;">
        Generated autonomously by BlogGuard SEO Platform • Multi-LLM AI & Google SERP Assisted
    </div>
</div>
</body>
</html>
"""
    return full_html

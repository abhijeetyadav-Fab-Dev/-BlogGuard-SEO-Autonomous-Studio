import os
import json
import requests

SERPAPI_URL = "https://serpapi.com/search"
PAGESPEED_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
DEEPSEEK_DEFAULT_URL = "https://api.deepseek.com/chat/completions"


# ---------------------------------------------------------------------------
# 1. Google SerpApi Live Competitor & PAA Intelligence
# ---------------------------------------------------------------------------
def fetch_serp_intelligence(keyword, api_key=None, num=10):
    api_key = api_key or os.environ.get("SERPAPI_KEY")
    if not api_key:
        return {"error": "No SerpApi Key provided. Set SERPAPI_KEY in your environment or enter it in the sidebar."}

    params = {
        "q": keyword,
        "engine": "google",
        "api_key": api_key,
        "num": num,
    }

    try:
        res = requests.get(SERPAPI_URL, params=params, timeout=15)
        if res.status_code != 200:
            return {"error": f"SerpApi returned status {res.status_code}: {res.text[:200]}"}

        data = res.json()
        organic = data.get("organic_results", [])
        competitors = []
        for item in organic[:num]:
            competitors.append({
                "position": item.get("position"),
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "displayed_link": item.get("displayed_link", ""),
                "snippet": item.get("snippet", ""),
            })

        paa = []
        for question in data.get("related_questions", []):
            paa.append({
                "question": question.get("question", ""),
                "snippet": question.get("snippet", ""),
                "title": question.get("title", ""),
                "link": question.get("link", ""),
            })

        related_searches = [r.get("query", "") for r in data.get("related_searches", [])]

        return {
            "success": True,
            "keyword": keyword,
            "competitors": competitors,
            "people_also_ask": paa,
            "related_searches": related_searches,
            "total_results": data.get("search_information", {}).get("total_results", "N/A"),
        }
    except Exception as e:
        return {"error": f"SerpApi connection failed: {str(e)}"}


# ---------------------------------------------------------------------------
# 2. Google PageSpeed Insights & Core Web Vitals
# ---------------------------------------------------------------------------
def fetch_pagespeed_insights(url, api_key=None, strategy="mobile"):
    params = {
        "url": url,
        "strategy": strategy,
    }
    if api_key:
        params["key"] = api_key

    try:
        res = requests.get(PAGESPEED_URL, params=params, timeout=25)
        if res.status_code != 200:
            return {
                "error": f"Google PageSpeed returned status {res.status_code}. (Note: Google free tier has IP rate limits; provide an API key for guaranteed throughput)."
            }

        data = res.json()
        lighthouse = data.get("lighthouseResult", {})
        categories = lighthouse.get("categories", {})
        audits = lighthouse.get("audits", {})

        perf_score = round(categories.get("performance", {}).get("score", 0) * 100)
        seo_score = round(categories.get("seo", {}).get("score", 0) * 100)

        # Core Web Vitals
        fcp = audits.get("first-contentful-paint", {}).get("displayValue", "N/A")
        lcp = audits.get("largest-contentful-paint", {}).get("displayValue", "N/A")
        cls_val = audits.get("cumulative-layout-shift", {}).get("displayValue", "N/A")
        tbt = audits.get("total-blocking-time", {}).get("displayValue", "N/A")
        speed_index = audits.get("speed-index", {}).get("displayValue", "N/A")

        # Top diagnostic opportunities
        opportunities = []
        for audit_id, audit in audits.items():
            if audit.get("details", {}).get("type") == "opportunity" and audit.get("score", 1.0) < 0.9:
                opportunities.append({
                    "title": audit.get("title", ""),
                    "savings": audit.get("displayValue", ""),
                    "description": audit.get("description", ""),
                })

        return {
            "success": True,
            "strategy": strategy,
            "perf_score": perf_score,
            "seo_score": seo_score,
            "fcp": fcp,
            "lcp": lcp,
            "cls": cls_val,
            "tbt": tbt,
            "speed_index": speed_index,
            "opportunities": opportunities[:5],
        }
    except Exception as e:
        return {"error": f"PageSpeed API connection error: {str(e)}"}


# ---------------------------------------------------------------------------
# 3. DeepSeek AI Strategic Copilot
# ---------------------------------------------------------------------------
def query_deepseek_copilot(prompt, api_key, model="deepseek-chat", base_url=DEEPSEEK_DEFAULT_URL, system_role=None):
    if not api_key:
        return {"error": "DeepSeek API Key is required. Please provide your key in the sidebar."}

    system_role = system_role or (
        "You are an Elite SEO Strategist and Head of Editorial at a top publication. "
        "Your role is to conduct rigorous, actionable, high-ROI audits and produce publish-ready SEO assets."
    )

    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_role},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5,
    }

    try:
        res = requests.post(base_url, headers=headers, json=payload, timeout=60)
        if res.status_code != 200:
            return {"error": f"DeepSeek API error {res.status_code}: {res.text[:300]}"}

        data = res.json()
        content = data["choices"][0]["message"]["content"]
        reasoning = data["choices"][0]["message"].get("reasoning_content")
        return {
            "success": True,
            "content": content,
            "reasoning": reasoning,
            "model": model,
            "usage": data.get("usage", {}),
        }
    except Exception as e:
        return {"error": f"DeepSeek request failed: {str(e)}"}


def generate_deepseek_audit(article_data, audit_results, api_key, model="deepseek-chat"):
    title = article_data.get("title", "")
    keyword = audit_results.get("keyword", "")
    word_count = audit_results.get("word_count", 0)
    score = audit_results.get("overall_score", 0)
    headings = [h["text"] for h in article_data.get("headings", [])[:15]]
    sample_text = article_data.get("clean_text", "")[:3500]

    prompt = f"""
Please perform a rigorous Executive SEO & Editorial Audit of this blog post.

CONTEXT:
- Title: {title}
- Target Focus Keyword: {keyword}
- Word Count: {word_count}
- Calculated BlogGuard Score: {score}/100
- Table of Headings: {json.dumps(headings)}
- Content Excerpt:
\"\"\"{sample_text}\"\"\"

TASK:
Provide a structured, executive-level report with these 4 sections:
1. 🎯 Search Intent & Value Proposition: Does this satisfy informational, commercial, or transactional search intent? Is there immediate answer delivery (Search Generative Experience/AI Overview ready)?
2. 🔍 Content Depth & Gaps: What crucial angles, data points, or counter-perspectives are missing compared to top rankers?
3. ⚡ CTR & Hook Optimization: Critique the current title and opening hook. Give 3 better, high-CTR headline alternatives.
4. 🚀 Top 3 High-Impact Action Items: Specific, numbered steps the writer/editor should take immediately to rank #1.
"""
    return query_deepseek_copilot(prompt, api_key, model=model)


def generate_ai_faq_schema(article_data, paa_questions, api_key, model="deepseek-chat"):
    title = article_data.get("title", "")
    sample_text = article_data.get("clean_text", "")[:3000]
    questions_str = "\n".join([f"- {p['question']}" for p in paa_questions[:6]]) if paa_questions else "None provided"

    prompt = f"""
Generate a complete, valid JSON-LD FAQPage Schema for this article.

Article Title: {title}
Google 'People Also Ask' Questions for inspiration:
{questions_str}

Content Context:
\"\"\"{sample_text}\"\"\"

Generate 4 to 5 relevant Frequently Asked Questions and accurate, concise answers based on the content.
Return ONLY valid JSON inside a ```json ... ``` code block containing the <script type="application/ld+json"> content.
"""
    return query_deepseek_copilot(prompt, api_key, model=model)


def rewrite_for_readability(article_data, api_key, model="deepseek-chat"):
    title = article_data.get("title", "")
    sample_text = article_data.get("clean_text", "")[:4000]

    prompt = f"""
You are an expert Copy Editor specializing in high-engagement, plain-language web writing.

The following blog post currently has a low Flesch Reading Ease score (difficult / college level).
Your task is to rewrite key complex sections of the text to achieve a Flesch Reading Ease score of 65–75 (conversational Grade 7-8 web standard).

SOURCE ARTICLE:
Title: {title}
Content Excerpt:
\"\"\"{sample_text}\"\"\"

REWRITE MANDATES:
1. Shorten sentences: Maximum 15–18 words per sentence. Split every compound or run-on sentence.
2. Cut corporate jargon & academic fluff: Replace multi-syllable terms (e.g. 'utilize', 'facilitate', 'subsequently', 'methodology') with simple, everyday verbs ('use', 'help', 'then', 'way').
3. Active Voice: Shift passive constructions to direct, active voice.
4. Retention formatting: Use bullet points, bold key insights, and conversational transition phrases.
5. Preserve topical authority: Retain all core technical facts, SEO keywords, and key arguments.

OUTPUT FORMAT:
Provide:
1. 💡 Top 3 Readability Flaws in the Original (with specific word/phrase callouts)
2. ✍️ Full Conversational Rewrite of the Key Sections (Grade 7-8 reading level)
3. 📊 Estimated Readability Boost (Before vs. After comparison)
"""
    return query_deepseek_copilot(prompt, api_key, model=model)

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


def verify_content_and_facts(article_data, api_key, model="deepseek-chat"):
    title = article_data.get("title", "")
    sample_text = article_data.get("clean_text", "")[:4500]

    prompt = f"""
You are a Lead Fact-Checker, Senior Proofreader, and Head of Content Quality.
Conduct an exhaustive, forensic verification of this blog post covering Grammar, Sentence Structure, Clarity, and Content-to-Information Alignment.

SOURCE ARTICLE:
Title: {title}
Content:
\"\"\"{sample_text}\"\"\"

AUDIT REQUIREMENTS:
1. 🎯 Content & Information Alignment Check:
   - Does the content actually deliver on the promise, angle, and expectation set in the Title?
   - Is there any title-content drift, bait-and-switch, or missing information promised in the headline or intro?
2. ⚠️ Logical & Factual Contradiction Scan:
   - Are there internal contradictions between different paragraphs, statistics, dates, or recommendations?
   - Point out any unsupported factual leaps or logical fallacies.
3. ✍️ Grammar, Syntax & Sentence Errors:
   - Identify specific grammatical errors, subject-verb disagreements, awkward idioms, punctuation blunders, or dangling modifiers.
   - For every error, provide the EXACT flawed sentence and the CORRECTED version.
4. 👓 Cognitive Clarity & Comprehension Review:
   - Point out any dense, vague, or muddy sentences that confuse the reader.
   - Provide a crystal-clear rewrite for the 3 most confusing passages.
5. 📊 Verdict & Readiness Score:
   - Provide an overall Clarity & Alignment Score (0-100) and an editorial sign-off verdict.
"""
    return query_deepseek_copilot(prompt, api_key, model=model)


# ---------------------------------------------------------------------------
# 4. Yoast SEO REST API & WordPress Integration Suite
# ---------------------------------------------------------------------------
def _normalize_site_url(site_url):
    if not site_url:
        return ""
    site_url = site_url.strip()
    if not site_url.startswith(("http://", "https://")):
        site_url = "https://" + site_url
    return site_url.rstrip("/")


def fetch_yoast_head(target_url, site_base_url=None, timeout=15):
    """
    Queries Yoast SEO's primary public REST API endpoint:
    GET /wp-json/yoast/v1/get_head?url={target_url}

    Returns full HTML <head> blob, structured JSON metadata (title, meta desc,
    canonical, robots, OpenGraph, Twitter, schema graph), and HTTP status.
    """
    if not target_url:
        return {"success": False, "error": "No target URL provided."}

    target_url = target_url.strip()
    if not target_url.startswith(("http://", "https://")):
        target_url = "https://" + target_url

    if not site_base_url:
        from urllib.parse import urlparse
        p = urlparse(target_url)
        site_base_url = f"{p.scheme}://{p.netloc}"

    base_url = _normalize_site_url(site_base_url)
    endpoint = f"{base_url}/wp-json/yoast/v1/get_head"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }

    try:
        res = requests.get(endpoint, params={"url": target_url}, headers=headers, timeout=timeout)
        if res.status_code == 200:
            data = res.json()
            head_json = data.get("json", {})
            schema_graph = head_json.get("schema", {}).get("@graph", []) if isinstance(head_json, dict) else []
            return {
                "success": True,
                "endpoint": res.url,
                "status_code": res.status_code,
                "html": data.get("html", ""),
                "json": head_json,
                "title": head_json.get("title", "") if isinstance(head_json, dict) else "",
                "description": head_json.get("description", "") if isinstance(head_json, dict) else "",
                "robots": head_json.get("robots", {}) if isinstance(head_json, dict) else {},
                "canonical": head_json.get("canonical", "") if isinstance(head_json, dict) else "",
                "og": {
                    "title": head_json.get("og_title", ""),
                    "description": head_json.get("og_description", ""),
                    "image": head_json.get("og_image", []),
                    "url": head_json.get("og_url", ""),
                    "type": head_json.get("og_type", ""),
                    "site_name": head_json.get("og_site_name", ""),
                } if isinstance(head_json, dict) else {},
                "twitter": {
                    "card": head_json.get("twitter_card", ""),
                    "title": head_json.get("twitter_title", ""),
                    "description": head_json.get("twitter_description", ""),
                    "image": head_json.get("twitter_image", ""),
                } if isinstance(head_json, dict) else {},
                "schema_graph": schema_graph,
            }
        elif res.status_code == 404:
            return {
                "success": False,
                "status_code": 404,
                "endpoint": endpoint,
                "error": f"Yoast SEO get_head endpoint returned 404. Target site '{base_url}' may not have Yoast SEO REST API enabled or post is not yet indexed by Yoast.",
            }
        else:
            return {
                "success": False,
                "status_code": res.status_code,
                "endpoint": endpoint,
                "error": f"Yoast API returned HTTP {res.status_code}: {res.text[:250]}",
            }
    except Exception as e:
        return {
            "success": False,
            "status_code": 0,
            "endpoint": endpoint,
            "error": f"Failed to connect to Yoast get_head endpoint: {str(e)}",
        }


def fetch_wp_yoast_posts(site_base_url, search=None, slug=None, post_id=None, per_page=5, timeout=15):
    """
    Queries WordPress REST API for Posts with embedded Yoast data:
    GET /wp-json/wp/v2/posts
    """
    base_url = _normalize_site_url(site_base_url)
    if not base_url:
        return {"success": False, "error": "No WordPress Site URL provided."}

    if post_id:
        endpoint = f"{base_url}/wp-json/wp/v2/posts/{post_id}"
        params = {}
    else:
        endpoint = f"{base_url}/wp-json/wp/v2/posts"
        params = {"per_page": min(per_page, 20)}
        if search:
            params["search"] = search
        if slug:
            params["slug"] = slug

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    try:
        res = requests.get(endpoint, params=params, headers=headers, timeout=timeout)
        if res.status_code == 200:
            raw_data = res.json()
            posts_list = [raw_data] if isinstance(raw_data, dict) else raw_data

            formatted_posts = []
            for p in posts_list:
                y_json = p.get("yoast_head_json") or {}
                formatted_posts.append({
                    "id": p.get("id"),
                    "slug": p.get("slug"),
                    "link": p.get("link"),
                    "title": p.get("title", {}).get("rendered", "") if isinstance(p.get("title"), dict) else str(p.get("title", "")),
                    "date": p.get("date"),
                    "status": p.get("status"),
                    "has_yoast": bool(y_json or p.get("yoast_head")),
                    "yoast_title": y_json.get("title", "") if isinstance(y_json, dict) else "",
                    "yoast_description": y_json.get("description", "") if isinstance(y_json, dict) else "",
                    "yoast_robots": y_json.get("robots", {}) if isinstance(y_json, dict) else {},
                    "yoast_canonical": y_json.get("canonical", "") if isinstance(y_json, dict) else "",
                    "yoast_head": p.get("yoast_head", ""),
                    "yoast_head_json": y_json,
                })

            return {
                "success": True,
                "endpoint": res.url,
                "count": len(formatted_posts),
                "posts": formatted_posts,
            }
        else:
            return {
                "success": False,
                "status_code": res.status_code,
                "error": f"WordPress Posts API returned HTTP {res.status_code}: {res.text[:200]}",
            }
    except Exception as e:
        return {"success": False, "error": f"WP Posts API request failed: {str(e)}"}


def fetch_yoast_statistics(site_base_url, username=None, app_password=None, timeout=15):
    """
    Queries Yoast SEO indexing statistics endpoint:
    GET /wp-json/yoast/v1/statistics
    Requires WordPress authentication (Application Passwords).
    """
    base_url = _normalize_site_url(site_base_url)
    if not base_url:
        return {"success": False, "error": "No WordPress Site URL provided."}

    endpoint = f"{base_url}/wp-json/yoast/v1/statistics"
    auth = (username, app_password) if (username and app_password) else None

    try:
        res = requests.get(endpoint, auth=auth, timeout=timeout)
        if res.status_code == 200:
            return {
                "success": True,
                "endpoint": endpoint,
                "statistics": res.json(),
            }
        elif res.status_code == 401:
            return {
                "success": False,
                "status_code": 401,
                "error": "Authentication required. Yoast statistics endpoint requires WordPress credentials (Username + Application Password).",
            }
        else:
            return {
                "success": False,
                "status_code": res.status_code,
                "error": f"Yoast statistics returned HTTP {res.status_code}: {res.text[:200]}",
            }
    except Exception as e:
        return {"success": False, "error": f"Yoast statistics request failed: {str(e)}"}


def fetch_yoast_settings(site_base_url, username=None, app_password=None, timeout=15):
    """
    Queries Yoast SEO configuration settings endpoint:
    GET /wp-json/yoast/v1/settings
    """
    base_url = _normalize_site_url(site_base_url)
    if not base_url:
        return {"success": False, "error": "No WordPress Site URL provided."}

    endpoint = f"{base_url}/wp-json/yoast/v1/settings"
    auth = (username, app_password) if (username and app_password) else None

    try:
        res = requests.get(endpoint, auth=auth, timeout=timeout)
        if res.status_code == 200:
            return {
                "success": True,
                "endpoint": endpoint,
                "settings": res.json(),
            }
        else:
            return {
                "success": False,
                "status_code": res.status_code,
                "error": f"Yoast settings returned HTTP {res.status_code}: {res.text[:200]}",
            }
    except Exception as e:
        return {"success": False, "error": f"Yoast settings request failed: {str(e)}"}


def update_wp_yoast_meta(site_base_url, post_id, username, app_password, focus_kw=None, seo_title=None, meta_desc=None, timeout=15):
    """
    Direct 2-Way Sync: Updates Yoast SEO post metadata on WordPress:
    POST /wp-json/wp/v2/posts/{post_id}
    Updates _yoast_wpseo_focuskw, _yoast_wpseo_title, and _yoast_wpseo_metadesc
    """
    base_url = _normalize_site_url(site_base_url)
    if not base_url or not post_id or not username or not app_password:
        return {
            "success": False,
            "error": "Missing required fields: site_base_url, post_id, username, and app_password are required to sync to WordPress."
        }

    endpoint = f"{base_url}/wp-json/wp/v2/posts/{post_id}"
    meta_payload = {}
    if focus_kw is not None:
        meta_payload["_yoast_wpseo_focuskw"] = focus_kw.strip()
    if seo_title is not None:
        meta_payload["_yoast_wpseo_title"] = seo_title.strip()
    if meta_desc is not None:
        meta_payload["_yoast_wpseo_metadesc"] = meta_desc.strip()

    if not meta_payload:
        return {"success": False, "error": "No Yoast meta fields provided to update."}

    headers = {"Content-Type": "application/json"}
    auth = (username, app_password)

    try:
        res = requests.post(
            endpoint,
            auth=auth,
            headers=headers,
            json={"meta": meta_payload},
            timeout=timeout
        )
        if res.status_code in (200, 201):
            updated_post = res.json()
            return {
                "success": True,
                "post_id": post_id,
                "link": updated_post.get("link", ""),
                "synced_meta": meta_payload,
                "message": f"Successfully updated Yoast SEO metadata for Post #{post_id} on {base_url}!",
            }
        else:
            return {
                "success": False,
                "status_code": res.status_code,
                "error": f"WordPress update failed with HTTP {res.status_code}: {res.text[:250]}",
            }
    except Exception as e:
        return {"success": False, "error": f"Failed to sync Yoast meta to WordPress: {str(e)}"}


def detect_yoast_seo(target_url, html_content=""):
    """
    Detects whether a live URL or HTML page is powered by WordPress & Yoast SEO plugin.
    """
    evidence = []
    if html_content:
        import re
        if re.search(r"This site is optimized with the Yoast SEO plugin", html_content, re.IGNORECASE):
            evidence.append("Yoast HTML Comment Marker")
        if re.search(r'<meta name="generator" content="Yoast SEO', html_content, re.IGNORECASE):
            evidence.append("Yoast Generator Meta Tag")
        if "yoast-schema-graph" in html_content:
            evidence.append("Yoast Schema Graph Class")
        if "plugins/wordpress-seo" in html_content:
            evidence.append("Yoast Plugin Asset Path")

    if evidence:
        return {"is_yoast": True, "evidence": evidence}

    # Optional fast probe on get_head
    if target_url:
        probe = fetch_yoast_head(target_url, timeout=5)
        if probe.get("success"):
            return {"is_yoast": True, "evidence": ["Yoast REST API get_head Active"]}

    return {"is_yoast": False, "evidence": []}


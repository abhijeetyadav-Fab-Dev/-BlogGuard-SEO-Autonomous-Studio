import os
import re
import time
import json
import subprocess
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup
import shutil

CHROME_PATHS = [
    # Windows
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    # Linux / Render / Docker
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    # Mac
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

AUTHORITY_DOMAINS = {
    "wikipedia.org", "gov", "edu", "statista.com", "reuters.com", "bloomberg.com",
    "nytimes.com", "nature.com", "sciencedirect.com", "nih.gov", "cdc.gov",
    "who.int", "arxiv.org", "forbes.com", "bbc.com", "techcrunch.com",
    "wsj.com", "harvard.edu", "mit.edu", "stanford.edu", "britannica.com"
}

STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
    "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
    "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
    "some", "such", "than", "that", "that's", "the", "their", "theirs", "them",
    "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll",
    "they're", "they've", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're",
    "we've", "were", "weren't", "what", "what's", "when", "when's", "where",
    "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with",
    "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've",
    "your", "yours", "yourself", "yourselves", "also", "one", "two", "use",
    "like", "make", "get", "even", "many", "much", "well", "way"
}


def get_browser_executable():
    for name in ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"]:
        found = shutil.which(name)
        if found and os.path.isfile(found):
            return found
    for path in CHROME_PATHS:
        if os.path.isfile(path):
            return path
    return None


def count_syllables(word):
    word = word.lower().strip()
    if len(word) <= 3:
        return 1
    word = re.sub(r'(?:[^laeiouy]|ed|es|e)$', '', word)
    word = re.sub(r'^y', '', word)
    syllables = len(re.findall(r'[aeiouy]{1,2}', word))
    return max(1, syllables)


def calculate_readability(text, words, sentences):
    word_count = len(words)
    sentence_count = max(1, len(sentences))
    if word_count == 0:
        return {
            "flesch_reading_ease": 0.0,
            "flesch_kincaid_grade": 0.0,
            "avg_sentence_length": 0.0,
            "complex_words": 0,
            "reading_ease_label": "N/A",
        }

    total_syllables = sum(count_syllables(w) for w in words)
    complex_words = sum(1 for w in words if count_syllables(w) >= 3)
    avg_sentence_length = round(word_count / sentence_count, 1)

    # Standard Flesch Reading Ease formula
    reading_ease = 206.835 - (1.015 * (word_count / sentence_count)) - (84.6 * (total_syllables / word_count))
    reading_ease = max(0.0, min(100.0, round(reading_ease, 1)))

    # Flesch-Kincaid Grade Level
    fk_grade = (0.39 * (word_count / sentence_count)) + (11.8 * (total_syllables / word_count)) - 15.59
    fk_grade = max(1.0, round(fk_grade, 1))

    if reading_ease >= 80:
        label = "Very Easy (Grade 5-6)"
    elif reading_ease >= 70:
        label = "Easy (Grade 7)"
    elif reading_ease >= 60:
        label = "Standard / Conversational (Grade 8-9)"
    elif reading_ease >= 50:
        label = "Fairly Difficult (High School)"
    elif reading_ease >= 30:
        label = "Difficult (College)"
    else:
        label = "Very Difficult (Academic/Technical)"

    return {
        "flesch_reading_ease": reading_ease,
        "flesch_kincaid_grade": fk_grade,
        "avg_sentence_length": avg_sentence_length,
        "complex_words": complex_words,
        "reading_ease_label": label,
    }


def extract_keywords(words):
    clean_words = [w.lower() for w in words if len(w) > 2 and w.lower() not in STOP_WORDS]
    freq = {}
    for w in clean_words:
        freq[w] = freq.get(w, 0) + 1

    # Unigram candidates
    top_unigrams = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:10]

    # Bigram candidates
    bigrams = {}
    for i in range(len(clean_words) - 1):
        bg = f"{clean_words[i]} {clean_words[i+1]}"
        bigrams[bg] = bigrams.get(bg, 0) + 1

    top_bigrams = sorted(bigrams.items(), key=lambda x: x[1], reverse=True)[:8]

    return {
        "top_unigrams": top_unigrams,
        "top_bigrams": top_bigrams,
        "primary_guess": top_bigrams[0][0] if top_bigrams else (top_unigrams[0][0] if top_unigrams else ""),
    }


def fetch_html(url, use_browser=True, timeout=20):
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    start_time = time.time()
    html = ""
    status_code = 200
    engine_used = "Fast HTTP"
    final_url = url

    browser_exe = get_browser_executable()
    if use_browser and browser_exe:
        try:
            cmd = [
                browser_exe,
                "--headless=new",
                "--disable-gpu",
                "--dump-dom",
                "--virtual-time-budget=6000",
                url
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout
            )
            if result.returncode == 0 and len(result.stdout) > 200:
                html = result.stdout
                engine_used = f"Headless Browser ({os.path.basename(browser_exe)})"
        except Exception:
            html = ""

    if not html:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/",
            "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Upgrade-Insecure-Requests": "1",
        }
        
        session = requests.Session()
        error_msg = ""
        try:
            res = session.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            status_code = res.status_code
            final_url = str(res.url)
            html = res.text or ""
            engine_used = "High-Fidelity HTTP"

            # If blocked with 403 / 401 or empty on cloud hosts (Render), retry with Bot bypass
            if status_code in (401, 403, 503) or len(html.strip()) < 200:
                bot_headers = {
                    "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
                    "Accept": "*/*",
                }
                res_retry = session.get(url, headers=bot_headers, timeout=timeout, allow_redirects=True)
                if res_retry.status_code < 400 and len(res_retry.text) > len(html):
                    status_code = res_retry.status_code
                    final_url = str(res_retry.url)
                    html = res_retry.text
                    engine_used = "HTTP (Verified Bot Fallback)"
        except requests.exceptions.SSLError:
            try:
                res = session.get(url, headers=headers, timeout=timeout, allow_redirects=True, verify=False)
                status_code = res.status_code
                final_url = str(res.url)
                html = res.text or ""
                engine_used = "HTTP (SSL Fallback)"
            except Exception as e:
                status_code = 500
                error_msg = f"SSL Error: {str(e)}"
                html = ""
        except Exception as e:
            status_code = 500
            error_msg = f"Network Connection Error: {str(e)}"
            html = ""

    load_time = round(time.time() - start_time, 2)
    return {
        "html": html,
        "url": url,
        "final_url": final_url,
        "status_code": status_code,
        "load_time_sec": load_time,
        "engine": engine_used,
        "error": error_msg if not html else "",
    }


def parse_page_data(fetch_result):
    html = fetch_result["html"]
    url = fetch_result["url"]
    soup = BeautifulSoup(html, "html.parser")

    # Title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Meta Description
    meta_desc_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
    if not meta_desc_tag:
        meta_desc_tag = soup.find("meta", attrs={"property": re.compile(r"^og:description$", re.I)})
    meta_description = meta_desc_tag.get("content", "").strip() if meta_desc_tag else ""

    # Canonical
    canonical_tag = soup.find("link", attrs={"rel": re.compile(r"^canonical$", re.I)})
    canonical_url = canonical_tag.get("href", "").strip() if canonical_tag else ""

    # Robots
    robots_tag = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
    robots_content = robots_tag.get("content", "").strip() if robots_tag else ""

    # OpenGraph
    og_data = {}
    for tag in soup.find_all("meta", attrs={"property": re.compile(r"^og:")}):
        prop = tag.get("property", "").lower()
        og_data[prop] = tag.get("content", "")

    # Twitter Cards
    twitter_data = {}
    for tag in soup.find_all("meta", attrs={"name": re.compile(r"^twitter:")}):
        name = tag.get("name", "").lower()
        twitter_data[name] = tag.get("content", "")

    # Author
    author = ""
    author_tag = soup.find("meta", attrs={"name": re.compile(r"^author$", re.I)})
    if author_tag:
        author = author_tag.get("content", "").strip()
    if not author and "og:article:author" in og_data:
        author = og_data["og:article:author"]
    if not author:
        author_el = soup.find(attrs={"rel": "author"}) or soup.find(class_=re.compile(r"author|byline", re.I))
        if author_el:
            author = author_el.get_text(strip=True)

    # Dates
    pub_date = ""
    date_tag = soup.find("meta", attrs={"property": re.compile(r"^article:published_time$", re.I)})
    if date_tag:
        pub_date = date_tag.get("content", "").strip()
    if not pub_date:
        time_tag = soup.find("time")
        if time_tag:
            pub_date = time_tag.get("datetime") or time_tag.get_text(strip=True)

    # JSON-LD Schema
    json_ld_list = []
    schema_types = set()
    for s in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(s.string or "{}")
            if isinstance(data, dict):
                stype = data.get("@type", "")
                if stype:
                    schema_types.add(str(stype))
                json_ld_list.append(data)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "@type" in item:
                        schema_types.add(str(item["@type"]))
                json_ld_list.extend(data)
        except Exception:
            pass

    # Headings hierarchy
    headings = []
    h1_list = []
    h2_list = []
    h3_list = []
    h4_list = []

    for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        level = int(h.name[1])
        text = h.get_text(strip=True)
        if text:
            entry = {"tag": h.name.lower(), "level": level, "text": text}
            headings.append(entry)
            if level == 1:
                h1_list.append(text)
            elif level == 2:
                h2_list.append(text)
            elif level == 3:
                h3_list.append(text)
            elif level == 4:
                h4_list.append(text)

    # Hierarchy validation
    hierarchy_valid = True
    prev_level = 0
    for h in headings:
        if prev_level > 0 and h["level"] > prev_level + 1:
            hierarchy_valid = False
            break
        prev_level = h["level"]

    # Main clean text extraction
    body_clone = soup.find("body") or soup
    # Remove junk nodes
    for unwanted in body_clone.find_all(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg"]):
        unwanted.decompose()

    # Prioritize semantic article container if found
    article_container = (
        body_clone.find("article")
        or body_clone.find(attrs={"role": "main"})
        or body_clone.find(class_=re.compile(r"post-content|entry-content|article-content|blog-content", re.I))
        or body_clone
    )

    clean_text = article_container.get_text(separator=" ", strip=True)
    clean_text = re.sub(r"\s+", " ", clean_text)

    # Words, sentences, paragraphs
    words = re.findall(r"\b[\w'-]+\b", clean_text)
    raw_sentences = [s.strip() for s in re.split(r"[.!?]+", clean_text) if s.strip()]
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", clean_text) if len(p.strip()) > 20]

    # Images
    images = []
    images_without_alt = []
    base_netloc = urlparse(url).netloc
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or ""
        alt = img.get("alt", "").strip()
        has_alt = bool(alt)
        ext = os.path.splitext(urlparse(src).path)[1].lower() or "other"
        img_info = {
            "src": urljoin(url, src),
            "alt": alt,
            "has_alt": has_alt,
            "format": ext,
            "loading": img.get("loading", "eager"),
        }
        images.append(img_info)
        if not has_alt:
            images_without_alt.append(img_info)

    # Links
    links = []
    citation_links = []
    internal_links_count = 0
    external_links_count = 0
    nofollow_links_count = 0

    for a in soup.find_all("a", href=True):
        href = a.get("href", "").strip()
        if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
            continue

        full_url = urljoin(url, href)
        link_netloc = urlparse(full_url).netloc.lower()
        rel = (a.get("rel") or [])
        is_nofollow = "nofollow" in [r.lower() for r in rel]
        is_internal = (link_netloc == base_netloc or not link_netloc)
        link_text = a.get_text(strip=True)

        is_citation = False
        for auth in AUTHORITY_DOMAINS:
            if auth in link_netloc:
                is_citation = True
                break

        link_entry = {
            "href": full_url,
            "text": link_text,
            "is_internal": is_internal,
            "is_nofollow": is_nofollow,
            "is_citation": is_citation,
        }
        links.append(link_entry)

        if is_internal:
            internal_links_count += 1
        else:
            external_links_count += 1
            if is_citation:
                citation_links.append(link_entry)
        if is_nofollow:
            nofollow_links_count += 1

    # Readability
    readability = calculate_readability(clean_text, words, raw_sentences)

    # Long sentences (> 28 words)
    long_sentences = []
    for s in raw_sentences:
        swords = re.findall(r"\b\w+\b", s)
        if len(swords) > 28:
            long_sentences.append({"sentence": s, "word_count": len(swords)})

    # Keywords discovery
    kw_data = extract_keywords(words)

    # In-text sources/citations detection
    in_text_sources = len(re.findall(r"(?i)\b(?:according to|study shows|published in|source:|research by|reported by|reference:)\b", clean_text))

    return {
        "url": fetch_result["url"],
        "final_url": fetch_result["final_url"],
        "status_code": fetch_result["status_code"],
        "load_time_sec": fetch_result["load_time_sec"],
        "engine": fetch_result["engine"],
        "title": title or (h1_list[0] if h1_list else "Untitled"),
        "title_len": len(title),
        "meta_description": meta_description,
        "meta_desc_len": len(meta_description),
        "canonical_url": canonical_url,
        "canonical_match": canonical_url.rstrip("/") == url.rstrip("/"),
        "robots": robots_content,
        "author": author or "Unknown",
        "published_date": pub_date or "Not detected",
        "headings": headings,
        "h1_list": h1_list,
        "h2_list": h2_list,
        "h3_list": h3_list,
        "h4_list": h4_list,
        "hierarchy_valid": hierarchy_valid,
        "clean_text": clean_text,
        "words": words,
        "word_count": len(words),
        "sentence_count": len(raw_sentences),
        "paragraph_count": len(paragraphs),
        "reading_time_min": round(len(words) / 200, 1),
        "images": images,
        "total_images": len(images),
        "images_without_alt": images_without_alt,
        "links": links,
        "internal_links_count": internal_links_count,
        "external_links_count": external_links_count,
        "nofollow_links_count": nofollow_links_count,
        "citation_links": citation_links,
        "in_text_sources": in_text_sources,
        "opengraph": og_data,
        "twitter_cards": twitter_data,
        "schema_types": list(schema_types),
        "json_ld_list": json_ld_list,
        "readability": readability,
        "long_sentences": long_sentences,
        "top_unigrams": kw_data["top_unigrams"],
        "top_bigrams": kw_data["top_bigrams"],
        "suggested_keyword": kw_data["primary_guess"],
    }


def discover_and_parse_sitemap(domain_or_url, max_urls=50, timeout=12):
    """
    Discovers and parses XML sitemaps for any domain or specific sitemap URL.
    Supports standard <urlset> and recursive <sitemapindex> structures.
    """
    input_clean = domain_or_url.strip()
    if not input_clean.startswith(("http://", "https://")):
        input_clean = "https://" + input_clean

    parsed = urlparse(input_clean)
    base_origin = f"{parsed.scheme}://{parsed.netloc}"

    candidate_sitemaps = []
    if parsed.path.endswith(".xml"):
        candidate_sitemaps.append(input_clean)
    else:
        candidate_sitemaps.extend([
            f"{base_origin}/sitemap.xml",
            f"{base_origin}/sitemap_index.xml",
            f"{base_origin}/wp-sitemap.xml",
            f"{base_origin}/post-sitemap.xml",
        ])

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 BlogGuard-Sitemap-Discovery/2.0",
        "Accept": "application/xml, text/xml, */*",
    }

    discovered_urls = []
    active_sitemap_url = ""

    for s_url in candidate_sitemaps:
        try:
            res = requests.get(s_url, headers=headers, timeout=timeout, allow_redirects=True)
            if res.status_code == 200 and ("xml" in res.headers.get("content-type", "").lower() or "<urlset" in res.text or "<sitemapindex" in res.text):
                active_sitemap_url = s_url
                soup = BeautifulSoup(res.text, "html.parser")

                # Check if it is a sitemap index containing child sitemaps
                child_sitemaps = [s.get_text(strip=True) for s in soup.find_all("loc") if s.find_parent("sitemap")]
                if child_sitemaps:
                    # Prioritize sub-sitemaps likely containing blog posts or articles
                    post_sitemaps = [c for c in child_sitemaps if any(k in c.lower() for k in ["post", "blog", "article"])]
                    selected_children = post_sitemaps if post_sitemaps else child_sitemaps[:3]

                    for child_url in selected_children:
                        try:
                            c_res = requests.get(child_url, headers=headers, timeout=timeout)
                            if c_res.status_code == 200:
                                c_soup = BeautifulSoup(c_res.text, "html.parser")
                                for u in c_soup.find_all("url"):
                                    loc = u.find("loc")
                                    if loc and loc.get_text(strip=True):
                                        lastmod = u.find("lastmod")
                                        priority = u.find("priority")
                                        discovered_urls.append({
                                            "url": loc.get_text(strip=True),
                                            "lastmod": lastmod.get_text(strip=True) if lastmod else "N/A",
                                            "priority": priority.get_text(strip=True) if priority else "0.5",
                                            "parent_sitemap": child_url,
                                        })
                                        if len(discovered_urls) >= max_urls:
                                            break
                        except Exception:
                            continue
                        if len(discovered_urls) >= max_urls:
                            break
                else:
                    # Direct urlset
                    for u in soup.find_all("url"):
                        loc = u.find("loc")
                        if loc and loc.get_text(strip=True):
                            lastmod = u.find("lastmod")
                            priority = u.find("priority")
                            discovered_urls.append({
                                "url": loc.get_text(strip=True),
                                "lastmod": lastmod.get_text(strip=True) if lastmod else "N/A",
                                "priority": priority.get_text(strip=True) if priority else "0.5",
                                "parent_sitemap": s_url,
                            })
                            if len(discovered_urls) >= max_urls:
                                break

                if discovered_urls:
                    break
        except Exception:
            continue

    if not discovered_urls:
        return {
            "success": False,
            "error": f"No accessible XML sitemaps found at {base_origin}. Checked: {', '.join(candidate_sitemaps)}",
            "sitemap_url": active_sitemap_url or candidate_sitemaps[0],
            "total_found": 0,
            "urls": [],
        }

    return {
        "success": True,
        "sitemap_url": active_sitemap_url,
        "total_found": len(discovered_urls),
        "urls": discovered_urls[:max_urls],
    }


def audit_links_health(links, base_url="", max_check=25, timeout=6):
    """
    Concurrently audits the health of extracted page links.
    Detects 404 dead links, server errors, redirect chains, and insecure HTTP mixed content.
    """
    to_check = links[:max_check]
    if not to_check:
        return {
            "total_checked": 0,
            "broken_count": 0,
            "redirect_count": 0,
            "mixed_content_count": 0,
            "broken_links": [],
            "redirect_links": [],
            "mixed_content": [],
            "all_results": [],
        }

    base_is_https = base_url.lower().startswith("https://") if base_url else False
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 BlogGuard-LinkSentinel/2.0",
        "Accept": "*/*",
    }

    def _probe_single_link(link_item):
        target_href = link_item.get("href", "")
        text = link_item.get("text", "") or "[No Anchor Text]"
        is_internal = link_item.get("is_internal", False)

        is_mixed = base_is_https and target_href.lower().startswith("http://")

        status_code = 0
        final_url = target_href
        is_redirect = False
        status_label = "Unknown"
        is_broken = False

        try:
            # Try HEAD first for performance
            res = requests.head(target_href, headers=headers, timeout=timeout, allow_redirects=True)
            if res.status_code == 405:  # Method Not Allowed -> fallback to GET
                res = requests.get(target_href, headers=headers, timeout=timeout, allow_redirects=True, stream=True)
            status_code = res.status_code
            final_url = str(res.url)
            is_redirect = (final_url.rstrip("/") != target_href.rstrip("/"))

            if 200 <= status_code < 400:
                status_label = "200 OK" if not is_redirect else f"{status_code} Redirect"
            elif status_code in (404, 410):
                status_label = f"🔴 {status_code} Dead Link"
                is_broken = True
            elif status_code >= 500:
                status_label = f"🔴 {status_code} Server Error"
                is_broken = True
            else:
                status_label = f"⚠️ HTTP {status_code}"
                if status_code in (401, 403):
                    # Some sites block scrapers with 403; flag but note bot restriction
                    status_label = f"🔒 HTTP {status_code} (Restricted/Auth)"
        except requests.exceptions.SSLError:
            status_code = 495
            status_label = "🔴 SSL Certificate Error"
            is_broken = True
        except requests.exceptions.Timeout:
            status_code = 408
            status_label = "🔴 Request Timeout"
            is_broken = True
        except Exception as e:
            status_code = 0
            status_label = f"🔴 Connection Failed ({type(e).__name__})"
            is_broken = True

        return {
            "href": target_href,
            "anchor_text": text[:60],
            "is_internal": is_internal,
            "status_code": status_code,
            "status_label": status_label,
            "final_url": final_url,
            "is_redirect": is_redirect,
            "is_broken": is_broken,
            "is_mixed_content": is_mixed,
        }

    results = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        future_to_link = {executor.submit(_probe_single_link, link): link for link in to_check}
        for future in as_completed(future_to_link):
            try:
                results.append(future.result())
            except Exception:
                pass

    broken = [r for r in results if r["is_broken"]]
    redirects = [r for r in results if r["is_redirect"]]
    mixed = [r for r in results if r["is_mixed_content"]]

    return {
        "total_checked": len(results),
        "broken_count": len(broken),
        "redirect_count": len(redirects),
        "mixed_content_count": len(mixed_content) if (mixed_content := mixed) else 0,
        "broken_links": broken,
        "redirect_links": redirects,
        "mixed_content": mixed,
        "all_results": results,
    }


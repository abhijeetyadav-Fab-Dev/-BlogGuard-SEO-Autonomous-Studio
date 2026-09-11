import re
import html

COMMON_SPELLING_FIXES = {
    "alot": "a lot",
    "recieve": "receive",
    "seperate": "separate",
    "definately": "definitely",
    "occured": "occurred",
    "untill": "until",
    "wich": "which",
    "teh": "the",
    "goverment": "government",
    "accomodation": "accommodation",
    "beleive": "believe",
    "truely": "truly",
    "arguement": "argument",
    "recommand": "recommend",
    "convinient": "convenient",
    "maintainance": "maintenance",
    "possession": "possession",
    "succesful": "successful",
    "refering": "referring",
    "tommorrow": "tomorrow",
}

COMMON_JARGON_REPLACEMENTS = {
    "utilize": "use",
    "utilizes": "uses",
    "utilizing": "using",
    "utilization": "use",
    "commence": "start",
    "commenced": "started",
    "facilitate": "help",
    "facilitates": "helps",
    "subsequently": "then / later",
    "furthermore": "also / plus",
    "consequently": "so / as a result",
    "implementation": "setup / launch",
    "implementing": "setting up",
    "approximately": "about",
    "demonstrate": "show",
    "demonstrates": "shows",
    "terminate": "end / stop",
    "expedite": "speed up",
    "leverage": "use",
    "leveraging": "using",
    "endeavor": "try",
    "methodology": "method / approach",
    "advantageous": "helpful",
    "disseminate": "share",
    "predominantly": "mostly",
}

COMMON_REDUNDANCIES = {
    "absolutely essential": "essential",
    "actual facts": "facts",
    "advance warning": "warning",
    "all-time record": "record",
    "alternative choice": "choice",
    "basic fundamentals": "fundamentals",
    "close proximity": "near",
    "completely finished": "finished",
    "end result": "result",
    "exact same": "same",
    "final outcome": "outcome",
    "first and foremost": "first",
    "future plans": "plans",
    "general consensus": "consensus",
    "join together": "join",
    "major breakthrough": "breakthrough",
    "past experience": "experience",
    "past history": "history",
    "plan ahead": "plan",
    "reason why": "reason",
    "revert back": "revert",
    "sum total": "total",
    "unexpected surprise": "surprise",
    "for the purpose of": "to",
    "in spite of the fact that": "although",
    "each and every": "every",
    "period of time": "period",
    "true facts": "facts",
    "at this point in time": "now",
    "prior to": "before",
    "in order to": "to",
    "due to the fact that": "because",
    "with regard to": "about",
    "at the present time": "now",
    "in the event that": "if",
    "a large number of": "many",
}


def detect_passive_voice(sentences):
    passive_sents = []
    pattern = re.compile(r'\b(?:am|is|are|was|were|be|been|being)\s+(?:\w+ed|written|made|done|seen|given|taken|built|chosen|known|shown|found|said|held|sent)\b', re.IGNORECASE)
    for s in sentences:
        if pattern.search(s):
            passive_sents.append(s)
    pct = round((len(passive_sents) / max(1, len(sentences))) * 100, 1)
    return {
        "count": len(passive_sents),
        "percentage": pct,
        "sentences": passive_sents[:8]
    }


def detect_redundancies(clean_text):
    found = []
    for red, sim in COMMON_REDUNDANCIES.items():
        count = len(re.findall(rf'\b{re.escape(red)}\b', clean_text, re.IGNORECASE))
        if count > 0:
            found.append({
                "Redundant Phrase": red,
                "Simpler Alternative": sim,
                "Occurrences": count,
                "phrase": red,
                "replacement": sim,
                "count": count
            })
    return found


def check_content_alignment(title, h1_list, h2_list, clean_text):
    stopwords = {"the", "and", "for", "with", "from", "best", "top", "this", "that", "your", "how", "what", "why", "when", "into"}
    title_words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', title) if w.lower() not in stopwords]

    if not title_words:
        return {"score": 90, "status": "Strong Match", "observations": ["Title is concise and matches core article focus."]}

    found_in_body = sum(1 for w in title_words if w in clean_text.lower())
    found_in_h2 = sum(1 for w in title_words if any(w in h.lower() for h in h2_list))

    body_ratio = found_in_body / len(title_words)
    score = int((body_ratio * 55) + (min(len(h2_list), 3) * 10) + (min(found_in_h2, len(title_words)) / len(title_words) * 15))
    score = min(100, max(10, score))

    observations = []
    promise_type = "general"
    promised_num = None

    # Check number promise in title: e.g. '10 Best Hotels in...'
    num_match = re.search(r'\b(\d+)\b', title)
    if num_match:
        val = int(num_match.group(1))
        if 2 <= val <= 100:
            promised_num = val
            promise_type = "listicle"
            if len(h2_list) < promised_num:
                observations.append(f"⚠️ Headline promises {promised_num} items, but only {len(h2_list)} H2 sections were detected.")
                score = max(35, score - 20)
            else:
                observations.append(f"✅ Headline promises {promised_num} items, and {len(h2_list)} H2 sections provide the promised breakdown.")

    # Check 'How To' promise
    if re.search(r'\b(?:how to|step-by-step|guide|tutorial)\b', title, re.IGNORECASE):
        if promise_type == "general":
            promise_type = "how_to"
        if not re.search(r'\b(?:step \d|step-by-step|instructions|method|guide|first,|second,|finally,)\b', clean_text, re.IGNORECASE):
            observations.append("⚠️ Title promises a practical 'How-To' guide, but text lacks clear step-by-step markers.")
            score = max(40, score - 15)
        else:
            observations.append("✅ Practical step-by-step instructions deliver on the 'How-To' promise.")

    # Check Comparison / Versus promise
    if re.search(r'\b(?:vs|versus|comparison|compared to)\b', title, re.IGNORECASE):
        if promise_type == "general":
            promise_type = "comparison"
        observations.append("ℹ️ Title indicates a comparative analysis. Ensure both subjects receive balanced depth and pros/cons.")

    if score >= 85:
        status = "Strong Match (High Fulfillment)"
    elif score >= 65:
        status = "Good Alignment (Minor Gaps)"
    else:
        status = "Content Mismatch Risk (Headline Drift)"

    return {
        "score": score,
        "status": status,
        "observations": observations,
        "title_keywords_matched": f"{found_in_body}/{len(title_words)}",
        "promise_type": promise_type,
        "promised_number": promised_num,
        "actual_h2_count": len(h2_list)
    }


def audit_page(data, keyword=None, writer=None):
    keyword = (keyword or data.get("suggested_keyword") or "").strip()
    title = data.get("title", "")
    meta_desc = data.get("meta_description", "")
    clean_text = data.get("clean_text", "")
    h1_list = data.get("h1_list", [])
    h2_list = data.get("h2_list", [])
    h3_list = data.get("h3_list", [])
    headings = data.get("headings", [])
    words = data.get("words", [])
    word_count = len(words)
    images = data.get("images", [])
    images_without_alt = data.get("images_without_alt", [])
    links = data.get("links", [])
    internal_links = [l for l in links if l.get("is_internal")]
    external_links = [l for l in links if not l.get("is_internal")]
    citation_links = data.get("citation_links", [])
    readability = data.get("readability", {})
    long_sentences = data.get("long_sentences", [])

    issues = []
    quick_wins = []

    # -------------------------------------------------------------
    # 1. Technical & Indexability SEO (0 - 100)
    # -------------------------------------------------------------
    tech_score = 0
    title_len = len(title)
    if title:
        tech_score += 20
        if 50 <= title_len <= 65:
            tech_score += 15
        elif 35 <= title_len < 50 or 65 < title_len <= 75:
            tech_score += 10
            issues.append({
                "severity": "warning",
                "pillar": "Technical SEO",
                "title": "Title tag length could be optimized",
                "detail": f"Title is {title_len} characters. Ideal length is 50-65 characters for optimal Google SERP display.",
                "fix": "Shorten or expand title to 50-65 characters."
            })
        else:
            issues.append({
                "severity": "critical",
                "pillar": "Technical SEO",
                "title": "Title tag too short or too long",
                "detail": f"Title is {title_len} characters. Search engines will truncate it or fail to grasp topical relevance.",
                "fix": "Rewrite title to be between 50 and 65 characters."
            })
    else:
        issues.append({
            "severity": "critical",
            "pillar": "Technical SEO",
            "title": "Missing Title Tag",
            "detail": "The page does not have a primary HTML <title> tag.",
            "fix": "Add a descriptive <title> tag containing the primary keyword."
        })

    meta_len = len(meta_desc)
    if meta_desc:
        tech_score += 20
        if 130 <= meta_len <= 165:
            tech_score += 15
        elif 100 <= meta_len < 130 or 165 < meta_len <= 180:
            tech_score += 10
        else:
            issues.append({
                "severity": "warning",
                "pillar": "Technical SEO",
                "title": "Suboptimal Meta Description Length",
                "detail": f"Meta description is {meta_len} chars. Google displays roughly 140-160 characters before truncation.",
                "fix": "Aim for 145-160 characters with a clear CTA and primary keyword."
            })
    else:
        issues.append({
            "severity": "critical",
            "pillar": "Technical SEO",
            "title": "Missing Meta Description",
            "detail": "Search engines will auto-generate a snippet, resulting in lower click-through rates (CTR).",
            "fix": "Write a compelling meta description between 140 and 160 characters."
        })

    if data.get("canonical_url"):
        tech_score += 15
    else:
        issues.append({
            "severity": "warning",
            "pillar": "Technical SEO",
            "title": "Missing Canonical Tag",
            "detail": "No rel='canonical' tag detected, exposing the article to duplicate content penalties.",
            "fix": "Add a self-referential canonical tag: <link rel='canonical' href='...'>"
        })

    robots = data.get("robots", "").lower()
    if "noindex" not in robots:
        tech_score += 10
    else:
        issues.append({
            "severity": "critical",
            "pillar": "Technical SEO",
            "title": "Page is blocked by 'noindex' directive",
            "detail": f"Robots meta contains: {data.get('robots')}. Search engines cannot index this page!",
            "fix": "Remove 'noindex' from the robots meta tag or HTTP header."
        })

    if data.get("schema_types"):
        tech_score += 15
    else:
        issues.append({
            "severity": "warning",
            "pillar": "Technical SEO",
            "title": "Missing JSON-LD Structured Data",
            "detail": "No Schema.org markup (Article, BlogPosting, FAQPage) detected.",
            "fix": "Add JSON-LD Article or BlogPosting schema to gain Google Rich Snippets."
        })

    if data.get("opengraph"):
        tech_score += 5

    tech_score = min(100, max(0, tech_score))

    # -------------------------------------------------------------
    # 2. Heading & Structural Hierarchy (0 - 100)
    # -------------------------------------------------------------
    struct_score = 0
    h1_count = len(h1_list)
    if h1_count == 1:
        struct_score += 35
    elif h1_count == 0:
        issues.append({
            "severity": "critical",
            "pillar": "Structure",
            "title": "No H1 heading detected",
            "detail": "Every blog post requires exactly one descriptive H1 heading to establish topic authority.",
            "fix": "Add an H1 tag at the top of the article body."
        })
    else:
        struct_score += 15
        issues.append({
            "severity": "warning",
            "pillar": "Structure",
            "title": f"Multiple H1 headings detected ({h1_count})",
            "detail": "Multiple H1 tags dilute topical relevance and confuse search crawlers.",
            "fix": "Convert auxiliary H1 headings into H2 section headings."
        })

    h2_count = len(h2_list)
    if h2_count >= 3:
        struct_score += 30
    elif h2_count in (1, 2):
        struct_score += 15
        issues.append({
            "severity": "warning",
            "pillar": "Structure",
            "title": "Low H2 section count",
            "detail": f"Found only {h2_count} H2 heading(s). In-depth blogs should break content into at least 3-5 thematic sections.",
            "fix": "Add more descriptive H2 headings to organize your arguments."
        })
    else:
        issues.append({
            "severity": "critical",
            "pillar": "Structure",
            "title": "Zero H2 headings detected",
            "detail": "The article is an unbroken wall of text with no clear structural sections.",
            "fix": "Add clear, topic-rich H2 headings every 300-400 words."
        })

    if len(h3_list) > 0:
        struct_score += 15

    if data.get("hierarchy_valid", True):
        struct_score += 20
    else:
        issues.append({
            "severity": "warning",
            "pillar": "Structure",
            "title": "Heading hierarchy skips levels",
            "detail": "Found headings jumping directly (e.g. H1 to H3 without an intervening H2).",
            "fix": "Nest headings logically: H1 -> H2 -> H3 -> H4."
        })

    struct_score = min(100, max(0, struct_score))

    # -------------------------------------------------------------
    # 3. Content Depth & Readability (0 - 100)
    # -------------------------------------------------------------
    content_score = 0
    if word_count >= 1500:
        content_score += 35
    elif word_count >= 1000:
        content_score += 28
    elif word_count >= 600:
        content_score += 20
    else:
        content_score += 10
        issues.append({
            "severity": "critical",
            "pillar": "Content Depth",
            "title": "Thin Content Warning",
            "detail": f"Article has only {word_count} words. Google algorithms prioritize comprehensive, high-utility content.",
            "fix": "Expand article to at least 1,000+ words with practical case studies, steps, and FAQs."
        })

    # Detect specific jargon in the text
    detected_jargon = []
    for jw, simpler in COMMON_JARGON_REPLACEMENTS.items():
        count = len(re.findall(rf"\b{re.escape(jw)}\b", clean_text, re.IGNORECASE))
        if count > 0:
            detected_jargon.append({
                "Jargon Word": jw,
                "Simpler Alternative": simpler,
                "Occurrences": count
            })

    reading_ease = readability.get("flesch_reading_ease", 60.0)
    if 60 <= reading_ease <= 80:
        content_score += 30
    elif 50 <= reading_ease < 60 or 80 < reading_ease <= 90:
        content_score += 22
    else:
        content_score += 14
        if reading_ease < 50:
            jargon_ex = ", ".join([f"'{item['Jargon Word']}' -> '{item['Simpler Alternative']}'" for item in detected_jargon[:4]])
            fix_text = "Break sentences over 20 words into 2 punchy sentences. "
            if jargon_ex:
                fix_text += f"Replace complex terms: {jargon_ex}."
            else:
                fix_text += "Substitute multi-syllable jargon with direct, everyday verbs."

            issues.append({
                "severity": "warning",
                "pillar": "Readability",
                "title": f"Content is difficult to read (Flesch {reading_ease})",
                "detail": f"Flesch Reading Ease is {reading_ease} (College level). Web readers scan quickly and bounce when cognitive strain is high. Aim for 60-75 (conversational Grade 7-8).",
                "fix": fix_text,
            })

    long_sent_count = len(long_sentences)
    sent_count = max(1, data.get("sentence_count", 1))
    long_sent_pct = (long_sent_count / sent_count) * 100

    if long_sent_pct <= 10:
        content_score += 20
    elif long_sent_pct <= 20:
        content_score += 12
    else:
        content_score += 5
        issues.append({
            "severity": "warning",
            "pillar": "Readability",
            "title": f"{long_sent_count} Run-On Sentences Detected",
            "detail": f"{round(long_sent_pct, 1)}% of sentences exceed 28 words, causing reader fatigue.",
            "fix": "Split sentences exceeding 25 words into two punchier sentences."
        })

    # Grammar, Sentence Errors & Clarity Checks
    sentences_list = [s.strip() for s in re.split(r"[.!?]+", clean_text) if s.strip()]
    passive_info = detect_passive_voice(sentences_list)
    redundancies_info = detect_redundancies(clean_text)
    alignment_info = check_content_alignment(title, h1_list, h2_list, clean_text)

    # Passive voice warning
    if passive_info["percentage"] > 18.0:
        issues.append({
            "severity": "warning",
            "pillar": "Readability",
            "title": f"Excessive Passive Voice ({passive_info['percentage']}%)",
            "detail": f"{passive_info['count']} sentences use passive voice constructions. Passive voice slows reader comprehension and weakens authority.",
            "fix": "Rewrite passive sentences in active voice (e.g. 'The report was compiled by our team' -> 'Our team compiled the report')."
        })

    # Redundancies / Wordiness warning
    if len(redundancies_info) > 0:
        red_examples = ", ".join([f"'{r['Redundant Phrase']}' -> '{r['Simpler Alternative']}'" for r in redundancies_info[:3]])
        issues.append({
            "severity": "info",
            "pillar": "Readability",
            "title": f"Wordy & Redundant Phrases Detected ({len(redundancies_info)})",
            "detail": f"Trimming wordy phrases improves sentence velocity: {red_examples}.",
            "fix": "Replace redundant pairings with their single-word equivalents."
        })

    # Headline vs Content Alignment warning
    if alignment_info["score"] < 70:
        issues.append({
            "severity": "warning",
            "pillar": "Content Depth",
            "title": "Headline-to-Content Information Mismatch",
            "detail": " ".join(alignment_info["observations"]) if alignment_info["observations"] else "Article body drifts away from the core premise established in the title.",
            "fix": "Align H2 subheadings and body sections to directly deliver on the specific promise made in the title."
        })

    # Calculate overall Clarity Score (0-100)
    clarity_deductions = (
        min(30, (100 - reading_ease) * 0.35)
        + min(25, passive_info["percentage"] * 0.75)
        + min(25, long_sent_pct * 0.75)
        + min(20, len(redundancies_info) * 3)
    )
    clarity_score = max(10, min(100, round(100 - clarity_deductions)))

    has_conclusion = bool(re.search(r"(?i)\b(?:conclusion|final thoughts|summary|wrap-up|key takeaways|wrapping up)\b", clean_text))
    if has_conclusion:
        content_score += 15
    else:
        issues.append({
            "severity": "warning",
            "pillar": "Content Depth",
            "title": "No Clear Conclusion Section",
            "detail": "Articles without a final summary or actionable next steps leave readers hanging and reduce dwell time.",
            "fix": "Add an H2 section titled 'Key Takeaways' or 'Conclusion' with a 3-bullet summary."
        })

    content_score = min(100, max(0, content_score))

    # -------------------------------------------------------------
    # 4. On-Page Keyword & Search Intent (0 - 100)
    # -------------------------------------------------------------
    kw_score = 0
    kw_lower = keyword.lower().strip()
    first_150_words = " ".join(words[:150]).lower()

    if kw_lower:
        # Title check
        if kw_lower in title.lower():
            kw_score += 25
            quick_wins.append("Primary keyword is present in the main title tag.")
        else:
            issues.append({
                "severity": "critical",
                "pillar": "On-Page Keyword",
                "title": f"Primary keyword '{keyword}' missing from Title",
                "detail": "Title is the single most important on-page SEO signal.",
                "fix": f"Include '{keyword}' as close to the beginning of the title as possible."
            })

        # Meta description check
        if kw_lower in meta_desc.lower():
            kw_score += 20
        else:
            issues.append({
                "severity": "warning",
                "pillar": "On-Page Keyword",
                "title": f"Primary keyword '{keyword}' missing from Meta Description",
                "detail": "Google bolds matching keywords in SERP snippets, boosting click-through rates.",
                "fix": f"Naturally incorporate '{keyword}' into the meta description."
            })

        # H1 check
        if any(kw_lower in h.lower() for h in h1_list):
            kw_score += 20
        else:
            issues.append({
                "severity": "critical",
                "pillar": "On-Page Keyword",
                "title": f"Primary keyword '{keyword}' missing from H1",
                "detail": "The main H1 heading should confirm the user's search query.",
                "fix": f"Include '{keyword}' in the H1 heading."
            })

        # H2 check
        if any(kw_lower in h.lower() for h in h2_list):
            kw_score += 15
        else:
            issues.append({
                "severity": "warning",
                "pillar": "On-Page Keyword",
                "title": f"Primary keyword missing from H2 subheadings",
                "detail": "Subheadings should reinforce semantic topical relevance.",
                "fix": f"Include '{keyword}' or close semantic variations in at least one H2."
            })

        # First 100 words check
        if kw_lower in first_150_words:
            kw_score += 10
        else:
            issues.append({
                "severity": "warning",
                "pillar": "On-Page Keyword",
                "title": "Keyword not in introductory hook",
                "detail": f"'{keyword}' does not appear within the first 150 words.",
                "fix": "Introduce the focus keyword in the opening paragraph."
            })

        # Keyword density
        matches = len(re.findall(rf"\b{re.escape(kw_lower)}\b", clean_text.lower()))
        density = (matches / max(1, word_count)) * 100
        if 0.6 <= density <= 2.5:
            kw_score += 10
        elif density > 2.5:
            issues.append({
                "severity": "critical",
                "pillar": "On-Page Keyword",
                "title": f"Keyword Stuffing Risk ({round(density, 2)}% density)",
                "detail": f"Keyword appears {matches} times. Densities above 2.5% can trigger Google over-optimization penalties.",
                "fix": "Replace repetitive keyword mentions with natural synonyms and LSI terms."
            })
        else:
            kw_score += 5
    else:
        kw_score = 65  # Default baseline when no keyword entered

    kw_score = min(100, max(0, kw_score))

    # -------------------------------------------------------------
    # 5. E-E-A-T & Authority Trust (0 - 100)
    # -------------------------------------------------------------
    eeat_score = 0
    author_val = data.get("author", "")
    if author_val and author_val.lower() not in ("unknown", "not specified", "admin"):
        eeat_score += 25
    else:
        issues.append({
            "severity": "warning",
            "pillar": "E-E-A-T",
            "title": "No Clear Author Byline Detected",
            "detail": "Google's Quality Rater Guidelines mandate clear authorship and expertise credentials.",
            "fix": "Add an author byline with a link to an author bio page."
        })

    if data.get("published_date") and data.get("published_date") != "Not detected":
        eeat_score += 20
    else:
        issues.append({
            "severity": "info",
            "pillar": "E-E-A-T",
            "title": "Missing Publication or Updated Date",
            "detail": "Freshness signals help readers and search engines gauge temporal relevance.",
            "fix": "Display an explicit 'Published on' and 'Last Updated' timestamp."
        })

    cit_count = len(citation_links)
    if cit_count >= 2:
        eeat_score += 30
        quick_wins.append(f"Strong outbound references: {cit_count} citations to recognized authority sources.")
    elif cit_count == 1:
        eeat_score += 20
    else:
        issues.append({
            "severity": "warning",
            "pillar": "E-E-A-T",
            "title": "Missing Outbound Authority Citations",
            "detail": "Articles lacking outbound links to trusted peer-reviewed, government, or industry sources score lower on Trust.",
            "fix": "Cite at least 2 external high-authority publications (.gov, .edu, Wikipedia, research studies)."
        })

    if data.get("in_text_sources", 0) > 0:
        eeat_score += 15
    else:
        issues.append({
            "severity": "info",
            "pillar": "E-E-A-T",
            "title": "No In-Text Data Attributions",
            "detail": "No attribution phrases like 'according to' or 'study shows' detected.",
            "fix": "Attribute statistical claims to specific studies or organizations."
        })

    has_article_schema = any(t in ("Article", "BlogPosting", "NewsArticle") for t in data.get("schema_types", []))
    if has_article_schema:
        eeat_score += 10

    eeat_score = min(100, max(0, eeat_score))

    # -------------------------------------------------------------
    # 6. Visual & Media Richness (0 - 100)
    # -------------------------------------------------------------
    media_score = 0
    total_imgs = len(images)
    if total_imgs >= 3:
        media_score += 40
    elif total_imgs in (1, 2):
        media_score += 25
    else:
        media_score += 10
        issues.append({
            "severity": "warning",
            "pillar": "Media & Visuals",
            "title": "No images detected in blog post",
            "detail": "Visuals break up long reading blocks and improve engagement signals (dwell time, scroll depth).",
            "fix": "Add at least 2-3 relevant images, infographics, or charts."
        })

    no_alt_count = len(images_without_alt)
    if total_imgs > 0:
        alt_pct = ((total_imgs - no_alt_count) / total_imgs) * 100
        if alt_pct == 100:
            media_score += 40
        elif alt_pct >= 70:
            media_score += 25
            issues.append({
                "severity": "warning",
                "pillar": "Media & Visuals",
                "title": f"{no_alt_count} image(s) missing alt text",
                "detail": "Missing image alt text hurts accessibility and forfeits Google Image Search traffic.",
                "fix": "Add descriptive, keyword-supportive alt attributes to all images."
            })
        else:
            media_score += 10
            issues.append({
                "severity": "critical",
                "pillar": "Media & Visuals",
                "title": f"Most images lack Alt Text ({no_alt_count}/{total_imgs} missing)",
                "detail": "Severe accessibility violation and lost image SEO opportunity.",
                "fix": "Populate alt text describing what is shown in each image."
            })
    else:
        media_score += 25

    # Check for modern formats (webp, avif) or lazy-loading
    modern_count = sum(1 for img in images if img.get("format") in (".webp", ".avif") or img.get("loading") == "lazy")
    if modern_count > 0:
        media_score += 20

    media_score = min(100, max(0, media_score))

    # -------------------------------------------------------------
    # 7. Internal & Outbound Link Graph (0 - 100)
    # -------------------------------------------------------------
    link_score = 0
    int_count = len(internal_links)
    ext_count = len(external_links)

    if int_count >= 3:
        link_score += 40
    elif int_count in (1, 2):
        link_score += 25
        issues.append({
            "severity": "warning",
            "pillar": "Link Graph",
            "title": f"Low internal link count ({int_count})",
            "detail": "Internal links pass PageRank and build topical cluster authority.",
            "fix": "Link to 3-5 relevant articles or product pages on your site."
        })
    else:
        issues.append({
            "severity": "critical",
            "pillar": "Link Graph",
            "title": "Zero Internal Links Detected",
            "detail": "Isolated pages are hard for crawlers and readers to navigate.",
            "fix": "Add contextual internal links pointing to related pillar pages."
        })

    if ext_count >= 2:
        link_score += 35
    elif ext_count == 1:
        link_score += 20
    else:
        issues.append({
            "severity": "warning",
            "pillar": "Link Graph",
            "title": "Zero Outbound Links Detected",
            "detail": "Linking out to trusted reference material reinforces web graph connectivity.",
            "fix": "Add 2+ outbound links to reputable third-party sources."
        })

    link_score += 25  # baseline anchor hygiene
    link_score = min(100, max(0, link_score))

    # -------------------------------------------------------------
    # Spelling & Formatting Quick Fixes
    # -------------------------------------------------------------
    corrections = []
    for incorrect, correct in COMMON_SPELLING_FIXES.items():
        if re.search(rf"\b{incorrect}\b", clean_text, re.IGNORECASE):
            corrections.append({
                "Original": incorrect,
                "Correction": correct,
                "Reason": "Common spelling correction",
            })

    repeated_spaces = len(re.findall(r" {2,}", clean_text))
    if repeated_spaces > 0:
        corrections.append({
            "Original": "Multiple spaces",
            "Correction": "Single space",
            "Reason": f"Detected {repeated_spaces} instances of consecutive spaces",
        })

    # -------------------------------------------------------------
    # Overall Weighted Score Calculation
    # -------------------------------------------------------------
    weights = {
        "Technical SEO": (tech_score, 0.15),
        "Structure & Hierarchy": (struct_score, 0.15),
        "Content & Readability": (content_score, 0.20),
        "Keyword & Intent": (kw_score, 0.20),
        "E-E-A-T & Trust": (eeat_score, 0.15),
        "Media & Visuals": (media_score, 0.075),
        "Link Architecture": (link_score, 0.075),
    }

    scores = {name: val[0] for name, val in weights.items()}
    overall_score = round(sum(val[0] * val[1] for val in weights.values()))

    if overall_score >= 85:
        status = "Elite - Ready to Dominate Search"
        status_color = "green"
    elif overall_score >= 70:
        status = "Strong - Minor Polish Recommended"
        status_color = "blue"
    elif overall_score >= 50:
        status = "Moderate - Actionable Gaps Present"
        status_color = "orange"
    else:
        status = "Critical - Major SEO Deficits Detected"
        status_color = "red"

    critical_issues = [i for i in issues if i["severity"] == "critical"]
    warnings = [i for i in issues if i["severity"] == "warning"]
    info_items = [i for i in issues if i["severity"] == "info"]

    return {
        "overall_score": overall_score,
        "status": status,
        "status_color": status_color,
        "keyword": keyword,
        "writer": writer or data.get("author") or "Not specified",
        "scores": scores,
        "issues": issues,
        "critical_issues": critical_issues,
        "warnings": warnings,
        "info_items": info_items,
        "quick_wins": quick_wins,
        "corrections": corrections,
        "word_count": word_count,
        "reading_time_min": data.get("reading_time_min", 1),
        "readability": readability,
        "detected_jargon": detected_jargon,
        "content_alignment": alignment_info,
        "passive_voice": passive_info,
        "redundancies": redundancies_info,
        "clarity_score": clarity_score,
        "h1_count": h1_count,
        "h2_count": h2_count,
        "h3_count": len(h3_list),
        "image_count": total_imgs,
        "missing_alt_count": no_alt_count,
        "internal_links_count": int_count,
        "external_links_count": ext_count,
        "citations_count": len(citation_links),
        "long_sentences_count": len(long_sentences),
    }


def generate_highlighted_html(raw_text, keyword="", jargon_map=None, typo_map=None, hl_kw=True, hl_jg=True, hl_tp=True, hl_ls=True, hl_rd=True, hl_pv=True):
    jargon_map = jargon_map or COMMON_JARGON_REPLACEMENTS
    typo_map = typo_map or COMMON_SPELLING_FIXES

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", raw_text) if p.strip()]
    if not paragraphs:
        paragraphs = [raw_text.strip()] if raw_text.strip() else []

    out_paragraphs = []
    passive_pattern = re.compile(r'\b(?:am|is|are|was|were|be|been|being)\s+(?:\w+ed|written|made|done|seen|given|taken|built|chosen|known|shown|found|said|held|sent)\b', re.IGNORECASE)

    for p in paragraphs:
        # Check if heading
        if p.startswith("#"):
            heading_level = len(p) - len(p.lstrip("#"))
            heading_text = html.escape(p.lstrip("#").strip())
            h_tag = f"h{min(max(heading_level, 1), 4)}"
            out_paragraphs.append(
                f"<{h_tag} style='color:#0f172a; margin-top:24px; margin-bottom:8px; border-bottom:1px solid #e2e8f0; padding-bottom:4px;'>"
                f"{heading_text}</{h_tag}>"
            )
            continue

        # Split into sentences while preserving trailing delimiter
        raw_sents = [s.strip() for s in re.split(r"([.!?]+\s*)", p) if s.strip()]
        reconstructed = []
        idx = 0
        while idx < len(raw_sents):
            s_part = raw_sents[idx]
            if idx + 1 < len(raw_sents) and re.match(r"^[.!?]+\s*$", raw_sents[idx + 1]):
                s_part += raw_sents[idx + 1]
                idx += 2
            else:
                idx += 1
            reconstructed.append(s_part)

        p_html_parts = []
        for s in reconstructed:
            words = re.findall(r"\b\w+\b", s)
            is_long = len(words) > 25
            is_passive = bool(passive_pattern.search(s))

            s_escaped = html.escape(s)

            # 1. Highlight target keyword
            if hl_kw and keyword and keyword.strip():
                kw = keyword.strip()
                s_escaped = re.sub(
                    rf"\b({re.escape(kw)})\b",
                    r'<span class="hl-kw" title="Target Focus Keyword">\1</span>',
                    s_escaped,
                    flags=re.IGNORECASE
                )

            # 2. Highlight typos
            if hl_tp:
                for typo, fix in typo_map.items():
                    s_escaped = re.sub(
                        rf"\b({re.escape(typo)})\b",
                        rf'<span class="hl-typo" title="Spelling Typo: Change to \'{fix}\'">\1 <small class="fix-tag">[&rarr; {fix}]</small></span>',
                        s_escaped,
                        flags=re.IGNORECASE
                    )

            # 3. Highlight redundancies & wordiness (multi-word phrases first)
            if hl_rd:
                for red, sim in COMMON_REDUNDANCIES.items():
                    s_escaped = re.sub(
                        rf"\b({re.escape(red)})\b",
                        rf'<span class="hl-redundant" title="Wordy/Redundant: Simplify to \'{sim}\'">\1 <small class="red-tag">[&rarr; {sim}]</small></span>',
                        s_escaped,
                        flags=re.IGNORECASE
                    )

            # 4. Highlight complex jargon words
            if hl_jg:
                for jg, sim in jargon_map.items():
                    s_escaped = re.sub(
                        rf"\b({re.escape(jg)})\b",
                        rf'<span class="hl-jargon" title="Complex Jargon: Consider \'{sim}\'">\1 <small class="sim-tag">[&rarr; {sim}]</small></span>',
                        s_escaped,
                        flags=re.IGNORECASE
                    )

            # 5. Highlight passive voice sentence
            if hl_pv and is_passive and not is_long:
                s_escaped = (
                    f'<span class="hl-passive" title="Passive voice sentence - switch to active voice for punchier clarity">'
                    f'{s_escaped}'
                    f'</span>'
                )

            # 6. Highlight run-on sentence wrapper
            if hl_ls and is_long:
                s_escaped = (
                    f'<span class="hl-long-sent" title="Run-on sentence ({len(words)} words - consider splitting)">'
                    f'{s_escaped}'
                    f'</span>'
                )

            p_html_parts.append(s_escaped)

        out_paragraphs.append(f"<p style='margin-bottom: 16px; line-height: 1.8; color: #1e293b;'>{' '.join(p_html_parts)}</p>")

    return "\n".join(out_paragraphs)


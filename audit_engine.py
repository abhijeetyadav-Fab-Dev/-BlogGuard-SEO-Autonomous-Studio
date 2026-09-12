import re
import html

COMMON_SPELLING_FIXES = {
    "alot": "a lot",
    "recieve": "receive",
    "acheive": "achieve",
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
        red_examples = ", ".join([f"'{r.get('phrase', r.get('Redundant Phrase'))}' -> '{r.get('replacement', r.get('Simpler Alternative'))}'" for r in redundancies_info[:3]])
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
        "yoast": evaluate_yoast_seo(data, keyword=keyword),
        "aeo": evaluate_aeo_readiness(data, keyword=keyword),
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


# ---------------------------------------------------------------------------
# 5. YOAST SEO OFFICIAL CRITERIA & READABILITY SCORING ENGINE
# ---------------------------------------------------------------------------
YOAST_TRANSITION_WORDS = {
    "above all", "accordingly", "additionally", "after all", "afterward", "afterwards",
    "also", "alternatively", "although", "and yet", "as a consequence", "as a matter of fact",
    "as a result", "as an illustration", "as well as", "at the same time", "besides",
    "certainly", "clearly", "consequently", "conversely", "correspondingly", "despite",
    "differently", "due to", "earlier", "especially", "even if", "even so", "even though",
    "evidently", "finally", "first", "first of all", "firstly", "for example", "for instance",
    "for one thing", "for that reason", "for this reason", "further", "furthermore",
    "hence", "however", "in addition", "in brief", "in case", "in conclusion",
    "in contrast", "in fact", "in general", "in order to", "in other words",
    "in particular", "in short", "in summary", "in the end", "in the first place",
    "in the meantime", "in the same way", "in truth", "indeed", "initially",
    "instead", "last but not least", "lastly", "later", "likewise", "meanwhile",
    "moreover", "naturally", "nevertheless", "next", "nonetheless", "not only",
    "notably", "obviously", "on the contrary", "on the one hand", "on the other hand",
    "otherwise", "overall", "particularly", "rather", "regardless", "second",
    "secondly", "similarly", "simultaneously", "since", "so", "specifically",
    "still", "subsequently", "such as", "that is to say", "then", "therefore",
    "third", "thirdly", "this is why", "though", "thus", "to begin with",
    "to clarify", "to conclude", "to illustrate", "to put it another way",
    "to sum up", "to summarize", "undoubtedly", "whereas", "while", "yet"
}


def evaluate_yoast_seo(page_data, keyword=None):
    """
    Evaluates article data against Yoast SEO's 14 Focus Keyphrase Criteria
    and 7 Readability Criteria, returning traffic lights (good, ok, bad) and scores.
    """
    kw = (keyword or page_data.get("suggested_keyword") or "").strip().lower()
    title = page_data.get("title", "")
    title_lower = title.lower()
    meta_desc = page_data.get("meta_description", "")
    url = page_data.get("url", "") or page_data.get("final_url", "")
    clean_text = page_data.get("clean_text", "")
    text_lower = clean_text.lower()
    words = page_data.get("words", [])
    word_count = len(words) or len(re.findall(r"\b[\w'-]+\b", clean_text))
    sentences = [s.strip() for s in re.split(r"[.!?]+", clean_text) if s.strip()]
    sentence_count = len(sentences) or 1
    h1_list = page_data.get("h1_list", [])
    h2_list = page_data.get("h2_list", [])
    h3_list = page_data.get("h3_list", [])
    all_subheadings = h2_list + h3_list
    images = page_data.get("images", [])
    internal_links_count = page_data.get("internal_links_count", 0)
    citation_links = page_data.get("citation_links", [])
    external_links_count = page_data.get("external_links_count", 0) + len(citation_links)

    kw_words = len(kw.split()) if kw else 0

    # -------------------------------------------------------------------------
    # PART 1: 14 YOAST SEO (KEYPHRASE) CRITERIA
    # -------------------------------------------------------------------------
    seo_items = []

    # 1. Keyphrase in SEO Title
    if not kw:
        seo_items.append({
            "name": "Focus Keyphrase",
            "status": "bad",
            "title": "Keyphrase in Title",
            "feedback": "No focus keyphrase specified. Set a keyphrase to enable full Yoast analysis.",
            "recommendation": "Provide a target focus keyphrase for this article."
        })
    elif kw in title_lower:
        seo_items.append({
            "name": "Keyphrase in Title",
            "status": "good",
            "title": "Keyphrase in SEO Title",
            "feedback": f"The focus keyphrase '{kw}' appears in the SEO title.",
            "recommendation": "Maintain keyphrase relevance in future revisions."
        })
    else:
        seo_items.append({
            "name": "Keyphrase in Title",
            "status": "bad",
            "title": "Keyphrase in SEO Title",
            "feedback": f"The focus keyphrase '{kw}' does not appear in the SEO title.",
            "recommendation": f"Add '{kw}' to your SEO title tag."
        })

    # 2. Keyphrase at beginning of SEO Title
    if kw and kw in title_lower:
        idx = title_lower.find(kw)
        if idx <= len(title) * 0.45:
            seo_items.append({
                "name": "Keyphrase at Title Start",
                "status": "good",
                "title": "Keyphrase at Beginning of Title",
                "feedback": "The focus keyphrase appears at or near the beginning of the SEO title.",
                "recommendation": "Great for search engine crawlers and click-through visibility."
            })
        else:
            seo_items.append({
                "name": "Keyphrase at Title Start",
                "status": "ok",
                "title": "Keyphrase at Beginning of Title",
                "feedback": "The keyphrase appears in the title, but not near the beginning.",
                "recommendation": "Move the focus keyphrase closer to the front of the title."
            })
    elif kw:
        seo_items.append({
            "name": "Keyphrase at Title Start",
            "status": "bad",
            "title": "Keyphrase at Beginning of Title",
            "feedback": "The focus keyphrase is not in the title at all.",
            "recommendation": "Place the focus keyphrase at the start of your SEO title."
        })

    # 3. SEO Title Width / Length
    t_len = len(title)
    if 35 <= t_len <= 65:
        seo_items.append({
            "name": "Title Width",
            "status": "good",
            "title": "SEO Title Length",
            "feedback": f"The SEO title is {t_len} characters long (optimal: 35-65 characters).",
            "recommendation": "Title fits Google desktop and mobile search snippets perfectly."
        })
    elif 25 <= t_len < 35 or 66 <= t_len <= 75:
        seo_items.append({
            "name": "Title Width",
            "status": "ok",
            "title": "SEO Title Length",
            "feedback": f"The SEO title is {t_len} characters long.",
            "recommendation": "Optimal snippet length is 35-65 characters to prevent truncation."
        })
    else:
        seo_items.append({
            "name": "Title Width",
            "status": "bad",
            "title": "SEO Title Length",
            "feedback": f"The SEO title is {t_len} characters long (too {'short' if t_len < 25 else 'long'}).",
            "recommendation": "Adjust title length to 35-65 characters."
        })

    # 4. Keyphrase in Meta Description
    if not meta_desc:
        seo_items.append({
            "name": "Keyphrase in Meta Description",
            "status": "bad",
            "title": "Keyphrase in Meta Description",
            "feedback": "No meta description has been specified.",
            "recommendation": "Add a meta description containing your focus keyphrase."
        })
    elif kw and kw in meta_desc.lower():
        seo_items.append({
            "name": "Keyphrase in Meta Description",
            "status": "good",
            "title": "Keyphrase in Meta Description",
            "feedback": f"The focus keyphrase '{kw}' appears in the meta description.",
            "recommendation": "Well done. Google often bolds matching keyphrases in SERP snippets."
        })
    else:
        seo_items.append({
            "name": "Keyphrase in Meta Description",
            "status": "bad",
            "title": "Keyphrase in Meta Description",
            "feedback": f"The focus keyphrase '{kw}' does not appear in the meta description.",
            "recommendation": f"Include '{kw}' naturally inside your meta description."
        })

    # 5. Meta Description Length
    m_len = len(meta_desc)
    if 120 <= m_len <= 156:
        seo_items.append({
            "name": "Meta Description Length",
            "status": "good",
            "title": "Meta Description Length",
            "feedback": f"Meta description is {m_len} characters (optimal: 120-156).",
            "recommendation": "Fits desktop and mobile SERPs without truncation."
        })
    elif 80 <= m_len < 120 or 157 <= m_len <= 175:
        seo_items.append({
            "name": "Meta Description Length",
            "status": "ok",
            "title": "Meta Description Length",
            "feedback": f"Meta description is {m_len} characters.",
            "recommendation": "Aim for 120-156 characters for optimal SERP display."
        })
    else:
        seo_items.append({
            "name": "Meta Description Length",
            "status": "bad",
            "title": "Meta Description Length",
            "feedback": f"Meta description is {m_len} characters ({'missing' if m_len == 0 else ('too short' if m_len < 80 else 'too long')}).",
            "recommendation": "Write a concise meta description between 120 and 156 characters."
        })

    # 6. Keyphrase in URL Slug
    url_slug = url.split("?")[0].rstrip("/").split("/")[-1].lower() if url else ""
    if kw and all(word in url_slug for word in kw.split()):
        seo_items.append({
            "name": "Keyphrase in Slug",
            "status": "good",
            "title": "Keyphrase in URL Slug",
            "feedback": f"All focus keyphrase terms appear in the URL slug ('{url_slug}').",
            "recommendation": "Clean and descriptive permalink structure."
        })
    elif kw and any(word in url_slug for word in kw.split() if len(word) > 3):
        seo_items.append({
            "name": "Keyphrase in Slug",
            "status": "ok",
            "title": "Keyphrase in URL Slug",
            "feedback": f"Part of the keyphrase appears in the URL slug ('{url_slug}').",
            "recommendation": "Include the complete focus keyphrase in your permalink slug."
        })
    else:
        seo_items.append({
            "name": "Keyphrase in Slug",
            "status": "bad",
            "title": "Keyphrase in URL Slug",
            "feedback": "The focus keyphrase does not appear in the URL slug.",
            "recommendation": f"Include '{kw}' in the URL permalink slug."
        })

    # 7. Keyphrase in Introduction
    first_paragraph = clean_text[:600].lower()
    if kw and kw in first_paragraph:
        seo_items.append({
            "name": "Keyphrase in Intro",
            "status": "good",
            "title": "Keyphrase in Introduction",
            "feedback": "Your focus keyphrase appears in the introductory paragraph.",
            "recommendation": "Strong topical signal established in the opening section."
        })
    else:
        seo_items.append({
            "name": "Keyphrase in Intro",
            "status": "bad",
            "title": "Keyphrase in Introduction",
            "feedback": "The focus keyphrase does not appear in the first paragraph.",
            "recommendation": f"Include '{kw}' in the very first 1-2 sentences of the article."
        })

    # 8. Keyphrase Density
    if kw and word_count > 0:
        kw_matches = len(re.findall(rf"\b{re.escape(kw)}\b", text_lower))
        density = round((kw_matches * kw_words / word_count) * 100, 2)
        if 0.5 <= density <= 3.0:
            seo_items.append({
                "name": "Keyphrase Density",
                "status": "good",
                "title": "Keyphrase Density",
                "feedback": f"The focus keyphrase occurs {kw_matches} times ({density}%). Great balance.",
                "recommendation": "Neither under-optimized nor keyword stuffed."
            })
        elif (0.3 <= density < 0.5) or (3.0 < density <= 3.5):
            seo_items.append({
                "name": "Keyphrase Density",
                "status": "ok",
                "title": "Keyphrase Density",
                "feedback": f"Keyphrase occurs {kw_matches} times ({density}%).",
                "recommendation": "Aim for keyphrase density between 0.5% and 3.0%."
            })
        else:
            seo_items.append({
                "name": "Keyphrase Density",
                "status": "bad",
                "title": "Keyphrase Density",
                "feedback": f"Keyphrase density is {density}% ({kw_matches} occurrences in {word_count} words).",
                "recommendation": f"{'Increase mentions of' if density < 0.3 else 'Reduce over-use of'} '{kw}' to achieve 0.5%–3.0%."
            })
    else:
        seo_items.append({
            "name": "Keyphrase Density",
            "status": "bad",
            "title": "Keyphrase Density",
            "feedback": "Cannot calculate keyphrase density without target keyword and content.",
            "recommendation": "Define a focus keyword."
        })

    # 9. Keyphrase in Subheadings (H2 / H3)
    if all_subheadings:
        matching_subs = [h for h in all_subheadings if kw and kw in h.lower()]
        sub_ratio = len(matching_subs) / len(all_subheadings)
        if 0.30 <= sub_ratio <= 0.75:
            seo_items.append({
                "name": "Keyphrase in Subheadings",
                "status": "good",
                "title": "Keyphrase in Subheadings",
                "feedback": f"{len(matching_subs)} of {len(all_subheadings)} subheadings ({round(sub_ratio*100)}%) contain your focus keyphrase.",
                "recommendation": "Optimal subheading topical alignment."
            })
        elif len(matching_subs) > 0:
            seo_items.append({
                "name": "Keyphrase in Subheadings",
                "status": "ok",
                "title": "Keyphrase in Subheadings",
                "feedback": f"{len(matching_subs)} of {len(all_subheadings)} subheadings contain your focus keyphrase ({round(sub_ratio*100)}%).",
                "recommendation": "Recommended target is between 30% and 75% of H2/H3 subheadings."
            })
        else:
            seo_items.append({
                "name": "Keyphrase in Subheadings",
                "status": "bad",
                "title": "Keyphrase in Subheadings",
                "feedback": f"None of your {len(all_subheadings)} subheadings contain the focus keyphrase.",
                "recommendation": f"Add '{kw}' to at least one or two H2 subheadings."
            })
    else:
        seo_items.append({
            "name": "Keyphrase in Subheadings",
            "status": "bad",
            "title": "Keyphrase in Subheadings",
            "feedback": "No H2 or H3 subheadings found in article.",
            "recommendation": "Organize your article into distinct sections using H2 subheadings."
        })

    # 10. Image Alt Attributes
    if images:
        missing_alt = len([img for img in images if not img.get("has_alt") and not img.get("alt")])
        kw_alt = len([img for img in images if kw and kw in (img.get("alt") or "").lower()])
        if missing_alt == 0 and kw_alt > 0:
            seo_items.append({
                "name": "Image Alt Attributes",
                "status": "good",
                "title": "Image Alt Attributes",
                "feedback": f"All {len(images)} images have alt attributes, and {kw_alt} image(s) include the focus keyphrase.",
                "recommendation": "Optimal accessibility and Google Image search indexing."
            })
        elif missing_alt == 0 and kw_alt == 0:
            seo_items.append({
                "name": "Image Alt Attributes",
                "status": "ok",
                "title": "Image Alt Attributes",
                "feedback": f"All {len(images)} images have alt attributes, but none contain the focus keyphrase.",
                "recommendation": f"Consider adding '{kw}' to an image alt tag that directly illustrates the topic."
            })
        else:
            seo_items.append({
                "name": "Image Alt Attributes",
                "status": "bad",
                "title": "Image Alt Attributes",
                "feedback": f"{missing_alt} of {len(images)} image(s) are missing alt attributes.",
                "recommendation": "Add descriptive alt attributes containing your keyphrase to all images."
            })
    else:
        seo_items.append({
            "name": "Image Alt Attributes",
            "status": "bad",
            "title": "Image Alt Attributes",
            "feedback": "No images appear on this page.",
            "recommendation": "Add at least one relevant image or graphic with descriptive alt text."
        })

    # 11. Internal Links
    if internal_links_count >= 1:
        seo_items.append({
            "name": "Internal Links",
            "status": "good",
            "title": "Internal Links",
            "feedback": f"Found {internal_links_count} internal link(s).",
            "recommendation": "Great for establishing topic clusters and distributing PageRank."
        })
    else:
        seo_items.append({
            "name": "Internal Links",
            "status": "bad",
            "title": "Internal Links",
            "feedback": "No internal links found on this page.",
            "recommendation": "Add internal links pointing to relevant cornerstone content on your domain."
        })

    # 12. Outbound / External Links
    if external_links_count >= 1:
        seo_items.append({
            "name": "Outbound Links",
            "status": "good",
            "title": "Outbound Links",
            "feedback": f"Found {external_links_count} outbound link(s) / authoritative source citation(s).",
            "recommendation": "Demonstrates research rigor and aids E-E-A-T trust signals."
        })
    else:
        seo_items.append({
            "name": "Outbound Links",
            "status": "bad",
            "title": "Outbound Links",
            "feedback": "No outbound links found on this page.",
            "recommendation": "Add at least one external link to an authoritative, trustworthy source."
        })

    # 13. Text Length
    if word_count >= 300:
        seo_items.append({
            "name": "Text Length",
            "status": "good",
            "title": "Text Word Count",
            "feedback": f"Text contains {word_count:,} words (exceeds the 300-word Yoast minimum).",
            "recommendation": "Solid depth for search engine evaluation."
        })
    elif word_count >= 250:
        seo_items.append({
            "name": "Text Length",
            "status": "ok",
            "title": "Text Word Count",
            "feedback": f"Text contains {word_count} words.",
            "recommendation": "The recommended minimum is 300 words for standard blog posts."
        })
    else:
        seo_items.append({
            "name": "Text Length",
            "status": "bad",
            "title": "Text Word Count",
            "feedback": f"Text contains {word_count} words (below 300-word minimum).",
            "recommendation": "Expand your content with deeper insights to rank competitively."
        })

    # 14. Keyphrase Length
    if 1 <= kw_words <= 4:
        seo_items.append({
            "name": "Keyphrase Length",
            "status": "good",
            "title": "Keyphrase Length",
            "feedback": f"Keyphrase is {kw_words} word(s) long (optimal: 1-4 words).",
            "recommendation": "Concise and focused search intent."
        })
    elif kw_words == 5:
        seo_items.append({
            "name": "Keyphrase Length",
            "status": "ok",
            "title": "Keyphrase Length",
            "feedback": f"Keyphrase is {kw_words} words long.",
            "recommendation": "Consider shortening slightly for broader search intent."
        })
    else:
        seo_items.append({
            "name": "Keyphrase Length",
            "status": "bad",
            "title": "Keyphrase Length",
            "feedback": f"Keyphrase is {kw_words} words long ({'empty' if kw_words == 0 else 'too long'}).",
            "recommendation": "Target focus keyphrases between 1 and 4 words."
        })

    # -------------------------------------------------------------------------
    # PART 2: 7 YOAST READABILITY CRITERIA
    # -------------------------------------------------------------------------
    readability_items = []
    read_data = page_data.get("readability", {})
    flesch_score = read_data.get("flesch_reading_ease", 50.0)

    # 1. Flesch Reading Ease
    if flesch_score >= 60.0:
        readability_items.append({
            "name": "Flesch Reading Ease",
            "status": "good",
            "title": "Flesch Reading Ease",
            "feedback": f"Score is {flesch_score:.1f} (conversational Grade 7-8 web standard).",
            "recommendation": "Easy for standard web readers to scan and understand."
        })
    elif flesch_score >= 50.0:
        readability_items.append({
            "name": "Flesch Reading Ease",
            "status": "ok",
            "title": "Flesch Reading Ease",
            "feedback": f"Score is {flesch_score:.1f} (fairly difficult).",
            "recommendation": "Aim for a Flesch score of 60+ by shortening sentences and replacing jargon."
        })
    else:
        readability_items.append({
            "name": "Flesch Reading Ease",
            "status": "bad",
            "title": "Flesch Reading Ease",
            "feedback": f"Score is {flesch_score:.1f} (difficult / college level).",
            "recommendation": "Break up compound sentences and use conversational vocabulary."
        })

    # 2. Passive Voice Percentage
    passive_info = detect_passive_voice(sentences)
    pv_pct = passive_info.get("percentage", 0.0)
    if pv_pct <= 10.0:
        readability_items.append({
            "name": "Passive Voice",
            "status": "good",
            "title": "Passive Voice Usage",
            "feedback": f"{pv_pct:.1f}% of sentences contain passive voice (target: <= 10%).",
            "recommendation": "Clear, direct, and active writing style."
        })
    elif pv_pct <= 15.0:
        readability_items.append({
            "name": "Passive Voice",
            "status": "ok",
            "title": "Passive Voice Usage",
            "feedback": f"{pv_pct:.1f}% of sentences contain passive voice.",
            "recommendation": "Reduce passive voice below 10% for punchier prose."
        })
    else:
        readability_items.append({
            "name": "Passive Voice",
            "status": "bad",
            "title": "Passive Voice Usage",
            "feedback": f"{pv_pct:.1f}% of sentences contain passive voice (exceeds 10% target).",
            "recommendation": "Rewrite passive sentences with direct subject-verb constructions."
        })

    # 3. Consecutive Sentences Check
    consec_runs = 0
    consec_words = []
    first_words = []
    for s in sentences:
        s_words = re.findall(r"\b\w+\b", s)
        if s_words:
            first_words.append(s_words[0].lower())

    for i in range(len(first_words) - 2):
        if first_words[i] == first_words[i+1] == first_words[i+2]:
            consec_runs += 1
            consec_words.append(first_words[i])

    if consec_runs == 0:
        readability_items.append({
            "name": "Consecutive Sentences",
            "status": "good",
            "title": "Consecutive Sentences",
            "feedback": "The text contains zero runs of 3+ consecutive sentences starting with the same word.",
            "recommendation": "Great sentence variety."
        })
    else:
        readability_items.append({
            "name": "Consecutive Sentences",
            "status": "bad",
            "title": "Consecutive Sentences",
            "feedback": f"Found {consec_runs} instance(s) where 3+ consecutive sentences start with the same word ('{', '.join(set(consec_words))}').",
            "recommendation": "Vary your sentence starters to keep readers engaged."
        })

    # 4. Subheading Distribution (no section over 300 words without an H2/H3)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", clean_text) if p.strip()]
    if word_count > 300 and not all_subheadings:
        readability_items.append({
            "name": "Subheading Distribution",
            "status": "bad",
            "title": "Subheading Distribution",
            "feedback": f"Text is {word_count} words but has 0 subheadings.",
            "recommendation": "Add subheadings every 250-300 words to break up wall of text."
        })
    else:
        readability_items.append({
            "name": "Subheading Distribution",
            "status": "good",
            "title": "Subheading Distribution",
            "feedback": f"Subheadings are distributed appropriately across the {word_count:,} words.",
            "recommendation": "Clear visual signposts for readers."
        })

    # 5. Paragraph Length (no paragraph over 150 words)
    long_paragraphs = [p for p in paragraphs if len(re.findall(r"\b[\w'-]+\b", p)) > 150]
    if not long_paragraphs:
        readability_items.append({
            "name": "Paragraph Length",
            "status": "good",
            "title": "Paragraph Length",
            "feedback": f"All {len(paragraphs)} paragraphs are under 150 words.",
            "recommendation": "Bite-sized mobile friendly layout."
        })
    else:
        readability_items.append({
            "name": "Paragraph Length",
            "status": "bad",
            "title": "Paragraph Length",
            "feedback": f"{len(long_paragraphs)} paragraph(s) contain more than 150 words.",
            "recommendation": "Split long paragraphs into 2-3 shorter chunks."
        })

    # 6. Sentence Length (<= 25% of sentences contain > 20 words)
    long_sentences = [s for s in sentences if len(re.findall(r"\b\w+\b", s)) > 20]
    long_sent_pct = round((len(long_sentences) / sentence_count) * 100, 1)
    if long_sent_pct <= 25.0:
        readability_items.append({
            "name": "Sentence Length",
            "status": "good",
            "title": "Sentence Length",
            "feedback": f"{long_sent_pct}% of sentences contain more than 20 words (target: <= 25%).",
            "recommendation": "Sentences are concise and easy to parse."
        })
    else:
        readability_items.append({
            "name": "Sentence Length",
            "status": "bad",
            "title": "Sentence Length",
            "feedback": f"{long_sent_pct}% of sentences contain more than 20 words (exceeds 25% target).",
            "recommendation": "Shorten long sentences by splitting clauses into independent sentences."
        })

    # 7. Transition Words (>= 30% of sentences contain transition words)
    trans_count = 0
    for s in sentences:
        s_low = s.lower()
        if any(re.search(rf"\b{re.escape(tw)}\b", s_low) for tw in YOAST_TRANSITION_WORDS):
            trans_count += 1

    trans_pct = round((trans_count / sentence_count) * 100, 1)
    if trans_pct >= 30.0:
        readability_items.append({
            "name": "Transition Words",
            "status": "good",
            "title": "Transition Words Usage",
            "feedback": f"{trans_pct}% of sentences contain transition words (exceeds 30% target).",
            "recommendation": "Smooth narrative flow and logical progression."
        })
    elif trans_pct >= 20.0:
        readability_items.append({
            "name": "Transition Words",
            "status": "ok",
            "title": "Transition Words Usage",
            "feedback": f"{trans_pct}% of sentences contain transition words.",
            "recommendation": "Aim for at least 30% of sentences containing transition words (e.g. 'furthermore', 'however', 'as a result')."
        })
    else:
        readability_items.append({
            "name": "Transition Words",
            "status": "bad",
            "title": "Transition Words Usage",
            "feedback": f"Only {trans_pct}% of sentences contain transition words (below 30% target).",
            "recommendation": "Add transition phrases ('furthermore', 'however', 'consequently', 'for example') to improve reading flow."
        })

    # -------------------------------------------------------------------------
    # PART 3: CALCULATE OVERALL TRAFFIC LIGHTS
    # -------------------------------------------------------------------------
    def _calc_score(items):
        weights = {"good": 9, "ok": 6, "bad": 3}
        if not items:
            return 0, "bad"
        total_pts = sum(weights[i["status"]] for i in items)
        max_pts = len(items) * 9
        score_pct = round((total_pts / max_pts) * 100)
        avg = total_pts / len(items)
        if avg >= 7.5:
            verdict = "good"
        elif avg >= 5.0:
            verdict = "ok"
        else:
            verdict = "bad"
        return score_pct, verdict

    seo_pct, seo_verdict = _calc_score(seo_items)
    read_pct, read_verdict = _calc_score(readability_items)

    traffic_light_badges = {
        "good": "🟢 Good",
        "ok": "🟠 OK",
        "bad": "🔴 Needs Improvement"
    }

    return {
        "seo": {
            "score": seo_pct,
            "verdict": seo_verdict,
            "badge": traffic_light_badges[seo_verdict],
            "passed_count": len([i for i in seo_items if i["status"] == "good"]),
            "ok_count": len([i for i in seo_items if i["status"] == "ok"]),
            "bad_count": len([i for i in seo_items if i["status"] == "bad"]),
            "total": len(seo_items),
            "items": seo_items,
        },
        "readability": {
            "score": read_pct,
            "verdict": read_verdict,
            "badge": traffic_light_badges[read_verdict],
            "passed_count": len([i for i in readability_items if i["status"] == "good"]),
            "ok_count": len([i for i in readability_items if i["status"] == "ok"]),
            "bad_count": len([i for i in readability_items if i["status"] == "bad"]),
            "total": len(readability_items),
            "items": readability_items,
            "metrics": {
                "flesch_score": flesch_score,
                "passive_voice_pct": pv_pct,
                "sentence_length_pct": long_sent_pct,
                "transition_words_pct": trans_pct,
                "consecutive_runs": consec_runs,
                "long_paragraphs": len(long_paragraphs),
            }
        },
        "keyword": kw,
    }


# ---------------------------------------------------------------------------
# 6. SAFE IN-TEXT EDITORIAL AUTO-PATCHER
# ---------------------------------------------------------------------------
def apply_safe_simplifications(clean_text):
    """
    Safely applies non-destructive editorial simplifications to blog drafts:
    1. Corrects confirmed spelling mistakes.
    2. Substitutes wordy redundancies with concise alternatives.
    3. Replaces corporate jargon with plain conversational English.
    Returns the patched text and an audit trail of every change applied.
    """
    if not clean_text:
        return {
            "original_text": "",
            "patched_text": "",
            "total_replacements": 0,
            "replacements": [],
            "spelling_fixes": [],
            "redundancy_fixes": [],
            "jargon_fixes": [],
            "words_saved": 0,
        }

    patched = clean_text
    replacements = []

    # 1. Spelling Fixes
    for typo, correct in COMMON_SPELLING_FIXES.items():
        pattern = re.compile(rf"\b{re.escape(typo)}\b", re.IGNORECASE)
        matches = pattern.findall(patched)
        if matches:
            patched = pattern.sub(correct, patched)
            replacements.append({
                "type": "spelling",
                "category": "Spelling Correction",
                "original": typo,
                "replacement": correct,
                "occurrences": len(matches),
            })

    # 2. Redundancy Fixes
    for red, concise in COMMON_REDUNDANCIES.items():
        pattern = re.compile(rf"\b{re.escape(red)}\b", re.IGNORECASE)
        matches = pattern.findall(patched)
        if matches:
            patched = pattern.sub(concise, patched)
            replacements.append({
                "type": "redundancy",
                "category": "Redundancy Removal",
                "original": red,
                "replacement": concise,
                "occurrences": len(matches),
            })

    # 3. Jargon Simplifications
    for jg, plain in COMMON_JARGON_REPLACEMENTS.items():
        pattern = re.compile(rf"\b{re.escape(jg)}\b", re.IGNORECASE)
        matches = pattern.findall(patched)
        if matches:
            clean_plain = plain.split("/")[0].strip()
            patched = pattern.sub(clean_plain, patched)
            replacements.append({
                "type": "jargon",
                "category": "Jargon Simplification",
                "original": jg,
                "replacement": clean_plain,
                "occurrences": len(matches),
            })

    orig_words = len(re.findall(r"\b\w+\b", clean_text))
    new_words = len(re.findall(r"\b\w+\b", patched))
    words_saved = max(0, orig_words - new_words)

    return {
        "original_text": clean_text,
        "patched_text": patched,
        "total_replacements": sum(r["occurrences"] for r in replacements),
        "replacements": replacements,
        "spelling_fixes": [r for r in replacements if r["type"] == "spelling"],
        "redundancy_fixes": [r for r in replacements if r["type"] == "redundancy"],
        "jargon_fixes": [r for r in replacements if r["type"] == "jargon"],
        "original_word_count": orig_words,
        "patched_word_count": new_words,
        "words_saved": words_saved,
    }


# ---------------------------------------------------------------------------
# 7. AEO & GEO (AI SEARCH ENGINE OPTIMIZATION) SCORING ENGINE
# ---------------------------------------------------------------------------
def evaluate_aeo_readiness(page_data, keyword=None):
    """
    Evaluates content for AEO (Answer Engine Optimization) & GEO (Generative Engine Optimization).
    Measures likelihood of citations by Perplexity, ChatGPT Search, and Google AI Overviews (SGE).
    Scored from 0 to 100 across 4 pillars (25 pts each):
    1. Direct Answer Delivery (Clear answers in headings and opening paragraphs)
    2. Quantitative Data & Entity Density (metrics, %, $, years)
    3. Authority Attribution & Quotations (citations, source attribution)
    4. Structured Extractability (lists, tables, FAQ schema)
    """
    clean_text = page_data.get("clean_text", "")
    word_count = len(re.findall(r"\b\w+\b", clean_text))
    criteria = []

    # Pillar 1: Direct Answer Delivery (0 - 25 pts)
    answer_starter_pattern = re.compile(
        r"(?i)\b(?:is defined as|refers to|works by|consists of|to achieve this|the primary cause|the key difference|for example|in summary|steps to|first,|the best way)\b"
    )
    starters_found = len(answer_starter_pattern.findall(clean_text))
    if starters_found >= 4:
        p1_score = 25
        p1_status = "good"
        p1_advice = f"Strong direct answer delivery detected ({starters_found} direct answer markers found)."
    elif starters_found >= 1:
        p1_score = 15
        p1_status = "ok"
        p1_advice = f"Moderate direct answer markers ({starters_found}). Ensure every H2 section answers the user's question directly in the first 2 sentences."
    else:
        p1_score = 5
        p1_status = "bad"
        p1_advice = "No direct answer structures detected. AI engines cite concise definition sentences (e.g. '[Concept] is...') placed immediately under headings."

    criteria.append({
        "pillar": "Direct Answer Delivery",
        "score": p1_score,
        "max": 25,
        "status": p1_status,
        "advice": p1_advice,
    })

    # Pillar 2: Quantitative Data & Entity Density (0 - 25 pts)
    stats_matches = re.findall(r"\b\d+[\.,]?\d*%\b|\$\d+[\.,]?\d*|\b(?:19\d\d|20[2-9]\d)\b", clean_text)
    stats_count = len(stats_matches)
    stats_per_1k = round((stats_count / max(1, word_count)) * 1000, 1)

    if stats_per_1k >= 6 or stats_count >= 8:
        p2_score = 25
        p2_status = "good"
        p2_advice = f"Excellent empirical data density ({stats_count} data/date/metric points detected, ~{stats_per_1k}/1,000 words)."
    elif stats_per_1k >= 2 or stats_count >= 3:
        p2_score = 15
        p2_status = "ok"
        p2_advice = f"Moderate data density ({stats_count} metrics). Generative engines heavily favor articles containing specific statistics, benchmarks, or dates."
    else:
        p2_score = 5
        p2_status = "bad"
        p2_advice = "Low factual data density. Add concrete percentages, monetary figures, years, or study findings to increase citation probability."

    criteria.append({
        "pillar": "Factual & Entity Density",
        "score": p2_score,
        "max": 25,
        "status": p2_status,
        "advice": p2_advice,
    })

    # Pillar 3: Authority Attribution & Source Anchors (0 - 25 pts)
    in_text_sources = page_data.get("in_text_sources", 0)
    citation_links = page_data.get("citation_links", [])
    total_sources = in_text_sources + len(citation_links)

    if total_sources >= 3:
        p3_score = 25
        p3_status = "good"
        p3_advice = f"Authoritative attribution present ({in_text_sources} in-text source phrases, {len(citation_links)} authority citations)."
    elif total_sources >= 1:
        p3_score = 15
        p3_status = "ok"
        p3_advice = "Some source attribution present. Include explicit phrases like 'According to research by...' or citations to academic/government domains."
    else:
        p3_score = 5
        p3_status = "bad"
        p3_advice = "Missing explicit source citations. LLMs penalize unsubstantiated claims and prioritize corroborated source references."

    criteria.append({
        "pillar": "Authority Citations & Sources",
        "score": p3_score,
        "max": 25,
        "status": p3_status,
        "advice": p3_advice,
    })

    # Pillar 4: Structured Extractability (0 - 25 pts)
    has_schema = bool(page_data.get("schema_types"))
    has_faq_schema = any("faq" in str(s).lower() for s in page_data.get("schema_types", []))
    has_steps_or_bullets = bool(re.search(r"(?m)^\s*[\*\-\•\d+\.]\s+", clean_text) or re.search(r"\b(?:step 1|step 2|1\.|2\.)\b", clean_text, re.I))

    p4_score = 0
    if has_steps_or_bullets:
        p4_score += 10
    if has_schema:
        p4_score += 10
    if has_faq_schema:
        p4_score += 5
    p4_score = min(25, p4_score)

    if p4_score >= 20:
        p4_status = "good"
        p4_advice = "High structural extractability (bullet points/numbered steps and JSON-LD schema detected)."
    elif p4_score >= 10:
        p4_status = "ok"
        p4_advice = "Moderate extractability. Add FAQPage schema or numbered step-by-step procedures to assist AI snippet extraction."
    else:
        p4_score = 5
        p4_status = "bad"
        p4_advice = "Poor extractability. Long unbroken text without bullet points or Schema.org markup is rarely selected for AI Overview cards."

    criteria.append({
        "pillar": "Structured Extractability",
        "score": p4_score,
        "max": 25,
        "status": p4_status,
        "advice": p4_advice,
    })

    total_aeo = sum(c["score"] for c in criteria)
    if total_aeo >= 80:
        verdict = "🟢 High AIO & Perplexity Citation Probability"
    elif total_aeo >= 60:
        verdict = "🟠 Moderate Citation Probability (Needs Data Density)"
    else:
        verdict = "🔴 Low Citation Probability (Content lacks structured proof points)"

    return {
        "aeo_score": total_aeo,
        "verdict": verdict,
        "criteria": criteria,
        "pillars": {c["pillar"]: c["score"] for c in criteria},
        "observations": [c["advice"] for c in criteria],
        "stats_count": stats_count,
        "attributions_count": total_sources,
        "extractability_score": p4_score,
    }


# ---------------------------------------------------------------------------
# 8. COMPETITOR SEMANTIC GAP & TF-IDF / N-GRAM ANALYZER
# ---------------------------------------------------------------------------
def analyze_competitor_semantic_gap(target_data, competitor_profiles, top_n=15, target_keyword=None):
    """
    Performs comparative semantic gap and TF-IDF analysis between the target
    blog post and crawled top ranking competitors.
    Returns:
    - Missing semantic keywords
    - Subtopic / Heading coverage gaps
    - Benchmarking metrics (Word count, Images, Citations)
    """
    target_text = (target_data.get("clean_text") or "").lower()
    target_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", target_text))
    target_h2s = [h.lower() for h in target_data.get("h2_list", [])]
    target_keyword = target_keyword or target_data.get("suggested_keyword") or ""

    if not competitor_profiles:
        return {
            "success": False,
            "target_keyword": target_keyword,
            "message": "No competitor profiles available for semantic gap comparison.",
            "missing_keywords": [],
            "missing_terms": [],
            "top_competitor_terms": [],
            "missing_topics": [],
            "benchmarks": {},
        }

    from crawler import STOP_WORDS

    comp_unigrams = {}
    comp_h2_topics = []
    total_comp_words = 0
    total_comp_imgs = 0
    total_comp_citations = 0

    for comp in competitor_profiles:
        words = comp.get("words")
        if not words and comp.get("clean_text"):
            words = re.findall(r"\b[a-zA-Z]{3,}\b", comp["clean_text"].lower())
        words = words or []
        total_comp_words += comp.get("word_count", 0) or len(words)
        total_comp_imgs += comp.get("images_count", 0)
        total_comp_citations += comp.get("citations_count", 0)

        for w in words:
            w_lower = w.lower()
            if len(w_lower) >= 4 and w_lower not in STOP_WORDS:
                comp_unigrams[w_lower] = comp_unigrams.get(w_lower, 0) + 1

        for h2 in comp.get("h2_list", []):
            comp_h2_topics.append({"topic": h2, "competitor_url": comp.get("url", "")})

    num_comps = max(1, len(competitor_profiles))
    avg_words = round(total_comp_words / num_comps)
    avg_imgs = round(total_comp_imgs / num_comps, 1)
    avg_citations = round(total_comp_citations / num_comps, 1)

    sorted_comp_words = sorted(comp_unigrams.items(), key=lambda x: x[1], reverse=True)
    missing_kw = []
    found_kw = []

    for w, freq in sorted_comp_words:
        if w not in target_words:
            missing_kw.append({
                "keyword": w,
                "competitor_frequency": freq,
                "importance": "High Impact" if freq >= 4 else "Medium Impact"
            })
        else:
            found_kw.append(w)
        if len(missing_kw) >= top_n:
            break

    missing_topics = []
    for t_item in comp_h2_topics:
        topic_text = t_item["topic"]
        topic_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", topic_text.lower()))
        matched = False
        for th in target_h2s:
            th_words = set(re.findall(r"\b[a-zA-Z]{3,}\b", th))
            if len(topic_words.intersection(th_words)) >= 2:
                matched = True
                break
        if not matched and len(topic_text) > 8:
            missing_topics.append(topic_text)

    unique_missing_topics = list(dict.fromkeys(missing_topics))[:8]

    target_word_count = len(target_data.get("words", []))
    target_img_count = len(target_data.get("images", []))
    target_cit_count = len(target_data.get("citation_links", []))

    benchmarks = {
        "word_count": {
            "target": target_word_count,
            "competitor_avg": avg_words,
            "gap": target_word_count - avg_words,
            "status": "Ahead" if target_word_count >= avg_words else f"Short by {avg_words - target_word_count:,} words"
        },
        "images": {
            "target": target_img_count,
            "competitor_avg": avg_imgs,
            "gap": target_img_count - avg_imgs,
            "status": "Ahead" if target_img_count >= avg_imgs else f"Add {round(avg_imgs - target_img_count)} images"
        },
        "citations": {
            "target": target_cit_count,
            "competitor_avg": avg_citations,
            "gap": target_cit_count - avg_citations,
            "status": "Ahead" if target_cit_count >= avg_citations else f"Add {round(avg_citations - target_cit_count)} authority links"
        }
    }

    return {
        "success": True,
        "target_keyword": target_keyword,
        "competitor_count": len(competitor_profiles),
        "missing_keywords": missing_kw,
        "missing_terms": [{"term": m["keyword"], "freq": m["competitor_frequency"]} for m in missing_kw],
        "top_competitor_terms": [w for w, _ in sorted_comp_words[:top_n]],
        "found_keywords_count": len(found_kw),
        "missing_subtopics": unique_missing_topics,
        "benchmarks": benchmarks,
    }


# ---------------------------------------------------------------------------
# 9. AUTONOMOUS FULL PIPELINE RUNNER
# ---------------------------------------------------------------------------
def run_autonomous_pipeline(url_or_text, keyword=None, serpapi_key=None, ai_key=None, ai_provider="deepseek", ai_model=None, save_history=True):
    """
    Executes an autonomous closed-loop audit & remediation run in a single pass:
    1. Crawls or parses content
    2. Audits 7 pillars + Yoast + AEO
    3. Applies safe text simplifications
    4. Gathers SERP intelligence and competitor semantic gaps (if SerpApi key provided)
    5. Runs AI Strategic Audit and FAQ Schema (if AI key provided)
    6. Persists snapshot to SQLite history
    """
    from crawler import fetch_html, parse_page_data
    from api_integrations import fetch_serp_intelligence, fetch_competitor_content, generate_deepseek_audit, generate_ai_faq_schema
    import db_history

    if isinstance(url_or_text, dict):
        article_data = url_or_text
    else:
        is_url = url_or_text.strip().startswith(("http://", "https://")) or ("." in url_or_text.split()[0] and "/" in url_or_text.split()[0])

        if is_url:
            fetch_res = fetch_html(url_or_text)
            article_data = parse_page_data(fetch_res)
        else:
            words = re.findall(r"\b[\w'-]+\b", url_or_text)
            sentences = [s.strip() for s in re.split(r"[.!?]+", url_or_text) if s.strip()]
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", url_or_text) if p.strip()]
            h1 = paragraphs[0][:80] if paragraphs else "Draft Post"
            article_data = {
                "url": "Offline Draft",
                "final_url": "Offline Draft",
                "title": h1,
                "meta_description": paragraphs[1][:150] if len(paragraphs) > 1 else "",
                "clean_text": url_or_text,
                "words": words,
                "word_count": len(words),
                "sentence_count": len(sentences),
                "paragraph_count": len(paragraphs),
                "reading_time_min": round(len(words) / 200, 1),
            "headings": [{"tag": "h1", "level": 1, "text": h1}],
            "h1_list": [h1],
            "h2_list": [],
            "h3_list": [],
            "h4_list": [],
            "hierarchy_valid": True,
            "images": [],
            "images_without_alt": [],
            "links": [],
            "internal_links_count": 0,
            "external_links_count": 0,
            "nofollow_links_count": 0,
            "citation_links": [],
            "in_text_sources": 0,
            "opengraph": {},
            "twitter_cards": {},
            "schema_types": [],
            "json_ld_list": [],
            "readability": {"flesch_reading_ease": 60.0, "flesch_kincaid_grade": 8.0},
            "long_sentences": [],
            "top_unigrams": [],
            "top_bigrams": [],
            "suggested_keyword": keyword or "",
        }

    audit_results = audit_page(article_data, keyword=keyword)
    patch_result = apply_safe_simplifications(article_data["clean_text"])

    serp_data = None
    competitor_gap = None
    if serpapi_key and audit_results.get("keyword"):
        serp_data = fetch_serp_intelligence(audit_results["keyword"], api_key=serpapi_key)
        if serp_data.get("success") and serp_data.get("competitors"):
            comp_profiles = fetch_competitor_content(serp_data["competitors"], max_comp=3)
            competitor_gap = analyze_competitor_semantic_gap(article_data, comp_profiles)

    ai_audit = None
    faq_schema = None
    if ai_key:
        ai_audit = generate_deepseek_audit(article_data, audit_results, api_key=ai_key, model=ai_model, provider=ai_provider)
        paa = serp_data.get("people_also_ask", []) if (serp_data and serp_data.get("success")) else []
        faq_schema = generate_ai_faq_schema(article_data, paa, api_key=ai_key, model=ai_model, provider=ai_provider)

    snapshot_id = None
    if save_history:
        try:
            snapshot_id = db_history.save_audit_snapshot(article_data, audit_results)
        except Exception:
            pass

    return {
        "article_data": article_data,
        "audit_results": audit_results,
        "safe_patch": patch_result,
        "serp_data": serp_data,
        "competitor_gap": competitor_gap,
        "ai_audit": ai_audit,
        "faq_schema": faq_schema,
        "snapshot_id": snapshot_id,
        "audit": audit_results,
        "patch": patch_result,
        "yoast": audit_results.get("yoast"),
        "aeo": audit_results.get("aeo"),
    }




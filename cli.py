#!/usr/bin/env python3
"""
BlogGuard SEO — Headless CLI & CI/CD Quality Gate
Enables developers to audit blog posts, sitemaps, and content drafts from the terminal
and enforce SEO quality scores in CI/CD deployment pipelines.
"""

import sys
import os
import argparse
import json
from datetime import datetime

# Guarantee UTF-8 stdout/stderr across Windows cmd & powershell
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import crawler
import audit_engine
import db_history


def cmd_audit(args):
    target = args.target.strip()
    keyword = args.keyword.strip() if args.keyword else None
    min_score = args.min_score

    print(f"🛡️ BlogGuard CLI: Auditing '{target}'...")
    if keyword:
        print(f"🎯 Target Keyword: '{keyword}'")

    save_hist = not args.no_history
    res = audit_engine.run_autonomous_pipeline(
        target,
        keyword=keyword,
        serpapi_key=args.serpapi_key,
        save_history=save_hist
    )

    art = res["article_data"]
    audit = res["audit_results"]
    score = audit["overall_score"]
    aeo = audit.get("aeo", {})
    aeo_score = aeo.get("aeo_score", 0)

    if args.json:
        out_data = {
            "url": art.get("url"),
            "title": art.get("title"),
            "keyword": audit.get("keyword"),
            "overall_score": score,
            "aeo_score": aeo_score,
            "pillar_scores": audit.get("scores", {}),
            "word_count": audit.get("word_count", 0),
            "reading_time_min": audit.get("reading_time_min", 0),
            "issues_count": len(audit.get("issues", [])),
            "issues": audit.get("issues", []),
            "snapshot_id": res.get("snapshot_id"),
        }
        print(json.dumps(out_data, indent=2))
    else:
        print("\n" + "=" * 60)
        print(f"📊 BlogGuard Overall SEO Score: {score}/100")
        print(f"🌐 AEO / GEO Citation Score:    {aeo_score}/100 ({aeo.get('verdict', 'N/A')})")
        print(f"📝 Word Count:                 {audit.get('word_count', 0):,} words ({audit.get('reading_time_min', 0)} min read)")
        print("-" * 60)
        print("PILLAR MATRIX:")
        for p, s in audit.get("scores", {}).items():
            print(f"  • {p:<26}: {s:>3}/100")
        print("-" * 60)
        print(f"🚨 Actionable Issues: {len(audit.get('issues', []))}")
        for i in audit.get("issues", [])[:5]:
            print(f"  [{i.get('severity', 'info').upper()}] {i.get('title')}: {i.get('fix')}")
        print("=" * 60)

    if min_score > 0:
        if score < min_score:
            print(f"\n❌ QUALITY GATE FAILED: Score {score} is below required threshold {min_score}.")
            sys.exit(1)
        else:
            print(f"\n✅ QUALITY GATE PASSED: Score {score} meets or exceeds required threshold {min_score}.")
            sys.exit(0)


def cmd_sitemap(args):
    domain = args.domain.strip()
    max_urls = args.max_urls
    print(f"🕷️ Discovering XML sitemap for '{domain}' (max: {max_urls})...")
    res = crawler.discover_and_parse_sitemap(domain, max_urls=max_urls)

    if not res.get("success"):
        print(f"❌ Error: {res.get('error')}")
        sys.exit(1)

    print(f"✅ Found sitemap: {res.get('sitemap_url')}")
    print(f"📑 Discovered {res.get('total_found')} published URLs:\n")

    if args.json:
        print(json.dumps(res, indent=2))
        return

    for idx, item in enumerate(res.get("urls", []), 1):
        print(f"  {idx:>2}. {item['url']} (Lastmod: {item.get('lastmod', 'N/A')})")


def cmd_history(args):
    url = args.url.strip() if args.url else None
    if args.velocity and url:
        vel = db_history.get_url_velocity(url)
        if not vel:
            print(f"No audit history found for '{url}'.")
            return
        print(f"📈 Audit Velocity for '{url}':")
        print(f"  Total Audits:  {vel['total_audits']}")
        print(f"  Initial Score: {vel['initial_score']} ({vel['first_audit_date']})")
        print(f"  Latest Score:  {vel['latest_score']} ({vel['latest_audit_date']})")
        print(f"  Score Delta:   {'+' if vel['score_delta'] >= 0 else ''}{vel['score_delta']} pts")
        print(f"  Word Delta:    {'+' if vel['word_delta'] >= 0 else ''}{vel['word_delta']} words")
        return

    hist = db_history.get_audit_history(url=url, limit=args.limit)
    if not hist:
        print("No audit history found in SQLite database.")
        return

    if args.json:
        print(json.dumps([dict(h) for h in hist], indent=2))
        return

    print(f"📈 Showing {len(hist)} audit snapshots:\n")
    for h in hist:
        print(f"  ID #{h['id']:<4} | {h['timestamp'][:19]} | Score: {h['overall_score']:>3}/100 | {h['url'][:45]}")


def cmd_fix(args):
    source = args.source.strip()
    if os.path.isfile(source):
        with open(source, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = source

    res = audit_engine.apply_safe_simplifications(text)
    if args.json:
        print(json.dumps(res, indent=2))
    elif args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(res["patched_text"])
        print(f"✅ Cleaned text written to '{args.output}'. Replacements applied: {res['total_replacements']}")
    else:
        print(res["patched_text"])


def main():
    parser = argparse.ArgumentParser(
        description="🛡️ BlogGuard SEO CLI: Autonomous audit & CI/CD quality gate."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. Audit
    p_audit = subparsers.add_parser("audit", help="Audit a live blog URL or draft file")
    p_audit.add_argument("target", help="URL or path to text/markdown file")
    p_audit.add_argument("-k", "--keyword", help="Target focus keyword")
    p_audit.add_argument("-m", "--min-score", type=int, default=0, help="Fails with exit code 1 if score is below this threshold")
    p_audit.add_argument("--json", action="store_true", help="Output results as JSON")
    p_audit.add_argument("--serpapi-key", help="Optional SerpApi key for competitor analysis")
    p_audit.add_argument("--no-history", action="store_true", help="Do not save snapshot to SQLite database")
    p_audit.set_defaults(func=cmd_audit)

    # 2. Sitemap
    p_sitemap = subparsers.add_parser("sitemap", help="Discover and parse XML sitemaps for a domain")
    p_sitemap.add_argument("domain", help="Domain or sitemap URL (e.g. https://example.com)")
    p_sitemap.add_argument("-n", "--max-urls", type=int, default=25, help="Max URLs to extract")
    p_sitemap.add_argument("--json", action="store_true", help="Output results as JSON")
    p_sitemap.set_defaults(func=cmd_sitemap)

    # 3. History
    p_hist = subparsers.add_parser("history", help="View past audit snapshots and SEO velocity")
    p_hist.add_argument("--url", help="Filter snapshots by URL")
    p_hist.add_argument("--limit", type=int, default=20, help="Max rows to return")
    p_hist.add_argument("--velocity", action="store_true", help="Show score progression and delta metrics")
    p_hist.add_argument("--json", action="store_true", help="Output results as JSON")
    p_hist.set_defaults(func=cmd_history)

    # 4. Fix
    p_fix = subparsers.add_parser("fix", help="Apply safe editorial simplifications to text or markdown")
    p_fix.add_argument("source", help="Raw text string or path to text file")
    p_fix.add_argument("-o", "--output", help="Path to write patched file")
    p_fix.add_argument("--json", action="store_true", help="Output replacements as JSON")
    p_fix.set_defaults(func=cmd_fix)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

import sqlite3
import os
import json
import time
from datetime import datetime
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blogguard_history.db")


@contextmanager
def get_db_connection():
    """Returns a SQLite connection with row factory enabled and guaranteed cleanup."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initializes the database schema if it doesn't already exist."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                title TEXT,
                keyword TEXT,
                writer TEXT,
                overall_score INTEGER NOT NULL,
                tech_score INTEGER,
                hierarchy_score INTEGER,
                content_score INTEGER,
                keyword_score INTEGER,
                eeat_score INTEGER,
                media_score INTEGER,
                link_score INTEGER,
                aeo_score INTEGER,
                yoast_seo_status TEXT,
                yoast_readability_status TEXT,
                word_count INTEGER,
                reading_time REAL,
                flesch_reading_ease REAL,
                flesch_grade REAL,
                issues_count INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                scores_json TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_url ON audit_snapshots(url)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_timestamp ON audit_snapshots(timestamp)")
        conn.commit()


def save_audit_snapshot(article_data, audit_results):
    """
    Saves a comprehensive snapshot of an audit run into SQLite.
    Returns the newly created row ID.
    """
    init_db()
    url = article_data.get("url") or article_data.get("final_url") or "Manual Draft / Offline"
    title = article_data.get("title", "")
    keyword = audit_results.get("keyword", "")
    writer = audit_results.get("writer", "")
    overall_score = int(audit_results.get("overall_score", 0))
    scores = audit_results.get("scores", {})
    
    aeo_data = audit_results.get("aeo", {})
    aeo_score = int(aeo_data.get("aeo_score", 0)) if isinstance(aeo_data, dict) else 0

    yoast_data = audit_results.get("yoast", {})
    yoast_seo_status = yoast_data.get("seo_verdict", "N/A") if isinstance(yoast_data, dict) else "N/A"
    yoast_read_status = yoast_data.get("readability_verdict", "N/A") if isinstance(yoast_data, dict) else "N/A"

    word_count = int(audit_results.get("word_count", 0))
    reading_time = float(audit_results.get("reading_time_min", 0.0))
    readability = audit_results.get("readability", {})
    flesch_reading_ease = float(readability.get("flesch_reading_ease", 0.0))
    flesch_grade = float(readability.get("flesch_kincaid_grade", 0.0))
    issues_count = len(audit_results.get("issues", []))
    scores_json = json.dumps(scores)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_snapshots (
                url, title, keyword, writer, overall_score,
                tech_score, hierarchy_score, content_score, keyword_score,
                eeat_score, media_score, link_score, aeo_score,
                yoast_seo_status, yoast_readability_status,
                word_count, reading_time, flesch_reading_ease, flesch_grade,
                issues_count, scores_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            url, title, keyword, writer, overall_score,
            scores.get("Technical SEO", 0),
            scores.get("Structure & Headings", 0),
            scores.get("Content & Readability", 0),
            scores.get("On-Page Keywords", 0),
            scores.get("E-E-A-T & Trust", 0),
            scores.get("Media & Visuals", 0),
            scores.get("Link Architecture", 0),
            aeo_score,
            yoast_seo_status,
            yoast_read_status,
            word_count, reading_time, flesch_reading_ease, flesch_grade,
            issues_count, scores_json
        ))
        conn.commit()
        return cursor.lastrowid


def get_audit_history(url=None, limit=50):
    """
    Retrieves historical audit snapshots, optionally filtered by URL.
    Returns list of dicts ordered chronologically descending.
    """
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if url:
            cursor.execute("""
                SELECT * FROM audit_snapshots
                WHERE url = ?
                ORDER BY id DESC
                LIMIT ?
            """, (url, limit))
        else:
            cursor.execute("""
                SELECT * FROM audit_snapshots
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        return [dict(r) for r in rows]


def get_url_velocity(url):
    """
    Calculates score velocity (progression over revisions) for a specific URL.
    Returns delta metrics between first recorded audit and most recent.
    """
    history = get_audit_history(url=url, limit=100)
    if not history:
        return None

    # history is newest first
    newest = history[0]
    oldest = history[-1]

    score_delta = newest["overall_score"] - oldest["overall_score"]
    word_delta = newest["word_count"] - oldest["word_count"]
    issues_delta = newest["issues_count"] - oldest["issues_count"]
    aeo_delta = (newest["aeo_score"] or 0) - (oldest["aeo_score"] or 0)
    ease_delta = round((newest["flesch_reading_ease"] or 0) - (oldest["flesch_reading_ease"] or 0), 1)

    return {
        "url": url,
        "total_audits": len(history),
        "first_audit_date": oldest["timestamp"],
        "latest_audit_date": newest["timestamp"],
        "initial_score": oldest["overall_score"],
        "latest_score": newest["overall_score"],
        "score_delta": score_delta,
        "word_delta": word_delta,
        "issues_delta": issues_delta,
        "aeo_delta": aeo_delta,
        "ease_delta": ease_delta,
        "improved": score_delta > 0,
    }


def delete_snapshot(snapshot_id):
    """Deletes a specific audit snapshot by ID."""
    init_db()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM audit_snapshots WHERE id = ?", (snapshot_id,))
        conn.commit()
        return cursor.rowcount > 0


def clear_all_history():
    """Clears all audit history."""
    init_db()
    with get_db_connection() as conn:
        conn.execute("DELETE FROM audit_snapshots")
        conn.commit()

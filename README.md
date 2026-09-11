# 🛡️ BlogGuard SEO — Autonomous Intelligence Studio

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40%2B-FF4B4B.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Free autonomous blog structure, language, and SERP quality intelligence platform.**
> Connects local Headless Browser DOM extraction, Google SerpApi, Google Core Web Vitals, and DeepSeek AI into a single unified SEO command center.

---

## 🌟 Key Features & Architecture

Like rivers meeting to form an ocean, BlogGuard connects four distinct intelligence engines:

1. **🌐 Autonomous Browser Harness (`crawler.py`)**:
   - Uses native Headless Chrome (`--headless=new --dump-dom`) to render modern client-side JavaScript (React, Next.js, hydration).
   - High-fidelity HTTP client fallback with realistic headers and anti-scraping resilience.
   - Extracts title, meta description, canonical, robots, author, publish timestamps, full heading hierarchy (H1–H4), OpenGraph, Twitter cards, JSON-LD Schema, images (with alt text audits), and internal vs. outbound authority citations.

2. **🔍 Google SERP Intelligence (`api_integrations.py`)**:
   - Queries Google search in real time via **SerpApi**.
   - Pulls top 10 organic ranking competitors, snippets, and displayed links.
   - Extracts Google **"People Also Ask" (PAA)** questions to capture Google Featured Snippets.
   - Discovers LSI related searches.

3. **🧠 DeepSeek AI Editorial Director (`api_integrations.py`)**:
   - Connects to `deepseek-chat` and `deepseek-reasoner` (R1).
   - Generates executive editorial audits, search intent critiques, content gap blueprints, 5 high-CTR headlines, 3 meta descriptions, and valid JSON-LD FAQPage Schema.

4. **⚡ Google Core Web Vitals (`api_integrations.py`)**:
   - Live mobile UX performance audit (LCP, CLS, FCP, TBT) directly from Google's Lighthouse API.

5. **📊 7-Pillar Algorithmic SEO Scorer (`audit_engine.py`)**:
   - Technical & Indexability SEO (0–100)
   - Structure & Heading Hierarchy (0–100)
   - Content Depth & Readability (Flesch-Kincaid & Flesch Reading Ease) (0–100)
   - On-Page Keyword & Search Intent (0–100)
   - E-E-A-T & Authority Trust (0–100)
   - Media & Visuals (0–100)
   - Link Architecture & Citations (0–100)

6. **📥 Executive Export Engine (`export_helper.py`)**:
   - 1-click printable Executive HTML/PDF Audit Report.
   - CSV export for spreadsheets and team tracking.

---

## 🎯 4 Operating Modes

- **🌐 Mode 1: Autonomous Live URL Audit**: Enter any blog URL. The engine crawls the live page, detects metadata and keywords, and audits all 7 pillars.
- **⚔️ Mode 2: Competitor Battle Mode**: Put your blog head-to-head against a ranking competitor to spot exact word count, heading, citation, and keyword gaps.
- **📑 Mode 3: Batch / Multi-URL Audit**: Audit multiple URLs or sitemaps simultaneously.
- **✍️ Mode 4: Draft Pre-Publish Audit**: Audit offline markdown or raw text before publication.

---

## 🚀 Quickstart (Run Locally)

### 1. Clone the repository
```bash
git clone https://github.com/abhijeetyadav-Fab-Dev/-BlogGuard-SEO-Autonomous-Studio.git
cd -BlogGuard-SEO-Autonomous-Studio
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. (Optional) Configure API Keys in your environment
```bash
# Windows PowerShell
$env:SERPAPI_KEY="your_serpapi_key_here"
$env:DEEPSEEK_API_KEY="your_deepseek_key_here"

# Linux / macOS
export SERPAPI_KEY="your_serpapi_key_here"
export DEEPSEEK_API_KEY="your_deepseek_key_here"
```
*(You can also paste API keys directly into the app sidebar at runtime).*

### 4. Run the Streamlit app
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## ☁️ Deploying on Render (Step-by-Step)

This repository includes a native [`render.yaml`](render.yaml) blueprint for 1-click deployment on [Render](https://render.com).

### Step 1: Create a Render Account
Sign up or log in at [dashboard.render.com](https://dashboard.render.com/).

### Step 2: Create a New Web Service
1. In the Render Dashboard, click **New +** &rarr; **Web Service**.
2. Connect your GitHub account and select repository:  
   `abhijeetyadav-Fab-Dev/-BlogGuard-SEO-Autonomous-Studio`
3. Configure the service settings:
   - **Name**: `blogguard-seo`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**:
     ```bash
     streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
     ```
   - **Plan**: `Free`

### Step 3: Add Environment Variables (Optional)
Under the **Environment Variables** tab on Render, you can optionally add:
- `SERPAPI_KEY`: Your SerpApi key for live Google SERP intelligence.
- `DEEPSEEK_API_KEY`: Your DeepSeek API key for AI copilot features.

### Step 4: Deploy
Click **Deploy Web Service**. Render will automatically build the environment and provide you with a live HTTPS URL (e.g. `https://blogguard-seo.onrender.com`).

---

## 🧪 Running Automated Tests

```bash
python -m unittest test_blogguard.py
```

---

## 📄 License
MIT License. Free for personal, editorial, and commercial use.

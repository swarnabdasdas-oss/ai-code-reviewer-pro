# 🚀 AI Code Reviewer Pro

A production-ready, full-stack AI-powered code review platform built with **Flask**, **SQLite**, and **Google Gemini AI**.

---

## ✨ Features

- **AI Code Review** — Upload or paste code; Gemini analyzes for bugs, security vulnerabilities, performance issues, code smells, best practice violations, and maintainability issues
- **Review Score (0–100)** — Every review gets a numeric quality score with a grade
- **Optimized Code** — Gemini returns a fully refactored, improved version of your code
- **Dashboard** — Live stats (total reviews, bugs found, quality score, issues fixed) + weekly trend chart + quality donut
- **History** — Search, filter by language & date, delete reviews, view full detail in modal
- **Reports** — Analytics charts: monthly reviews, language distribution, bug distribution, score trend
- **PDF Export** — Professional dark-theme PDF reports for individual reviews and full analytics
- **Delete Buttons** — Delete any review from recent activity dashboard, history table, or detail modal

---

## 🗂 Project Structure

```
ai_code_reviewer/
├── app.py                  # Flask application factory + page routes
├── database.py             # SQLite connection + schema init
├── models.py               # All DB query functions
├── routes.py               # API Blueprint (/api/*)
├── gemini_service.py       # Google Gemini AI integration
├── report_generator.py     # ReportLab PDF generation
├── requirements.txt
├── .env.example
├── README.md
├── templates/
│   └── index.html          # Full SPA — all 5 pages in one template
├── static/                 # (reserved for future assets)
└── instance/
    └── database.db         # SQLite DB (auto-created on first run)
```

---

## ⚙️ Setup — Localhost

### 1. Clone / download the project

```bash
cd ai_code_reviewer
```

### 2. Create a Python virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get a Google Gemini API key

1. Go to [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Click **Create API key**
3. Copy the key

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
FLASK_SECRET_KEY=any_long_random_string_here
FLASK_DEBUG=False
MAX_UPLOAD_SIZE_MB=5
```

### 6. Run the application

```bash
python app.py
```

Open your browser at **http://localhost:5000**

The SQLite database (`instance/database.db`) is created automatically on first run.

---

## 🌐 Deployment — Render

1. Push your project to a GitHub repository (exclude `.env` and `instance/`)

2. Go to [https://render.com](https://render.com) → **New Web Service**

3. Connect your GitHub repo

4. Set the build and start commands:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`

5. Add environment variables in Render dashboard:
   - `GEMINI_API_KEY` = your key
   - `FLASK_SECRET_KEY` = random secret
   - `FLASK_DEBUG` = False

6. Deploy — Render gives you a free `*.onrender.com` URL

> **Note:** Render's free tier uses ephemeral storage. The SQLite database resets on redeploy. For production, use Render's PostgreSQL add-on or migrate to SQLAlchemy + a persistent DB.

---

## 🚂 Deployment — Railway

1. Push to GitHub

2. Go to [https://railway.app](https://railway.app) → **New Project** → **Deploy from GitHub**

3. Select your repo

4. In the Variables tab, add:
   - `GEMINI_API_KEY`
   - `FLASK_SECRET_KEY`
   - `FLASK_DEBUG=False`

5. Railway auto-detects Python and deploys. Your app gets a `*.railway.app` URL.

> For persistent SQLite on Railway, add a **Volume** and point `DB_PATH` to the mounted path, or switch to Railway's PostgreSQL plugin.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/review` | Submit code for AI review |
| GET | `/api/history` | Get all reviews (search, filter, paginate) |
| GET | `/api/history/<id>` | Get single review with full detail |
| DELETE | `/api/delete-review/<id>` | Delete a review |
| GET | `/api/stats` | Dashboard stats + recent activity |
| GET | `/api/report` | Full analytics data |
| GET | `/api/export-pdf/<id>` | Export single review as PDF |
| GET | `/api/export-pdf` | Export full analytics as PDF |

---

## 🗄 Database Schema

### `reviews`
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER PK | Auto-increment |
| filename | TEXT | Source file name |
| language | TEXT | Programming language |
| uploaded_code | TEXT | Full source code |
| review_score | INTEGER | 0–100 quality score |
| bug_count | INTEGER | Number of bugs detected |
| issue_count | INTEGER | Total non-bug issues |
| review_summary | TEXT | AI summary |
| suggestions | TEXT | JSON array of suggestions |
| review_date | TEXT | ISO datetime |
| status | TEXT | `completed` |

### `review_results`
Individual issues (bugs, security vulns, performance issues, etc.) linked to a review.

### `optimized_code`
Stores the Gemini-generated refactored code for each review.

### `statistics` / `reports`
Reserved for future analytics aggregation.

---

## 🔒 Security

- API key stored in `.env` — never committed to version control
- File uploads restricted to safe extensions (`.py`, `.js`, `.ts`, `.java`, `.go`, etc.)
- Max upload size: 5 MB (configurable)
- Max code length: 50,000 characters
- All user input HTML-escaped in the frontend
- Input validation on all API endpoints

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, Flask 3.0 |
| AI | Google Gemini 1.5 Flash |
| Database | SQLite (via Python stdlib) |
| PDF | ReportLab |
| Frontend | HTML5, CSS3, Vanilla JS |
| Charts | Chart.js 4.4 |
| Fonts | Rajdhani + Space Mono (Google Fonts) |

---

## 📝 License

MIT — feel free to use, modify, and distribute.

---

*Built with ❤️ for clean code and developer experience.*

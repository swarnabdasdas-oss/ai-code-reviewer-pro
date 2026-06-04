import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')

def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            language TEXT NOT NULL,
            uploaded_code TEXT NOT NULL,
            review_score INTEGER DEFAULT 0,
            bug_count INTEGER DEFAULT 0,
            issue_count INTEGER DEFAULT 0,
            review_summary TEXT,
            suggestions TEXT,
            review_date TEXT NOT NULL,
            status TEXT DEFAULT 'completed'
        );

        CREATE TABLE IF NOT EXISTS review_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            severity TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            line_number INTEGER,
            suggestion TEXT,
            FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stat_date TEXT NOT NULL,
            total_reviews INTEGER DEFAULT 0,
            bugs_found INTEGER DEFAULT 0,
            avg_quality_score REAL DEFAULT 0.0,
            issues_fixed INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date TEXT NOT NULL,
            report_type TEXT NOT NULL,
            report_data TEXT,
            generated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS optimized_code (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            review_id INTEGER NOT NULL,
            optimized TEXT,
            FOREIGN KEY (review_id) REFERENCES reviews(id) ON DELETE CASCADE
        );
    ''')

    conn.commit()
    conn.close()

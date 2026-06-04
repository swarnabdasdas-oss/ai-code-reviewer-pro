from database import get_db
from datetime import datetime
import json


# ─── REVIEWS ───────────────────────────────────────────────────────────────────

def create_review(filename, language, uploaded_code, review_score,
                  bug_count, issue_count, review_summary, suggestions):
    conn = get_db()
    cursor = conn.cursor()
    review_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO reviews
            (filename, language, uploaded_code, review_score, bug_count,
             issue_count, review_summary, suggestions, review_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (filename, language, uploaded_code, review_score,
          bug_count, issue_count, review_summary,
          json.dumps(suggestions) if isinstance(suggestions, list) else suggestions,
          review_date, 'completed'))
    review_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return review_id


def save_review_results(review_id, issues):
    conn = get_db()
    cursor = conn.cursor()
    for issue in issues:
        cursor.execute('''
            INSERT INTO review_results
                (review_id, category, severity, title, description, line_number, suggestion)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            review_id,
            issue.get('category', 'General'),
            issue.get('severity', 'low'),
            issue.get('title', ''),
            issue.get('description', ''),
            issue.get('line_number'),
            issue.get('suggestion', '')
        ))
    conn.commit()
    conn.close()


def save_optimized_code(review_id, optimized_code):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO optimized_code (review_id, optimized)
        VALUES (?, ?)
    ''', (review_id, optimized_code))
    conn.commit()
    conn.close()


def get_all_reviews(search='', language='', date_from='', date_to='', limit=50, offset=0):
    conn = get_db()
    cursor = conn.cursor()
    query = 'SELECT * FROM reviews WHERE 1=1'
    params = []
    if search:
        query += ' AND (filename LIKE ? OR review_summary LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])
    if language:
        query += ' AND language = ?'
        params.append(language)
    if date_from:
        query += ' AND review_date >= ?'
        params.append(date_from)
    if date_to:
        query += ' AND review_date <= ?'
        params.append(date_to + ' 23:59:59')
    query += ' ORDER BY review_date DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_review_by_id(review_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reviews WHERE id = ?', (review_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    review = dict(row)
    cursor.execute('SELECT * FROM review_results WHERE review_id = ?', (review_id,))
    review['issues'] = [dict(r) for r in cursor.fetchall()]
    cursor.execute('SELECT optimized FROM optimized_code WHERE review_id = ?', (review_id,))
    opt = cursor.fetchone()
    review['optimized_code'] = opt['optimized'] if opt else ''
    conn.close()
    return review


def delete_review(review_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM review_results WHERE review_id = ?', (review_id,))
    cursor.execute('DELETE FROM optimized_code WHERE review_id = ?', (review_id,))
    cursor.execute('DELETE FROM reviews WHERE id = ?', (review_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def get_recent_reviews(limit=10):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT * FROM reviews ORDER BY review_date DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── STATISTICS ────────────────────────────────────────────────────────────────

def get_dashboard_stats():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as total FROM reviews')
    total_reviews = cursor.fetchone()['total']

    cursor.execute('SELECT COALESCE(SUM(bug_count), 0) as total FROM reviews')
    bugs_found = cursor.fetchone()['total']

    cursor.execute('SELECT COALESCE(AVG(review_score), 0) as avg FROM reviews')
    avg_quality = round(cursor.fetchone()['avg'], 1)

    cursor.execute('SELECT COALESCE(SUM(issue_count), 0) as total FROM reviews WHERE review_score >= 70')
    issues_fixed = cursor.fetchone()['total']

    conn.close()
    return {
        'total_reviews': total_reviews,
        'bugs_found': bugs_found,
        'avg_quality': avg_quality,
        'issues_fixed': issues_fixed
    }


def get_weekly_quality_trend():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            strftime('%w', review_date) as dow,
            strftime('%Y-%m-%d', review_date) as day,
            AVG(review_score) as avg_score,
            COUNT(*) as count
        FROM reviews
        WHERE review_date >= date('now', '-7 days')
        GROUP BY strftime('%Y-%m-%d', review_date)
        ORDER BY day ASC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_monthly_reviews():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            strftime('%Y-%m', review_date) as month,
            COUNT(*) as count,
            AVG(review_score) as avg_score
        FROM reviews
        GROUP BY strftime('%Y-%m', review_date)
        ORDER BY month ASC
        LIMIT 12
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_language_distribution():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT language, COUNT(*) as count
        FROM reviews
        GROUP BY language
        ORDER BY count DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_bug_distribution():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT category, COUNT(*) as count
        FROM review_results
        GROUP BY category
        ORDER BY count DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_score_trend():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            strftime('%Y-%m-%d', review_date) as day,
            AVG(review_score) as avg_score
        FROM reviews
        GROUP BY strftime('%Y-%m-%d', review_date)
        ORDER BY day ASC
        LIMIT 30
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_quality_overview():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total FROM reviews')
    total = cursor.fetchone()['total'] or 1

    cursor.execute('SELECT COUNT(*) as c FROM reviews WHERE review_score >= 70')
    passed = cursor.fetchone()['c']

    cursor.execute('SELECT COUNT(*) as c FROM reviews WHERE review_score >= 40 AND review_score < 70')
    warned = cursor.fetchone()['c']

    cursor.execute('SELECT COUNT(*) as c FROM reviews WHERE review_score < 40')
    failed = cursor.fetchone()['c']

    conn.close()
    return {
        'passed': passed,
        'warned': warned,
        'failed': failed,
        'pass_pct': round(passed / total * 100),
        'warn_pct': round(warned / total * 100),
        'fail_pct': round(failed / total * 100),
    }

import json
import os
from flask import Blueprint, request, jsonify, send_file
import io
from werkzeug.utils import secure_filename

import models
import gemini_service
import report_generator

api = Blueprint('api', __name__)

ALLOWED_EXTENSIONS = {
    'py', 'js', 'ts', 'jsx', 'tsx', 'java', 'c', 'cpp', 'cs',
    'go', 'rb', 'php', 'swift', 'kt', 'rs', 'html', 'css', 'sql',
    'sh', 'bash', 'r', 'dart', 'scala', 'lua', 'pl', 'txt', 'md'
}
MAX_UPLOAD_BYTES = int(os.getenv('MAX_UPLOAD_SIZE_MB', 5)) * 1024 * 1024

LANG_EXT_MAP = {
    'py': 'Python', 'js': 'JavaScript', 'ts': 'TypeScript',
    'jsx': 'JavaScript', 'tsx': 'TypeScript', 'java': 'Java',
    'c': 'C', 'cpp': 'C++', 'cs': 'C#', 'go': 'Go',
    'rb': 'Ruby', 'php': 'PHP', 'swift': 'Swift', 'kt': 'Kotlin',
    'rs': 'Rust', 'html': 'HTML', 'css': 'CSS', 'sql': 'SQL',
    'sh': 'Shell', 'bash': 'Shell', 'r': 'R', 'dart': 'Dart',
    'scala': 'Scala', 'lua': 'Lua', 'pl': 'Perl',
}


def _ext_allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _detect_language(filename, provided_lang=''):
    if provided_lang and provided_lang.strip():
        return provided_lang.strip()
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return LANG_EXT_MAP.get(ext, 'Unknown')


# ── Review ─────────────────────────────────────────────────────────────────────

@api.route('/api/review', methods=['POST'])
def submit_review():
    code = ''
    filename = 'pasted_code.txt'
    language = ''

    if 'file' in request.files and request.files['file'].filename:
        f = request.files['file']
        if not _ext_allowed(f.filename):
            return jsonify({'error': 'File type not allowed.'}), 400
        content = f.read()
        if len(content) > MAX_UPLOAD_BYTES:
            return jsonify({'error': f'File exceeds {os.getenv("MAX_UPLOAD_SIZE_MB", 5)} MB limit.'}), 400
        try:
            code = content.decode('utf-8')
        except UnicodeDecodeError:
            return jsonify({'error': 'File must be valid UTF-8 text.'}), 400
        filename = secure_filename(f.filename)
        language = _detect_language(filename, request.form.get('language', ''))
    else:
        data = request.get_json(silent=True) or {}
        code = data.get('code', request.form.get('code', '')).strip()
        language = data.get('language', request.form.get('language', 'Unknown')).strip()
        filename = data.get('filename', request.form.get('filename', 'pasted_code.txt')).strip()

    if not code:
        return jsonify({'error': 'No code provided.'}), 400
    if len(code) > 50_000:
        return jsonify({'error': 'Code is too long (max 50 000 chars).'}), 400

    try:
        result = gemini_service.review_code(code, language, filename)
    except ValueError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': f'AI review failed: {str(e)}'}), 500

    review_id = models.create_review(
        filename=filename,
        language=language,
        uploaded_code=code,
        review_score=result['review_score'],
        bug_count=result['bug_count'],
        issue_count=result['issue_count'],
        review_summary=result['summary'],
        suggestions=result['suggestions'],
    )
    models.save_review_results(review_id, result['issues'])
    models.save_optimized_code(review_id, result['optimized_code'])

    return jsonify({
        'success': True,
        'review_id': review_id,
        'review_score': result['review_score'],
        'summary': result['summary'],
        'bug_count': result['bug_count'],
        'issue_count': result['issue_count'],
        'issues': result['issues'],
        'suggestions': result['suggestions'],
        'optimized_code': result['optimized_code'],
    })


# ── History ────────────────────────────────────────────────────────────────────

@api.route('/api/history', methods=['GET'])
def get_history():
    search   = request.args.get('search', '')
    language = request.args.get('language', '')
    date_from = request.args.get('date_from', '')
    date_to   = request.args.get('date_to', '')
    limit  = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))

    reviews = models.get_all_reviews(search, language, date_from, date_to, limit, offset)
    return jsonify({'reviews': reviews, 'count': len(reviews)})


@api.route('/api/history/<int:review_id>', methods=['GET'])
def get_single_review(review_id):
    review = models.get_review_by_id(review_id)
    if not review:
        return jsonify({'error': 'Review not found.'}), 404
    return jsonify(review)


# ── Delete ─────────────────────────────────────────────────────────────────────

@api.route('/api/delete-review/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    ok = models.delete_review(review_id)
    if not ok:
        return jsonify({'error': 'Review not found.'}), 404
    return jsonify({'success': True, 'message': 'Review deleted.'})


# ── Stats ──────────────────────────────────────────────────────────────────────

@api.route('/api/stats', methods=['GET'])
def get_stats():
    overview = models.get_dashboard_stats()
    weekly   = models.get_weekly_quality_trend()
    recent   = models.get_recent_reviews(10)
    quality  = models.get_quality_overview()
    return jsonify({
        'overview': overview,
        'weekly_trend': weekly,
        'recent_reviews': recent,
        'quality_overview': quality,
    })


# ── Reports ────────────────────────────────────────────────────────────────────

@api.route('/api/report', methods=['GET'])
def get_report_data():
    overview   = models.get_dashboard_stats()
    monthly    = models.get_monthly_reviews()
    lang_dist  = models.get_language_distribution()
    bug_dist   = models.get_bug_distribution()
    score_trend = models.get_score_trend()
    quality    = models.get_quality_overview()
    return jsonify({
        'overview': overview,
        'monthly_reviews': monthly,
        'language_distribution': lang_dist,
        'bug_distribution': bug_dist,
        'score_trend': score_trend,
        'quality_overview': quality,
    })


# ── Export PDFs ────────────────────────────────────────────────────────────────

@api.route('/api/export-pdf/<int:review_id>', methods=['GET'])
def export_review_pdf(review_id):
    review = models.get_review_by_id(review_id)
    if not review:
        return jsonify({'error': 'Review not found.'}), 404
    try:
        pdf_bytes = report_generator.generate_review_pdf(review)
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'review_{review_id}_{review["filename"]}.pdf'
        )
    except Exception as e:
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500


@api.route('/api/export-pdf', methods=['GET'])
def export_analytics_pdf():
    overview    = models.get_dashboard_stats()
    lang_dist   = models.get_language_distribution()
    bug_dist    = models.get_bug_distribution()
    score_trend = models.get_score_trend()
    try:
        pdf_bytes = report_generator.generate_analytics_pdf({
            'overview': overview,
            'language_distribution': lang_dist,
            'bug_distribution': bug_dist,
            'score_trend': score_trend,
        })
        from datetime import datetime
        fname = f'analytics_report_{datetime.now().strftime("%Y%m%d_%H%M")}.pdf'
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=fname
        )
    except Exception as e:
        return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500

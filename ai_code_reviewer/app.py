import os
from flask import Flask, render_template, jsonify
from dotenv import load_dotenv
from database import init_db
from routes import api

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-prod')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_UPLOAD_SIZE_MB', 5)) * 1024 * 1024

# Try to enable CORS (optional dependency)
try:
    from flask_cors import CORS
    CORS(app)
except ImportError:
    pass

# Register API blueprint
app.register_blueprint(api)

# Initialise database on startup
with app.app_context():
    init_db()


# ── Page routes ────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html', page='dashboard')

@app.route('/review')
def review():
    return render_template('index.html', page='review')

@app.route('/history')
def history():
    return render_template('index.html', page='history')

@app.route('/reports')
def reports():
    return render_template('index.html', page='reports')

@app.route('/about')
def about():
    return render_template('index.html', page='about')


# ── Error handlers ─────────────────────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 5MB.'}), 413

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=5000, debug=debug)

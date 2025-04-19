import os
import logging
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
import tempfile
from io import BytesIO

from resume_parser import parse_resume
from text_processor import extract_skills_experience

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-dev-secret")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure upload settings
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
UPLOAD_FOLDER = tempfile.gettempdir()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if file part exists in the request
    if 'resume' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    
    file = request.files['resume']
    
    # Check if user submitted an empty form
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Parse the resume
            text_content = parse_resume(filepath)
            
            # Extract skills and experience
            extracted_data = extract_skills_experience(text_content)
            
            # Store results in session
            session['extracted_data'] = extracted_data
            
            # Clean up the temporary file
            os.remove(filepath)
            
            # Redirect to results page
            return redirect(url_for('show_results'))
        
        except Exception as e:
            # Clean up the temporary file in case of error
            if os.path.exists(filepath):
                os.remove(filepath)
                
            logger.error(f"Error processing file: {str(e)}")
            flash(f'Error processing file: {str(e)}', 'danger')
            return redirect(url_for('index'))
    else:
        flash('File type not allowed. Please upload PDF or DOCX files only.', 'danger')
        return redirect(url_for('index'))

@app.route('/results')
def show_results():
    # Retrieve data from session
    extracted_data = session.get('extracted_data')
    
    if not extracted_data:
        flash('No data to display. Please upload a resume.', 'warning')
        return redirect(url_for('index'))
    
    return render_template('results.html', data=extracted_data)

@app.route('/download')
def download_results():
    # Retrieve data from session
    extracted_data = session.get('extracted_data')
    
    if not extracted_data:
        flash('No data to download. Please upload a resume.', 'warning')
        return redirect(url_for('index'))
    
    # Create JSON file in memory
    mem = BytesIO()
    mem.write(json.dumps(extracted_data, indent=4).encode())
    mem.seek(0)
    
    return send_file(
        mem,
        as_attachment=True,
        download_name='resume_extracted_data.json',
        mimetype='application/json'
    )

@app.route('/clear')
def clear_session():
    session.clear()
    flash('Session cleared. You can upload a new resume.', 'info')
    return redirect(url_for('index'))

@app.errorhandler(413)
def request_entity_too_large(error):
    flash('File too large. Maximum size is 16MB.', 'danger')
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(error):
    return render_template('index.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('index.html', error='Internal server error. Please try again.'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

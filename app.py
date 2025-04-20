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
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}  # Added txt for testing
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
    # Add more detailed logging
    print("\n\n***** UPLOAD REQUEST RECEIVED *****\n\n")
    logger.debug("Upload request received")
    
    # Check if file part exists in the request
    if 'resume' not in request.files:
        print("NO FILE PART IN REQUEST")
        logger.warning("No file part in the request")
        flash('No file part', 'danger')
        return redirect(url_for('index'))
    
    file = request.files['resume']
    print(f"FILE RECEIVED: {file.filename}")
    logger.debug(f"File received: {file.filename}")
    
    # Check if user submitted an empty form
    if file.filename == '':
        print("EMPTY FILENAME SUBMITTED")
        logger.warning("Empty filename submitted")
        flash('No file selected', 'danger')
        return redirect(url_for('index'))
    
    # Check file extension
    if not allowed_file(file.filename):
        print(f"INVALID FILE TYPE: {file.filename}")
        logger.warning(f"Invalid file type: {file.filename}")
        flash('File type not allowed. Please upload PDF, DOCX, or TXT files only.', 'danger')
        return redirect(url_for('index'))
    
    # Process valid file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        print(f"SAVING FILE TO: {filepath}")
        logger.debug(f"Saving file to: {filepath}")
        file.save(filepath)
        
        # Parse the resume
        print(f"PARSING RESUME: {filename}")
        logger.debug(f"Parsing resume file: {filename}")
        
        # Create a simple text file handler for the sample resume
        if filename.endswith('.txt'):
            with open(filepath, 'r') as f:
                text_content = f.read()
        else:
            text_content = parse_resume(filepath)
        
        print("RESUME PARSING SUCCESSFUL")
        logger.debug("Resume parsing successful")
        
        # Extract skills and experience
        print("EXTRACTING SKILLS AND EXPERIENCE")
        logger.debug("Extracting skills and experience")
        extracted_data = extract_skills_experience(text_content)
        
        skill_count = len(extracted_data.get('skills', {}).get('identified', []))
        print(f"EXTRACTION COMPLETE. SKILLS FOUND: {skill_count}")
        logger.debug(f"Extraction complete. Skills found: {skill_count}")
        
        # Store results in session
        print("STORING RESULTS IN SESSION")
        logger.debug("Storing results in session")
        session['extracted_data'] = extracted_data
        
        # Clean up the temporary file
        print(f"REMOVING TEMPORARY FILE: {filepath}")
        logger.debug(f"Removing temporary file: {filepath}")
        os.remove(filepath)
        
        # Redirect to results page
        print("REDIRECTING TO RESULTS PAGE")
        logger.debug("Redirecting to results page")
        return redirect(url_for('show_results'))
    
    except Exception as e:
        # Clean up the temporary file in case of error
        if 'filepath' in locals() and os.path.exists(filepath):
            print(f"REMOVING TEMPORARY FILE AFTER ERROR: {filepath}")
            logger.debug(f"Removing temporary file after error: {filepath}")
            os.remove(filepath)
            
        print(f"ERROR PROCESSING FILE: {str(e)}")
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        flash(f'Error processing file: {str(e)}', 'danger')
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

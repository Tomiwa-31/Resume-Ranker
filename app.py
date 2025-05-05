import os
import logging
import json
import re
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
import tempfile
from io import BytesIO

from sqlalchemy import text
from resume_parser import parse_resume
from text_processor import extract_skills_experience
from models import db, JobDescription, Resume


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-dev-secret")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Add custom filters
@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to <br> tags for display in HTML"""
    if not value:
        return ''
    return value.replace('\n', '<br>')

# Configure database
database_url = os.environ.get('DATABASE_URL')
if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Fallback to MySQL (local) if no DATABASE_URL is provided
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:tomiwa@localhost/resumedb'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

#@app.route('/test-db')
#def test_db_connection():
    #try:
        # Try a simple database query
        #result = db.session.execute(text('SELECT 1'))
        #return "✅ Database connection successful!"
    #except Exception as e:
        #return f"❌ Database connection failed: {str(e)}"

#if __name__ =="__main__":
    #app.run(host='0.0.0.0', port=5000, debug=True)

# Configure upload settings
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}  # Added txt for testing
UPLOAD_FOLDER = tempfile.gettempdir()
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Create database tables
with app.app_context():#####with statement
    db.create_all()
    
# Helper function to extract candidate information from resume text
def extract_candidate_info(text):
    """Extract candidate name, email, and phone from resume text"""
    info = {
        'name': None,
        'email': None,
        'phone': None
    }
    
    # Try to extract email
    email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
    if email_match:
        info['email'] = email_match.group(0)
    
    # Try to extract phone (simple pattern for various formats)
    phone_match = re.search(r'(\+\d{1,3}[\s.-])?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', text)
    if phone_match:
        info['phone'] = phone_match.group(0)
    
    # Try to extract name (this is more complex, using first 2 lines if they don't match email/phone)
    lines = text.split('\n')
    for line in lines[:3]:  # Check first 3 lines for name
        line = line.strip() #removen any spaces or empty character before and after the text
        if line and len(line) > 3:
            # Skip if line contains email or phone
            if info['email'] and info['email'] in line:
                continue
            if info['phone'] and info['phone'] in line:
                continue
            if not re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', line) and not re.search(r'(\+\d{1,3}[\s.-])?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}', line):
                info['name'] = line
                break
    
    return info

@app.route('/')
def index():
    # Get job descriptions for the dropdown
    job_descriptions = JobDescription.query.order_by(JobDescription.created_at.desc()).all()
    return render_template('index.html', job_descriptions=job_descriptions)

@app.route('/jobs')
def job_descriptions():
    """List all job descriptions"""
    jobs = JobDescription.query.order_by(JobDescription.created_at.desc()).all()
    return render_template('jobs.html', jobs=jobs)

@app.route('/jobs/create', methods=['GET', 'POST'])
def create_job():
    """Create a new job description"""
    if request.method == 'POST':
        title = request.form.get('title')
        company = request.form.get('company')
        description = request.form.get('description')
        
        # Extract required skills from the description
        skills_text = request.form.get('required_skills', '')
        # Split by commas, newlines or semicolons and clean up
        skills = [skill.strip() for skill in re.split(r'[,;\n]', skills_text) if skill.strip()]
        
        if not title or not description:
            flash('Job title and description are required', 'danger')
            return render_template('create_job.html')
        
        try:
            job = JobDescription(
                title=title,
                company=company,
                description=description
            )
            job.set_required_skills(skills)
            
            db.session.add(job)
            db.session.commit()
            
            flash('Job description created successfully', 'success')
            return redirect(url_for('job_descriptions'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating job description: {str(e)}", exc_info=True)
            flash(f'Error creating job description: {str(e)}', 'danger')
    
    return render_template('create_job.html')

@app.route('/jobs/<int:job_id>')
def view_job(job_id):
    """View a job description and associated resumes"""
    job = JobDescription.query.get_or_404(job_id)
    resumes = Resume.query.filter_by(job_description_id=job_id).order_by(Resume.match_score.desc()).all()

    print("Job Required Skills:", job.get_required_skills())
    for resume in resumes:
        print(f"Resume: {resume.filename}")
        print("Extracted Skills:", resume.get_skills())
        print("Match Score:", resume.match_score)
    
    return render_template('view_job.html', job=job, resumes=resumes)

@app.route('/upload', methods=['POST'])
def upload_file():
    # Add more detailed logging
    print("\n\n***** UPLOAD REQUEST RECEIVED *****\n\n")
    logger.debug("Upload request received")
    
    # Get job description ID if provided
    job_id = request.form.get('job_id')
    job = None
    
    if job_id:
        try:
            job = JobDescription.query.get(job_id)
            if not job:
                flash('Selected job description not found', 'warning')
        except Exception as e:
            logger.error(f"Error retrieving job description: {str(e)}", exc_info=True)
    
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
        
        # Extract candidate information
        candidate_info = extract_candidate_info(text_content)
        
        # Store in the database if a job was selected
        if job:
            # Create a new Resume record
            resume = Resume(
                filename=filename,
                candidate_name=candidate_info['name'],
                email=candidate_info['email'],
                phone=candidate_info['phone'],
                experience=extracted_data.get('experience', {}).get('content'),
                raw_text=text_content[:5000],  # Limit the stored text
                job_description_id=job.id
            )
            
            # Set the skills
            resume.set_skills(extracted_data.get('skills', {}).get('identified', []))
            
            # Print debug info before calculating match score
            print("Resume skills (before match):", resume.get_skills())
            print("Job required skills (before match):", job.get_required_skills())
            print("Resume job_description_id:", resume.job_description_id)
            print("Resume job_description:", resume.job_description)
            
            # Save to database and flush to get relationships
            db.session.add(resume)
            db.session.flush()  # This will assign the relationship
            
            # Now calculate match score
            resume.calculate_match_score()
            
            db.session.commit()
            
            # Add job info to the extracted data
            extracted_data['job_match'] = {
                'job_title': job.title,
                'match_score': resume.match_score,
                'job_id': job.id
            }
        
        # Store results in session
        print("STORING RESULTS IN SESSION")
        logger.debug("Storing results in session")
        session['extracted_data'] = extracted_data
        
        # Add candidate info to session
        session['candidate_info'] = candidate_info
        
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
    candidate_info = session.get('candidate_info', {})
    
    if not extracted_data:
        flash('No data to display. Please upload a resume.', 'warning')
        return redirect(url_for('index'))
    
    # Add candidate info to the data if available
    if candidate_info:
        extracted_data['candidate_info'] = candidate_info
    
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
    return "404 Not Found", 404#render_template('index.html', error='Page not found'), 404

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('index.html', error='Internal server error. Please try again.'), 500

@app.route('/resumes/<int:resume_id>/delete', methods=['POST'])
def delete_resume(resume_id):
    """Delete a resume by its ID and redirect to the associated job description page."""
    resume = Resume.query.get_or_404(resume_id)
    job_id = resume.job_description_id
    db.session.delete(resume)
    db.session.commit()
    flash('Resume deleted successfully.', 'success')
    return redirect(url_for('view_job', job_id=job_id))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

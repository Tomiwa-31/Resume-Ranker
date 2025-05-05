from datetime import datetime
import json
from flask_sqlalchemy import SQLAlchemy
import re

db = SQLAlchemy()

class JobDescription(db.Model):
    __tablename__ = 'job_descriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=False)
    required_skills = db.Column(db.Text, nullable=True)  # Stored as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with Resume
    resumes = db.relationship('Resume', back_populates='job_description', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<JobDescription {self.title}>'
    
    def get_required_skills(self):
        """Return the required skills as a list"""
        if self.required_skills:
            return json.loads(self.required_skills)
        return []
    
    def set_required_skills(self, skills):            #saves it back in the database in the right format
        """Set required skills from a list"""
        if skills:
            self.required_skills = json.dumps(skills)
        else:
            self.required_skills = None


class Resume(db.Model):
    __tablename__ = 'resumes'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    candidate_name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    extracted_skills = db.Column(db.Text, nullable=True)  # Stored as JSON
    experience = db.Column(db.Text, nullable=True)
    raw_text = db.Column(db.Text, nullable=True)
    match_score = db.Column(db.Float, nullable=True)  # Score against job description
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Key
    job_description_id = db.Column(db.Integer, db.ForeignKey('job_descriptions.id'))
    
    # Relationship
    job_description = db.relationship('JobDescription', back_populates='resumes')
    
    def __repr__(self):
        return f'<Resume {self.filename}>'
    
    def get_skills(self):
        """Return the extracted skills as a list"""
        if self.extracted_skills:
            return json.loads(self.extracted_skills)
        return []
    
    def set_skills(self, skills):
        """Set extracted skills from a list"""
        if skills:
            self.extracted_skills = json.dumps(skills)
        else:
            self.extracted_skills = None
    
    

    def calculate_match_score(self):
        """Calculate match score against job description"""
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.job_description or not self.extracted_skills:
            logger.debug("Missing job description or extracted skills")
            self.match_score = 0
            return 0
        
        resume_skills = self.get_skills()
        job_skills = self.job_description.get_required_skills()
        
        logger.debug(f"Resume skills: {resume_skills}")
        logger.debug(f"Job skills: {job_skills}")
        
        if not resume_skills or not job_skills:
            logger.debug("Empty skills list detected")
            self.match_score = 0
            return 0
        
        # Convert to lowercase for better matching
        resume_skills_lower = [skill.lower().strip() for skill in resume_skills]
        job_skills_lower = [skill.lower().strip() for skill in job_skills]
        
        # Improved matching - check if resume skills contain any part of job skills
        matches = []
        for job_skill in job_skills_lower:
            # Direct match
            if job_skill in resume_skills_lower:
                matches.append(job_skill)
                continue
                
            # Partial match - look for job skill within resume skills
            for resume_skill in resume_skills_lower:
                if (job_skill in resume_skill) or (resume_skill in job_skill):
                    matches.append(job_skill)
                    break
        
        matching_skills = len(matches)
        logger.debug(f"Matching skills found: {matching_skills}")
        logger.debug(f"Matches: {matches}")
        
        # Calculate score based on percentage of matching skills
        if len(job_skills) > 0:
            score = (matching_skills / len(job_skills)) * 100
        else:
            score = 0
        
        logger.debug(f"Match score: {score}%")    
        self.match_score = score
        return score
import re
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Common skill keywords to look for in resumes
COMMON_SKILLS = [
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "php", "swift", "go", "rust", "kotlin", "scala",
    # Web development
    "html", "css", "react", "angular", "vue", "node.js", "express", "django", "flask", "rails", "asp.net",
    # Data science
    "machine learning", "data analysis", "deep learning", "nlp", "data mining", "pandas", "numpy", "scikit-learn", 
    "tensorflow", "pytorch", "r", "statistics", "tableau", "power bi", "sql",
    # DevOps
    "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "jenkins", "terraform", "ansible", "git", "github",
    "gitlab", "devops",
    # Mobile
    "android", "ios", "react native", "flutter", "swift", "xamarin",
    # Soft skills
    "leadership", "communication", "teamwork", "problem solving", "critical thinking", "time management", 
    "project management", "agile", "scrum"
]

# Common section headers in resumes
EXPERIENCE_HEADERS = [
    "experience", "work experience", "employment history", "work history", "professional experience",
    "career", "professional background"
]

SKILLS_HEADERS = [
    "skills", "technical skills", "core competencies", "proficiencies", "expertise", "competencies",
    "technical proficiencies", "key skills", "skill set"
]

def extract_skills_experience(text):
    """
    Extract skills and experience from resume text
    
    Args:
        text (str): Raw text content from a resume
        
    Returns:
        dict: Dictionary containing extracted skills and experience sections
    """
    try:
        # Normalize text
        text = normalize_text(text)
        
        # Extract sections
        sections = extract_sections(text)
        
        # Extract skills
        skills = extract_skills(text, sections)
        
        # Extract experience
        experience = extract_experience(text, sections)
        
        # Calculate simple confidence scores
        skill_confidence = min(1.0, len(skills) / 20) if skills else 0
        exp_confidence = min(1.0, len(experience) / 200) if experience else 0
        
        result = {
            "skills": {
                "identified": skills,
                "confidence": round(skill_confidence * 100, 1)
            },
            "experience": {
                "content": experience,
                "confidence": round(exp_confidence * 100, 1)
            },
            "raw_text_sample": text[:500] + "..." if len(text) > 500 else text  # For debugging
        }
        
        return result
    except Exception as e:
        logger.error(f"Error extracting information: {str(e)}")
        raise

def normalize_text(text):
    """Normalize the text by removing extra spaces and converting to lowercase"""
    text = re.sub(r'\s+', ' ', text)
    text = text.lower().strip()
    return text

def extract_sections(text):
    """
    Extract different sections from the resume text
    
    Returns:
        dict: Dictionary with section names as keys and section content as values
    """
    sections = defaultdict(str)
    
    # Combine all possible headers
    all_headers = EXPERIENCE_HEADERS + SKILLS_HEADERS
    
    # Create a pattern to match section headers
    header_pattern = r'(?:^|\n)(?:' + '|'.join(all_headers) + r')[\s:]*\n'
    
    # Find potential section headers
    matches = list(re.finditer(header_pattern, text, re.IGNORECASE))
    
    if matches:
        for i, match in enumerate(matches):
            header = match.group().strip().lower()
            header = re.sub(r'[:\s]+', '', header)
            
            start_pos = match.end()
            end_pos = matches[i+1].start() if i < len(matches) - 1 else len(text)
            
            section_content = text[start_pos:end_pos].strip()
            sections[header] = section_content
    
    return sections

def extract_skills(text, sections):
    """
    Extract skills from the resume text
    
    Args:
        text (str): Full resume text
        sections (dict): Extracted sections
        
    Returns:
        list: List of identified skills
    """
    identified_skills = set()
    
    # Check if we have a dedicated skills section
    for header in SKILLS_HEADERS:
        if header in sections:
            section_text = sections[header]
            # Look for comma or bullet separated skills
            skill_candidates = re.split(r'[,•\n]', section_text)
            for skill in skill_candidates:
                skill = skill.strip()
                if skill and len(skill) > 2:  # Avoid very short matches
                    identified_skills.add(skill)
    
    # Also look for common skills throughout the text
    for skill in COMMON_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
            identified_skills.add(skill)
    
    return sorted(list(identified_skills))

def extract_experience(text, sections):
    """
    Extract work experience from the resume text
    
    Args:
        text (str): Full resume text
        sections (dict): Extracted sections
        
    Returns:
        str: Extracted experience section
    """
    # Look for dedicated experience sections
    for header in EXPERIENCE_HEADERS:
        if header in sections:
            return sections[header]
    
    # If no dedicated section found, try to identify experience blocks by patterns
    experience_patterns = [
        # Pattern for dates (e.g., 2018-2020, Jan 2018 - Present)
        r'(?:\d{4}\s*-\s*(?:\d{4}|present|current))[\s\n]+(.*?)(?=\d{4}\s*-|\Z)',
        # Pattern for job titles
        r'(?:senior|junior|lead|chief|principal|director|manager|engineer|developer|analyst|consultant|specialist|associate)[\s\n]+(.*?)(?=\n\n|\Z)'
    ]
    
    combined_experience = ""
    for pattern in experience_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            combined_experience += match.group() + "\n\n"
    
    return combined_experience.strip()

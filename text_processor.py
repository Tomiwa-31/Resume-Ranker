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
    "perl", "shell", "bash", "powershell", "vba", "matlab", "r programming", "objective-c", "groovy", "haskell",
    "lua", "clojure", "elixir", "dart", "fortran", "cobol", "assembly", "delphi", "pascal",
    
    # Web development
    "html", "css", "react", "angular", "vue", "node.js", "express", "django", "flask", "rails", "asp.net",
    "spring boot", "laravel", "symfony", "jquery", "bootstrap", "tailwind css", "material ui", "redux", "next.js",
    "nuxt.js", "svelte", "webpack", "babel", "pwa", "graphql", "rest api", "soap", "xml", "json", "seo",
    
    # Data science & Database
    "machine learning", "data analysis", "deep learning", "nlp", "data mining", "pandas", "numpy", "scikit-learn", 
    "tensorflow", "pytorch", "r", "statistics", "tableau", "power bi", "sql", "mysql", "postgresql", "mongodb",
    "oracle", "sqlite", "nosql", "redis", "elasticsearch", "cassandra", "mariadb", "ms sql server", "hadoop",
    "spark", "hive", "data warehouse", "etl", "data modeling", "data visualization", "big data", "ai",
    
    # DevOps & Cloud
    "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "jenkins", "terraform", "ansible", "git", "github",
    "gitlab", "devops", "devsecops", "infrastructure as code", "cloud computing", "serverless", "microservices",
    "containers", "virtualization", "vmware", "linux", "unix", "windows server", "networking", "cybersecurity",
    "security", "penetration testing", "firewall", "encryption", "ssl/tls", "vpn", 
    
    # Mobile & Desktop
    "android", "ios", "react native", "flutter", "swift", "xamarin", "mobile development", "app development",
    "winforms", "wpf", "uwp", "electron", "qt", "gtk", "desktop applications", "mobile apps",
    
    # Project Management & Tools
    "jira", "confluence", "trello", "asana", "scrum", "agile", "kanban", "waterfall", "prince2", "pmp", "msp",
    "project management", "product management", "slack", "microsoft teams", "microsoft office", "excel",
    "word", "powerpoint", "visio", "adobe", "photoshop", "illustrator", "figma", "sketch",
    
    # Soft skills
    "leadership", "communication", "teamwork", "problem solving", "critical thinking", "time management",
    "collaboration", "organization", "analytical skills", "attention to detail", "creativity", "adaptability",
    "flexibility", "interpersonal skills", "conflict resolution", "decision making", "strategic thinking",
    "negotiation", "customer service", "presentation skills", "mentoring"
]

# Common section headers in resumes
EXPERIENCE_HEADERS = [
    "experience", "work experience", "employment history", "work history", "professional experience",
    "career", "professional background"
]

SKILLS_HEADERS = [
    "skills", "technical skills", "core competencies", "proficiencies", "expertise", "competencies",
    "technical proficiencies", "key skills", "skill set", "technologies", "tech stack", "languages",
    "programming languages", "frameworks", "tools", "software", "platforms", "qualifications",
    "professional skills", "technical expertise", "areas of expertise", "strengths", "capabilities",
    "relevant skills", "professional competencies", "specialties", "specializations", "key strengths",
    "abilities", "key capabilities", "technologies used", "technical tools", "soft skills", "hard skills",
    "knowledge areas", "computer skills"
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
    import logging
    logger = logging.getLogger(__name__)
    
    identified_skills = set()
    
    # Check if we have a dedicated skills section
    for header in SKILLS_HEADERS:
        if header in sections:
            section_text = sections[header]
            logger.debug(f"Found skills section with header: {header}")
            # Look for comma, bullet, semicolon or newline separated skills
            skill_candidates = re.split(r'[,;•\n]', section_text)
            for skill in skill_candidates:
                skill = skill.strip()
                if skill and len(skill) > 2:  # Avoid very short matches
                    identified_skills.add(skill)
    
    # Also look for common skills throughout the text
    for skill in COMMON_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', text, re.IGNORECASE):
            identified_skills.add(skill)
    
    # Try to find skill lists with bullets or numbers
    bullet_lists = re.findall(r'(?:•|\* |\d+\.) (.+?)(?=(?:•|\* |\d+\.)|$)', text)
    for item in bullet_lists:
        item = item.strip()
        if item and len(item) > 2 and len(item) < 50:  # Reasonable length for a skill
            identified_skills.add(item)
    
    # Try to extract skills from "proficient in" or "experienced with" phrases
    skill_phrases = [
        r'proficient (?:in|with) (.+?)(?=\.|,|\n|$)',
        r'experienced (?:in|with) (.+?)(?=\.|,|\n|$)',
        r'knowledge of (.+?)(?=\.|,|\n|$)',
        r'familiar with (.+?)(?=\.|,|\n|$)',
        r'expertise in (.+?)(?=\.|,|\n|$)'
    ]
    
    for phrase in skill_phrases:
        matches = re.finditer(phrase, text, re.IGNORECASE)
        for match in matches:
            skill_text = match.group(1).strip()
            if skill_text and len(skill_text) > 2:
                # Further split by commas or 'and'
                sub_skills = re.split(r',|\sand\s', skill_text)
                for sub_skill in sub_skills:
                    sub_skill = sub_skill.strip()
                    if sub_skill and len(sub_skill) > 2:
                        identified_skills.add(sub_skill)
    
    logger.debug(f"Extracted {len(identified_skills)} skills")
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

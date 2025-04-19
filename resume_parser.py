import os
import logging
from io import StringIO

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def parse_resume(file_path):
    """
    Parse a resume file and extract its text content.
    
    Args:
        file_path (str): Path to the resume file (PDF or DOCX)
        
    Returns:
        str: Extracted text content from the resume
    """
    file_extension = file_path.split('.')[-1].lower()
    
    try:
        if file_extension == 'pdf':
            return parse_pdf(file_path)
        elif file_extension == 'docx':
            return parse_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    except Exception as e:
        logger.error(f"Error parsing resume: {str(e)}")
        raise

def parse_pdf(file_path):
    """
    Parse PDF files using PyPDF2
    
    Args:
        file_path (str): Path to the PDF file
        
    Returns:
        str: Extracted text content
    """
    try:
        # Import PyPDF2 here to avoid unnecessary imports when parsing DOCX
        import PyPDF2
        
        text = StringIO()
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Extract text from each page
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text.write(page.extract_text())
        
        return text.getvalue()
    except ImportError:
        logger.error("PyPDF2 is not installed. Please install it to parse PDF files.")
        raise
    except Exception as e:
        logger.error(f"Error parsing PDF: {str(e)}")
        raise

def parse_docx(file_path):
    """
    Parse DOCX files using python-docx
    
    Args:
        file_path (str): Path to the DOCX file
        
    Returns:
        str: Extracted text content
    """
    try:
        # Import python-docx here to avoid unnecessary imports when parsing PDF
        import docx
        
        doc = docx.Document(file_path)
        
        # Extract text from paragraphs
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
            
        # Also extract text from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        if para.text.strip():
                            full_text.append(para.text)
        
        return '\n'.join(full_text)
    except ImportError:
        logger.error("python-docx is not installed. Please install it to parse DOCX files.")
        raise
    except Exception as e:
        logger.error(f"Error parsing DOCX: {str(e)}")
        raise

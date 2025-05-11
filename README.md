# Resume-Ranker

Resume Ranker
Resume Ranker is a smart application designed to parse and analyze resumes (in PDF or DOC format), then intelligently match them to predefined job descriptions stored in a MySQL database. It automatically calculates a match rate for each resume and ranks them based on how well they align with the job requirements.

🚀 Features
✅ Supports PDF and DOC/DOCX resume uploads

📄 Extracts relevant information like skills, experience, and education

📊 Compares multiple resumes to a single job description

🧠 Uses keyword-matching logic to determine how well a resume fits

🔢 Calculates a match rate (%) for each resume

🏆 Ranks resumes from highest to lowest match rate for a given job

🛠️ Tech Stack
Backend: Python (Flask)

Database: MySQL

Parsing Libraries: pdfminer, python-docx

Frontend: HTML/CSS (Bootstrap if used)

Others: Resume parsing and keyword matching logic

🧩 How It Works
Upload Resume: The user uploads a resume in PDF or DOC format.

Resume Parsing: The system extracts text from the file and structures it.

Job Description Retrieval: A job description is fetched from the MySQL DB.

Match & Rank: The resume is matched against the job description using a keyword-based approach. A match percentage is calculated.

Display: The system ranks all uploaded resumes based on the match rate.

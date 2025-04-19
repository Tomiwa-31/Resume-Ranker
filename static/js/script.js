// Main JavaScript file for Resume Parser application

document.addEventListener('DOMContentLoaded', function() {
    // Handle file upload UI
    setupFileUpload();
    
    // Handle skill filtering if on results page
    setupSkillFiltering();
});

function setupFileUpload() {
    const uploadInput = document.getElementById('resumeUpload');
    const uploadWrapper = document.querySelector('.file-upload-wrapper');
    const selectedFileName = document.getElementById('selectedFileName');
    
    if (!uploadInput) return;
    
    // Handle file selection
    uploadInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            displayFileName(file.name);
        }
    });
    
    // Handle drag and drop events
    if (uploadWrapper) {
        uploadWrapper.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadWrapper.classList.add('dragover');
        });
        
        uploadWrapper.addEventListener('dragleave', function(e) {
            e.preventDefault();
            uploadWrapper.classList.remove('dragover');
        });
        
        uploadWrapper.addEventListener('drop', function(e) {
            uploadWrapper.classList.remove('dragover');
        });
    }
    
    function displayFileName(fileName) {
        if (selectedFileName) {
            selectedFileName.querySelector('span').textContent = fileName;
            selectedFileName.classList.remove('d-none');
        }
    }
}

function setupSkillFiltering() {
    // This function can be expanded if we want to add skill filtering functionality
    const skillBadges = document.querySelectorAll('.skill-badge');
    
    if (!skillBadges.length) return;
    
    skillBadges.forEach(badge => {
        badge.addEventListener('click', function() {
            // Toggle 'active' class for visual feedback
            this.classList.toggle('active');
            
            // This is where we could implement filtering logic if needed
            // For now, just providing visual feedback
            if (this.classList.contains('active')) {
                this.style.backgroundColor = 'rgba(var(--bs-info-rgb), 0.3)';
            } else {
                this.style.backgroundColor = 'rgba(var(--bs-info-rgb), 0.1)';
            }
        });
    });
}

// Add form validation if needed
function validateForm() {
    const fileInput = document.getElementById('resumeUpload');
    if (!fileInput || !fileInput.files.length) {
        alert('Please select a file to upload');
        return false;
    }
    
    const file = fileInput.files[0];
    const fileSize = file.size / 1024 / 1024; // in MB
    const fileExt = file.name.split('.').pop().toLowerCase();
    
    if (fileSize > 16) {
        alert('File size exceeds 16MB. Please select a smaller file.');
        return false;
    }
    
    if (!['pdf', 'docx'].includes(fileExt)) {
        alert('Invalid file type. Please upload a PDF or DOCX file.');
        return false;
    }
    
    return true;
}

// Form submission with validation
const resumeForm = document.getElementById('resumeForm');
if (resumeForm) {
    resumeForm.addEventListener('submit', function(e) {
        if (!validateForm()) {
            e.preventDefault();
        }
        
        // Add a loading state to the button
        const submitButton = this.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing...';
            submitButton.disabled = true;
        }
    });
}

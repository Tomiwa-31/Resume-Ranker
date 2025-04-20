// Main JavaScript file for Resume Parser application

// Add logging function
function logMessage(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
}

document.addEventListener('DOMContentLoaded', function() {
    logMessage('DOM loaded, initializing app');
    
    // Handle file upload UI
    setupFileUpload();
    
    // Handle skill filtering if on results page
    setupSkillFiltering();

    // Setup form submission
    setupFormSubmission();
});

function setupFileUpload() {
    const uploadInput = document.getElementById('resumeUpload');
    const uploadWrapper = document.querySelector('.file-upload-wrapper');
    const selectedFileName = document.getElementById('selectedFileName');
    
    if (!uploadInput) {
        logMessage('Upload input element not found', 'error');
        return;
    }
    
    logMessage('Setting up file upload');
    
    // Handle file selection
    uploadInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            logMessage(`File selected: ${file.name} (${Math.round(file.size / 1024)} KB)`);
            displayFileName(file.name);
        } else {
            logMessage('No file selected', 'warn');
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
            e.preventDefault(); // Add this to prevent default behavior
            uploadWrapper.classList.remove('dragover');
            // Make sure files are properly handled
            if (e.dataTransfer && e.dataTransfer.files.length > 0) {
                logMessage('File dropped on upload area');
                uploadInput.files = e.dataTransfer.files;
                const file = e.dataTransfer.files[0];
                displayFileName(file.name);
                // Trigger change event manually
                const changeEvent = new Event('change', { bubbles: true });
                uploadInput.dispatchEvent(changeEvent);
            }
        });
    } else {
        logMessage('Upload wrapper element not found', 'warn');
    }
    
    function displayFileName(fileName) {
        if (selectedFileName) {
            selectedFileName.querySelector('span').textContent = fileName;
            selectedFileName.classList.remove('d-none');
            logMessage(`Displayed filename: ${fileName}`);
        } else {
            logMessage('Selected file name element not found', 'warn');
        }
    }
}

function setupSkillFiltering() {
    // This function can be expanded if we want to add skill filtering functionality
    const skillBadges = document.querySelectorAll('.skill-badge');
    
    if (!skillBadges.length) {
        logMessage('No skill badges found, skipping skill filtering setup');
        return;
    }
    
    logMessage(`Setting up filtering for ${skillBadges.length} skill badges`);
    
    skillBadges.forEach(badge => {
        badge.addEventListener('click', function() {
            // Toggle 'active' class for visual feedback
            this.classList.toggle('active');
            
            // This is where we could implement filtering logic if needed
            // For now, just providing visual feedback
            if (this.classList.contains('active')) {
                this.style.backgroundColor = 'rgba(var(--bs-info-rgb), 0.3)';
                logMessage(`Skill activated: ${this.textContent}`);
            } else {
                this.style.backgroundColor = 'rgba(var(--bs-info-rgb), 0.1)';
                logMessage(`Skill deactivated: ${this.textContent}`);
            }
        });
    });
}

// Add form validation if needed
function validateForm() {
    const fileInput = document.getElementById('resumeUpload');
    if (!fileInput || !fileInput.files.length) {
        logMessage('No file selected', 'error');
        alert('Please select a file to upload');
        return false;
    }
    
    const file = fileInput.files[0];
    const fileSize = file.size / 1024 / 1024; // in MB
    const fileExt = file.name.split('.').pop().toLowerCase();
    
    logMessage(`Validating file: ${file.name}, size: ${fileSize.toFixed(2)}MB, type: ${fileExt}`);
    
    if (fileSize > 16) {
        logMessage(`File too large: ${fileSize.toFixed(2)}MB`, 'error');
        alert('File size exceeds 16MB. Please select a smaller file.');
        return false;
    }
    
    if (!['pdf', 'docx'].includes(fileExt)) {
        logMessage(`Invalid file type: ${fileExt}`, 'error');
        alert('Invalid file type. Please upload a PDF or DOCX file.');
        return false;
    }
    
    logMessage('Form validation passed');
    return true;
}

// Form submission with validation
function setupFormSubmission() {
    const resumeForm = document.getElementById('resumeForm');
    if (!resumeForm) {
        logMessage('Resume form not found', 'warn');
        return;
    }
    
    logMessage('Setting up form submission handler');
    
    resumeForm.addEventListener('submit', function(e) {
        logMessage('Form submission initiated');
        
        if (!validateForm()) {
            logMessage('Form validation failed, canceling submission', 'error');
            e.preventDefault();
            return;
        }
        
        // Add a loading state to the button
        const submitButton = this.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Processing...';
            submitButton.disabled = true;
            logMessage('Set button to loading state');
        }
        
        // Log form data being submitted
        const formData = new FormData(this);
        const fileInfo = formData.get('resume');
        if (fileInfo) {
            logMessage(`Submitting file: ${fileInfo.name}, size: ${Math.round(fileInfo.size / 1024)}KB, type: ${fileInfo.type}`);
        }
        
        logMessage('Form submission proceeding');
    });
}

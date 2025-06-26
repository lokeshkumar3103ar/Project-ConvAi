/**
 * ConvAi-IntroEval
 * Frontend Application Script
 * 
 * This script handles the user interface for the ConvAi-IntroEval system,
 * including file uploads, streaming API responses, and results display.
*/

// Initialize global app state and handlers
window.appState = {
    file: null,
    taskId: null,
    transcriptPath: null,
    transcriptText: null,
    extractedFields: null,
    profileRating: null,
    introRating: null,
    eventSources: []
};

// Initialize file handling functions globally
window.handleFileSelect = function(file) {
    console.log('handleFileSelect called with file:', file);
    if (!file) return false;
    
    // Check if file is audio or video
    const fileType = file.type.split('/')[0];
    if (fileType !== 'audio' && fileType !== 'video') {
        console.error('Invalid file type:', fileType);
        if (typeof window.showError === 'function') {
            window.showError('Please select an audio or video file.');
        } else {
            console.error('Please select an audio or video file.');
        }
        return false;
    }

    // Update global state
    window.appState = window.appState || {};
    window.appState.file = file;
    
    // Get DOM elements - For recording we need to handle this synchronously
    const fileInput = document.getElementById('file-input');
    const fileName = document.getElementById('file-name');
    const fileInfo = document.getElementById('file-info');
    
    if (fileInput && fileName && fileInfo) {
        try {
            // Create a DataTransfer object to update file input
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;
            
            // Update file information display
            fileName.textContent = file.name;
            fileInfo.classList.remove('d-none');
            
            return true;
        } catch (error) {
            console.error('Error updating file input:', error);
            return false;
        }
    } else {
        // If DOM elements aren't ready, still save the file but return false
        // This allows the recording functionality to know there was an issue
        console.warn('DOM elements not ready for file display, but file is saved');
        return false;
    }
};

document.addEventListener('DOMContentLoaded', function() {
    // Profile elements
    const profileUsername = document.getElementById('profile-username');
    const profileRollNumber = document.getElementById('profile-roll-number');
    const profileUserType = document.getElementById('profile-user-type');
    const logoutBtn = document.getElementById('logout-btn');
    
    // Load user profile information
    async function loadUserProfile() {
        try {
            console.log('Starting user profile load...');
            console.log('Document cookies:', document.cookie);
            
            const response = await fetch('/api/auth/me', {
                credentials: 'include' // Include cookies for authentication
            });
            
            console.log('Profile response status:', response.status);
            console.log('Profile response headers:', [...response.headers.entries()]);
            
            if (response.ok) {
                const userInfo = await response.json();
                console.log('User profile loaded successfully:', userInfo);
                
                // Update profile elements
                if (profileUsername) {
                    profileUsername.textContent = userInfo.username || 'Unknown';
                }
                  if (profileRollNumber) {
                    profileRollNumber.textContent = userInfo.roll_number || 'N/A';
                }
                
                if (profileUserType) {
                    const userType = userInfo.user_type || 'student';
                    profileUserType.textContent = userType.charAt(0).toUpperCase() + userType.slice(1);
                    profileUserType.className = `badge ${userType === 'teacher' ? 'bg-primary' : 'bg-success'}`;
                }
            } 
            else if (response.status === 401) {
                console.log('User not authenticated, redirecting to login');
                // User is not authenticated, redirect to login
                window.location.href = '/login';
            } else {
                console.error('Failed to load user profile:', response.status);
                // Set default values on error
                if (profileUsername) profileUsername.textContent = 'Not logged in';
                if (profileRollNumber) profileRollNumber.textContent = 'N/A';
                if (profileUserType) {
                    profileUserType.textContent = 'Unknown';
                    profileUserType.className = 'badge bg-secondary';
                }
            }
        } catch (error) {
            console.error('Error loading user profile:', error);
            // Set error values and redirect to login
            if (profileUsername) profileUsername.textContent = 'Error';
            if (profileRollNumber) profileRollNumber.textContent = 'Error';
            if (profileUserType) {
                profileUserType.textContent = 'Error';
                profileUserType.className = 'badge bg-danger';
            }
            // On network error, also redirect to login after a delay
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        }
    }
    
    // Logout functionality
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function(e) {
            e.preventDefault(); // Prevent default link behavior
            
            try {
                const response = await fetch('/logout', {
                    method: 'POST',
                    credentials: 'include', // Include cookies
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                });
                
                // Clear any stored data
                localStorage.removeItem('showFluidTransition');
                
                // Always redirect to login page regardless of response
                window.location.href = '/login';
                
            } catch (error) {
                console.error('Error during logout:', error);
                // Force redirect anyway
                window.location.href = '/login';
            }
        });
    }
      // Load user profile on page load with a small delay to ensure cookies are available
    setTimeout(() => {
        loadUserProfile();
    }, 500); // 500ms delay

    // DOM Elements
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const dropZone = document.getElementById('drop-zone');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const clearFileBtn = document.getElementById('clear-file');
    const extractFieldsCheckbox = document.getElementById('extract-fields');
    const generateRatingsCheckbox = document.getElementById('generate-ratings');
    const uploadButton = document.getElementById('upload-button');
    
    const uploadSection = document.getElementById('upload-section');
    const processingSection = document.getElementById('processing-section');
    const resultsSection = document.getElementById('results-section');
    
    const transcriptionStatus = document.getElementById('transcription-status');
    const extractionStatus = document.getElementById('extraction-status');
    const ratingStatus = document.getElementById('rating-status');
    
    const processingMessage = document.getElementById('processing-message');
    const processingMessageText = document.getElementById('processing-message-text');
      const transcriptContent = document.getElementById('transcript-content');
    // Note: Extracted fields tab is hidden in the UI for production but still functional in the backend
    const extractedFieldsContent = document.getElementById('extracted-fields-content');
    const profileRatingContent = document.getElementById('profile-rating-content');
    const introRatingContent = document.getElementById('intro-rating-content');
      const startNewButton = document.getElementById('start-new-button');
      // Tips modal elements
    const tipsToggle = document.getElementById('tips-toggle');
    const tipsModal = document.getElementById('tips-modal');
    const tipsCloseBtn = document.getElementById('tips-close-btn');
    
    // Rubrics modal elements
    const rubricsToggle = document.getElementById('rubrics-toggle');
    const rubricsModal = document.getElementById('rubrics-modal');
    const rubricsCloseBtn = document.getElementById('rubrics-close-btn');
    const rubricsTabs = document.querySelectorAll('.rubrics-tab');
    const rubricsTabContents = document.querySelectorAll('.rubrics-tab-content');
    
    const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
    const errorMessage = document.getElementById('error-message');
    
    // Progress steps
    const stepUpload = document.getElementById('step-upload');
    const stepTranscribe = document.getElementById('step-transcribe');
    const stepExtract = document.getElementById('step-extract');
    const stepRate = document.getElementById('step-rate');
      // Use the global app state
    const appState = window.appState;
      // Reset the application
    function resetApp() {
        // Close any open event sources
        appState.eventSources.forEach(es => {
            if (es && es.close) es.close();
        });
        appState.eventSources = [];
        
        // Stop task status polling
        stopTaskPolling();
        
        // Reset file input and state
        fileInput.value = '';
        appState.file = null;
        appState.taskId = null;
        fileInfo.classList.add('d-none');
        
        // Reset sections visibility
        uploadSection.classList.remove('d-none');
        processingSection.classList.add('d-none');
        resultsSection.classList.add('d-none');
        
        // Reset progress steps
        stepUpload.classList.add('active');
        stepUpload.classList.remove('completed');
        stepTranscribe.classList.remove('active', 'completed');
        stepExtract.classList.remove('active', 'completed');
        stepRate.classList.remove('active', 'completed');
        
        // Reset status elements
        updateStatusElement(transcriptionStatus, 'waiting', 'Transcribing Audio', 'Waiting to process your audio...');
        updateStatusElement(extractionStatus, 'waiting', 'Extracting Information', 'Waiting to extract information from transcript...');
        updateStatusElement(ratingStatus, 'waiting', 'Generating Ratings', 'Waiting to evaluate your introduction...');
        
        // Reset progress bars
        document.querySelectorAll('.progress-bar').forEach(bar => {
            bar.style.width = '0%';
        });
        
        // Reset content areas
        transcriptContent.textContent = '';
        extractedFieldsContent.innerHTML = '';
        profileRatingContent.innerHTML = '';
        introRatingContent.innerHTML = '';
        
        // Hide processing message
        processingMessage.classList.add('d-none');
        
        // Enable form elements
        uploadButton.disabled = false;
        extractFieldsCheckbox.disabled = false;
        generateRatingsCheckbox.disabled = false;
    }
    
    // Update a status element (transcription, extraction, rating)
    function updateStatusElement(element, status, title, message, progress = null) {
        const statusIcon = element.querySelector('.status-icon');
        const statusTitle = element.querySelector('h4');
        const statusMessage = element.querySelector('.status-message');
        const progressBar = element.querySelector('.progress-bar');
        
        // Update icon state
        statusIcon.className = 'status-icon ' + status;
        
        // Update title and message if provided
        if (title) statusTitle.textContent = title;
        if (message) statusMessage.textContent = message;
        
        // Update progress bar if provided
        if (progress !== null && progressBar) {
            progressBar.style.width = `${progress}%`;
        }
    }
      // Show an error message
    function showError(message) {
        errorMessage.textContent = message;
        errorModal.show();
    }
    
    // Make showError function globally available for recording functionality
    window.showError = showError;// Handle file selection is now defined globally
    
    // Display extracted fields in a formatted way
    function displayExtractedFields(fields) {
        if (!fields || typeof fields !== 'object') {
            extractedFieldsContent.innerHTML = '<div class="alert alert-warning">No fields were extracted.</div>';
            return;
        }
        
        let html = '';
        
        for (const [key, value] of Object.entries(fields)) {
            if (value === null || value === undefined || value === '') continue;
            
            const fieldName = key
                .replace(/_/g, ' ')
                .replace(/\b\w/g, l => l.toUpperCase());
            
            html += `
                <div class="field-item">
                    <div class="field-label">${fieldName}</div>
                    <div class="field-value">${value}</div>
                </div>
            `;
        }
        
        if (html === '') {
            extractedFieldsContent.innerHTML = '<div class="alert alert-warning">No fields were extracted.</div>';
        } else {
            extractedFieldsContent.innerHTML = html;
        }
    }
      // Display rating data in a formatted way
    function displayRating(ratingData, container) {
        console.log('Display rating called with container:', container ? container.id : 'undefined');
        
        if (!container) {
            console.error('Rating display container is null or undefined');
            return;
        }
        
        try {
            if (!ratingData || typeof ratingData !== 'object') {
                container.innerHTML = '<div class="alert alert-warning">No rating data available.</div>';
                console.error('Invalid rating data provided:', ratingData);
                return;
            }
              console.log('Rating data structure:', Object.keys(ratingData).join(', '));
            console.log('Rating data values:', JSON.stringify(ratingData, null, 2).substring(0, 500) + '...');
            
            // Specific check for hiring insights
            if (ratingData.hiring_insights) {
                console.log('🎯 Found hiring_insights in data:', ratingData.hiring_insights);
            } else {
                console.log('❌ No hiring_insights found in data');
            }
              // Make a copy of the data to avoid manipulation issues
            const data = JSON.parse(JSON.stringify(ratingData));
            
            // Determine if it's a profile or intro rating based on the presence of specific fields
            const isProfileRating = data.hasOwnProperty('profile_rating');
            const isIntroRating = data.hasOwnProperty('intro_rating');
            
            console.log(`Detected rating type: ${isProfileRating ? 'Profile' : (isIntroRating ? 'Introduction' : 'Unknown')}`);
            console.log(`Profile rating field present: ${data.hasOwnProperty('profile_rating')}`);
            console.log(`Intro rating field present: ${data.hasOwnProperty('intro_rating')}`);
            
            let html = '';
            // Overall rating processing - handle both profile and intro ratings
            let overallScore;
            
            if (isProfileRating && data.profile_rating !== undefined) {
                // Handle profile_rating using our normalize utility if available
                if (typeof window.normalizeRating === 'function') {
                    overallScore = window.normalizeRating(data.profile_rating, 5);
                    console.log(`Using normalizeRating utility for profile_rating: ${data.profile_rating} -> ${overallScore}/5`);
                } else {
                    // Fallback to the manual conversion if utility not available
                    let profileRating = data.profile_rating;
                    console.log(`Original profile_rating: ${profileRating}, type: ${typeof profileRating}`);
                    
                    // Extract numeric part if it's in format like "2.61/10"
                    if (typeof profileRating === 'string' && profileRating.includes('/')) {
                        profileRating = profileRating.split('/')[0].trim();
                        console.log(`Extracted numeric part: ${profileRating}`);
                    }
                    
                    // Parse to a number, ensuring it's valid
                    const numericRating = parseFloat(profileRating);
                    console.log(`Parsed numeric rating: ${numericRating}`);
                    
                    if (!isNaN(numericRating)) {
                        // Convert from 0-10 scale to 0-5 scale
                        overallScore = (numericRating / 10 * 5).toFixed(1);
                        console.log(`Converted to 0-5 scale: ${overallScore}`);
                    } else {
                        overallScore = "0.0";
                        console.log(`Invalid rating detected, defaulting to ${overallScore}`);
                    }
                }
                  console.log(`Final profile_rating: ${data.profile_rating} -> ${overallScore}/5`);
            } else if (isIntroRating && data.intro_rating !== undefined) {
                // Handle intro_rating - intro ratings are already on 0-10 scale
                let introRating = data.intro_rating;
                console.log(`Original intro_rating: ${introRating}, type: ${typeof introRating}`);
                
                // Extract numeric part if it's in format like "9.0/10"
                if (typeof introRating === 'string' && introRating.includes('/')) {
                    introRating = introRating.split('/')[0].trim();
                    console.log(`Extracted numeric part: ${introRating}`);
                }
                
                // Parse to a number, ensuring it's valid
                const numericRating = parseFloat(introRating);
                console.log(`Parsed numeric rating: ${numericRating}`);
                
                if (!isNaN(numericRating)) {
                    // Intro ratings are already on 0-10 scale, convert to 0-5 for star display
                    overallScore = (numericRating / 2).toFixed(1);
                    console.log(`Converted intro rating for star display: ${numericRating}/10 -> ${overallScore}/5`);
                } else {
                    overallScore = "0.0";
                    console.log(`Invalid intro rating detected, defaulting to ${overallScore}`);
                }                
                console.log(`Final intro_rating: ${data.intro_rating} -> ${overallScore}/5 for stars, ${numericRating}/10 for display`);
            } else {
                // Fallback to other possible score fields
                const fallbackFields = ['overall_score', 'overall_rating', 'score', 'rating'];
                let foundValue = null;
                
                for (const field of fallbackFields) {
                    if (data[field] !== undefined) {
                        foundValue = data[field];
                        console.log(`Found fallback rating in field "${field}": ${foundValue}`);
                        break;
                    }
                }
                
                if (foundValue !== null) {
                    // Process the found value
                    if (typeof foundValue === 'string' && foundValue.includes('/')) {
                        const parts = foundValue.split('/');
                        foundValue = parts[0].trim();
                        console.log(`Extracted numeric part from fallback: ${foundValue}`);
                    }
                    
                    // Convert to a number if needed
                    const numericValue = parseFloat(foundValue);
                    if (!isNaN(numericValue)) {
                        // Check if it needs scaling (if value > 5, assume it's on a 0-10 scale)
                        if (numericValue > 5) {
                            overallScore = (numericValue / 10 * 5).toFixed(1);
                            console.log(`Scaled fallback value from 0-10 to 0-5: ${numericValue} -> ${overallScore}`);
                        } else {
                            overallScore = numericValue.toFixed(1);
                            console.log(`Using fallback numeric value as is: ${overallScore}`);
                        }
                    } else {
                        overallScore = "0.0";
                        console.log(`Invalid fallback value, defaulting to ${overallScore}`);
                    }                } else {
                    overallScore = "0.0";
                    console.log(`No fallback rating found, defaulting to ${overallScore}`);
                }
            }
            
            // Ensure overallScore is a valid number for star calculation
            const numericScore = parseFloat(overallScore);
            const starCount = isNaN(numericScore) ? 0 : Math.round(numericScore);
            console.log(`Star count calculated: ${starCount} from score ${overallScore}, numeric: ${numericScore}`);
            
            // Generate star representation
            const filledStar = '★';
            const emptyStar = '☆';
            const stars = filledStar.repeat(starCount) + emptyStar.repeat(Math.max(0, 5 - starCount));
            console.log(`Stars representation: "${stars}" (${starCount} filled stars)`);
            
            // Calculate display score - for intro ratings use original value, for profile ratings convert back to 10-scale
            let displayScore;
            if (!isProfileRating && data.intro_rating !== undefined) {
                // For intro ratings, use the original intro_rating value directly (already 0-10 scale)
                let originalIntroRating = data.intro_rating;
                if (typeof originalIntroRating === 'string' && originalIntroRating.includes('/')) {
                    originalIntroRating = originalIntroRating.split('/')[0].trim();                }
                displayScore = parseFloat(originalIntroRating).toFixed(1);
                console.log(`Display score for intro rating (using original): ${displayScore}/10`);
            } else {
                // For profile ratings, convert back from 0-5 scale to 0-10 scale
                displayScore = (parseFloat(overallScore) * 2).toFixed(1);
                console.log(`Display score for profile rating (converted): ${displayScore}/10`);
            }
            
            html += `
                <div class="rating-card">
                    <div class="rating-header">
                        <h5 class="rating-title">Overall Rating</h5>
                        <span class="rating-score">${displayScore}/10</span>
                    </div>
                    <div class="rating-stars">${stars}</div>
                    <div class="rating-comment">
                        ${getFeedbackText(data)}
                    </div>
                </div>
            `;
              // Helper function to extract appropriate feedback text based on data structure
            function getFeedbackText(data) {
                // For intro ratings
                if (!isProfileRating) {
                    // Check feedback array first (intro ratings typically have this)
                    if (data.feedback && Array.isArray(data.feedback) && data.feedback.length > 0) {
                        return data.feedback.join('<br>');
                    }
                    
                    // Check for notes in grading_debug
                    if (data.grading_debug && data.grading_debug.notes) {
                        return data.grading_debug.notes;
                    }
                }
                
                // For profile ratings
                if (isProfileRating) {
                    // Check for notes in grading_debug
                    if (data.grading_debug && data.grading_debug.notes) {
                        // Remove brackets if present
                        let notes = data.grading_debug.notes;
                        if (notes.startsWith('[') && notes.endsWith(']')) {
                            notes = notes.substring(1, notes.length - 1);
                        }
                        return notes;
                    }
                }
                
                // Fallback to other possible fields
                return data.overall_feedback || data.summary || data.feedback || 'No overall feedback provided.';
            }            // Add grading explanation categories if available
            if (data.grading_explanation && typeof data.grading_explanation === 'object') {
                html += `
                    <div class="rating-card" style="margin-top: 24px;">
                        <div class="rating-header">
                            <h4 class="rating-title">
                                <i class="fas fa-chart-bar me-2"></i>Category Ratings
                            </h4>
                        </div>
                        <div class="rating-details">
                `;
                
                for (const [category, score] of Object.entries(data.grading_explanation)) {                    // Create mapping for updated intro rating field names  
                    const categoryDisplayMap = {
                        // New intro rating field names
                        'grammar_and_clarity': 'Grammar & Clarity',
                        'structure': 'Structure & Organization', 
                        'information_coverage': 'Information Coverage',
                        'relevance_to_professional_context': 'Professional Relevance',
                        // Legacy intro rating field names (for backward compatibility)
                        'info_coverage': 'Information Coverage',
                        'relevance_to_role': 'Professional Relevance',
                        // Profile rating field names (for compatibility)
                        'practical_foundation': 'Practical Foundation',
                        'technical_competency': 'Technical Competency',
                        'hands_on_experience': 'Hands-On Experience',
                        'growth_potential': 'Growth Potential'
                    };
                    
                    // Use mapped display name or format the original category name
                    const categoryDisplay = categoryDisplayMap[category] || 
                        category
                            .replace(/_/g, ' ')
                            .split(' ')
                            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                            .join(' ');
                    
                    html += `
                        <div class="rating-subcategory mb-2">
                            <div class="rating-subcategory-header">
                                <strong>${categoryDisplay}:</strong>
                            </div>
                            <div class="rating-subcategory-score">
                                ${score}
                            </div>
                        </div>
                    `;
                }
                
                html += `
                        </div>
                    </div>
                `;
            }
              // Add insights section for intro ratings
            if (!isProfileRating && data.insights && Array.isArray(data.insights) && data.insights.length > 0) {
                html += `
                    <div class="rating-card" style="margin-top: 24px;">
                        <div class="rating-header">
                            <h4 class="rating-title">
                                <i class="fas fa-lightbulb me-2"></i>Key Insights
                            </h4>
                        </div>
                        <div class="rating-details">
                            <ul class="list-group list-group-flush">
                `;
                
                data.insights.forEach(insight => {
                    html += `<li class="list-group-item" style="background: var(--background-primary); border-color: var(--border-color); color: var(--text-secondary);">
                        <i class="fas fa-lightbulb text-warning me-2"></i>${insight}
                    </li>`;
                });
                
                html += `
                            </ul>
                        </div>
                    </div>
                `;
            }
              // Add specific feedback section for intro ratings
            if (!isProfileRating && data.feedback && Array.isArray(data.feedback) && data.feedback.length > 0) {
                html += `
                    <div class="rating-card" style="margin-top: 24px;">
                        <div class="rating-header">
                            <h4 class="rating-title">
                                <i class="fas fa-comment-dots me-2"></i>Detailed Feedback
                            </h4>
                        </div>
                        <div class="rating-details">
                            <ul class="list-group list-group-flush">
                `;
                
                data.feedback.forEach(feedbackItem => {
                    html += `<li class="list-group-item" style="background: var(--background-primary); border-color: var(--border-color); color: var(--text-secondary);">
                        <i class="fas fa-comment-dots text-primary me-2"></i>${feedbackItem}
                    </li>`;
                });
                
                html += `                            </ul>
                        </div>
                    </div>
                `;
            }
            
            // Profile-specific ratings
            if (isProfileRating) {
                // Skills section
                const skills = data.skills || {};
                if (Object.keys(skills).length > 0) {
                    html += `<h5 class="mt-4">Skills Assessment</h5>`;
                    
                    for (const [skill, details] of Object.entries(skills)) {
                        let skillScore, skillFeedback;
                        
                        if (typeof details === 'object') {
                            skillScore = details.score || 'N/A';
                            skillFeedback = details.feedback || 'No feedback provided.';
                        } else if (typeof details === 'number' || !isNaN(parseFloat(details))) {
                            skillScore = details;
                            skillFeedback = 'No feedback provided.';
                        } else if (typeof details === 'string') {
                            skillScore = 'N/A';
                            skillFeedback = details;
                        }
                          // Convert skill score to 0-5 scale for stars, but keep original for display
                        let skillScoreForDisplay = skillScore;
                        let skillScoreForStars = skillScore;
                        
                        if (typeof skillScore === 'number' || !isNaN(parseFloat(skillScore))) {
                            const numericSkillScore = parseFloat(skillScore);
                            if (numericSkillScore > 5) {
                                // Scale down from 0-10 to 0-5 for stars
                                skillScoreForStars = (numericSkillScore / 10 * 5);
                                // Keep original 0-10 scale for display
                                skillScoreForDisplay = numericSkillScore.toFixed(1);
                            } else {
                                skillScoreForStars = numericSkillScore;
                                skillScoreForDisplay = numericSkillScore.toFixed(1);
                            }
                        }
                        
                        const skillStarCount = Math.round(parseFloat(skillScoreForStars)) || 0;
                        const skillStars = '★'.repeat(skillStarCount) + '☆'.repeat(5 - skillStarCount);
                        
                        html += `
                            <div class="rating-card">
                                <div class="rating-header">
                                    <h5 class="rating-title">${skill}</h5>
                                    <span class="rating-score">${skillScoreForDisplay}/10</span>
                                </div>
                                <div class="rating-stars">${skillStars}</div>
                                <div class="rating-comment">
                                    ${skillFeedback}
                                </div>
                            </div>
                        `;
                    }
                }
                
                // Strengths and improvement areas - try multiple property paths
                let strengths = data.profile_strengths || data.strengths || [];
                if (typeof strengths === 'string') {
                    // If strengths is a string, convert to array
                    strengths = [strengths];
                } else if (typeof strengths === 'object' && !Array.isArray(strengths)) {
                    // If strengths is an object but not array, convert to array of values
                    strengths = Object.values(strengths);
                }
                
                if (strengths && strengths.length > 0) {
                    html += `<h5 class="mt-4">Strengths</h5>`;
                    html += `<ul class="list-group mb-4">`;
                    
                    strengths.forEach(strength => {
                        if (strength && typeof strength === 'string') {
                            html += `<li class="list-group-item"><i class="fas fa-check-circle text-success me-2"></i>${strength}</li>`;
                        }
                    });
                    
                    html += `</ul>`;
                }
                
                let improvements = data.improvement_areas || data.areas_for_improvement || [];
                if (typeof improvements === 'string') {
                    // If improvements is a string, convert to array
                    improvements = [improvements];
                } else if (typeof improvements === 'object' && !Array.isArray(improvements)) {
                    // If improvements is an object but not array, convert to array of values
                    improvements = Object.values(improvements);
                }
                
                if (improvements && improvements.length > 0) {
                    html += `<h5 class="mt-4">Areas for Improvement</h5>`;
                    html += `<ul class="list-group mb-4">`;
                    
                    improvements.forEach(improvement => {
                        if (improvement && typeof improvement === 'string') {
                            html += `<li class="list-group-item"><i class="fas fa-arrow-alt-circle-up text-primary me-2"></i>${improvement}</li>`;
                        }
                    });
                      html += `</ul>`;
                }                // Add hiring insights section for profile ratings
                if (data.hiring_insights && typeof data.hiring_insights === 'object') {
                    console.log('🔍 Processing hiring insights:', data.hiring_insights);
                    html += `
                        <div class="rating-card" style="margin-top: 24px;">
                            <div class="rating-header">
                                <h4 class="rating-title">
                                    <i class="fas fa-briefcase text-info me-2"></i>Hiring Insights
                                </h4>
                            </div>
                            <div class="rating-details">
                    `;
                    
                    const insights = data.hiring_insights;
                    
                    // Helper function to extract text from array or string
                    const extractText = (value) => {
                        if (Array.isArray(value)) {
                            return value.join(', ');
                        } else if (typeof value === 'string') {
                            // Remove brackets if they exist
                            return value.replace(/^\[|\]$/g, '').trim();
                        }
                        return value;
                    };
                    
                    // Strongest Assets
                    if (insights.strongest_assets) {
                        const assetsText = extractText(insights.strongest_assets);
                        console.log('📊 Assets text:', assetsText);
                        if (assetsText && assetsText.length > 0) {
                            html += `
                                <div class="insight-section mb-3">
                                    <h6 class="insight-title"><i class="fas fa-star text-warning me-2"></i>Strongest Assets</h6>
                                    <div class="insight-content">
                                        ${assetsText}
                                    </div>
                                </div>
                            `;
                        }
                    }
                    
                    // Development Areas
                    if (insights.development_areas) {
                        const developmentText = extractText(insights.development_areas);
                        console.log('📈 Development text:', developmentText);
                        if (developmentText && developmentText.length > 0) {
                            html += `
                                <div class="insight-section mb-3">
                                    <h6 class="insight-title"><i class="fas fa-chart-line text-primary me-2"></i>Development Areas</h6>
                                    <div class="insight-content">
                                        ${developmentText}
                                    </div>
                                </div>
                            `;
                        }
                    }
                    
                    // Industry Readiness
                    if (insights.industry_readiness) {
                        const readinessText = extractText(insights.industry_readiness);
                        console.log('🏭 Readiness text:', readinessText);
                        if (readinessText && readinessText.length > 0) {
                            html += `
                                <div class="insight-section mb-3">
                                    <h6 class="insight-title"><i class="fas fa-industry text-success me-2"></i>Industry Readiness</h6>
                                    <div class="insight-content">
                                        ${readinessText}
                                    </div>
                                </div>
                            `;                        }
                    }
                    
                    // Close the rating card structure
                    html += `
                            </div>
                        </div>
                    `;
                } else {
                    console.log('❌ No hiring insights found or invalid format:', data.hiring_insights);
                }

                // Add employability level if available
                if (data.employability_level && data.employability_level.length > 0) {
                    // Get color class based on employability level
                    let levelColor = 'secondary';
                    if (data.employability_level.includes('HIGHLY EMPLOYABLE')) levelColor = 'success';
                    else if (data.employability_level.includes('GOOD EMPLOYABILITY')) levelColor = 'info';
                    else if (data.employability_level.includes('MODERATE EMPLOYABILITY')) levelColor = 'warning';
                    else if (data.employability_level.includes('DEVELOPING POTENTIAL')) levelColor = 'primary';
                    else if (data.employability_level.includes('LIMITED EMPLOYABILITY')) levelColor = 'danger';
                    
                    html += `
                        <div class="employability-badge mt-3 mb-4">
                            <h6 class="mb-2"><i class="fas fa-user-tie me-2"></i>Employability Assessment</h6>
                            <span class="badge bg-${levelColor} fs-6 px-3 py-2">
                                <i class="fas fa-briefcase me-1"></i>${data.employability_level}
                            </span>
                        </div>
                    `;
                }
            } 
            // Introduction-specific ratings
            else {
                // Content quality
                if (data.content_rating) {
                    const contentScore = typeof data.content_rating === 'object' ? 
                                       (data.content_rating.score || 'N/A') : 
                                       (typeof data.content_rating === 'number' ? data.content_rating : 'N/A');
                    
                    const contentFeedback = typeof data.content_rating === 'object' ? 
                                          (data.content_rating.feedback || 'No feedback provided.') :
                                          (typeof data.content_rating === 'string' ? data.content_rating : 'No feedback provided.');
                      // Convert content score for proper display and stars
                    let contentScoreForDisplay = contentScore;
                    let contentScoreForStars = contentScore;
                    
                    if (typeof contentScore === 'number' || !isNaN(parseFloat(contentScore))) {
                        const numericContentScore = parseFloat(contentScore);
                        if (numericContentScore > 5) {
                            // Scale down from 0-10 to 0-5 for stars
                            contentScoreForStars = (numericContentScore / 10 * 5);
                            // Keep original 0-10 scale for display
                            contentScoreForDisplay = numericContentScore.toFixed(1);
                        } else {
                            contentScoreForStars = numericContentScore;
                            contentScoreForDisplay = numericContentScore.toFixed(1);
                        }
                    }
                    
                    const contentStarCount = Math.round(parseFloat(contentScoreForStars)) || 0;
                    const contentStars = '★'.repeat(contentStarCount) + '☆'.repeat(5 - contentStarCount);
                    
                    html += `
                        <div class="rating-card">
                            <div class="rating-header">
                                <h5 class="rating-title">Content Quality</h5>
                                <span class="rating-score">${contentScoreForDisplay}/10</span>
                            </div>
                            <div class="rating-stars">${contentStars}</div>
                            <div class="rating-comment">
                                ${contentFeedback}
                            </div>
                        </div>
                    `;
                }
                
                // Delivery quality
                if (data.delivery_rating) {
                    const deliveryScore = typeof data.delivery_rating === 'object' ? 
                                        (data.delivery_rating.score || 'N/A') : 
                                        (typeof data.delivery_rating === 'number' ? data.delivery_rating : 'N/A');
                    
                    const deliveryFeedback = typeof data.delivery_rating === 'object' ? 
                                           (data.delivery_rating.feedback || 'No feedback provided.') :
                                           (typeof data.delivery_rating === 'string' ? data.delivery_rating : 'No feedback provided.');
                      // Convert delivery score for proper display and stars
                    let deliveryScoreForDisplay = deliveryScore;
                    let deliveryScoreForStars = deliveryScore;
                    
                    if (typeof deliveryScore === 'number' || !isNaN(parseFloat(deliveryScore))) {
                        const numericDeliveryScore = parseFloat(deliveryScore);
                        if (numericDeliveryScore > 5) {
                            // Scale down from 0-10 to 0-5 for stars
                            deliveryScoreForStars = (numericDeliveryScore / 10 * 5);
                            // Keep original 0-10 scale for display
                            deliveryScoreForDisplay = numericDeliveryScore.toFixed(1);
                        } else {
                            deliveryScoreForStars = numericDeliveryScore;
                            deliveryScoreForDisplay = deliveryScoreForDisplay.toFixed(1);
                        }
                    }
                    
                    const deliveryStarCount = Math.round(parseFloat(deliveryScoreForStars)) || 0;
                    const deliveryStars = '★'.repeat(deliveryStarCount) + '☆'.repeat(5 - deliveryStarCount);
                    
                    html += `
                        <div class="rating-card">
                            <div class="rating-header">
                                <h5 class="rating-title">Delivery Quality</h5>
                                <span class="rating-score">${deliveryScoreForDisplay}/10</span>
                            </div>
                            <div class="rating-stars">${deliveryStars}</div>
                            <div class="rating-comment">
                                ${deliveryFeedback}
                            </div>
                        </div>
                    `;
                }
                
                // Handle flat structure ratings (without nested objects)
                const ratingCategories = {
                    'content': ['content', 'content_quality', 'content_score'],
                    'delivery': ['delivery', 'delivery_quality', 'delivery_score'],
                    'structure': ['structure', 'structure_quality', 'structure_score'],
                    'clarity': ['clarity', 'clarity_quality', 'clarity_score']
                };
                
                const feedbackCategories = {
                    'content': ['content_feedback'],
                    'delivery': ['delivery_feedback'],
                    'structure': ['structure_feedback'],
                    'clarity': ['clarity_feedback']
                };
                
                for (const [category, keys] of Object.entries(ratingCategories)) {
                    // Skip if we already processed this category above
                    if ((category === 'content' && data.content_rating) || 
                        (category === 'delivery' && data.delivery_rating)) {
                        continue;
                    }
                    
                    // Check if any of the keys exist in the rating data
                    const matchedKey = keys.find(key => key in data);
                    if (matchedKey) {
                        const categoryData = data[matchedKey];
                        let categoryScore, categoryFeedback;
                        
                        if (typeof categoryData === 'object') {
                            categoryScore = categoryData.score || 'N/A';
                            categoryFeedback = categoryData.feedback || 'No feedback provided.';
                        } else if (typeof categoryData === 'number' || !isNaN(parseFloat(categoryData))) {
                            // If it's a direct score value
                            categoryScore = categoryData;
                            
                            // Look for corresponding feedback
                            const feedbackKey = feedbackCategories[category].find(key => key in data);
                            categoryFeedback = feedbackKey && data[feedbackKey] ? data[feedbackKey] : 'No feedback provided.';
                        } else if (typeof categoryData === 'string') {
                            // If it's a string, assume it's feedback and score is missing
                            categoryScore = 'N/A';
                            categoryFeedback = categoryData;
                        }
                          // Convert category score for proper display and stars
                        let categoryScoreForDisplay = categoryScore;
                        let categoryScoreForStars = categoryScore;
                        
                        if (typeof categoryScore === 'number' || !isNaN(parseFloat(categoryScore))) {
                            const numericCategoryScore = parseFloat(categoryScore);
                            if (numericCategoryScore > 5) {
                                // Scale down from 0-10 to 0-5 for stars
                                categoryScoreForStars = (numericCategoryScore / 10 * 5);
                                // Keep original 0-10 scale for display
                                categoryScoreForDisplay = numericCategoryScore.toFixed(1);
                            } else {
                                categoryScoreForStars = numericCategoryScore;
                                categoryScoreForDisplay = numericCategoryScore.toFixed(1);
                            }
                        }
                        
                        const categoryStarCount = Math.round(parseFloat(categoryScoreForStars)) || 0;
                        const categoryStars = '★'.repeat(categoryStarCount) + '☆'.repeat(5 - categoryStarCount);
                        
                        html += `
                            <div class="rating-card">
                                <div class="rating-header">
                                    <h5 class="rating-title">${category.charAt(0).toUpperCase() + category.slice(1)} Quality</h5>
                                    <span class="rating-score">${categoryScoreForDisplay}/10</span>
                                </div>
                                <div class="rating-stars">${categoryStars}</div>
                                <div class="rating-comment">
                                    ${categoryFeedback}
                                </div>
                            </div>
                        `;
                    }
                }
                
                // Recommendations
                let recommendations = data.recommendations || data.recommendation || [];
                if (typeof recommendations === 'string') {
                    // If recommendations is a string, convert to array
                    recommendations = [recommendations];
                } else if (typeof recommendations === 'object' && !Array.isArray(recommendations)) {
                    // If recommendations is an object but not array, convert to array of values
                    recommendations = Object.values(recommendations);
                }
                
                if (recommendations && recommendations.length > 0) {
                    html += `<h5 class="mt-4">Recommendations</h5>`;
                    html += `<ul class="list-group mb-4">`;
                    
                    recommendations.forEach(rec => {
                        if (rec && typeof rec === 'string') {
                            html += `<li class="list-group-item"><i class="fas fa-lightbulb text-warning me-2"></i>${rec}</li>`;
                        }
                    });
                    
                    html += `</ul>`;
                }
            }
            
            // Final debug output and container update
            console.log('Generated rating HTML:', html.substring(0, 200) + '...');
            
            // Set the HTML content
            container.innerHTML = html;
            
            // Force a reflow/repaint - sometimes needed to ensure content is visible
            container.style.display = 'none';
            setTimeout(() => { 
                container.style.display = ''; 
                console.log(`Rating display for ${isProfileRating ? 'profile' : 'intro'} complete. Container is now visible.`);
            }, 50);
            
        } catch (error) {
            console.error('Error displaying rating:', error);
            container.innerHTML = `<div class="alert alert-danger">Error displaying rating: ${error.message}</div>`;
        }
    }    // Upload the file and handle the full processing pipeline
    window.uploadAndProcess = async function() {
        try {
            // Check both fileInput and global state
            let fileToProcess = null;
            
            if (fileInput.files && fileInput.files[0]) {
                fileToProcess = fileInput.files[0];
            } else if (window.appState && window.appState.file) {
                fileToProcess = window.appState.file;
            }
            
            if (!fileToProcess) {
                showError('Please select a file or record an introduction first.');
                return;
            }
            
            // Ensure file is set in both states
            window.appState = window.appState || {};
            window.appState.file = fileToProcess;
            appState.file = fileToProcess;
            
            // Update UI for processing
            uploadSection.classList.add('d-none');
            processingSection.classList.remove('d-none');
            
            // Update progress steps
            stepUpload.classList.remove('active');
            stepUpload.classList.add('completed');
            stepTranscribe.classList.add('active');
            
            // Update transcription status
            updateStatusElement(
                transcriptionStatus, 
                'processing', 
                'Transcribing Audio', 
                'Converting your audio to text...', 
                25
            );
            
            // Create form data for upload
            const formData = new FormData();
            formData.append('file', fileToProcess);
            formData.append('extract_fields', extractFieldsCheckbox.checked);
            formData.append('generate_ratings', generateRatingsCheckbox.checked);            // Submit file to queue system
            const response = await fetch('/queue/submit', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to submit file to queue');
            }
            
            const data = await response.json();
            
            // Store the task ID for polling
            appState.taskId = data.task_id;
            
            // Show queue status
            updateStatusElement(
                transcriptionStatus, 
                'pending', 
                'In Queue', 
                `Your task is queued. Position: ${data.queue_position || 'Unknown'}`, 
                25
            );
              // Show queue monitor if it exists
            const queueMonitor = document.getElementById('queue-status-monitor');
            if (queueMonitor) {
                queueMonitor.style.display = 'block';
                
                // Start queue stats polling if available
                if (typeof startQueueStatsPolling === 'function') {
                    startQueueStatsPolling();
                    console.log('🚀 Queue stats polling started');
                }
            }
            
            // Show task status if it exists
            const taskStatus = document.getElementById('task-status');
            if (taskStatus) {
                taskStatus.style.display = 'block';
                const statusElement = document.getElementById('your-task-status');
                const positionElement = document.getElementById('your-queue-position');
                
                if (statusElement) statusElement.textContent = 'Queued';
                if (positionElement) positionElement.textContent = data.queue_position || 'N/A';
            }
            
            // Start polling for task status
            startTaskStatusPolling(data.task_id);
            
        } catch (error) {
            console.error('Upload and process error:', error);
            
            // Update UI to show error
            updateStatusElement(
                transcriptionStatus, 
                'error', 
                'Transcription Failed', 
                error.message || 'Failed to process your file', 
                100
            );
            
            processingMessage.classList.remove('d-none');
            processingMessage.classList.add('alert-danger');
            processingMessageText.textContent = 'An error occurred during processing. Please try again.';
            
            // Show error modal
            showError(error.message || 'Failed to process your file. Please try again.');
        }
    }
    
    // Stream field extraction
    async function streamFieldExtraction() {
        return new Promise((resolve, reject) => {
            try {
                updateStatusElement(
                    extractionStatus, 
                    'processing', 
                    'Extracting Information', 
                    'Analyzing transcript to extract information...', 
                    25
                );
                
                const eventSource = new EventSource(`/extract-fields-stream?transcript_path=${encodeURIComponent(appState.transcriptPath)}`);
                appState.eventSources.push(eventSource);
                
                eventSource.onmessage = function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        
                        // Handle different status messages
                        if (data.status === 'processing') {
                            // Update progress
                            updateStatusElement(
                                extractionStatus, 
                                'processing', 
                                'Extracting Information', 
                                data.message || 'Processing transcript...', 
                                50
                            );
                        } else if (data.status === 'completed' || data.status === 'done') {
                            // Extraction completed
                            updateStatusElement(
                                extractionStatus, 
                                'completed', 
                                'Information Extracted', 
                                'Successfully extracted information from transcript', 
                                100
                            );
                            
                            // Save and display the extracted fields
                            if (data.data) {
                                appState.extractedFields = data.data;
                                displayExtractedFields(data.data);
                            }
                            
                            // Close the event source
                            eventSource.close();                            // Move to ratings step if requested
                            if (generateRatingsCheckbox.checked) {
                                stepExtract.classList.remove('active');
                                stepExtract.classList.add('completed');
                                stepRate.classList.add('active');
                                
                                // Start rating generation using polling method
                                pollRatingStatus()
                                    .then(() => {
                                        showResults();
                                        resolve();
                                    })
                                    .catch(error => {
                                        reject(error);
                                    });
                            } else {
                                // Skip ratings
                                stepExtract.classList.remove('active');
                                stepExtract.classList.add('completed');
                                
                                updateStatusElement(
                                    ratingStatus, 
                                    'completed', 
                                    'Rating Generation Skipped', 
                                    'Rating generation was not requested', 
                                    100
                                );
                                
                                showResults();
                                resolve();
                            }
                        } else if (data.status === 'error') {
                            // Handle error
                            updateStatusElement(
                                extractionStatus, 
                                'error', 
                                'Extraction Failed', 
                                data.message || 'Failed to extract information', 
                                100
                            );
                            
                            eventSource.close();
                            reject(new Error(data.message || 'Field extraction failed'));
                        } else if (data.status === 'disabled') {
                            // LLM functionality disabled
                            updateStatusElement(
                                extractionStatus, 
                                'completed', 
                                'Information Extraction Disabled', 
                                'LLM functionality is currently disabled', 
                                100
                            );
                            
                            eventSource.close();
                            
                            // Skip to results
                            stepExtract.classList.remove('active');
                            stepExtract.classList.add('completed');
                            
                            updateStatusElement(
                                ratingStatus, 
                                'completed', 
                                'Rating Generation Disabled', 
                                'LLM functionality is currently disabled', 
                                100
                            );
                            
                            showResults();
                            resolve();
                        }
                    } catch (error) {
                        console.error('Error processing field extraction event:', error);
                    }
                };
                
                eventSource.onerror = function(error) {
                    console.error('Field extraction stream error:', error);
                    eventSource.close();
                    
                    updateStatusElement(
                        extractionStatus, 
                        'error', 
                        'Extraction Failed', 
                        'Stream connection error', 
                        100
                    );
                    
                    reject(new Error('Field extraction stream connection failed'));
                };
                
            } catch (error) {
                console.error('Field extraction setup error:', error);
                reject(error);
            }
        });    }    // Poll for rating status    // Legacy function - now handled by task status polling
    async function pollRatingStatus() {
        console.log("pollRatingStatus called - now handled by task status polling");
        // This function is deprecated in favor of the new queue-based task status polling
        // The new system handles all phases (STT, extraction, ratings) through a single polling mechanism
    }
    
    // Load existing ratings directly from server
    async function loadExistingRatings() {
        try {
            console.log("Checking for existing ratings...");
            
            // Get list of available ratings
            const response = await fetch('/ratings/check_status');
            if (!response.ok) {
                throw new Error('Failed to check rating status');
            }
            
            const data = await response.json();
            console.log('Available ratings:', data);
            
            let ratingsLoaded = false;
            
            // Verify rating content elements exist
            if (!profileRatingContent) {
                console.error('profileRatingContent element not found in DOM');
            }
            
            if (!introRatingContent) {
                console.error('introRatingContent element not found in DOM');
            }
            
            // Load profile rating if available
            if (data.profile_ready && data.profile_files && data.profile_files.length > 0) {
                try {
                    console.log(`Directly loading profile rating: ${data.profile_files[0]}`);
                    const profileResponse = await fetch(`/rating/${encodeURIComponent(data.profile_files[0])}`);
                    
                    if (profileResponse.ok) {
                        const profileData = await profileResponse.json();
                        console.log('Raw profile rating data:', profileData);
                          // Extract the actual rating data - try multiple paths
                        let ratingData = null;
                        console.log('🔍 Extracting rating data, profileData structure:', Object.keys(profileData));
                        
                        if (profileData.rating_data) {
                            console.log('📍 Using path 1: profileData.rating_data');
                            ratingData = profileData.rating_data;
                        } else if (profileData.success && profileData.data) {
                            console.log('📍 Using path 2: profileData.data (success=true)');
                            ratingData = profileData.data;
                        } else if (profileData.data && profileData.data.rating_data) {
                            console.log('📍 Using path 3: profileData.data.rating_data');
                            ratingData = profileData.data.rating_data;
                        } else {
                            console.log('📍 Using path 4: fallback to entire profileData');
                            // Try to use the entire response as rating data if it has expected properties
                            if (profileData.overall_score || profileData.overall_rating || 
                                profileData.skills || profileData.strengths) {
                                ratingData = profileData;
                            }
                        }
                        
                        console.log('🎯 Final ratingData to be displayed:', ratingData);
                        if (ratingData && ratingData.hiring_insights) {
                            console.log('✅ hiring_insights found in ratingData:', ratingData.hiring_insights);
                        } else {
                            console.log('❌ No hiring_insights in ratingData');
                        }
                        
                        // Store and display the rating
                        if (ratingData) {
                            appState.profileRating = ratingData;
                            console.log('Profile rating data to display:', ratingData);
                            
                            if (profileRatingContent) {
                                // Force the tab to update even if it's already been populated
                                profileRatingContent.innerHTML = '';
                                displayRating(ratingData, profileRatingContent);
                                console.log('Profile rating display complete');
                                ratingsLoaded = true;
                            } else {
                                console.error('Profile rating content element not found');
                            }
                        } else {
                            console.error('Could not extract profile rating data from response:', profileData);
                        }
                    } else {
                        console.error('Failed to load profile rating:', await profileResponse.text());
                    }
                } catch (err) {
                    console.error('Error loading profile rating:', err);
                }
            }
            
            // Load intro rating if available
            if (data.intro_ready && data.intro_files && data.intro_files.length > 0) {
                try {
                    console.log(`Directly loading intro rating: ${data.intro_files[0]}`);
                    const introResponse = await fetch(`/rating/${encodeURIComponent(data.intro_files[0])}`);
                    
                    if (introResponse.ok) {
                        const introData = await introResponse.json();
                        console.log('Raw intro rating data:', introData);
                        
                        // Extract the actual rating data - try multiple paths
                        let ratingData = null;
                        if (introData.rating_data) {
                            ratingData = introData.rating_data;
                        } else if (introData.success && introData.data) {
                            ratingData = introData.data;
                        } else if (introData.data && introData.data.rating_data) {
                            ratingData = introData.data.rating_data;
                        } else {
                            // Try to use the entire response as rating data if it has expected properties
                            if (introData.overall_score || introData.overall_rating || 
                                introData.content_rating || introData.delivery_rating) {
                                ratingData = introData;
                            }
                        }
                        
                        // Store and display the rating
                        if (ratingData) {
                            appState.introRating = ratingData;
                            console.log('Intro rating data to display:', ratingData);
                            
                            if (introRatingContent) {
                                // Force the tab to update even if it's already been populated
                                introRatingContent.innerHTML = '';
                                displayRating(ratingData, introRatingContent);
                                console.log('Intro rating display complete');
                                ratingsLoaded = true;
                            } else {
                                console.error('Intro rating content element not found');
                            }
                        } else {
                            console.error('Could not extract intro rating data from response:', introData);
                        }
                    } else {
                        console.error('Failed to load intro rating:', await introResponse.text());
                    }
                } catch (err) {
                    console.error('Error loading intro rating:', err);
                }
            }
            
            // Show results if ratings were loaded
            if (ratingsLoaded) {
                // Make sure processing section is hidden and results section is shown
                processingSection.classList.add('d-none');
                resultsSection.classList.remove('d-none');
                
                // Activate relevant tab with improved timing and error handling
                setTimeout(() => {
                    try {
                        // First ensure tabs are initialized by clicking the first tab
                        const firstTab = document.querySelector('#resultsTabs .nav-link');
                        if (firstTab) {
                            console.log('Activating first tab to initialize tabs');
                            firstTab.click();
                            
                            // Then activate the appropriate rating tab
                            setTimeout(() => {
                                try {
                                    if (appState.profileRating) {
                                        const profileTab = document.getElementById('profile-tab');
                                        if (profileTab) {
                                            console.log('Activating profile tab');
                                            profileTab.click();
                                        } else {
                                            console.error('Profile tab element not found');
                                        }
                                    } else if (appState.introRating) {
                                        const introTab = document.getElementById('intro-tab');
                                        if (introTab) {
                                            console.log('Activating intro tab');
                                            introTab.click();
                                        } else {
                                            console.error('Intro tab element not found');
                                        }
                                    }
                                } catch (e) {
                                    console.error('Error activating rating tab:', e);
                                }
                            }, 500); // Longer delay for rating tab activation
                        } else {
                            console.error('No tabs found in #resultsTabs');
                        }
                    } catch (e) {
                        console.error('Error initializing tabs:', e);
                    }
                }, 300);
                
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('Error loading existing ratings:', error);
            return false;
        }
    }
    
    // Modified showResults function to ensure tabs are working
    function showResults() {
        processingSection.classList.add('d-none');
        resultsSection.classList.remove('d-none');
        
        console.log("Showing results section. Available ratings:", {
            "profile": appState.profileRating ? "Available" : "Not available",
            "intro": appState.introRating ? "Available" : "Not available"
        });
        
        // Ensure tabs are properly initialized - fixes potential Bootstrap tab issues
        setTimeout(() => {
            try {
                const firstTab = document.querySelector('#resultsTabs .nav-link');
                if (firstTab) {
                    console.log('Activating first tab:', firstTab);
                    firstTab.click();
                    
                    // Verify content elements exist
                    console.log('Tab content elements:',
                        'profileRatingContent:', profileRatingContent ? 'exists' : 'missing',
                        'introRatingContent:', introRatingContent ? 'exists' : 'missing'
                    );
                    
                    // If ratings exist, activate their tab after a longer delay
                    setTimeout(() => {
                        try {
                            if (appState.profileRating) {
                                const profileTab = document.getElementById('profile-tab');
                                if (profileTab) {
                                    console.log('Activating profile tab');
                                    profileTab.click();
                                } else {
                                    console.error('Profile tab element not found');
                                }
                            } else if (appState.introRating) {
                                const introTab = document.getElementById('intro-tab');
                                if (introTab) {
                                    console.log('Activating intro tab');
                                    introTab.click();
                                } else {
                                    console.error('Intro tab element not found');
                                }
                            }
                        } catch (e) {
                            console.error('Error activating rating tab:', e);
                        }
                    }, 800); // Increased delay for better reliability
                } else {
                    console.error('No tabs found in #resultsTabs');
                }
            } catch (e) {
                console.error('Error initializing tabs:', e);
            }
        }, 300); // Increased initial delay
    }
    
    // Task status polling for queue-based processing
    let taskStatusInterval = null;
    
    function startTaskStatusPolling(taskId) {
        console.log(`Starting task status polling for task: ${taskId}`);
        
        if (taskStatusInterval) {
            clearInterval(taskStatusInterval);
        }
        
        taskStatusInterval = setInterval(async () => {
            try {
                const response = await fetch(`/queue/status/${taskId}`, {
                    credentials: 'include' // Include cookies for authentication
                });
                
                if (response.status === 401) {
                    // Authentication failed - redirect to login
                    console.error('Authentication expired during status polling');
                    clearInterval(taskStatusInterval);
                    taskStatusInterval = null;
                    showError('Your session has expired. Don\'t worry - your file is still processing in the background! Please log in again to check your results.');
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 2000);
                    return;
                }
                
                if (response.status === 403) {
                    // Access denied to this task
                    console.error('Access denied to task');
                    clearInterval(taskStatusInterval);
                    taskStatusInterval = null;
                    showError('Access denied to this task.');
                    return;
                }
                
                if (!response.ok) {
                    console.warn(`Status polling returned ${response.status}: ${response.statusText}`);
                    // Don't stop polling for temporary server errors, but log them
                    if (response.status >= 500) {
                        console.warn('Server error during status polling, will retry...');
                        return;
                    }
                    // For client errors other than auth, stop polling
                    if (response.status >= 400) {
                        clearInterval(taskStatusInterval);
                        taskStatusInterval = null;
                        showError(`Failed to get task status: ${response.statusText}`);
                        return;
                    }
                    return;
                }
                
                const status = await response.json();
                handleTaskStatusUpdate(status);
                
            } catch (error) {
                console.error('Status polling error:', error);
                // Check if it's a network error
                if (error.name === 'TypeError' && error.message.includes('fetch')) {
                    console.warn('Network error during status polling, will retry...');
                    return; // Continue polling for network errors
                }
                // For other errors, show user message but continue polling
                console.warn('Unexpected error during status polling, continuing...');
            }
        }, 2000); // Poll every 2 seconds
        
        // Stop polling after 80 minutes to match backend session timeout exactly
        setTimeout(() => {
            if (taskStatusInterval) {
                clearInterval(taskStatusInterval);
                taskStatusInterval = null;
                console.log('Task status polling stopped after timeout');
            }
        }, 4800000); // 80 minutes
    }
      function handleTaskStatusUpdate(status) {
        const taskStatus = status.status;
        const queuePosition = status.queue_position || status.users_ahead;
        
        console.log(`Task status update: ${taskStatus}, position: ${queuePosition}`);
        
        // Update queue position display
        const positionElement = document.getElementById('your-queue-position');
        if (positionElement) {
            positionElement.textContent = queuePosition || 'N/A';
        }
        
        const statusElement = document.getElementById('your-task-status');
        if (statusElement) {
            statusElement.textContent = taskStatus;
        }
        
        // Add safeguard for completed tasks
        if (taskStatus === 'complete') {
            console.log('👉 Task is complete, ensuring UI updates...');
            
            // Store the completed status in local storage as a backup
            try {
                localStorage.setItem('lastCompletedTask', JSON.stringify(status));
            } catch (e) {
                console.warn('Could not save completed task to localStorage:', e);
            }
        }
        
        switch (taskStatus) {
            case 'pending':
                updateStatusElement(
                    transcriptionStatus, 
                    'pending', 
                    'In Queue',
                    status.message || `Waiting in queue. Position: ${queuePosition || 'Unknown'}`, 
                    25
                );
                break;
                
            case 'processing':
                updateStatusElement(
                    transcriptionStatus, 
                    'processing', 
                    'Processing', 
                    status.message || 'Your file is being processed...', 
                    50
                );
                
                // Update step indicators
                stepTranscribe.classList.add('active');
                stepUpload.classList.remove('active');
                stepUpload.classList.add('completed');
                break;
                
            case 'stt_complete':
                updateStatusElement(
                    transcriptionStatus, 
                    'completed', 
                    'Transcription Complete', 
                    'Audio converted to text successfully', 
                    100
                );
                
                // Load transcript data
                loadTaskResults(status);
                
                // Move to extraction phase
                stepTranscribe.classList.remove('active');
                stepTranscribe.classList.add('completed');
                stepExtract.classList.add('active');
                
                updateStatusElement(
                    extractionStatus, 
                    'processing', 
                    'Extracting Information', 
                    'Analyzing transcript to extract information...', 
                    50
                );
                break;
                
            case 'form_complete':
                updateStatusElement(
                    extractionStatus, 
                    'completed', 
                    'Information Extracted', 
                    'Information extracted from transcript', 
                    100
                );
                  // Load form data
                loadTaskResults(status);
                
                // Move to rating phase if enabled
                if (generateRatingsCheckbox.checked) {
                    stepExtract.classList.remove('active');
                    stepExtract.classList.add('completed');
                    stepRate.classList.add('active');
                    
                    updateStatusElement(
                        ratingStatus, 
                        'processing', 
                        'Generating Ratings', 
                        'Evaluating your introduction...', 
                        50
                    );
                } else {
                    // Skip ratings and show results
                    stepExtract.classList.remove('active');
                    stepExtract.classList.add('completed');
                    showResults();
                    stopTaskPolling();
                }
                break;
                
            case 'complete':
                // Stop polling
                stopTaskPolling();
                
                // Mark all steps as complete
                updateStatusElement(
                    transcriptionStatus, 
                    'completed', 
                    'Transcription Complete', 
                    'Audio converted to text successfully', 
                    100
                );
                
                updateStatusElement(
                    extractionStatus, 
                    'completed', 
                    'Information Extracted', 
                    'Information extracted from transcript', 
                    100
                );
                
                updateStatusElement(
                    ratingStatus, 
                    'completed', 
                    'Ratings Complete', 
                    'Evaluation completed successfully', 
                    100
                );
                  // Update step indicators
                stepTranscribe.classList.remove('active');
                stepTranscribe.classList.add('completed');
                stepExtract.classList.remove('active');
                stepExtract.classList.add('completed');
                stepRate.classList.remove('active');
                stepRate.classList.add('completed');
                
                // Load all results using the existing ratings mechanism
                setTimeout(async () => {
                    try {
                        // First load basic task results (transcript, form)
                        await loadTaskResults(status);
                        
                        // Then load ratings using the proper mechanism
                        const ratingsLoaded = await loadExistingRatings();
                        
                        if (ratingsLoaded) {
                            console.log('Successfully loaded ratings from existing files');
                        } else {
                            console.log('No existing ratings found, that\'s okay');
                        }
                        
                        // Show results
                        showResults();
                    } catch (error) {
                        console.error('Error loading complete task results:', error);
                        // Still show results even if there's an error
                        showResults();
                    }
                }, 1000); // Give a moment for file operations to complete
                
                break;
                
            case 'failed':
                // Stop polling
                stopTaskPolling();
                
                updateStatusElement(
                    transcriptionStatus, 
                    'error', 
                    'Processing Failed', 
                    status.error_message || 'Processing failed', 
                    100
                );
                
                // Show error
                showError(status.error_message || 'Processing failed. Please try again.');
                break;
                
            default:
                console.log(`Unknown task status: ${taskStatus}`);
                break;
        }
    }
      function stopTaskPolling() {
        if (taskStatusInterval) {
            clearInterval(taskStatusInterval);
            taskStatusInterval = null;
            console.log('Task status polling stopped');
        }
        
        // Also stop queue stats polling if available
        if (typeof stopQueueStatsPolling === 'function') {
            stopQueueStatsPolling();
            console.log('Queue stats polling stopped');
        }
    }    
    // Add robust error handling in loadTaskResults to handle cases where data might be unavailable
    async function loadTaskResults(status) {
        try {
            console.log('Loading task results from status:', status);
            
            // Store the task ID in localStorage as a fallback reference
            if (status && status.task_id) {
                try {
                    localStorage.setItem('lastTaskId', status.task_id);
                } catch (e) {
                    console.warn('Could not save task ID to localStorage:', e);
                }
            }
            
            // If we have data directly from the task status, use it
            if (status.data) {
                console.log('Loading results from task data:', status.data);
                
                // Load transcript content
                if (status.data.transcript_content) {
                    appState.transcriptText = status.data.transcript_content;
                    transcriptContent.textContent = status.data.transcript_content;
                    console.log('Loaded transcript from task data');
                }
                
                // Load form data
                if (status.data.form_data) {
                    appState.extractedFields = status.data.form_data;
                    displayExtractedFields(status.data.form_data);
                    console.log('Loaded form data from task data');
                }
                
                // Load ratings
                if (status.data.profile_rating) {
                    appState.profileRating = status.data.profile_rating;
                    displayRating(status.data.profile_rating, profileRatingContent);
                    console.log('Loaded profile rating from task data');
                }
                
                if (status.data.intro_rating) {
                    appState.introRating = status.data.intro_rating;
                    displayRating(status.data.intro_rating, introRatingContent);
                    console.log('Loaded intro rating from task data');
                }
                
                // Check if we should automatically show results
                const isProcessingSectionActive = document.getElementById('processing-section').style.display === 'block';
                if (isProcessingSectionActive && status.status === 'complete') {
                    console.log('Task complete but still in processing view, showing results...');
                    setTimeout(showResults, 500);
                }
                
                return; // Exit early since we loaded everything from task data
            }
            
            // Fallback to file-based loading (legacy support)
            console.log('Falling back to file-based loading...');
            
            // Get current user's roll number for proper path construction
            let userRollNumber = null;
            try {
                const userResponse = await fetch('/api/auth/me', { credentials: 'include' });
                if (userResponse.status === 401) {
                    console.error('Authentication expired while loading results');
                    showError('Your session has expired. Don\'t worry - your file processing is complete! Please log in again to view your results.');
                    setTimeout(() => {
                        window.location.href = '/login';
                    }, 2000);
                    return;
                }
                if (userResponse.ok) {
                    const userInfo = await userResponse.json();
                    userRollNumber = userInfo.roll_number;
                    console.log('Current user roll number:', userRollNumber);
                } else {
                    console.warn('Could not get user info for result loading:', userResponse.status);
                    showError('Failed to load user information. Please refresh the page.');
                    return;
                }
            } catch (error) {
                console.error('Error getting user roll number:', error);
                if (error.name === 'TypeError' && error.message.includes('fetch')) {
                    showError('Network error. Please check your connection and try again.');
                } else {
                    showError('Failed to verify user session. Please refresh the page.');
                }
                return;
            }
            
            // Load transcript if available
            if (status.transcript_path) {
                try {
                    // Try to extract roll number and construct proper path
                    const pathParts = status.transcript_path.split(/[/\\]/);
                    const filename = pathParts[pathParts.length - 1];
                    
                    // Build possible paths including roll number subdirectory
                    const possiblePaths = [
                        `/transcription/${filename}`,
                        `/api/files/transcript/${filename}`,
                        status.transcript_path
                    ];
                    
                    // If we have a roll number, add paths with roll number subdirectories
                    if (userRollNumber) {
                        possiblePaths.unshift(
                            `/transcription/${userRollNumber}/${filename}`,
                            `/api/files/transcript/${userRollNumber}/${filename}`
                        );
                    }
                    
                    console.log('Trying transcript paths:', possiblePaths);
                    
                    for (const path of possiblePaths) {
                        try {
                            const transcriptResponse = await fetch(path);
                            if (transcriptResponse.ok) {
                                const transcript = await transcriptResponse.text();
                                appState.transcriptText = transcript;
                                transcriptContent.textContent = transcript;
                                console.log(`Loaded transcript successfully from: ${path}`);
                                break;
                            }
                        } catch (err) {
                            console.warn(`Failed to load transcript from ${path}:`, err);
                        }
                    }
                } catch (error) {
                    console.error('Error loading transcript:', error);
                }
            }
            
            // Load form data if available
            if (status.form_path) {
                try {
                    const pathParts = status.form_path.split(/[/\\]/);
                    const filename = pathParts[pathParts.length - 1];
                    
                    // Build possible paths including roll number subdirectory
                    const possiblePaths = [
                        `/filled_forms/${filename}`,
                        `/api/files/form/${filename}`,
                        status.form_path
                    ];
                    
                    // If we have a roll number, add paths with roll number subdirectories
                    if (userRollNumber) {
                        possiblePaths.unshift(
                            `/filled_forms/${userRollNumber}/${filename}`,
                            `/api/files/form/${userRollNumber}/${filename}`
                        );
                    }
                    
                    console.log('Trying form paths:', possiblePaths);
                    
                    for (const path of possiblePaths) {
                        try {
                            const formResponse = await fetch(path);
                            if (formResponse.ok) {
                                const formData = await formResponse.json();
                                appState.extractedFields = formData;
                                displayExtractedFields(formData);
                                console.log(`Loaded form data successfully from: ${path}`);
                                break;
                            }
                        } catch (err) {
                            console.warn(`Failed to load form data from ${path}:`, err);
                        }
                    }
                } catch (error) {
                    console.error('Error loading form data:', error);
                }
            }
            
            // Load ratings using the existing rating status endpoints
            if (status.profile_rating_path || status.intro_rating_path) {
                try {
                    const [profileResponse, introResponse] = await Promise.all([
                        fetch('/profile-rating-status', { credentials: 'include' }),
                        fetch('/intro-rating-status', { credentials: 'include' })
                    ]);
                    
                    // Check for authentication errors
                    if (profileResponse.status === 401 || introResponse.status === 401) {
                        console.error('Authentication expired while loading ratings');
                        showError('Your session has expired. Your ratings have been generated! Please log in again to view them.');
                        setTimeout(() => {
                            window.location.href = '/login';
                        }, 2000);
                        return;
                    }
                    
                    if (profileResponse.ok) {
                        const profileStatus = await profileResponse.json();
                        if (profileStatus.status === 'completed' && profileStatus.data) {
                            appState.profileRating = profileStatus.data;
                            displayRating(profileStatus.data, profileRatingContent);
                            console.log('Loaded profile rating successfully');
                        }
                    } else {
                        console.warn('Failed to load profile rating:', profileResponse.status);
                    }
                    
                    if (introResponse.ok) {
                        const introStatus = await introResponse.json();
                        if (introStatus.status === 'completed' && introStatus.data) {
                            appState.introRating = introStatus.data;
                            displayRating(introStatus.data, introRatingContent);
                            console.log('Loaded intro rating successfully');
                        }
                    } else {
                        console.warn('Failed to load intro rating:', introResponse.status);
                    }
                } catch (error) {
                    console.error('Error loading ratings:', error);
                    if (error.name === 'TypeError' && error.message.includes('fetch')) {
                        console.warn('Network error loading ratings, will continue without them');
                    } else {
                        console.warn('Unexpected error loading ratings:', error);
                    }
                }
            }
            
        } catch (error) {
            console.error('Error loading task results:', error);
        }
    }

    // Check for completed tasks function
    function checkForCompletedTasks() {
        console.log('Checking for completed tasks...');
        // This function is implemented in auto-recovery.js
        if (typeof window.checkForMissingResults === 'function') {
            window.checkForMissingResults();
        }
    }
    
    // Make this function available globally
    window.checkForCompletedTasks = checkForCompletedTasks;

    // Event listeners
    
    // File input change
    fileInput.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            handleFileSelect(this.files[0]);
        }
    });
    
    // Drop zone events
    ['dragover', 'dragenter'].forEach(eventName => {
        dropZone.addEventListener(eventName, function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.add('drop-zone--over');
        }, false);
    });
    
    ['dragleave', 'dragend', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, function(e) {
            e.preventDefault();
            e.stopPropagation();
            this.classList.remove('drop-zone--over');
        }, false);
    });
    
    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    }, false);
    
    dropZone.addEventListener('click', function() {
        fileInput.click();
    });    // Clear file button
    clearFileBtn.addEventListener('click', function() {
        fileInput.value = '';
        appState.file = null;
        fileInfo.classList.add('d-none');
    });

    // Start new button
    startNewButton.addEventListener('click', function() {
        resetApp();
    });

    // Form submit handler - prevent default and handle upload via JavaScript
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            e.preventDefault(); // Prevent default form submission
            uploadAndProcess(); // Call the upload function
        });
    }
    
    // Tips modal functionality
    if (tipsToggle) {
        tipsToggle.addEventListener('click', function() {
            tipsModal.style.display = 'block';
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
        });
    }
    
    if (tipsCloseBtn) {
        tipsCloseBtn.addEventListener('click', function() {
            tipsModal.style.display = 'none';
            document.body.style.overflow = 'auto'; // Restore scrolling
        });
    }
    
    // Close tips modal when clicking outside
    if (tipsModal) {
        tipsModal.addEventListener('click', function(e) {
            if (e.target === tipsModal) {
                tipsModal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });
    }
      // Close tips modal with Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && tipsModal && tipsModal.style.display === 'block') {
            tipsModal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
        if (e.key === 'Escape' && rubricsModal && rubricsModal.style.display === 'block') {
            rubricsModal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }
    });

    // Rubrics modal functionality
    if (rubricsToggle) {
        rubricsToggle.addEventListener('click', function() {
            rubricsModal.style.display = 'block';
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
        });
    }
    
    if (rubricsCloseBtn) {
        rubricsCloseBtn.addEventListener('click', function() {
            rubricsModal.style.display = 'none';
            document.body.style.overflow = 'auto'; // Restore scrolling
        });
    }
    
    // Close rubrics modal when clicking outside
    if (rubricsModal) {
        rubricsModal.addEventListener('click', function(e) {
            if (e.target === rubricsModal) {
                rubricsModal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });
    }

    // Rubrics tabs functionality
    rubricsTabs.forEach(tab => {
        tab.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            // Remove active class from all tabs and contents
            rubricsTabs.forEach(t => t.classList.remove('active'));
            rubricsTabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Show corresponding content
            const targetContent = document.getElementById(`${targetTab}-rubrics`);
            if (targetContent) {
                targetContent.classList.add('active');
            }
        });
    });
    
    // Theme Toggle Functionality
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const html = document.documentElement;

    if (themeToggle && themeIcon) {
        // Check for saved theme preference or default to dark
        const savedTheme = localStorage.getItem('theme') || 'dark';
        html.setAttribute('data-theme', savedTheme);
        updateThemeIcon(savedTheme);

        themeToggle.addEventListener('click', function () {
            const currentTheme = html.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

            html.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
        });

        function updateThemeIcon(theme) {
            if (theme === 'dark') {
                themeIcon.className = 'fas fa-sun'; // Show sun icon in dark mode
            } else {
                themeIcon.className = 'fas fa-moon'; // Show moon icon in light mode
            }
        }
    }

    // Voice Input Modal Functionality
    const voiceInputToggle = document.getElementById('voice-input-toggle');
    const voiceModal = document.getElementById('voice-input-modal');
    const voiceStartBtn = document.getElementById('voice-start-btn');
    const voiceStopBtn = document.getElementById('voice-stop-btn');
    const voiceCloseBtn = document.getElementById('voice-close-btn');
    const voiceStatusMessage = document.getElementById('voice-status-message');
    const voiceTranscript = document.getElementById('voice-transcript');
    const voicePulseRing = document.querySelector('.voice-pulse-ring');
    const voiceMicIcon = document.querySelector('.voice-microphone-icon');

    let isVoiceRecording = false;
    let speechRecognition = null;

    // Initialize speech recognition if available
    if (voiceInputToggle && voiceModal) {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            speechRecognition = new SpeechRecognition();
            speechRecognition.continuous = true;
            speechRecognition.interimResults = true;
            speechRecognition.lang = 'en-US';

            speechRecognition.onstart = function () {
                if (voiceStatusMessage) voiceStatusMessage.textContent = "Listening... Speak now!";
                if (voiceTranscript) voiceTranscript.classList.remove('empty');
                if (voicePulseRing) voicePulseRing.classList.add('listening');
                if (voiceMicIcon) voiceMicIcon.classList.add('listening');
            };

            speechRecognition.onresult = function (event) {
                let finalTranscript = '';
                let interimTranscript = '';

                for (let i = event.resultIndex; i < event.results.length; i++) {
                    const transcript = event.results[i][0].transcript;
                    if (event.results[i].isFinal) {
                        finalTranscript += transcript + ' ';
                    } else {
                        interimTranscript += transcript;
                    }
                }

                if (voiceTranscript) {
                    voiceTranscript.innerHTML = finalTranscript + '<span style="color: #888;">' + interimTranscript + '</span>';
                }
            };

            speechRecognition.onerror = function (event) {
                if (voiceStatusMessage) voiceStatusMessage.textContent = "Error occurred in recognition: " + event.error;
                stopVoiceRecording();
            };

            speechRecognition.onend = function () {
                if (isVoiceRecording && voiceStatusMessage) {
                    voiceStatusMessage.textContent = "Recording stopped. Click Start to record again.";
                }
                stopVoiceRecording();
            };
        }

        // Open voice modal
        voiceInputToggle.addEventListener('click', function () {
            voiceModal.classList.add('active');
            if (voiceStatusMessage) voiceStatusMessage.textContent = "Tell me who you are...";
            if (voiceTranscript) {
                voiceTranscript.textContent = "";
                voiceTranscript.classList.add('empty');
            }
            resetVoiceModalState();
        });

        // Close voice modal
        if (voiceCloseBtn) {
            voiceCloseBtn.addEventListener('click', function () {
                voiceModal.classList.remove('active');
                if (isVoiceRecording) {
                    stopVoiceRecording();
                }
            });
        }

        // Start recording
        if (voiceStartBtn) {
            voiceStartBtn.addEventListener('click', function () {
                if (speechRecognition) {
                    startVoiceRecording();
                } else if (voiceStatusMessage) {
                    voiceStatusMessage.textContent = "Speech recognition not supported in this browser.";
                }
            });
        }

        // Stop recording
        if (voiceStopBtn) {
            voiceStopBtn.addEventListener('click', function () {
                stopVoiceRecording();
            });
        }

        // Close modal when clicking outside
        voiceModal.addEventListener('click', function (e) {
            if (e.target === voiceModal) {
                voiceModal.classList.remove('active');
                if (isVoiceRecording) {
                    stopVoiceRecording();
                }
            }
        });

        function startVoiceRecording() {
            if (!isVoiceRecording && speechRecognition) {
                isVoiceRecording = true;
                voiceInputToggle.classList.add('recording');
                if (voiceStartBtn) voiceStartBtn.style.display = 'none';
                if (voiceStopBtn) voiceStopBtn.style.display = 'flex';
                if (voiceStatusMessage) voiceStatusMessage.textContent = "Starting recording...";

                try {
                    speechRecognition.start();
                } catch (error) {
                    console.error('Error starting recognition:', error);
                    if (voiceStatusMessage) voiceStatusMessage.textContent = "Error starting recording. Please try again.";
                    stopVoiceRecording();
                }
            }
        }

        function stopVoiceRecording() {
            if (isVoiceRecording && speechRecognition) {
                isVoiceRecording = false;
                speechRecognition.stop();
            }

            voiceInputToggle.classList.remove('recording');
            if (voiceStartBtn) voiceStartBtn.style.display = 'flex';
            if (voiceStopBtn) voiceStopBtn.style.display = 'none';
            if (voicePulseRing) voicePulseRing.classList.remove('listening');
            if (voiceMicIcon) voiceMicIcon.classList.remove('listening');

            if (voiceTranscript && voiceStatusMessage) {
                if (voiceTranscript.textContent.trim()) {
                    voiceStatusMessage.textContent = "Recording complete! You can start a new recording or close.";
                } else {
                    voiceStatusMessage.textContent = "No speech detected. Try again.";
                }
            }
        }

        function resetVoiceModalState() {
            isVoiceRecording = false;
            if (voiceStartBtn) voiceStartBtn.style.display = 'flex';
            if (voiceStopBtn) voiceStopBtn.style.display = 'none';
            if (voicePulseRing) voicePulseRing.classList.remove('listening');
            if (voiceMicIcon) voiceMicIcon.classList.remove('listening');
            voiceInputToggle.classList.remove('recording');
        }
    }

    // Record and Upload Modal Functionality
    const recordUploadButton = document.getElementById('record-upload-button');
    const recordModal = document.getElementById('record-upload-modal');
    const recordStartBtn = document.getElementById('record-start-btn');
    const recordStopBtn = document.getElementById('record-stop-btn');
    const recordUploadFileBtn = document.getElementById('record-upload-file-btn');
    const recordCloseBtn = document.getElementById('record-close-btn');
    const recordStatusMessage = document.getElementById('record-status-message');
    const recordTimer = document.getElementById('record-timer');
    const recordWaveform = document.getElementById('record-waveform');
    const recordPulseRing = document.querySelector('.record-pulse-ring');
    const recordPulseRingSecondary = document.querySelector('.record-pulse-ring-secondary');
    const recordMicIcon = document.querySelector('.record-microphone-icon');

    let isRecordingAudio = false;
    let mediaRecorder = null;
    let recordedChunks = [];
    let startTime = null;
    let timerInterval = null;
    let recordedBlob = null;

    if (recordUploadButton && recordModal) {
        // Check for MediaRecorder support
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            recordUploadButton.disabled = true;
            recordUploadButton.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i>Recording Not Supported';
        }

        // Open record modal
        recordUploadButton.addEventListener('click', function () {
            recordModal.classList.add('active');
            if (recordStatusMessage) recordStatusMessage.textContent = "Ready to record your introduction...";
            resetRecordingState();
        });

        // Close record modal
        if (recordCloseBtn) {
            recordCloseBtn.addEventListener('click', function () {
                recordModal.classList.remove('active');
                if (isRecordingAudio) {
                    stopAudioRecording();
                }
            });
        }

        // Close modal when clicking outside
        recordModal.addEventListener('click', function (e) {
            if (e.target === recordModal) {
                recordModal.classList.remove('active');
                if (isRecordingAudio) {
                    stopAudioRecording();
                }
            }
        });

        // Start recording
        if (recordStartBtn) {
            recordStartBtn.addEventListener('click', async function () {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({
                        audio: {
                            echoCancellation: true,
                            noiseSuppression: true,
                            sampleRate: 44100
                        }
                    });

                    recordedChunks = [];
                    mediaRecorder = new MediaRecorder(stream, {
                        mimeType: 'audio/webm;codecs=opus'
                    });

                    mediaRecorder.ondataavailable = function (event) {
                        if (event.data.size > 0) {
                            recordedChunks.push(event.data);
                        }
                    };

                    mediaRecorder.onstop = function () {
                        recordedBlob = new Blob(recordedChunks, { type: 'audio/webm' });
                        stream.getTracks().forEach(track => track.stop());

                        if (recordStatusMessage) recordStatusMessage.textContent = "Recording completed! Click upload to process.";
                        if (recordUploadFileBtn) recordUploadFileBtn.style.display = 'flex';
                    };

                    mediaRecorder.start();
                    startRecordingUI();

                } catch (error) {
                    console.error('Error accessing microphone:', error);
                    if (recordStatusMessage) recordStatusMessage.textContent = "Error accessing microphone. Please check permissions.";
                }
            });
        }

        // Stop recording
        if ( recordStopBtn) {
            recordStopBtn.addEventListener('click', function () {
                stopAudioRecording();
            });
        }

        // Upload recorded file
        if (recordUploadFileBtn) {
            recordUploadFileBtn.addEventListener('click', async function () {
                if (recordedBlob) {
                    try {
                        // Convert blob to file
                        const recordedFile = new File([recordedBlob], `recording_${Date.now()}.webm`, {
                            type: 'audio/webm'
                        });

                        console.log('Created recorded file:', recordedFile);

                        // Use the global file handler
                        const fileHandled = window.handleFileSelect(recordedFile);
                        if (!fileHandled) {
                            throw new Error('Failed to process the recorded file.');
                        }

                        // Close the modal
                        recordModal.classList.remove('active');

                        // Submit the form to trigger normal file upload processing
                        const uploadForm = document.getElementById('upload-form');
                        if (uploadForm && !window.isSubmitting) {
                            console.log('Submitting form with recorded file');
                            window.isSubmitting = true;
                            uploadForm.dispatchEvent(new Event('submit', {
                                bubbles: true,
                                cancelable: true
                            }));
                        } else if (window.isSubmitting) {
                            console.log('Preventing duplicate submission from recording');
                        } else {
                            throw new Error('Upload form not found');
                        }
                    } catch (error) {
                        console.error('Error processing recording:', error);
                        if (recordStatusMessage) recordStatusMessage.textContent = error.message || "Error processing recording. Please try again.";
                    }
                }
            });
        }

        function startRecordingUI() {
            isRecordingAudio = true;
            startTime = Date.now();

            // Update UI
            if (recordStartBtn) recordStartBtn.style.display = 'none';
            if (recordStopBtn) recordStopBtn.style.display = 'flex';
            if (recordUploadFileBtn) recordUploadFileBtn.style.display = 'none';

            // Add recording classes
            if (recordPulseRing) recordPulseRing.classList.add('recording');
            if (recordPulseRingSecondary) recordPulseRingSecondary.classList.add('recording');
            if (recordMicIcon) recordMicIcon.classList.add('recording');
            if (recordTimer) recordTimer.classList.add('recording');
            if (recordWaveform) recordWaveform.classList.add('active');

            // Start timer
            timerInterval = setInterval(updateTimer, 100);

            if (recordStatusMessage) recordStatusMessage.textContent = "Recording in progress... Speak clearly!";
        }

        function stopAudioRecording() {
            if (isRecordingAudio && mediaRecorder) {
                isRecordingAudio = false;
                mediaRecorder.stop();
            }

            // Update UI
            if (recordStartBtn) recordStartBtn.style.display = 'flex';
            if (recordStopBtn) recordStopBtn.style.display = 'none';

            // Remove recording classes
            if (recordPulseRing) recordPulseRing.classList.remove('recording');
            if (recordPulseRingSecondary) recordPulseRingSecondary.classList.remove('recording');
            if (recordMicIcon) recordMicIcon.classList.remove('recording');
            if (recordTimer) recordTimer.classList.remove('recording');
            if (recordWaveform) recordWaveform.classList.remove('active');

            // Stop timer
            if (timerInterval) {
                clearInterval(timerInterval);
                timerInterval = null;
            }
        }

        function updateTimer() {
            if (startTime && recordTimer) {
                const elapsed = Date.now() - startTime;
                const minutes = Math.floor(elapsed / 60000);
                const seconds = Math.floor((elapsed % 60000) / 1000);
                recordTimer.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }

        function resetRecordingState() {
            isRecordingAudio = false;
            recordedChunks = [];
            recordedBlob = null;
            startTime = null;

            if (timerInterval) {
                clearInterval(timerInterval);
                timerInterval = null;
            }

            // Reset UI
            if (recordStartBtn) recordStartBtn.style.display = 'flex';
            if (recordStopBtn) recordStopBtn.style.display = 'none';
            if (recordUploadFileBtn) recordUploadFileBtn.style.display = 'none';

            if (recordPulseRing) recordPulseRing.classList.remove('recording');
            if (recordPulseRingSecondary) recordPulseRingSecondary.classList.remove('recording');
            if (recordMicIcon) recordMicIcon.classList.remove('recording');
            if (recordTimer) {
                recordTimer.classList.remove('recording');
                recordTimer.textContent = '00:00';
            }
            if (recordWaveform) recordWaveform.classList.remove('active');
        }
    }

    // Health check on load
    fetch('/health')
        .then(response => response.json())
        .then(data => {
            console.log('Server health check:', data);
            if (data.llm_disabled) {
                processingMessage.classList.remove('d-none');
                processingMessage.classList.add('alert-warning');
                processingMessageText.textContent = 'Note: LLM functionality is currently disabled. Field extraction and rating generation will not work.';
            }
        })
        .catch(error => {
            console.error('Health check error:', error);
        });
    
    // Initialize queue enhancer if available
    if (typeof enhanceQueuePolling === 'function') {
        enhanceQueuePolling();
        console.log('Queue enhancer initialized');
    }
    
    // Initialize result display fix if available
    if (typeof fixResultDisplay === 'function') {
        fixResultDisplay();
        console.log('Result display fix initialized');
    }
});
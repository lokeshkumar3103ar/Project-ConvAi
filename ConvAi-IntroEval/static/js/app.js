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
        
        // Reset file input and state
        fileInput.value = '';
        appState.file = null;
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
            }
              // Add grading explanation categories if available
            if (data.grading_explanation && typeof data.grading_explanation === 'object') {
                html += `<h5 class="mt-4">Category Ratings</h5>`;
                
                for (const [category, score] of Object.entries(data.grading_explanation)) {
                    // Format the category name for display
                    const categoryDisplay = category
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
            }
            
            // Add insights section for intro ratings
            if (!isProfileRating && data.insights && Array.isArray(data.insights) && data.insights.length > 0) {
                html += `<h5 class="mt-4">Key Insights</h5>`;
                html += `<ul class="list-group mb-4">`;
                
                data.insights.forEach(insight => {
                    html += `<li class="list-group-item"><i class="fas fa-lightbulb text-warning me-2"></i>${insight}</li>`;
                });
                
                html += `</ul>`;
            }
            
            // Add specific feedback section for intro ratings
            if (!isProfileRating && data.feedback && Array.isArray(data.feedback) && data.feedback.length > 0) {
                html += `<h5 class="mt-4">Detailed Feedback</h5>`;
                html += `<ul class="list-group mb-4">`;
                
                data.feedback.forEach(feedbackItem => {
                    html += `<li class="list-group-item"><i class="fas fa-comment-dots text-primary me-2"></i>${feedbackItem}</li>`;
                });
                
                html += `</ul>`;
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
                            deliveryScoreForDisplay = numericDeliveryScore.toFixed(1);
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
            formData.append('generate_ratings', generateRatingsCheckbox.checked);
            
            // Upload file and get transcription
            const response = await fetch('/transcribe', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to transcribe file');
            }
            
            const data = await response.json();
            
            // Update transcription status
            updateStatusElement(
                transcriptionStatus, 
                'completed', 
                'Transcription Completed', 
                'Successfully converted audio to text', 
                100
            );
            
            // Save transcript data
            appState.transcriptPath = data.transcription_file;
            appState.transcriptText = data.transcript;
            transcriptContent.textContent = data.transcript || 'No transcript available.';
            
            // Check if fields were extracted directly in the transcribe endpoint
            if (data.extracted_fields && data.extracted_fields.status === 'saved' && data.extracted_fields.data) {
                // Handle directly returned field data
                appState.extractedFields = data.extracted_fields.data;
                stepTranscribe.classList.remove('active');
                stepTranscribe.classList.add('completed');
                stepExtract.classList.add('completed');
                
                updateStatusElement(
                    extractionStatus, 
                    'completed', 
                    'Information Extraction Complete', 
                    'Successfully extracted information from transcript', 
                    100
                );
                
                displayExtractedFields(appState.extractedFields);
                
                if (data.ratings && data.ratings.status === 'saved' && data.ratings.data) {
                    // Handle directly returned ratings
                    appState.profileRating = data.ratings.data.profile_rating;
                    appState.introRating = data.ratings.data.intro_rating;
                    
                    stepRate.classList.add('completed');
                    
                    updateStatusElement(
                        ratingStatus, 
                        'completed', 
                        'Rating Generation Complete', 
                        'Generated profile and introduction ratings', 
                        100
                    );
                      displayRating(appState.profileRating, profileRatingContent);
                    displayRating(appState.introRating, introRatingContent);
                    
                    // Show results
                    showResults();                } else if (generateRatingsCheckbox.checked) {
                    // Start rating generation using polling method
                    await pollRatingStatus();
                    // Show results
                    showResults();
                } else {
                    // Show results without ratings
                    showResults();
                }
            } else if (extractFieldsCheckbox.checked) {
                // Start field extraction streaming
                await streamFieldExtraction();
            } else {
                // Skip field extraction
                stepTranscribe.classList.remove('active');
                stepTranscribe.classList.add('completed');
                
                updateStatusElement(
                    extractionStatus, 
                    'completed', 
                    'Information Extraction Skipped', 
                    'Field extraction was not requested', 
                    100
                );
                
                // Show results section
                showResults();
            }
            
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
        });    }    // Poll for rating status
    async function pollRatingStatus() {
        try {
            console.log("Starting rating status polling...");
            
            // Check if ratings already exist - direct approach
            await loadExistingRatings();
            
            // Start polling for new ratings
            const pollInterval = setInterval(async () => {
                try {
                    const response = await fetch('/ratings/check_status');
                    if (!response.ok) {
                        throw new Error('Failed to check rating status');
                    }
                    
                    const data = await response.json();
                    console.log('Rating status poll response:', data);
                    
                    if (data.profile_ready || data.intro_ready) {
                        // Load the ratings
                        await loadExistingRatings();
                        
                        // Update rating status
                        updateStatusElement(
                            ratingStatus, 
                            'completed', 
                            'Ratings Complete', 
                            'Successfully evaluated your introduction', 
                            100
                        );
                        
                        // Update step status
                        stepRate.classList.add('completed');
                        
                        // Show results if not already visible
                        if (processingSection.classList.contains('d-none') === false) {
                            showResults();
                        }
                        
                        // Clear the polling interval
                        clearInterval(pollInterval);
                    }
                } catch (error) {
                    console.error('Rating poll error:', error);
                }
            }, 3000); // Poll every 3 seconds
            
            // Stop polling after 2 minutes
            setTimeout(() => {
                clearInterval(pollInterval);
                
                // If ratings not loaded, update status
                if (!appState.profileRating && !appState.introRating) {
                    updateStatusElement(
                        ratingStatus, 
                        'error', 
                        'Rating Timeout', 
                        'Rating generation took too long', 
                        100
                    );
                }
                
                // Show results anyway
                showResults();
            }, 120000);
            
        } catch (error) {
            console.error('Rating poll setup error:', error);
        }
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
                        if (profileData.rating_data) {
                            ratingData = profileData.rating_data;
                        } else if (profileData.success && profileData.data) {
                            ratingData = profileData.data;
                        } else if (profileData.data && profileData.data.rating_data) {
                            ratingData = profileData.data.rating_data;
                        } else {
                            // Try to use the entire response as rating data if it has expected properties
                            if (profileData.overall_score || profileData.overall_rating || 
                                profileData.skills || profileData.strengths) {
                                ratingData = profileData;
                            }
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
    });
    
    // Clear file button
    clearFileBtn.addEventListener('click', function() {
        fileInput.value = '';
        appState.file = null;
        fileInfo.classList.add('d-none');
    });    // Form submission
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        uploadAndProcess();
    });
      // Start new button
    startNewButton.addEventListener('click', function() {
        resetApp();
    });
    
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
});

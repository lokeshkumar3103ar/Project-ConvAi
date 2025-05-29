/**
 * Updated utilities for handling rating operations with the actual JSON data structure
 */

// Normalize profile rating data from API response
function normalizeProfileRatingData(apiResponse) {
    console.log("Normalizing profile API response:", apiResponse);
    
    // If the API response is a string (happens sometimes with certain backends)
    if (typeof apiResponse === 'string') {
        try {
            apiResponse = JSON.parse(apiResponse);
        } catch (e) {
            console.error("Failed to parse profile rating JSON:", e);
            return null;
        }
    }
    
    // Ensure the response has the expected structure
    if (!apiResponse) return null;
    
    // Create a standardized structure
    return {
        profile_rating: apiResponse.profile_rating || apiResponse.overall_rating || apiResponse.rating || "0.0/10",
        feedback: apiResponse.feedback || apiResponse.notes || "",
        grading_explanation: apiResponse.grading_explanation || apiResponse.categories || {},
        notes: apiResponse.notes || ""
    };
}

// Format profile rating data for display
function formatProfileRatingData(result) {
    if (!result) {
        console.error("Invalid profile rating data (null or undefined):", result);
        return null;
    }
    console.log("Profile Rating Data:", JSON.stringify(result, null, 2));
    
    // Handle rating format that might be like "2.61/10"
    let profileRating = result.profile_rating;
    if (typeof profileRating === 'string' && profileRating.includes('/')) {
        profileRating = profileRating.split('/')[0].trim();
        console.log(`Handling profile rating in format with slash: ${result.profile_rating} -> ${profileRating}`);
    }
    
    // Ensure we have a valid number for the overall score
    const overallScore = parseFloat(profileRating) || 0;
    console.log(`Profile rating: ${overallScore}/10`);
    
    const categoriesData = result.grading_explanation || {};
    
    // Get feedback directly from the right property
    let feedbackText = "";
    
    // Try to get feedback from the most reliable sources first
    if (result.feedback) {
        if (Array.isArray(result.feedback)) {
            feedbackText = result.feedback.join('\n');
        } else {
            feedbackText = result.feedback;
        }
    } else if (result.notes) {
        feedbackText = result.notes;
    } else if (result.grading_debug && result.grading_debug.notes) {
        feedbackText = result.grading_debug.notes.replace(/^\[|\]$/g, '').trim();
    }
    
    // If we still don't have feedback, generate something meaningful
    if (!feedbackText || feedbackText.includes("Rating details not available")) {
        const categories = Object.keys(categoriesData);
        if (categories.length > 0) {
            feedbackText = `The candidate's profile shows ${overallScore > 5 ? 'strengths' : 'areas for improvement'} in ${categories.length} key areas: ${categories.join(', ').replace(/_/g, ' ')}. ${
                overallScore > 7 ? 'Overall, this is a strong profile that matches well with the requirements.' : 
                overallScore > 4 ? 'The profile shows potential but could benefit from additional details in key areas.' :
                'The profile needs significant improvement to better match job requirements.'
            }`;
        } else {
            feedbackText = `Profile evaluation completed with an overall score of ${overallScore}/10. ${
                overallScore > 7 ? 'This indicates a strong match with the target role requirements.' : 
                overallScore > 4 ? 'This indicates moderate alignment with the target role requirements.' :
                'This indicates a need for significant improvements to better align with the target role requirements.'
            }`;
        }
    }
    
    return {
        overallScore: overallScore,
        categories: categoriesData,
        feedback: feedbackText
    };
}

// Format intro rating data for display
function formatIntroRatingData(result) {
    if (!result) {
        console.error("Invalid intro rating data (null or undefined):", result);
        return null;
    }
      console.log("Intro Rating Data:", JSON.stringify(result, null, 2));    // Handle rating format that might be like "2.61/10"
    let introRating = result.intro_rating;
    if (typeof introRating === 'string' && introRating.includes('/')) {
        introRating = introRating.split('/')[0].trim();
        console.log(`Handling intro rating in format with slash: ${result.intro_rating} -> ${introRating}`);
    }
    
    // Keep original 0-10 scale for display
    const overallScore = parseFloat(introRating) || 0;
    console.log(`Intro rating: ${overallScore}/10`);
    
    const categoriesData = result.grading_explanation || {};
    
    // Format the insights section if available
    let insightsText = "";
    if (result.insights && Array.isArray(result.insights) && result.insights.length > 0) {
        insightsText = "Key Insights:\n• " + result.insights.join('\n• ') + "\n\n";
    }
    
    // Format the feedback - if it's an array, join it; if it's a string, use it directly
    let feedbackText = "";
    if (result.feedback) {
        if (Array.isArray(result.feedback)) {
            feedbackText = "Feedback:\n• " + result.feedback.join('\n• ');
        } else {
            feedbackText = "Feedback:\n" + result.feedback;
        }
    }
    
    // Get notes from either the grading_debug or directly from the result
    let notes = "";
    if (result.grading_debug && result.grading_debug.notes) {
        notes = "\n\nNotes: " + result.grading_debug.notes;
    } else if (result.notes) {
        notes = "\n\nNotes: " + result.notes;
    }
    
    // Combine all feedback sections
    const combinedFeedback = insightsText + feedbackText + notes;
    
    return {
        overallScore: overallScore,
        categories: categoriesData,
        feedback: combinedFeedback || "No detailed feedback available."
    };
}

// Create HTML for rating display
function createRatingHTML(formattedData, type) {
    if (!formattedData) {
        return '<div class="alert alert-warning">Unable to format rating data</div>';
    }
    
    let title = type === 'profile' ? 'Profile Evaluation' : 'Introduction Evaluation';
    
    // Calculate overall score for stars (convert 0-10 to 0-5 for display)
    const overallScore = formattedData.overallScore;
    const scoreForStars = overallScore > 5 ? (overallScore / 10 * 5) : overallScore;
    const fullStars = Math.floor(scoreForStars);
    const hasHalfStar = (scoreForStars % 1) >= 0.5;
    const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
    
    // Create star HTML
    let starHTML = '';
    for (let i = 0; i < fullStars; i++) {
        starHTML += '★';
    }
    if (hasHalfStar) {
        starHTML += '☆';
    }
    for (let i = 0; i < emptyStars; i++) {
        starHTML += '☆';
    }
    
    let html = `
        <div class="card mb-4">
            <div class="card-header bg-primary text-white">
                <h4>${title}</h4>
            </div>
            <div class="card-body">
                <!-- Overall Rating Display -->
                <div class="text-center mb-4 p-3 bg-light rounded">
                    <h3>Overall Rating</h3>
                    <div class="rating-display mb-2">
                        <span class="rating-score">${overallScore.toFixed(1)}/10</span>
                    </div>
                    <div class="rating-stars mb-2" style="font-size: 2em; color: #ffc107;">
                        ${starHTML}
                    </div>
                    <p class="mb-0 text-muted">${formattedData.feedback.split('\n')[0] || 'Rating assessment complete'}</p>
                </div>
                
                <div class="mb-4">
                    <h5>Category Ratings</h5>
    `;
    
    // Categories section with individual star ratings
    for (const [category, scoreText] of Object.entries(formattedData.categories)) {
        // Capitalize the category name for display
        const categoryDisplay = category
            .replace(/_/g, ' ')
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
        
        // Extract numeric score from scoreText for star calculation
        let categoryScore = 0;
        const scoreMatch = scoreText.match(/(\d+\.?\d*)/);
        if (scoreMatch) {
            categoryScore = parseFloat(scoreMatch[1]);
        }
        
        // Calculate stars for category (assume category scores are on similar scale)
        const categoryStars = categoryScore > 5 ? (categoryScore / 10 * 5) : categoryScore;
        const catFullStars = Math.floor(categoryStars);
        const catHalfStar = (categoryStars % 1) >= 0.5;
        const catEmptyStars = 5 - catFullStars - (catHalfStar ? 1 : 0);
        
        let categoryStarHTML = '';
        for (let i = 0; i < catFullStars; i++) {
            categoryStarHTML += '★';
        }
        if (catHalfStar) {
            categoryStarHTML += '☆';
        }
        for (let i = 0; i < catEmptyStars; i++) {
            categoryStarHTML += '☆';
        }
        
        html += `
            <div class="mb-3 p-2 border rounded">
                <div class="d-flex justify-content-between align-items-center">
                    <strong>${categoryDisplay}:</strong>
                    <div class="text-end">
                        <div class="rating-stars" style="color: #ffc107; font-size: 1.2em;">
                            ${categoryStarHTML}
                        </div>
                        <small class="text-muted">${scoreText}</small>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add feedback section
    html += `
                </div>
                <div class="mb-3">
                    <h5>Detailed Feedback:</h5>
                    <div class="p-3 bg-light rounded">
                        ${formattedData.feedback.replace(/\n/g, '<br>')}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    return html;
}

// Display rating results
function displayRating(ratingData, type) {
    console.log(`[Rating Debug] Displaying ${type} rating:`, ratingData);
    
    const resultElement = document.getElementById(`${type}-rating-result`);
    if (!resultElement) {
        console.error(`Element with id "${type}-rating-result" not found`);
        return;
    }
    
    // Format the data based on the rating type
    let formattedData;
    if (type === 'profile') {
        formattedData = formatProfileRatingData(ratingData);
        console.log('Formatted profile data:', formattedData);
    } else {
        formattedData = formatIntroRatingData(ratingData);
        console.log('Formatted intro data:', formattedData);
    }
    
    if (!formattedData) {
        resultElement.innerHTML = `<div class="alert alert-warning">Unable to format ${type} rating data</div>`;
        return;
    }
    
    // Add this debug line to verify formatted data structure
    console.log(`Final ${type} formatted data:`, JSON.stringify(formattedData));
    
    // Create and insert the HTML
    const html = createRatingHTML(formattedData, type);
    resultElement.innerHTML = html;
    console.log(`[Rating Debug] ${type} rating display complete`);
}

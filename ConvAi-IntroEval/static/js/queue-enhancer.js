/**
 * Queue Status and Results Enhancement Module
 * This module fixes the frontend polling issues when multiple users submit files simultaneously
 */

// Immediately invoked function to avoid polluting global scope
(function() {
    // Store task status by ID
    const taskStatusCache = {};
    
    // Add a helper to check if a task has completed but the UI hasn't updated
    window.fixResultDisplay = function() {
        console.log('🔧 Installing result display fix for multi-user support');
        
        // Poll for my-results endpoint to force UI update for completed tasks
        setInterval(async function() {
            try {
                // Only check if we're not already showing results
                if (document.getElementById('upload-section').style.display !== 'none') {
                    // Get user's results from the backend
                    const response = await fetch('/queue/my-results');
                    if (!response.ok) return;
                    
                    const data = await response.json();
                    console.log('📊 Checking my results:', data);
                    
                    // Check if there's a completed task but UI hasn't updated
                    if (data.has_results && data.latest_completed) {
                        const completedTask = data.latest_completed;
                        
                        // More aggressive detection - check if we have a task ID and any of these conditions:
                        // 1. We're still in processing section for a completed task
                        // 2. Upload section is still visible even though we have results
                        // 3. Results haven't been loaded yet (missing from DOM)
                        const isProcessingSectionActive = document.getElementById('processing-section').style.display === 'block';
                        const isUploadSectionActive = document.getElementById('upload-section').style.display === 'block';
                        const resultsNotLoaded = !document.getElementById('transcript-content').textContent || 
                                               document.getElementById('transcript-content').textContent.trim() === '';
                        
                        if (window.appState.taskId && 
                            completedTask.status === 'complete' && 
                            (isProcessingSectionActive || (isUploadSectionActive && data.has_results) || resultsNotLoaded)) {
                            
                            console.log('🔄 Found completed task but UI not updated, forcing update');
                            console.log('   - Processing section visible:', isProcessingSectionActive);
                            console.log('   - Upload section still active:', isUploadSectionActive);
                            console.log('   - Results not loaded:', resultsNotLoaded);
                            console.log('   - Task data available:', !!completedTask.data);
                            
                            // Force UI update by simulating a completion status
                            const simulatedStatus = {
                                status: 'complete',
                                task_id: completedTask.task_id,
                                transcript_path: completedTask.transcript_path,
                                form_path: completedTask.form_path,
                                profile_rating_path: completedTask.profile_rating_path,
                                intro_rating_path: completedTask.intro_rating_path,
                                data: completedTask.data,
                                message: "Processing complete! Your results are ready to view.",
                                progress_percent: 100
                            };
                            
                            // Call the task status handler with our completed status
                            if (typeof handleTaskStatusUpdate === 'function') {
                                console.log('🔧 Applying fix: Forcing UI update with completed status');
                                handleTaskStatusUpdate(simulatedStatus);
                                
                                // Try to load results directly for all users
                                if (typeof loadTaskResults === 'function') {
                                    setTimeout(() => {
                                        console.log('🔧 Forcing results load for completed task');
                                        loadTaskResults(simulatedStatus);
                                        
                                        // Also try to show results directly
                                        if (typeof showResults === 'function') {
                                            setTimeout(showResults, 1000);
                                        }
                                    }, 500);
                                }
                            }
                        }
                    }
                }
            } catch (error) {
                console.warn('Result display fix check error:', error);
            }
        }, 5000); // Check every 5 seconds for all users
    };
    
    // Enhanced queue polling with automatic retry and better task completion detection
    window.enhanceQueuePolling = function() {
        console.log('🔧 Installing enhanced queue polling for better multi-user support');
        
        // Enhance the existing polling mechanism by adding a backup check
        const originalStartTaskStatusPolling = window.startTaskStatusPolling;
        
        // Replace the original function with our enhanced version
        window.startTaskStatusPolling = function(taskId) {
            console.log(`Starting enhanced task status polling for task: ${taskId}`);
            
            // Call the original function to maintain existing behavior
            if (originalStartTaskStatusPolling) {
                originalStartTaskStatusPolling(taskId);
            }
            
            // Add our own backup polling that continues checking even when backend says "complete"
            // This helps in cases where the browser didn't receive or process the "complete" status
            const backupInterval = setInterval(async function() {
                try {
                    // Get current task status from server
                    const response = await fetch(`/queue/my-results`);
                    if (!response.ok) return;
                    
                    const data = await response.json();
                    
                    // Find our task in the results
                    const ourTask = data.all_tasks?.find(task => task.task_id === taskId);
                    
                    // Also check if this is the latest completed task (sometimes the exact task ID may not match)
                    const latestCompletedTask = data.latest_completed;
                    const relevantTask = ourTask || (latestCompletedTask && data.has_results ? latestCompletedTask : null);
                    
                    // If we have a completed task but UI hasn't updated, force the update
                    if (relevantTask && relevantTask.status === 'complete') {
                        console.log(`🔍 Backup polling: Found completed task, ensuring UI is updated`);
                        
                        // Construct a complete status object
                        const statusObj = {
                            status: 'complete',
                            task_id: relevantTask.task_id || taskId,
                            ...relevantTask,
                            message: "Processing complete! Your results are ready to view.",
                            progress_percent: 100
                        };
                        
                        // Force UI update by calling the handler
                        if (typeof handleTaskStatusUpdate === 'function') {
                            handleTaskStatusUpdate(statusObj);
                        }
                        
                        // If we have a latest completed task with data, use it
                        if (data.latest_completed && data.latest_completed.data) {
                            statusObj.data = data.latest_completed.data;
                            console.log('📋 Applying data from latest completed task');
                            
                            // Try to load results again
                            if (typeof loadTaskResults === 'function') {
                                loadTaskResults(statusObj);
                                
                                // Also try to show results directly after a delay
                                if (typeof showResults === 'function') {
                                    setTimeout(showResults, 1000);
                                }
                            }
                        }
                    } else if (data.has_results && data.latest_completed) {
                        // Even if our specific task isn't found, if there are results available
                        // and we're still in the processing view, force a display update
                        const isProcessingSectionActive = document.getElementById('processing-section').style.display === 'block';
                        const isUploadSectionActive = document.getElementById('upload-section').style.display === 'block';
                        
                        if ((isProcessingSectionActive || isUploadSectionActive) && data.latest_completed.status === 'complete') {
                            console.log('🔄 Detected available results but UI not updated, forcing display');
                            
                            // Create a synthetic status object from latest completed
                            const statusObj = {
                                status: 'complete',
                                task_id: data.latest_completed.task_id,
                                ...data.latest_completed,
                                message: "Processing complete! Your results are ready to view.",
                                progress_percent: 100
                            };
                            
                            if (typeof handleTaskStatusUpdate === 'function') {
                                handleTaskStatusUpdate(statusObj);
                            }
                            
                            if (typeof loadTaskResults === 'function') {
                                setTimeout(() => loadTaskResults(statusObj), 500);
                                
                                // Also try to show results directly
                                if (typeof showResults === 'function') {
                                    setTimeout(showResults, 1500);
                                }
                            }
                        }
                    }
                } catch (error) {
                    console.warn('Backup polling error:', error);
                }
            }, 5000); // Check every 5 seconds for all users
            
            // Stop backup polling after 15 minutes (increased from 10 minutes)
            setTimeout(() => {
                clearInterval(backupInterval);
                console.log('Backup polling stopped after timeout');
            }, 900000); // 15 minutes
        };
    };
})();

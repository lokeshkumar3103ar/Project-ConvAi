/**
 * Result Auto-Recovery Module for ConvAi-IntroEval
 * 
 * This module adds advanced recovery mechanisms to detect and restore
 * lost results when the UI fails to update properly for some users.
 */

// Immediately invoked function to avoid polluting global scope
(function() {
    // Track displayed task IDs to prevent multiple recoveries of the same task
    const displayedTasks = new Set();
      /**
     * Initialize the recovery system
     */
    window.initializeRecoverySystem = function() {
        console.log('🔄 Initializing result recovery system...');
        
        // Add event listener for page visibility changes
        document.addEventListener('visibilitychange', handleVisibilityChange);
        
        // Try recovery on initial load
        setTimeout(checkForMissingResults, 3000);
        
        // Set up periodic checks for missing results
        setInterval(checkForMissingResults, 30000); // Check every 30 seconds
    };
    
    // Export checkForMissingResults to global scope to be called from app.js
    window.checkForMissingResults = checkForMissingResults;
    
    /**
     * Handle page visibility changes (when user switches tabs/windows)
     * This is a good time to check for missing results
     */
    function handleVisibilityChange() {
        if (document.visibilityState === 'visible') {
            console.log('📋 Page became visible, checking for missing results...');
            checkForMissingResults();
        }
    }
      /**
     * Check for completed tasks that haven't been displayed and recover them
     */
    async function checkForMissingResults() {
        try {
            // Only check if we're not already showing results
            const uploadSection = document.getElementById('upload-section');
            const processingSection = document.getElementById('processing-section');
            
            if ((uploadSection && uploadSection.style.display !== 'none') ||
                (processingSection && processingSection.style.display !== 'none')) {
                
                console.log('🔍 Checking for missing results...');
                
                // Try to load from localStorage first (fastest recovery)
                const storedTask = localStorage.getItem('lastCompletedTask');
                if (storedTask) {
                    try {
                        const taskData = JSON.parse(storedTask);
                        if (taskData && taskData.status === 'complete' && !displayedTasks.has(taskData.task_id)) {
                            console.log('🔄 Found completed task in localStorage:', taskData.task_id);
                            recoverTask(taskData);
                            return; // Exit early if we recovered from localStorage
                        }
                    } catch (e) {
                        console.warn('Error parsing stored task:', e);
                    }
                }
                
                // Fall back to API check
                const response = await fetch('/queue/my-results');
                if (!response.ok) return;
                
                const data = await response.json();
                if (data.has_results && data.latest_completed) {
                    const completedTask = data.latest_completed;
                    
                    // Check if this task has already been displayed
                    if (completedTask.status === 'complete' && !displayedTasks.has(completedTask.task_id)) {
                        console.log('🔄 Found completed task via API that needs recovery:', completedTask.task_id);
                        recoverTask(completedTask);
                    }
                }
            }
        } catch (error) {
            console.warn('Error checking for missing results:', error);
        }
    }
    
    /**
     * Recover a task by forcing UI update and result display
     */
    function recoverTask(taskData) {
        console.log('🔄 Recovering task:', taskData.task_id);
        
        // Mark as displayed to prevent duplicate recovery
        displayedTasks.add(taskData.task_id);
        
        // Ensure we have a proper status object format
        const status = {
            status: 'complete',
            task_id: taskData.task_id,
            progress_percent: 100,
            message: "Processing complete! Your results are ready to view.",
            ...taskData
        };
        
        // Force UI update
        if (typeof handleTaskStatusUpdate === 'function') {
            console.log('📋 Updating task status for recovery');
            handleTaskStatusUpdate(status);
        }
        
        // Force results load
        if (typeof loadTaskResults === 'function') {
            console.log('📋 Loading task results for recovery');
            setTimeout(() => {
                loadTaskResults(status);
                
                // Show results
                if (typeof showResults === 'function') {
                    setTimeout(showResults, 1000);
                }
            }, 500);
        }
        
        console.log('✅ Recovery attempt completed for task:', taskData.task_id);
    }
})();

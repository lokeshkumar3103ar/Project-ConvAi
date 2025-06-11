/**
 * Queue Enhancement Module
 * Handles queue statistics polling and UI updates for the frontend queue monitor
 */

let queueStatsInterval = null;
let isQueueMonitorActive = false;

/**
 * Main function to enhance queue polling with system-wide statistics
 */
function enhanceQueuePolling() {
    console.log('🚀 Queue Enhancer: Initializing queue statistics polling...');
    
    // Start polling queue stats if the monitor is visible
    const queueMonitor = document.getElementById('queue-status-monitor');
    if (queueMonitor && queueMonitor.style.display !== 'none') {
        startQueueStatsPolling();
    }
    
    // Set up observer to start/stop polling when queue monitor becomes visible/hidden
    if (queueMonitor) {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
                    const isVisible = queueMonitor.style.display !== 'none';
                    if (isVisible && !isQueueMonitorActive) {
                        startQueueStatsPolling();
                    } else if (!isVisible && isQueueMonitorActive) {
                        stopQueueStatsPolling();
                    }
                }
            });
        });
        
        observer.observe(queueMonitor, { attributes: true });
    }
}

/**
 * Start polling queue statistics from the backend
 */
function startQueueStatsPolling() {
    if (queueStatsInterval) {
        clearInterval(queueStatsInterval);
    }
    
    isQueueMonitorActive = true;
    console.log('📊 Queue Stats: Starting polling...');
    
    // Poll immediately
    pollQueueStats();
    
    // Then poll every 3 seconds
    queueStatsInterval = setInterval(pollQueueStats, 3000);
}

/**
 * Stop polling queue statistics
 */
function stopQueueStatsPolling() {
    if (queueStatsInterval) {
        clearInterval(queueStatsInterval);
        queueStatsInterval = null;
    }
    
    isQueueMonitorActive = false;
    console.log('⏹️ Queue Stats: Stopped polling');
}

/**
 * Poll queue statistics from the backend and update UI
 */
async function pollQueueStats() {
    try {
        const response = await fetch('/queue/stats');
        if (!response.ok) {
            console.warn(`Queue stats endpoint returned status: ${response.status}`);
            return;
        }
        
        const stats = await response.json();
        console.log('📈 Queue Stats received:', stats);
        
        // Validate that we have the necessary data before updating UI
        if (!stats || typeof stats !== 'object') {
            console.warn('Invalid queue stats data received', stats);
            return;
        }
        
        updateQueueStatsUI(stats);
        
    } catch (error) {
        console.error('❌ Error polling queue stats:', error);
    }
}

/**
 * Update the queue monitor UI with statistics
 */
function updateQueueStatsUI(stats) {
    // Update system phase
    updateSystemPhase(stats.current_phase || 'idle');
    
    // Update queue counts
    updateQueueCounts(stats);
    
    // Update performance metrics
    updatePerformanceMetrics(stats);
    
    // Update system status indicator
    updateSystemStatus(stats);
}

/**
 * Update the current system phase indicator
 */
function updateSystemPhase(phase) {
    const phaseElement = document.getElementById('current-phase');
    if (!phaseElement) return;
    
    // Remove all phase classes
    phaseElement.className = 'phase-badge';    // Map phases to display text and classes
    const phaseConfig = {
        'idle': { text: 'Idle', class: 'idle' },
        'stt_phase': { text: 'Speech Processing', class: 'stt' },
        'evaluation_phase': { text: 'Evaluation Phase', class: 'eval' },
        'processing': { text: 'Active Processing', class: 'processing' },
        'maintenance': { text: 'Maintenance', class: 'maintenance' }
    };
    
    const config = phaseConfig[phase] || phaseConfig['idle'];
    phaseElement.textContent = config.text;
    phaseElement.classList.add(config.class);
}

/**
 * Update queue position counts
 */
function updateQueueCounts(stats) {
    // STT Queue count
    const sttCountElement = document.getElementById('stt-queue-count');
    if (sttCountElement) {
        // Use the exact property name from backend
        const sttCount = stats.stt_queue_size !== undefined ? stats.stt_queue_size : 0;
        sttCountElement.textContent = sttCount;
    }
    
    // Evaluation Queue count
    const evalCountElement = document.getElementById('eval-queue-count');
    if (evalCountElement) {
        // Use the exact property name from backend
        const evalCount = stats.evaluation_queue_size !== undefined ? stats.evaluation_queue_size : 0;
        evalCountElement.textContent = evalCount;
    }
}

/**
 * Update performance metrics
 */
function updatePerformanceMetrics(stats) {
    // Completed count
    const completedElement = document.getElementById('completed-count');
    if (completedElement) {
        completedElement.textContent = stats.completed_tasks || 0;
    }
    
    // Failed count
    const failedElement = document.getElementById('failed-count');
    if (failedElement) {
        failedElement.textContent = stats.failed_tasks || 0;
    }
      // Average processing time
    const avgTimeElement = document.getElementById('avg-time');
    if (avgTimeElement) {
        if (stats.average_processing_time !== undefined && stats.average_processing_time > 0) {
            avgTimeElement.textContent = Math.round(stats.average_processing_time) + 's';
        } else {
            avgTimeElement.textContent = '-';
        }
    }
}

/**
 * Update system status indicator
 */
function updateSystemStatus(stats) {
    const statusDot = document.getElementById('system-status-dot');
    const statusText = document.getElementById('system-status-text');
    
    if (!statusDot || !statusText) return;    // Determine status based on queue activity and system health
    let status = 'active';
    let statusTextValue = 'Active';
    
    if (stats.system_status) {
        status = stats.system_status.toLowerCase();
        statusTextValue = stats.system_status;
    } else {
        // Infer status from processing_active flag, current phase, and queue sizes
        if (stats.current_phase === 'idle') {
            // If current phase is explicitly idle, show idle status
            status = 'idle';
            statusTextValue = 'Idle';
        } else if (stats.processing_active === true) {
            // If processing is active with tasks in queue or active phases, show busy
            if (stats.stt_queue_size > 0 || stats.evaluation_queue_size > 0 || 
                stats.current_phase === 'stt_phase' || stats.current_phase === 'evaluation_phase') {
                status = 'busy';
                statusTextValue = 'Busy';
            } else {
                // No tasks but processing active - transitioning state
                status = 'active';
                statusTextValue = 'Active';
            }
        } else {
            // Processing not active
            status = 'idle';
            statusTextValue = 'Idle';
        }
    }
    
    // Remove all status classes
    statusDot.className = 'status-dot';
    
    // Add appropriate status class
    const statusClasses = {
        'active': 'active',
        'idle': 'idle', 
        'busy': 'busy',
        'error': 'error',
        'maintenance': 'maintenance'
    };
    
    if (statusClasses[status]) {
        statusDot.classList.add(statusClasses[status]);
    }
    
    statusText.textContent = statusTextValue;
}



// Export functions for global access
window.enhanceQueuePolling = enhanceQueuePolling;
window.startQueueStatsPolling = startQueueStatsPolling;
window.stopQueueStatsPolling = stopQueueStatsPolling;

console.log('📦 Queue Enhancer module loaded successfully');

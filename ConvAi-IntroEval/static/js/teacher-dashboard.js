/**
 * Teacher Dashboard JavaScript
 * Handles all functionality for the teacher dashboard including:
 * - Theme management
 * - Student search and assignment
 * - Analytics visualization
 * - Chart management
 */

// Global variables
let teacherUsername = null;
let currentStudent = null;
let trendsChart = null;
let comparisonChart = null;

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Get teacher username from template variable (will be set in HTML)
    teacherUsername = window.TEACHER_USERNAME;
    
    initializeTheme();
    initializeEventListeners();
    loadStudents();

    //class filter
    const classFilter = document.getElementById('classFilter');
    if (classFilter) {
        classFilter.addEventListener('input', function() {
            loadStudents(classFilter.value);
        });
    }

    //logout
    const logoutBtn = document.getElementById('logout-btn');
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
});

/**
 * Theme Management
 */
function initializeTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const html = document.documentElement;

    // Check for saved theme preference or default to dark
    const savedTheme = localStorage.getItem('theme') || 'dark';
    html.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    themeToggle.addEventListener('click', function() {
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

/**
 * Event Listeners
 */
function initializeEventListeners() {
    // Student search form
    document.getElementById('studentSearchForm').addEventListener('submit', handleStudentSearch);
    
    // Modal close functionality
    window.onclick = function(event) {
        const modal = document.getElementById('searchModal');
        if (event.target === modal) {
            closeSearchModal();
        }
    };
}

/**
 * Modal Functions
 */
function openSearchModal() {
    document.getElementById('searchModal').style.display = 'flex';
    document.getElementById('studentRoll').focus();
}

function closeSearchModal() {
    document.getElementById('searchModal').style.display = 'none';
    document.getElementById('studentRoll').value = '';
    document.getElementById('searchResult').innerHTML = '';
    document.getElementById('assignButton').style.display = 'none';
}

/**
 * Student Management
 */
async function loadStudents(classname='') {
    try {
        const studentList = document.getElementById('studentList');
        studentList.innerHTML = '<div class="student-item loading">Loading students...</div>';

        // Encoding the filter
        let url = `/api/teacher/students/${teacherUsername}`;
        if (classname) {
            url += `?classname=${encodeURIComponent(classname)}`;
        }

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        studentList.innerHTML = '';

        if (!data.students || data.students.length === 0) {
            studentList.innerHTML = '<div class="student-item">No students assigned yet</div>';
            return;
        }

        data.students.forEach(student => {
            const div = document.createElement('div');
            div.className = 'student-item';
            div.innerHTML = `
                <div class="student-name">${student.name}</div>
                <div class="student-roll">${student.roll_number}</div>
            `;
            div.onclick = () => showStudentRatings(student.roll_number, student.name);
            studentList.appendChild(div);
        });
    } catch (error) {
        console.error('Error loading students:', error);
        document.getElementById('studentList').innerHTML = 
            `<div class="student-item error">Error loading students: ${error.message}</div>`;
    }
}

async function handleStudentSearch(e) {
    e.preventDefault();
    const rollNumber = document.getElementById('studentRoll').value;
    const searchResult = document.getElementById('searchResult');
    const assignButton = document.getElementById('assignButton');

    try {
        const response = await fetch(`/api/teacher/search_student/${rollNumber}`);
        const data = await response.json();

        if (response.ok) {
            searchResult.innerHTML = `
                <div class="alert alert-success">
                    <div class="student-info">
                        <div class="info-item">
                            <strong>Student Name:</strong> ${data.name}
                        </div>
                        <div class="info-item">
                            <strong>Roll Number:</strong> ${data.roll_number}
                        </div>
                    </div>
                </div>
            `;
            currentStudent = data;
            assignButton.style.display = 'block';
        } else {
            searchResult.innerHTML = `
                <div class="alert alert-error">
                    Student not found
                </div>
            `;
            assignButton.style.display = 'none';
        }
    } catch (error) {
        searchResult.innerHTML = `
            <div class="alert alert-error">
                Error searching for student: ${error.message}
            </div>
        `;
        assignButton.style.display = 'none';
    }
}

async function assignStudent() {
    if (!currentStudent) return;

    const assignButton = document.getElementById('assignButton').querySelector('button');
    const searchResult = document.getElementById('searchResult');

    try {
        assignButton.disabled = true;
        assignButton.textContent = 'Assigning...';

        const response = await fetch('/api/teacher/assign_student', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                student_roll: currentStudent.roll_number,
                teacher_username: teacherUsername
            })
        });

        const result = await response.json();

        if (response.ok) {
            searchResult.innerHTML = `
                <div class="alert alert-success">
                    ${result.message}
                </div>
            `;
            document.getElementById('studentRoll').value = '';
            document.getElementById('assignButton').style.display = 'none';
            loadStudents();
        } else {
            throw new Error(result.detail || 'Failed to assign student');
        }
    } catch (error) {
        searchResult.innerHTML = `
            <div class="alert alert-error">
                ${error.message}
            </div>
        `;
        document.getElementById('assignButton').style.display = 'block';
    } finally {
        assignButton.disabled = false;
        assignButton.textContent = 'Add Student to My List';
    }
}

/**
 * Analytics and Visualization
 */
async function showStudentRatings(rollNumber, name) {
    try {
        // Highlight active student
        document.querySelectorAll('.student-item').forEach(item => {
            item.classList.remove('active');
            if (item.querySelector('.student-roll')?.textContent === rollNumber) {
                item.classList.add('active');
            }
        });

        // Fetch comprehensive analytics
        const response = await fetch(`/api/student/analytics/${rollNumber}`);
        if (!response.ok) {
            throw new Error('Failed to fetch student analytics');
        }

        const analytics = await response.json();
        const studentDetails = document.getElementById('studentDetails');

        studentDetails.style.display = 'block';
        studentDetails.innerHTML = createAnalyticsHTML(analytics, name);

        // Initialize charts after DOM is ready
        setTimeout(() => {
            initializeCharts(analytics);
            initializeTabs();
        }, 100);

    } catch (error) {
        console.error('Error loading student analytics:', error);
        document.getElementById('studentDetails').innerHTML = `
            <div class="alert alert-error">
                Error loading student analytics: ${error.message}
            </div>
        `;
    }
}

function createAnalyticsHTML(analytics, name) {
    const { performance_summary, score_trends, latest_feedback, improvement_areas, strengths } = analytics;
    
    return `
        <h3>${name}'s Performance Analytics</h3>
        
        <!-- Performance Summary Cards -->
        <div class="analytics-grid">
            <div class="analytics-card">
                <h4>Overall Average</h4>
                <div class="value">${performance_summary.overall_average || 'N/A'}</div>
                <div class="label">out of 10</div>
            </div>
            <div class="analytics-card">
                <h4>Total Assessments</h4>
                <div class="value">${performance_summary.total_assessments || 0}</div>
                <div class="label">completed</div>
            </div>
            <div class="analytics-card">
                <h4>Highest Score</h4>
                <div class="value">${performance_summary.highest_score || 'N/A'}</div>
                <div class="label">best performance</div>
            </div>
            <div class="analytics-card">
                <h4>Latest Scores</h4>
                <div class="value">
                    ${score_trends.map(trend => 
                        `<span class="${getScoreBadgeClass(trend.latest)}">${trend.latest}/10</span>`
                    ).join(' ')}
                </div>
                <div class="label">intro & profile</div>
            </div>
        </div>

        <!-- Chart Tabs -->
        <div class="tabs">
            <button class="tab-button active" onclick="switchTab('trends')">Score Trends</button>
            <button class="tab-button" onclick="switchTab('comparison')">Score Comparison</button>
            <button class="tab-button" onclick="switchTab('detailed')">Detailed Ratings</button>
        </div>

        <!-- Chart Content -->
        <div id="trends-tab" class="tab-content active">
            <div class="chart-container">
                <h4>Score Progression Over Time</h4>
                <div class="chart-wrapper">
                    <canvas id="trendsChart"></canvas>
                </div>
            </div>
        </div>

        <div id="comparison-tab" class="tab-content">
            <div class="chart-container">
                <h4>Introduction vs Profile Scores</h4>
                <div class="chart-wrapper">
                    <canvas id="comparisonChart"></canvas>
                </div>
            </div>
        </div>

        <div id="detailed-tab" class="tab-content">
            ${createDetailedRatingsHTML(analytics)}
        </div>

        <!-- Insights Section -->
        <div class="insights-grid">
            <div class="insights-card">
                <h5><i class="fas fa-check-circle"></i> Strengths</h5>
                <ul class="insights-list">
                    ${strengths.length > 0 ? 
                        strengths.map(strength => `<li>${strength}</li>`).join('') : 
                        '<li>No specific strengths identified yet</li>'
                    }
                </ul>
            </div>
            <div class="insights-card">
                <h5><i class="fas fa-arrow-up"></i> Areas for Improvement</h5>
                <ul class="insights-list">
                    ${improvement_areas.length > 0 ? 
                        improvement_areas.map(area => `<li>${area}</li>`).join('') : 
                        '<li>No specific improvement areas identified yet</li>'
                    }
                </ul>
            </div>
        </div>
    `;
}

function createDetailedRatingsHTML(analytics) {
    const { intro_ratings, profile_ratings } = analytics;

    let html = '<div class="chart-container">';
    html += '<h4>All Evaluation Details</h4>';

    if (intro_ratings.length > 0) {
        html += '<h5 style="margin-top: 1.5rem; color: var(--secondary-color);">Introduction Evaluations</h5>';
        intro_ratings.forEach(rating => {
            const data = rating.data;
            html += `
                <div class="analytics-card detail-card" style="margin-bottom: 1rem;">
                    <h6>Score: ${data.intro_rating} <span class="${getScoreBadgeClass(parseFloat(data.intro_rating))}">${getScoreLabel(parseFloat(data.intro_rating))}</span></h6>
                    <p><strong>Date:</strong> ${new Date(rating.timestamp).toLocaleDateString()}</p>
                    ${data.grading_explanation ? `
                        <div style="margin-top: 0.8rem;">
                            <strong>Category Breakdown:</strong>
                            <ul style="margin: 0.5rem 0; padding-left: 1.2rem;">
                                ${Object.entries(data.grading_explanation).map(([cat, score]) => 
                                    `<li><strong>${cat.replace(/_/g, ' ')}:</strong> ${score}</li>`
                                ).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    ${data.insights ? `
                        <div style="margin-top: 0.8rem;">
                            <strong>Insights:</strong> ${data.insights.join(', ')}
                        </div>
                    ` : ''}
                </div>
            `;
        });
    }

    if (profile_ratings.length > 0) {
        html += '<h5 style="margin-top: 1.5rem; color: var(--secondary-color);">Profile Evaluations</h5>';
        profile_ratings.forEach(rating => {
            const data = rating.data;
            html += `
                <div class="analytics-card detail-card" style="margin-bottom: 1rem;">
                    <h6>Score: ${data.profile_rating} <span class="${getScoreBadgeClass(parseFloat(data.profile_rating))}">${getScoreLabel(parseFloat(data.profile_rating))}</span></h6>
                    <p><strong>Date:</strong> ${new Date(rating.timestamp).toLocaleDateString()}</p>
                    ${data.grading_explanation ? `
                        <div style="margin-top: 0.8rem;">
                            <strong>Category Breakdown:</strong>
                            <ul style="margin: 0.5rem 0; padding-left: 1.2rem;">
                                ${Object.entries(data.grading_explanation).map(([cat, score]) => 
                                    `<li><strong>${cat.replace(/_/g, ' ')}:</strong> ${score}</li>`
                                ).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            `;
        });
    }

    if (intro_ratings.length === 0 && profile_ratings.length === 0) {
        html += '<div class="alert alert-info">No detailed evaluations available yet.</div>';
    }

    html += '</div>';
    return html;
}

/**
 * Utility Functions
 */
function getScoreBadgeClass(score) {
    if (score >= 8) return 'score-excellent';
    if (score >= 6) return 'score-good';
    if (score >= 4) return 'score-average';
    return 'score-poor';
}

function getScoreLabel(score) {
    if (score >= 8) return 'Excellent';
    if (score >= 6) return 'Good';
    if (score >= 4) return 'Average';
    return 'Needs Improvement';
}

/**
 * Tab Management
 */
function switchTab(tabName) {
    // Remove active class from all tabs and content
    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    // Add active class to clicked tab and corresponding content
    event.target.classList.add('active');
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

function initializeTabs() {
    // Tab functionality is handled by switchTab function
    // This function can be extended for additional tab setup if needed
}

/**
 * Chart Management
 */
function initializeCharts(analytics) {
    const { score_trends } = analytics;

    // Destroy existing charts if they exist
    if (trendsChart) {
        trendsChart.destroy();
        trendsChart = null;
    }
    if (comparisonChart) {
        comparisonChart.destroy();
        comparisonChart = null;
    }

    // Initialize trends chart
    const trendsCtx = document.getElementById('trendsChart');
    if (trendsCtx && score_trends.length > 0) {
        const datasets = score_trends.map((trend, index) => ({
            label: trend.type === 'intro' ? 'Introduction Scores' : 'Profile Scores',
            data: trend.scores,
            borderColor: trend.type === 'intro' ? '#e74c3c' : '#3498db',
            backgroundColor: trend.type === 'intro' ? 'rgba(231, 76, 60, 0.1)' : 'rgba(52, 152, 219, 0.1)',
            tension: 0.4,
            fill: true
        }));

        trendsChart = new Chart(trendsCtx, {
            type: 'line',
            data: {
                labels: score_trends[0]?.timestamps || [],
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Score Progression Over Time',
                        color: getComputedStyle(document.documentElement).getPropertyValue('--primary-color')
                    },
                    legend: {
                        labels: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--primary-color')
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 10,
                        grid: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--border-color')
                        },
                        ticks: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--primary-color')
                        }
                    },
                    x: {
                        grid: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--border-color')
                        },
                        ticks: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--primary-color')
                        }
                    }
                }
            }
        });
    }

    // Initialize comparison chart
    const comparisonCtx = document.getElementById('comparisonChart');
    if (comparisonCtx && score_trends.length > 0) {
        const introTrend = score_trends.find(t => t.type === 'intro');
        const profileTrend = score_trends.find(t => t.type === 'profile');

        comparisonChart = new Chart(comparisonCtx, {
            type: 'bar',
            data: {
                labels: ['Average Score', 'Latest Score', 'Improvement'],
                datasets: [
                    {
                        label: 'Introduction',
                        data: [
                            introTrend?.average || 0,
                            introTrend?.latest || 0,
                            introTrend?.improvement || 0
                        ],
                        backgroundColor: 'rgba(231, 76, 60, 0.8)',
                        borderColor: '#e74c3c',
                        borderWidth: 1
                    },
                    {
                        label: 'Profile',
                        data: [
                            profileTrend?.average || 0,
                            profileTrend?.latest || 0,
                            profileTrend?.improvement || 0
                        ],
                        backgroundColor: 'rgba(52, 152, 219, 0.8)',
                        borderColor: '#3498db',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Introduction vs Profile Performance',
                        color: getComputedStyle(document.documentElement).getPropertyValue('--primary-color')
                    },
                    legend: {
                        labels: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--primary-color')
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 10,
                        grid: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--border-color')
                        },
                        ticks: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--primary-color')
                        }
                    },
                    x: {
                        grid: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--border-color')
                        },
                        ticks: {
                            color: getComputedStyle(document.documentElement).getPropertyValue('--primary-color')
                        }
                    }
                }
            }
        });
    }
}

// Make functions available globally for onclick handlers
window.openSearchModal = openSearchModal;
window.closeSearchModal = closeSearchModal;
window.assignStudent = assignStudent;
window.switchTab = switchTab;

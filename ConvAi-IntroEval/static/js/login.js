/**
 * Login Page JavaScript
 * Handles login, registration, password reset, and theme functionality
 */

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
    initializeTheme();
});

/**
 * Theme Toggle Functionality
 */
function initializeTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const html = document.documentElement;

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

// Section switching logic
function showSection(sectionId) {
  document.querySelectorAll('.form-section').forEach(sec => sec.classList.remove('active'));
  document.getElementById(sectionId).classList.add('active');
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  if (sectionId === 'loginSection') document.querySelector('.tab-btn:nth-child(1)').classList.add('active');
  if (sectionId === 'registerSection') document.querySelector('.tab-btn:nth-child(2)').classList.add('active');
  // Forgot section: no menu tab is active
}    // Login
document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const submitBtn = e.target.querySelector('button[type="submit"]');
  const originalBtnText = submitBtn.textContent;
  submitBtn.disabled = true;
  submitBtn.textContent = 'Logging in...';
  
  const formData = new FormData(e.target);
  const loginType = formData.get('loginType');
  const params = new URLSearchParams();
  for (const pair of formData) {
    if (pair[0] !== 'loginType') {
      params.append(pair[0], pair[1]);
    }
  }
  
  try {
    const endpoint = loginType === 'teacher' ? '/teacher/login' : '/login';
    const response = await fetch(endpoint, {
      method: "POST",
      body: params,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      redirect: 'follow'
    });

    if (response.redirected) {
      window.location.href = response.url;
    } else if (response.ok) {
      localStorage.setItem('showFluidTransition', 'true');
      window.location.href = loginType === 'teacher' ? "/teacher/dashboard" : "/index";
    } else {
      const result = await response.json();
      document.getElementById("loginResult").innerHTML = 
        `<div class="alert alert-error">${result.detail || 'Login failed'}</div>`;
    }
  } catch (error) {
    document.getElementById("loginResult").innerHTML = 
      `<div class="alert alert-error">Login error: ${error.message}</div>`;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = originalBtnText;
  }
});

// Register
document.getElementById("registerForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);
  const registerType = formData.get('registerType');
  const params = new URLSearchParams();
  
  for (const pair of formData) {
    if (pair[0] !== 'registerType') {
      params.append(pair[0], pair[1]);
    }
  }

  const endpoint = registerType === 'teacher' ? '/teacher/register' : '/register';
  const response = await fetch(endpoint, {
    method: "POST",
    body: params,
    headers: { "Content-Type": "application/x-www-form-urlencoded" }
  });
  
  const result = await response.json();
  if (response.ok) {
    document.getElementById("registerResult").innerHTML = `<span style="color:green">${result.message}</span>`;
    // Clear form and switch to login section after successful registration
    e.target.reset();
    showSection('loginSection');
  } else {
    document.getElementById("registerResult").innerHTML = `<span style="color:red">${result.detail}</span>`;
  }
});

// Forgot Password - send OTP request
document.getElementById("forgotPasswordForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = e.target.querySelector("button[type=submit]");
  btn.disabled = true;
  const formData = new FormData(e.target);
  const params = new URLSearchParams();
  for (const pair of formData) params.append(pair[0], pair[1]);
  try {
    const response = await fetch("/request-password-reset", {
      method: "POST",
      body: params,
      headers: { "Content-Type": "application/x-www-form-urlencoded" }
    });
    const result = await response.json();
    document.getElementById("forgotPasswordResult").textContent = result.message;
  } catch (error) {
    document.getElementById("forgotPasswordResult").textContent = "Error sending OTP. Please try again.";
  } finally {
    btn.disabled = false;
  }
});



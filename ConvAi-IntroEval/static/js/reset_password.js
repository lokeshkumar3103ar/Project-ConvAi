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

document.addEventListener('DOMContentLoaded', function () {
    initializeTheme();
});

document.getElementById("resetPasswordForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const resultDiv = document.getElementById("resetPasswordResult");
  resultDiv.textContent = "";

  // Get form values and trim whitespace where applicable
  const username = document.getElementById("username").value.trim();
  const otp = document.getElementById("otp").value.trim();
  const newPassword = document.getElementById("new_password").value;
  const newPassword2 = document.getElementById("new_password2").value;

  // Frontend validation: check if passwords match
  if (newPassword !== newPassword2) {
    resultDiv.textContent = "Passwords do not match.";
    return;
  }

  // Verify OTP first by sending username and otp to /verify-otp
  try {
    const verifyResponse = await fetch("/verify-otp", {
      method: "POST",
      body: new URLSearchParams({ username, otp }),  // form-urlencoded body
      headers: { "Content-Type": "application/x-www-form-urlencoded" }
    });

    if (!verifyResponse.ok) {
      const err = await verifyResponse.json();
      resultDiv.textContent = err.detail || "Invalid or expired OTP.";
      return;
    }

    // If OTP verified, proceed to reset password
    // Prepare form data with username and new_password (as backend expects)
    const params = new URLSearchParams();
    params.append("username", username);
    params.append("otp",otp);
    params.append("new_password", newPassword);

    const resetResponse = await fetch("/reset-password", {
      method: "POST",
      body: params,
      headers: { "Content-Type": "application/x-www-form-urlencoded" }
    });

    if (resetResponse.ok) {
      const data = await resetResponse.json();
      resultDiv.textContent = data.message || "Password reset successfully.";
      // Optionally, redirect user after success
      // window.location.href = "/login";
    } else {
      const err = await resetResponse.json();
      resultDiv.textContent = err.detail || "Failed to reset password.";
    }
  } catch (error) {
    resultDiv.textContent = "An error occurred. Please try again.";
  }
});

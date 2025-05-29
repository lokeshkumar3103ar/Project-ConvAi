    // Section switching logic
    function showSection(sectionId) {
      document.querySelectorAll('.form-section').forEach(sec => sec.classList.remove('active'));
      document.getElementById(sectionId).classList.add('active');
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      if (sectionId === 'loginSection') document.querySelector('.tab-btn:nth-child(1)').classList.add('active');
      if (sectionId === 'registerSection') document.querySelector('.tab-btn:nth-child(2)').classList.add('active');
      // Forgot section: no menu tab is active
    }

    // Login
    document.getElementById("loginForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      const params = new URLSearchParams();
      for (const pair of formData) params.append(pair[0], pair[1]);
      const response = await fetch("/login", {
        method: "POST",
        body: params,
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
      });
      const result = await response.json();
      if (response.ok) {
        window.location.href = "/index";
      } else {
        document.getElementById("loginResult").innerHTML = `<span style="color:red">${result.detail}</span>`;
      }
    });

    // Register
    document.getElementById("registerForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      const params = new URLSearchParams();
      for (const pair of formData) params.append(pair[0], pair[1]);
      const response = await fetch("/register", {
        method: "POST",
        body: params,
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
      });
      const result = await response.json();
      if (response.ok) {
        document.getElementById("registerResult").innerHTML = `<span style="color:green">${result.message}</span>`;
      } else {
        document.getElementById("registerResult").innerHTML = `<span style="color:red">${result.detail}</span>`;
      }
    });

    // Forgot Password
    document.getElementById("forgotPasswordForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(e.target);
      const params = new URLSearchParams();
      for (const pair of formData) params.append(pair[0], pair[1]);
      const response = await fetch("/request-password-reset", {
        method: "POST",
        body: params,
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
      });
      const result = await response.json();
      document.getElementById("forgotPasswordResult").innerHTML = result.message;
    });
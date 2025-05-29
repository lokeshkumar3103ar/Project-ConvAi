    // Get token from URL
    function getToken() {
      const params = new URLSearchParams(window.location.search);
      return params.get("token");
    }
    document.getElementById("resetPasswordForm").addEventListener("submit", async (e) => {
      e.preventDefault();
      const new_password = e.target.new_password.value;
      const token = getToken();
      if (!token) {
        document.getElementById("resetPasswordResult").innerHTML = "Invalid or missing token.";
        return;
      }
      const params = new URLSearchParams();
      params.append("token", token);
      params.append("new_password", new_password);
      const response = await fetch("/reset-password", {
        method: "POST",
        body: params,
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
      });
      const result = await response.json();
      if (response.ok) {
        document.getElementById("resetPasswordResult").innerHTML = `<span style="color:green">${result.message}</span>`;
      } else {
        document.getElementById("resetPasswordResult").innerHTML = `<span style="color:red">${result.detail}</span>`;
      }
    });
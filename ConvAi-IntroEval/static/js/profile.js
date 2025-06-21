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

document.addEventListener('DOMContentLoaded', function() {
    // Profile elements
    const profileUsername = document.getElementById('profile-username');
    const profileName = document.getElementById('profile-name');
    const profileEmail = document.getElementById('profile-email');
    const profileClassname = document.getElementById('profile-class');
    const logoutBtn = document.getElementById('logout-btn');
    
    // Load user profile information
    async function loadUserProfile() {
        try {
            console.log('Starting user profile load...');
            console.log('Document cookies:', document.cookie);
            
            const response = await fetch('/api/auth/profile', {
                credentials: 'include' // Include cookies for authentication
            });
            
            console.log('Profile response status:', response.status);
            console.log('Profile response headers:', [...response.headers.entries()]);
            
            if (response.ok) {
                const userInfo = await response.json();
                console.log('User profile loaded successfully:', userInfo);
                
                // Update profile elements
                if (profileUsername) {
                    profileUsername.textContent = userInfo.username || 'Unknown';
                }
                if (profileName) {
                    profileName.textContent = userInfo.name || 'N/A';
                }
                
                if (profileEmail) {
                    profileEmail.textContent = userInfo.email || 'N/A';
                }
                if (profileClassname){
                    profileClassname.textContent = userInfo.classname || 'N/A';
                }
            } 
            else if (response.status === 401) {
                console.log('User not authenticated, redirecting to login');
                // User is not authenticated, redirect to login
                window.location.href = '/login';
            } else {
                console.error('Failed to load user profile:', response.status);
                // Set default values on error
                if (profileUsername) profileUsername.textContent = 'Not logged in';
                if (profileName) profileName.textContent = 'N/A';
                if (profileEmail) profileEmail.textContent = 'N/A';
                if (profileClassname) profileClassname.textContent = 'N/A';
            }
        } catch (error) {
            console.error('Error loading user profile:', error);
            // Set error values and redirect to login
            if (profileUsername) profileUsername.textContent = 'Error';
            if (profileName) profileName.textContent = 'Error';
            if (profileEmail) profileEmail.textContent = 'Error';
            if(profileClassname) profileClassname.textContent = 'Error';
            // On network error, also redirect to login after a delay
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        }
    }
    const editBtn = document.getElementById('edit-btn');
    let inEditMode = false;
    let originalData = {};

    editBtn.addEventListener('click', function () {
        if (!inEditMode) {
            // Switch to edit mode
            originalData = {
                name: profileName.textContent,
                email: profileEmail.textContent,
                classname: profileClassname.textContent,
            };

            replaceWithInput(profileName, 'input-name', originalData.name);
            replaceWithInput(profileEmail, 'input-email', originalData.email);
            replaceWithInput(profileClassname, 'input-classname', originalData.classname);

            editBtn.innerHTML = '<i class="fas fa-save"></i>';
            inEditMode = true;
        } else {
            // Save changes
            const updatedData = {};

            const inputName = document.getElementById('input-name');
            const inputEmail = document.getElementById('input-email');
            const inputClass = document.getElementById('input-classname');

            if (inputName.value !== originalData.name) updatedData.name = inputName.value;
            if (inputEmail.value !== originalData.email) updatedData.email = inputEmail.value;
            if (inputClass.value !== originalData.classname) updatedData.classname = inputClass.value;

            if (Object.keys(updatedData).length === 0) {
                alert('No changes detected.');
                return;
            }

            fetch('/api/auth/profile', {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(updatedData)
            })
            .then(res => {
                if (!res.ok) throw new Error('Update failed');
                return res.json();
            })
            .then(data => {
                alert('Profile updated successfully!');
                location.reload(); // Reload to reflect changes
            })
            .catch(err => {
                console.error('Error updating profile:', err);
                alert('Failed to update profile.');
            });
        }
    });

    function replaceWithInput(spanElement, inputId, value) {
    const input = document.createElement('input');
    input.type = 'text';
    input.id = inputId;
    input.name = inputId.replace("input-", ""); // e.g., "classname"
    input.value = value;
    input.classList.add('profile-input');

    // Add pattern for class validation if this is the classname field
    if (input.name === 'classname') {
        input.pattern = '^[A-Z]{3,5}\\d[A-Z]$';
        input.title = 'Format must be like CSE4A';
    }

    spanElement.replaceWith(input);
}


    // Logout functionality
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
      // Load user profile on page load with a small delay to ensure cookies are available
    setTimeout(() => {
        loadUserProfile();
    }, 500); // 500ms delay
});
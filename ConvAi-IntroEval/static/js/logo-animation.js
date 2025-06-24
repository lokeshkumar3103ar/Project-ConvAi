// Logo eye tracking and expressions
document.addEventListener('DOMContentLoaded', function() {
    const logoContainer = document.querySelector('.logo-container');
    
    // Eye tracking variables
    const maxEyeMovement = 2.5; // Reduced for more subtle movement
    let logoRect;
    let currentX = 0;
    let currentY = 0;
    let targetX = 0;
    let targetY = 0;
    
    // Update logo position on resize or scroll
    function updateLogoPosition() {
        logoRect = logoContainer.getBoundingClientRect();
    }
    
    // Initial position calculation
    updateLogoPosition();
    window.addEventListener('resize', updateLogoPosition);
    window.addEventListener('scroll', updateLogoPosition);
    
    // Ensure reflection color updates with theme
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            // The CSS handles the actual color change via CSS variables
            // This is just to force a repaint in some browsers
            const leftReflection = document.querySelector('.letter:first-child::after');
            const rightReflection = document.querySelector('.letter.q-right::after');
            if (leftReflection) leftReflection.style.transition = 'transform 0.1s ease, background 0.3s ease';
            if (rightReflection) rightReflection.style.transition = 'transform 0.1s ease, background 0.3s ease';
        });
    }
    
    // Track cursor position and move eyes
    document.addEventListener('mousemove', function(e) {
        if (!logoRect) return;
        
        // Calculate cursor position relative to logo center
        const centerX = logoRect.left + logoRect.width / 2;
        const centerY = logoRect.top + logoRect.height / 2;
        
        // Calculate normalized direction vector from logo center to cursor
        const deltaX = (e.clientX - centerX) / (window.innerWidth / 2);
        const deltaY = (e.clientY - centerY) / (window.innerHeight / 2);
        
        // Set target position with limits
        // Slightly reduced max movement to keep reflections inside eyeballs
        targetX = Math.min(Math.max(deltaX * maxEyeMovement, -maxEyeMovement), maxEyeMovement) * 0.9;
        targetY = Math.min(Math.max(deltaY * maxEyeMovement, -maxEyeMovement), maxEyeMovement) * 0.9;
    });
    
    // Smooth animation for eye movement
    function updateEyes() {
        // Smooth interpolation
        currentX += (targetX - currentX) * 0.1;
        currentY += (targetY - currentY) * 0.1;
        
        // Apply slightly different movement to each eye for more natural look
        // Left eye
        document.querySelector('.letter:first-child').style.setProperty('--eye-move-x', `${currentX * 0.9}px`);
        document.querySelector('.letter:first-child').style.setProperty('--eye-move-y', `${currentY * 0.9}px`);
        
        // Right eye - slightly different movement for natural look
        document.querySelector('.letter.q-right').style.setProperty('--eye-move-x', `${currentX * 0.85}px`);
        document.querySelector('.letter.q-right').style.setProperty('--eye-move-y', `${currentY * 0.85}px`);
        
        requestAnimationFrame(updateEyes);
    }
    
    // Start the animation loop
    updateEyes();
    
    // Click expressions
    const expressions = ['surprised', 'love', 'dizzy'];
    let currentExpression = -1;
    
    logoContainer.addEventListener('click', function() {
        // Clear any existing expression
        expressions.forEach(expr => {
            logoContainer.classList.remove(expr);
        });
        
        // Move to next expression
        currentExpression = (currentExpression + 1) % expressions.length;
        
        // Apply new expression
        logoContainer.classList.add(expressions[currentExpression]);
        
        // Remove the expression after a delay
        setTimeout(() => {
            logoContainer.classList.remove(expressions[currentExpression]);
        }, 2000);
    });
});

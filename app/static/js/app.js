// Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('Service Worker registered'))
            .catch(err => console.log('Service Worker registration failed:', err));
    });
}

// PWA Install Prompt
let deferredPrompt;
const installPrompt = document.getElementById('installPrompt');
const installButton = document.getElementById('installButton');
const dismissInstall = document.getElementById('dismissInstall');

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    // Show install prompt if not dismissed
    if (!localStorage.getItem('installDismissed')) {
        installPrompt.style.display = 'block';
    }
});

if (installButton) {
    installButton.addEventListener('click', async () => {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            const { outcome } = await deferredPrompt.userChoice;
            console.log(`User response: ${outcome}`);
            deferredPrompt = null;
            installPrompt.style.display = 'none';
        }
    });
}

if (dismissInstall) {
    dismissInstall.addEventListener('click', () => {
        installPrompt.style.display = 'none';
        localStorage.setItem('installDismissed', 'true');
    });
}

// Habit Checkbox Toggle with Optimistic Updates
document.addEventListener('DOMContentLoaded', () => {
    const checkboxes = document.querySelectorAll('.habit-checkbox-input');
    
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', async (e) => {
            const habitId = e.target.dataset.habitId;
            const date = e.target.dataset.date;
            const isChecked = e.target.checked;
            
            // Optimistic update - checkbox is already checked by browser
            
            try {
                const response = await fetch('/api/toggle', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        habit_id: habitId,
                        date: date
                    })
                });
                
                const data = await response.json();
                
                if (!response.ok || !data.success) {
                    // Revert on failure
                    e.target.checked = !isChecked;
                    showToast('Failed to save. Please try again.', 'error');
                } else {
                    // Add celebration animation on check
                    if (data.completed) {
                        addCelebrationEffect(e.target);
                    }
                }
            } catch (error) {
                console.error('Error toggling habit:', error);
                // Revert on error
                e.target.checked = !isChecked;
                showToast('Network error. Please check your connection.', 'error');
            }
        });
    });
});

// Celebration Effect
function addCelebrationEffect(checkbox) {
    const label = checkbox.nextElementSibling;
    if (!label) return;
    
    // Create confetti-like particles
    for (let i = 0; i < 5; i++) {
        const particle = document.createElement('div');
        particle.style.position = 'absolute';
        particle.style.width = '8px';
        particle.style.height = '8px';
        particle.style.background = '#4CAF50';
        particle.style.borderRadius = '50%';
        particle.style.pointerEvents = 'none';
        particle.style.zIndex = '1000';
        
        const rect = label.getBoundingClientRect();
        particle.style.left = `${rect.left + rect.width / 2}px`;
        particle.style.top = `${rect.top + rect.height / 2}px`;
        
        document.body.appendChild(particle);
        
        // Animate particle
        const angle = (Math.PI * 2 * i) / 5;
        const distance = 50 + Math.random() * 30;
        const tx = Math.cos(angle) * distance;
        const ty = Math.sin(angle) * distance;
        
        particle.animate([
            { transform: 'translate(0, 0) scale(1)', opacity: 1 },
            { transform: `translate(${tx}px, ${ty}px) scale(0)`, opacity: 0 }
        ], {
            duration: 600,
            easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)'
        }).onfinish = () => particle.remove();
    }
}

// Toast Notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        bottom: 100px;
        left: 50%;
        transform: translateX(-50%);
        background: ${type === 'error' ? '#ef5350' : '#4CAF50'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        z-index: 2000;
        animation: toastSlide 0.3s ease;
    `;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'toastSlide 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Swipe Gesture Support for Date Navigation
let touchStartX = 0;
let touchEndX = 0;

const dailyContainer = document.querySelector('.daily-container');

if (dailyContainer) {
    dailyContainer.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });
    
    dailyContainer.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        handleSwipe();
    }, { passive: true });
}

function handleSwipe() {
    const swipeThreshold = 100;
    const swipeDistance = touchEndX - touchStartX;
    
    if (Math.abs(swipeDistance) < swipeThreshold) return;
    
    const dateNavigation = document.querySelector('.date-navigation');
    if (!dateNavigation) return;
    
    if (swipeDistance > 0) {
        // Swipe right - go to previous day
        const prevLink = dateNavigation.querySelector('.nav-arrow[href*="date="]');
        if (prevLink && prevLink.textContent.includes('Previous')) {
            window.location.href = prevLink.href;
        }
    } else {
        // Swipe left - go to next day
        const navArrows = dateNavigation.querySelectorAll('.nav-arrow[href*="date="]');
        const nextLink = navArrows[navArrows.length - 1];
        if (nextLink && nextLink.textContent.includes('Next')) {
            window.location.href = nextLink.href;
        }
    }
}

// Keyboard Shortcuts
document.addEventListener('keydown', (e) => {
    // Arrow keys for date navigation
    if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
        const dateNavigation = document.querySelector('.date-navigation');
        if (!dateNavigation) return;
        
        if (e.key === 'ArrowLeft') {
            const prevLink = dateNavigation.querySelector('.nav-arrow[href*="date="]');
            if (prevLink && prevLink.textContent.includes('Previous')) {
                window.location.href = prevLink.href;
            }
        } else {
            const navArrows = dateNavigation.querySelectorAll('.nav-arrow[href*="date="]');
            const nextLink = navArrows[navArrows.length - 1];
            if (nextLink && nextLink.textContent.includes('Next')) {
                window.location.href = nextLink.href;
            }
        }
    }
    
    // T key to jump to today
    if (e.key === 't' || e.key === 'T') {
        const todayButton = document.querySelector('.btn-today');
        if (todayButton) {
            window.location.href = todayButton.href;
        }
    }
});

// Add CSS for toast animation
const style = document.createElement('style');
style.textContent = `
    @keyframes toastSlide {
        from {
            transform: translateX(-50%) translateY(20px);
            opacity: 0;
        }
        to {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }
    }
`;
document.head.appendChild(style);

// Form Validation for Setup
const setupForm = document.getElementById('setupForm');
if (setupForm) {
    setupForm.addEventListener('submit', (e) => {
        const inputs = setupForm.querySelectorAll('input[type="text"]');
        let emptyCount = 0;
        
        inputs.forEach(input => {
            if (!input.value.trim()) {
                emptyCount++;
            }
        });
        
        if (emptyCount === inputs.length) {
            e.preventDefault();
            showToast('Please enter at least one habit', 'error');
            return;
        }
        
        // Show loading state
        const submitBtn = setupForm.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.textContent = 'Saving...';
            submitBtn.disabled = true;
        }
    });
}

// Auto-focus first empty input on setup page
if (window.location.pathname === '/setup') {
    const firstEmptyInput = document.querySelector('input[type="text"]:not([value])');
    if (firstEmptyInput) {
        firstEmptyInput.focus();
    }
}

// Offline Detection
window.addEventListener('online', () => {
    showToast('Back online! ✅', 'info');
});

window.addEventListener('offline', () => {
    showToast('You are offline. Changes will sync when reconnected.', 'error');
});

// Prevent zoom on double-tap (iOS Safari)
let lastTouchEnd = 0;
document.addEventListener('touchend', (e) => {
    const now = Date.now();
    if (now - lastTouchEnd <= 300) {
        e.preventDefault();
    }
    lastTouchEnd = now;
}, { passive: false });

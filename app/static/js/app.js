// Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('Service Worker registered'))
            .catch(err => console.log('Service Worker registration failed:', err));
    });
}

// ==================== User Management ====================

// Save username to localStorage
function saveUsername(username) {
    localStorage.setItem('habitTrackerUsername', username);
}

// Load username from localStorage
function loadUsername() {
    return localStorage.getItem('habitTrackerUsername');
}

// Clear username from localStorage
function clearUsername() {
    localStorage.removeItem('habitTrackerUsername');
}

// Load current user info and update UI
async function loadCurrentUser() {
    try {
        const response = await fetch('/api/user/current');
        const data = await response.json();
        
        if (data.username) {
            const userNameEl = document.getElementById('userName');
            if (userNameEl) {
                userNameEl.textContent = data.username;
            }
            
            // Update achievement badge
            updateAchievementBadge(data.unviewed_achievements || 0);
        }
    } catch (error) {
        console.error('Error loading user:', error);
    }
}

// Update achievement badge count
function updateAchievementBadge(count) {
    const badge = document.getElementById('achievementsBadge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count;
            badge.style.display = 'inline-block';
        } else {
            badge.style.display = 'none';
        }
    }
}

// Check for new achievements
async function checkNewAchievements() {
    try {
        const response = await fetch('/api/achievements/new');
        const data = await response.json();
        
        if (data.achievements && data.achievements.length > 0) {
            for (const achievement of data.achievements) {
                // Database tracks viewed status, so just show all unviewed achievements
                showAchievementToast(achievement);
            }
        }
    } catch (error) {
        console.error('Error checking achievements:', error);
    }
}

// Show achievement toast notification with confetti
function showAchievementToast(achievement) {
    const toast = document.createElement('div');
    toast.className = 'achievement-toast';
    toast.innerHTML = `
        <div class="achievement-toast-emoji">${achievement.emoji}</div>
        <div class="achievement-toast-content">
            <div class="achievement-toast-title">Achievement Unlocked!</div>
            <div class="achievement-toast-name">${achievement.name}</div>
            <div class="achievement-toast-desc">${achievement.description}</div>
        </div>
        <button class="achievement-toast-close">&times;</button>
    `;
    
    document.body.appendChild(toast);
    
    // Trigger confetti
    createConfetti();
    
    // Close button
    const closeBtn = toast.querySelector('.achievement-toast-close');
    closeBtn.addEventListener('click', () => {
        closeAchievementToast(toast, achievement.achievement_key);
    });
    
    // Auto-close after 5 seconds
    setTimeout(() => {
        closeAchievementToast(toast, achievement.achievement_key);
    }, 5000);
}

// Close achievement toast and mark as viewed in database
async function closeAchievementToast(toast, achievementKey) {
    toast.style.animation = 'toastSlideOut 0.3s ease';
    
    // Mark as viewed in database - this syncs across all devices/browsers
    try {
        await fetch('/api/achievements/mark-viewed', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ achievement_keys: [achievementKey] })
        });
        
        // Update badge count
        loadCurrentUser();
    } catch (error) {
        console.error('Error marking achievement as viewed:', error);
    }
    
    setTimeout(() => toast.remove(), 300);
}

// Create confetti animation
function createConfetti() {
    const colors = ['#FFD700', '#FFA500', '#FF6347', '#4CAF50', '#2196F3', '#9C27B0'];
    const confettiCount = 30;
    
    for (let i = 0; i < confettiCount; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'confetti';
        confetti.style.left = Math.random() * 100 + 'vw';
        confetti.style.background = colors[Math.floor(Math.random() * colors.length)];
        confetti.style.animationDelay = Math.random() * 0.3 + 's';
        confetti.style.animationDuration = (Math.random() * 2 + 2) + 's';
        
        document.body.appendChild(confetti);
        
        setTimeout(() => confetti.remove(), 4000);
    }
}

// User badge dropdown toggle
document.addEventListener('DOMContentLoaded', () => {
    const userBadge = document.getElementById('userBadge');
    const userDropdown = document.getElementById('userDropdown');
    
    if (userBadge && userDropdown) {
        userBadge.addEventListener('click', (e) => {
            e.stopPropagation();
            userDropdown.classList.toggle('show');
        });
        
        document.addEventListener('click', () => {
            userDropdown.classList.remove('show');
        });
    }
    
    // Load current user on page load
    loadCurrentUser();
    
    // Always check for new achievements on page load to update badge, but only show toasts once per session
    checkNewAchievements();
});

// ==================== PWA Install Prompt ====================

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
                    
                    // Check for new achievements
                    if (data.new_achievements && data.new_achievements.length > 0) {
                        for (const achievement of data.new_achievements) {
                            setTimeout(() => showAchievementToast(achievement), 300);
                        }
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

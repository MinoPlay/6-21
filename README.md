# 21-Day Habit Tracker 🎯

A mobile-first Progressive Web App (PWA) for tracking 6 habits over 21 days. Built with Flask and designed for optimal mobile experience.

## Features ✨

- **6 Habit Tracking**: Set up and track 6 custom habits
- **21-Day Challenge**: Complete tracking over 21 days
- **Mobile-First Design**: Optimized for mobile phones with 44px touch targets
- **Daily View**: Easy checkbox interface for marking habits complete/incomplete
- **Date Navigation**: Navigate between dates with arrows, date picker, or swipe gestures
- **Statistics Dashboard**: 
  - Current and longest streaks
  - Completion rates per habit
  - Overall progress tracking
  - Best/worst performing habits
  - Day-of-week analysis
- **21-Day Calendar**: Visual overview of all habits across the challenge period
- **Data Export**: Export all data to JSON for backup
- **PWA Support**: Install to home screen, works offline
- **Animations**: Smooth checkbox animations and celebration effects
- **Keyboard Shortcuts**: Arrow keys for navigation, 'T' to jump to today

## Technology Stack 🛠️

- **Backend**: Flask 3.0 + Flask-SQLAlchemy
- **Database**: SQLite (easily migrates to PostgreSQL)
- **Frontend**: HTML5 + CSS3 (Vanilla JavaScript)
- **PWA**: Service Worker for offline support

## Installation 📦

1. **Clone or download** this repository

2. **Install dependencies**:
```powershell
pip install -r requirements.txt
```

3. **Run the application**:
```powershell
python run.py
```

4. **Open in browser**:
```
http://localhost:5000
```

## Usage 📱

### First Time Setup

1. Navigate to http://localhost:5000
2. You'll be redirected to the Setup page
3. Enter your 6 habits you want to track
4. Click "Start Tracking"

### Daily Usage

1. Open the app (or visit the home page)
2. Check off completed habits for the day
3. Use navigation arrows or swipe to change dates
4. View your progress on the Stats page
5. See the full 21-day overview in Calendar view

### Export Data

1. Go to Setup or Stats page
2. Click "Export Data (JSON)"
3. Your data will download as a JSON file

### Reset Challenge

1. Go to Setup page
2. Click "Reset Challenge"
3. This keeps your habits but clears all completion data

## Mobile Installation 📲

When you visit the site on your mobile phone:

1. A prompt will appear asking to install the app
2. Click "Install" to add it to your home screen
3. The app will work offline once installed!

**iOS Safari**: Tap Share → Add to Home Screen
**Android Chrome**: Tap Menu → Install App

## Project Structure 📁

```
6-21/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── models.py            # Database models
│   ├── routes.py            # API routes and views
│   ├── utils.py             # Statistics calculations
│   ├── static/
│   │   ├── css/
│   │   │   └── main.css     # Mobile-first styles
│   │   ├── js/
│   │   │   └── app.js       # JavaScript interactivity
│   │   ├── icons/           # PWA icons
│   │   └── service-worker.js
│   └── templates/
│       ├── base.html        # Base template
│       ├── index.html       # Daily tracking view
│       ├── setup.html       # Habit setup form
│       ├── stats.html       # Statistics dashboard
│       └── calendar.html    # 21-day calendar
├── config.py                # Configuration
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
└── habits.db               # SQLite database (created on first run)
```

## Data Storage 💾

### SQLite (Default)

- Simple, zero-configuration setup
- Single file database (`habits.db`)
- Perfect for personal use
- Easy to backup (just copy the file)

### Migrate to PostgreSQL (Optional)

To use PostgreSQL instead:

1. Install PostgreSQL
2. Create a database
3. Set environment variable:
```powershell
$env:DATABASE_URL="postgresql://user:password@localhost/habitdb"
```
4. Run the app (tables will be created automatically)

**Note**: No code changes needed! Flask-SQLAlchemy handles both.

## Features in Detail 🔍

### Statistics Tracked

- **Current Streak**: Consecutive days from today backwards
- **Longest Streak**: Best streak ever achieved
- **Completion Rate**: Percentage of days completed
- **Best Day of Week**: Which weekday has highest completion
- **Overall Progress**: Total habits completed vs possible

### Mobile Optimizations

- Viewport meta tags for proper mobile rendering
- 44×44px minimum touch targets (iOS/Android guidelines)
- Swipe gestures for date navigation
- Prevent double-tap zoom
- Touch-friendly checkbox animations
- Responsive grid layouts
- Fast loading (<3 seconds on 3G)

### Offline Support

- Service Worker caches all pages
- Works offline after first visit
- Automatic sync when back online
- Install prompt for home screen

## Keyboard Shortcuts ⌨️

- **←/→**: Navigate between dates
- **T**: Jump to today
- **Numbers 1-6**: Quick select habits (on desktop)

## Browser Support 🌐

- ✅ Chrome/Edge (Desktop & Mobile)
- ✅ Firefox (Desktop & Mobile)
- ✅ Safari (Desktop & iOS)
- ✅ Samsung Internet
- ✅ Opera

## Future Enhancements 🚀

Potential features to add:

- [ ] User authentication for multi-user support
- [ ] Habit reminders/notifications
- [ ] Custom challenge duration (7, 14, 30, 90 days)
- [ ] Habit notes/journaling
- [ ] Dark mode
- [ ] Data visualization charts (Chart.js)
- [ ] Import data from JSON
- [ ] Habit categories/tags
- [ ] Social sharing
- [ ] Streak rewards/badges

## Troubleshooting 🔧

### Port Already in Use

If port 5000 is taken:
```powershell
# In run.py, change:
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Database Errors

Delete `habits.db` and restart:
```powershell
rm habits.db
python run.py
```

### Service Worker Not Updating

Clear browser cache:
- Chrome: DevTools → Application → Clear Storage
- Firefox: DevTools → Storage → Clear All
- Safari: Develop → Empty Caches

## License 📄

MIT License - Feel free to use and modify!

## Contributing 🤝

Contributions welcome! Feel free to:
- Report bugs
- Suggest features
- Submit pull requests
- Improve documentation

## Author ✍️

Built with Flask and ❤️ for habit tracking enthusiasts!

---

**Happy Habit Tracking! 🎉**

Remember: It takes 21 days to form a habit. You've got this! 💪

# Deploying to PythonAnywhere

## Step-by-Step Deployment Guide

### 1. Upload Your Files

**Option A: Using Git (Recommended)**
1. Log in to PythonAnywhere
2. Open a Bash console (from Dashboard)
3. Clone or upload your project:
   ```bash
   git clone <your-repo-url>
   # OR if no git repo, upload files manually (see Option B)
   ```

**Option B: Manual Upload**
1. On PythonAnywhere Dashboard, go to **Files** tab
2. Create directory: `/home/yourusername/6-21`
3. Upload all files:
   - `app/` folder (all files inside)
   - `config.py`
   - `run.py`
   - `requirements.txt`

### 2. Install Dependencies

1. Go to **Consoles** tab → Start a **Bash console**
2. Navigate to your project:
   ```bash
   cd ~/6-21
   ```
3. Create a virtual environment:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 habittracker
   ```
4. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

### 3. Configure Web App

1. Go to **Web** tab
2. Click **Add a new web app**
3. Choose **Manual configuration** (NOT Flask!)
4. Select **Python 3.10**

### 4. Edit WSGI Configuration File

1. On the Web tab, find **WSGI configuration file** link (e.g., `/var/www/yourusername_pythonanywhere_com_wsgi.py`)
2. Click to edit
3. **Delete all content** and replace with this:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/6-21'  # CHANGE 'yourusername' to your actual username
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variable for production
os.environ['DATABASE_URL'] = 'sqlite:////home/yourusername/6-21/habits.db'  # CHANGE 'yourusername'

# Import Flask app
from app import create_app
application = create_app()
```

**Important**: Replace `yourusername` with your actual PythonAnywhere username (appears in the path)

### 5. Configure Virtual Environment

1. Still on the **Web** tab, scroll to **Virtualenv** section
2. Enter the path to your virtualenv:
   ```
   /home/yourusername/.virtualenvs/habittracker
   ```
   (Replace `yourusername` with your actual username)

### 6. Set Static Files

1. On the **Web** tab, scroll to **Static files** section
2. Add a new mapping:
   - **URL**: `/static/`
   - **Directory**: `/home/yourusername/6-21/app/static`

### 7. Initialize Database

1. Go back to your **Bash console**
2. Activate virtualenv:
   ```bash
   workon habittracker
   ```
3. Navigate to project:
   ```bash
   cd ~/6-21
   ```
4. Initialize database:
   ```bash
   python
   ```
   Then in Python shell:
   ```python
   from app import create_app, db
   app = create_app()
   with app.app_context():
       db.create_all()
   exit()
   ```

### 8. Reload Web App

1. Go back to **Web** tab
2. Click the big green **Reload** button
3. Your app should now be live at: `https://yourusername.pythonanywhere.com`

## Troubleshooting

### Check Error Log
If the site doesn't work:
1. Go to **Web** tab
2. Scroll to **Log files**
3. Click **Error log** to see what went wrong

### Common Issues

**Import Error**: Check that all paths in WSGI file use your correct username

**Database Error**: Make sure you ran `db.create_all()` in the bash console

**Static Files Not Loading**: Verify the static files path is correct

**500 Error**: Check error log for details, usually a typo in WSGI file

### Update Your App Later

When you make changes:
1. Upload new files (via Files tab or git pull)
2. Go to Web tab → click **Reload**

## Free Account Limitations

- Your app URL will be: `yourusername.pythonanywhere.com`
- App expires after 3 months (you'll get email reminder to extend)
- Limited CPU/bandwidth (plenty for personal use)
- Always-on tasks not available on free tier

## Testing

After deployment:
1. Visit your app URL
2. Go through setup to create 6 habits
3. Test on your phone's browser
4. Add to home screen from phone for PWA experience

## Backup Your Data

Since you're on free tier:
1. Regularly export JSON (from Setup or Stats page)
2. Download the `habits.db` file from Files tab as backup

---

Your habit tracker will be accessible from anywhere at:
**https://yourusername.pythonanywhere.com** 🎉

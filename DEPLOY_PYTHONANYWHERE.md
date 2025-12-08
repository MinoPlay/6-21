# Deploying to PythonAnywhere

This guide will help you deploy your 21-Day Habit Tracker to PythonAnywhere's free tier.

## Prerequisites

- A [PythonAnywhere](https://www.pythonanywhere.com) account (free tier works fine)
- Your code pushed to GitHub

## Step-by-Step Deployment

### 1. Create a PythonAnywhere Account

1. Go to [https://www.pythonanywhere.com](https://www.pythonanywhere.com)
2. Sign up for a free Beginner account
3. Confirm your email address

### 2. Clone Your Repository

1. Open a **Bash console** from the PythonAnywhere dashboard
2. Clone your repository:
   ```bash
   git clone https://github.com/MinoPlay/6-21.git
   cd 6-21
   ```

### 3. Create a Virtual Environment

```bash
mkvirtualenv --python=/usr/bin/python3.10 habittracker
pip install -r requirements.txt
```

### 4. Set Up the Database

```bash
python run.py
```

Press `Ctrl+C` after it starts (this initializes the database).

### 5. Configure the Web App

1. Go to the **Web** tab in PythonAnywhere dashboard
2. Click **Add a new web app**
3. Choose **Manual configuration**
4. Select **Python 3.10**

### 6. Configure WSGI File

1. In the Web tab, click on the **WSGI configuration file** link
2. Delete all content and replace with:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/YOUR_USERNAME/6-21'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# Set environment variables
os.environ['DATABASE_URL'] = 'sqlite:////home/YOUR_USERNAME/6-21/habits.db'

# Import the Flask app
from run import app as application
```

**Important:** Replace `YOUR_USERNAME` with your actual PythonAnywhere username in both places.

### 7. Configure Virtual Environment

1. In the Web tab, find the **Virtualenv** section
2. Enter the path to your virtual environment:
   ```
   /home/YOUR_USERNAME/.virtualenvs/habittracker
   ```
   Replace `YOUR_USERNAME` with your actual username.

### 8. Set Static Files

In the Web tab, add a static files mapping:

| URL          | Directory                                    |
|--------------|----------------------------------------------|
| `/static/`   | `/home/YOUR_USERNAME/6-21/app/static/`      |

Replace `YOUR_USERNAME` with your actual username.

### 9. Reload Your Web App

1. Scroll to the top of the Web tab
2. Click the green **Reload** button
3. Your app should now be live at `https://YOUR_USERNAME.pythonanywhere.com`

## Updating Your App

When you make changes to your code:

1. Open a Bash console
2. Navigate to your project:
   ```bash
   cd ~/6-21
   git pull
   ```
3. If you updated dependencies:
   ```bash
   workon habittracker
   pip install -r requirements.txt
   ```
4. Go to the Web tab and click **Reload**

## Troubleshooting

### Check Error Logs

If your app doesn't work:
1. Go to the Web tab
2. Check the **Error log** and **Server log** links at the bottom
3. Look for error messages

### Common Issues

**Import Error**: Make sure the WSGI file path matches your actual username and project location.

**Database Error**: Ensure the database file path in the WSGI configuration is correct and the file has write permissions:
```bash
chmod 644 ~/6-21/habits.db
```

**Static Files Not Loading**: Verify the static files mapping in the Web tab is correct.

**Module Not Found**: Make sure you're using the correct virtual environment and all dependencies are installed:
```bash
workon habittracker
pip install -r requirements.txt
```

## Free Tier Limitations

- Your app URL will be `https://YOUR_USERNAME.pythonanywhere.com`
- Only HTTPS connections to whitelisted sites
- Apps sleep after inactivity (wakes up on first request)
- 512 MB disk space
- 100 seconds of CPU time per day

## Custom Domain (Paid Plans Only)

To use a custom domain, you'll need to upgrade to a paid plan. See [PythonAnywhere's documentation](https://help.pythonanywhere.com/pages/CustomDomains) for details.

## Security Considerations

For production use, consider:
1. Setting a secret key in `config.py`:
   ```python
   SECRET_KEY = 'your-secret-key-here'
   ```
2. Using environment variables for sensitive data
3. Enabling HTTPS (included by default on PythonAnywhere)

## Support

- [PythonAnywhere Forums](https://www.pythonanywhere.com/forums/)
- [PythonAnywhere Help](https://help.pythonanywhere.com/)

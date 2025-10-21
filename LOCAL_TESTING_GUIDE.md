# 🧪 Complete Local Testing Guide
## Full Messenger Bot Testing with Database + ngrok

---

## Prerequisites

- ✅ Python 3.13 installed
- ✅ MySQL Server installed (XAMPP, MySQL Workbench, or standalone)
- ✅ ngrok.exe (already in your project)
- ✅ Facebook Developer Account

---

## Step 1: Set Up Local MySQL Database

### Option A: Using XAMPP (Easiest)

1. **Download and Install XAMPP**
   - Download from: https://www.apachefriends.org/
   - Install and start **MySQL** service

2. **Access phpMyAdmin**
   - Go to: http://localhost/phpmyadmin
   - Username: `root`
   - Password: (leave empty)

3. **Create Database**
   ```sql
   CREATE DATABASE quicksell_chatbot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

4. **Import Schema**
   - Click on `quicksell_chatbot` database
   - Click **Import** tab
   - Choose file: `database/quicksell_complete_v2.sql`
   - Click **Go**

### Option B: Using MySQL Command Line

```bash
# Login to MySQL
mysql -u root -p

# Create database
CREATE DATABASE quicksell_chatbot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Exit MySQL
exit

# Import schema
mysql -u root -p quicksell_chatbot < database/quicksell_complete_v2.sql
```

---

## Step 2: Configure Environment Variables

1. **Copy the example environment file**
   ```bash
   copy .env.example .env
   ```

2. **Edit `.env` file** with your settings:
   ```env
   # Database (Local)
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=
   DB_NAME=quicksell_chatbot

   # Facebook Messenger
   PAGE_ACCESS_TOKEN=your_facebook_page_access_token
   VERIFY_TOKEN=my_secret_token

   # Server
   PORT=5000
   FLASK_ENV=development
   ```

3. **Get Facebook Page Access Token**
   - Go to: https://developers.facebook.com/
   - Your App → Messenger → Settings
   - Under "Access Tokens", generate token
   - Copy and paste into `.env`

---

## Step 3: Re-enable Admin Routes (for local testing)

**Edit `app.py` (lines 18-21):**

**Change FROM:**
```python
# Register admin blueprint (temporarily disabled for testing)
# TODO: Re-enable after database is configured
# from admin_routes import admin_bp
# app.register_blueprint(admin_bp)
```

**Change TO:**
```python
# Register admin blueprint
from admin_routes import admin_bp
app.register_blueprint(admin_bp)
```

---

## Step 4: Install Dependencies

```bash
# Create virtual environment (if not exists)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Step 5: Start Your Local Server

```bash
# Make sure venv is activated
.\venv\Scripts\activate

# Run the app
python app.py
```

**Expected Output:**
```
✅ Database pool created successfully
✅ NLP model loaded successfully (or warning if not found - OK)
🚀 Starting QuickSell Bot on port 5000
 * Running on http://0.0.0.0:5000
```

---

## Step 6: Expose with ngrok

**Open a NEW terminal/PowerShell window:**

```bash
# Navigate to your project
cd C:\Users\erong\OneDrive\Documents\automation_bot

# Run ngrok
.\ngrok.exe http 5000
```

**Expected Output:**
```
ngrok

Session Status                online
Account                       Your Name (Plan: Free)
Region                        United States (us)
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:5000
```

**⚠️ IMPORTANT: Copy the `https://` URL (e.g., `https://abc123.ngrok-free.app`)**

---

## Step 7: Configure Facebook Webhook

1. **Go to Facebook Developer Console**
   - https://developers.facebook.com/

2. **Your App → Messenger → Settings → Webhooks**

3. **Click "Edit" or "Add Callback URL"**
   - **Callback URL**: `https://abc123.ngrok-free.app/webhook` (use YOUR ngrok URL)
   - **Verify Token**: `my_secret_token`
   - **Subscription Fields**: Check `messages`, `messaging_postbacks`

4. **Click "Verify and Save"**
   - Should see "Complete" ✅

5. **Subscribe to Page**
   - Select your Facebook Page
   - Click "Subscribe"

---

## Step 8: Test Your Bot!

### Method 1: Send Message on Facebook

1. Go to your Facebook Page
2. Click "Send Message"
3. Type "hi" or "hello"
4. Bot should respond!

### Method 2: Check Terminal Logs

**In your app terminal, you should see:**
```
📩 Received webhook data
✅ New user created: 123456789
Sending message to 123456789
```

**In ngrok terminal, you should see:**
```
HTTP Requests
-------------
POST /webhook    200 OK
```

---

## 🎯 Testing Checklist

- [ ] MySQL database running (check phpMyAdmin or MySQL Workbench)
- [ ] `.env` file configured with correct credentials
- [ ] `python app.py` running without errors
- [ ] ngrok running and showing HTTPS URL
- [ ] Facebook webhook verified ✅
- [ ] Page subscribed to webhook
- [ ] Test message sent and bot responds

---

## 🐛 Troubleshooting

### Issue: "Can't connect to MySQL server"
**Solution:**
- Make sure XAMPP/MySQL is running
- Check `DB_HOST=localhost` in `.env`
- Check `DB_USER` and `DB_PASSWORD` are correct

### Issue: "Webhook verification failed"
**Solution:**
- Check `VERIFY_TOKEN=my_secret_token` matches in both `.env` and Facebook
- Make sure ngrok URL is correct (include `/webhook` at the end)
- Try regenerating ngrok URL

### Issue: "Bot doesn't respond"
**Solution:**
- Check app terminal for errors
- Check ngrok terminal for incoming requests
- Verify Facebook Page is subscribed to webhook
- Check `PAGE_ACCESS_TOKEN` in `.env` is correct

### Issue: "Module not found" errors
**Solution:**
```bash
# Make sure venv is activated
.\venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## 📝 Summary

**Local Testing Flow:**
```
MySQL Running (localhost:3306)
         ↓
Python App Running (localhost:5000)
         ↓
ngrok Tunnel (https://abc123.ngrok-free.app)
         ↓
Facebook Webhook → Your Bot
         ↓
Test Messages Work! 🎉
```

**Production Flow (Render - No ngrok needed):**
```
Render Deploy (automation-bot-5bho.onrender.com)
         ↓
External Database (PlanetScale/Railway/Render PostgreSQL)
         ↓
Facebook Webhook → Your Bot
```

---

## ⚡ Quick Start Commands

```bash
# Terminal 1: Start MySQL (if using standalone)
# Or just start XAMPP Control Panel → Start MySQL

# Terminal 2: Run app
.\venv\Scripts\activate
python app.py

# Terminal 3: Run ngrok
.\ngrok.exe http 5000

# Then update Facebook webhook with ngrok URL
```

---

## 🎓 Tips

1. **ngrok URL changes** every time you restart it (free plan)
   - You'll need to update Facebook webhook each time
   - Consider ngrok paid plan for static URLs

2. **Keep terminals open**
   - Don't close app or ngrok terminals while testing

3. **Database changes**
   - Any changes to local DB stay local
   - Production uses different database

4. **Environment separation**
   - Local: `.env` file
   - Render: Environment variables in dashboard

---

Good luck with testing! 🚀

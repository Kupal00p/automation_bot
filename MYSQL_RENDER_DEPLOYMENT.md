# MySQL + Aiven + Render Deployment Guide

## ✅ Current Status

Your app is configured to use **MySQL on Aiven** with **Python 3.13** compatibility.

### What's Fixed:
- ✅ Python 3.13 compatible packages (pandas, Pillow, cryptography, etc.)
- ✅ MySQL configuration with SSL support
- ✅ All service files use MySQL syntax
- ✅ Keep-alive URL updated to current deployment

---

## 🚀 Deployment Steps

### Step 1: Set Render Environment Variables

From your Aiven screenshot, set these variables in Render:

**Go to Render Dashboard → Your Service → Environment → Add:**

```bash
# MySQL Database (Aiven)
# Get these values from your Aiven Console
DB_HOST=mysql-1c3f5577-automationbot-5abf.i.aivencloud.com
DB_PORT=25620
DB_USER=avnadmin
DB_PASSWORD=YOUR_AIVEN_PASSWORD_HERE
DB_NAME=defaultdb
DB_SSL=true

# Facebook Messenger
VERIFY_TOKEN=my_secret_token
PAGE_ACCESS_TOKEN=EAASk3ZAn0F6EBPo6jpVVtjdC9wW7qDqZBShDZCbbh5tWOGf8MXdssgu9dftyOVGOZBlGuM9A0kmRN8lt1ByilPWcE90MZBJ5S0LKbZARTLcJdafztIOGtAjGmFWyxAqyTPIhU4aLNrl3aEUm5YTlORMOZApMb3noz6ZBAH5NZA49jfwy2pZBmDGIYV4h4aCTNsMMde4kN1MgZDZD

# Optional
SECRET_KEY=your-random-secret-key-change-this
LOG_LEVEL=INFO
FLASK_ENV=production
```

### Step 2: Set Up Database Tables

You already have MySQL database files. Run one of these on your Aiven MySQL:

**Option A: Using MySQL Client**
```bash
mysql -h mysql-1c3f5577-automationbot-5abf.l.aivencloud.com \
  -P 25620 \
  -u avnadmin \
  -p \
  --ssl-mode=REQUIRED \
  defaultdb < database/quicksell_complete_v2.sql
```

**Option B: Using Aiven Console**
1. Go to Aiven Console → Your MySQL Database
2. Click "Query Editor"
3. Copy contents from `database/quicksell_complete_v2.sql`
4. Adjust the first lines (remove `DROP DATABASE` and `CREATE DATABASE`)
5. Execute the SQL

**Important:** Since Aiven gives you a pre-created database (`defaultdb`), remove these lines from the SQL:
```sql
DROP DATABASE IF EXISTS quicksell_chatbot;
CREATE DATABASE quicksell_chatbot CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE quicksell_chatbot;
```

Just run the table creation scripts directly on `defaultdb`.

### Step 3: Deploy to Render

```bash
git add .
git commit -m "Keep MySQL, fix Python 3.13 compatibility"
git push origin main
```

Render will automatically:
1. Pull latest changes
2. Build with Python 3.13
3. Install MySQL connector 9.1.0
4. Start gunicorn

---

## ✅ Expected Logs

After deployment, Render logs should show:

```
==> Installing Python version 3.13.4...
==> Running build command 'pip install -r requirements.txt'...
Collecting mysql-connector-python==9.1.0
...
✅ Database pool created successfully
✅ Starting gunicorn 21.2.0
✅ Listening at: http://0.0.0.0:10000
==> Your service is live 🎉
```

---

## 📦 Updated Packages for Python 3.13

These packages were updated to support Python 3.13:

| Package | Old Version | New Version |
|---------|------------|-------------|
| mysql-connector-python | 8.2.0 | 9.1.0 |
| PyMySQL | 1.1.0 | 1.1.1 |
| pandas | 2.1.4 | 2.2.3 |
| Pillow | 10.1.0 | 10.4.0 |
| cryptography | 41.0.7 | 43.0.0 |
| bcrypt | 5.0.0 | 4.2.0 |
| pytest | 7.4.3 | 8.3.0 |
| pytest-cov | 4.1.0 | 5.0.0 |
| flake8 | 6.1.0 | 7.1.0 |
| black | 23.12.1 | 24.8.0 |

---

## 🔍 Verify Database Connection

After deployment, you can test the database connection:

```bash
curl https://automation-bot-wbsx.onrender.com/
```

Check Render logs - you should see:
- ✅ Database pool created successfully
- No connection errors

---

## 🐛 Troubleshooting

### Error: "Can't connect to MySQL server"

**Check:**
1. Environment variables set correctly on Render?
2. Password copied correctly from Aiven Console (no typos)?
3. DB_SSL=true is set?
4. Aiven MySQL database is running?

### Error: "Access denied for user"

**Solution:**
- Double-check the password in Render environment variables
- Make sure user is `avnadmin`
- Verify from Aiven console

### Error: Table doesn't exist

**Solution:**
- Run the SQL schema on your Aiven database
- Make sure you're using `defaultdb` database

---

## 🔒 SSL/TLS Connection

Aiven MySQL requires SSL. The configuration already includes:

```python
"ssl_disabled": False if os.getenv("DB_SSL", "true").lower() == "true" else True
```

This ensures SSL is enabled when `DB_SSL=true` is set.

---

## 📊 Your Current Setup

- **Platform**: Render
- **Database**: Aiven MySQL 
- **Python**: 3.13.4
- **Web Server**: Gunicorn
- **Framework**: Flask 3.0.0
- **Connection**: SSL/TLS encrypted

---

## 🎉 Ready to Deploy!

1. ✅ Set environment variables on Render
2. ✅ Run SQL schema on Aiven MySQL
3. ✅ Commit and push changes
4. ✅ Watch deployment succeed!

Your app will be live at: `https://automation-bot-wbsx.onrender.com` 🚀

# 🚀 Render Database Configuration Guide

## Current Status
✅ **Your app is deployed and running**  
⚠️ **Database connection needs configuration**

## Option 1: Use Render PostgreSQL (Recommended)

### Step 1: Create PostgreSQL Database on Render
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `automation-bot-db`
   - **Database**: `automation_bot`
   - **User**: (auto-generated)
   - **Region**: Same as your web service
   - **Plan**: Free (or paid for production)
4. Click **"Create Database"**
5. Wait for database to be created (takes ~2 minutes)

### Step 2: Get Database Connection Details
After creation, Render will show:
- **Internal Database URL** (use this for web services on Render)
- **External Database URL** (use this for external connections)
- **PSQL Command** (for manual access)

### Step 3: Update Your Code for PostgreSQL
You'll need to:
1. Replace `mysql-connector-python` with `psycopg2` in `requirements.txt`
2. Update `services/db_service.py` to use PostgreSQL syntax
3. Update `config.py` to parse PostgreSQL connection URL

### Step 4: Set Environment Variables on Render
1. Go to your web service: `automation-bot-5bho`
2. Click **"Environment"** tab
3. Add these variables:
   ```
   DATABASE_URL=<paste Internal Database URL from Step 2>
   ```

---

## Option 2: Use External MySQL Database (Your Current Setup)

If you want to keep using MySQL, you need to host it externally:

### Recommended MySQL Hosting Options:
1. **PlanetScale** (Free tier available)
   - Visit: https://planetscale.com/
   - Create database
   - Get connection details

2. **Railway** (MySQL/PostgreSQL)
   - Visit: https://railway.app/
   - Add MySQL plugin
   - Get connection details

3. **Aiven** (Free tier available)
   - Visit: https://aiven.io/
   - Create MySQL service
   - Get connection details

### Configure Environment Variables for MySQL:
1. Go to your Render web service: `automation-bot-5bho`
2. Click **"Environment"** tab
3. Add these variables:
   ```
   DB_HOST=<your-mysql-host>
   DB_PORT=3306
   DB_USER=<your-mysql-username>
   DB_PASSWORD=<your-mysql-password>
   DB_NAME=quicksell_chatbot
   ```

### Important: Import Your Database Schema
After setting up your database, you need to import your schema:
- Find your SQL schema file in the `database/` folder
- Execute it on your hosted database
- Most services provide web-based SQL editors or CLI access

---

## Option 3: Skip Database (Temporary Solution)

If you want to test the app without a database first:

### Update `config.py` to Handle Missing Database:
I can modify the code to gracefully handle database connection failures and use in-memory fallbacks for testing.

---

## Which Option Do You Prefer?

Please let me know:
1. **PostgreSQL on Render** - Most integrated, but requires code changes
2. **External MySQL** - Keeps current code, but needs external service
3. **Skip Database** - Temporary solution for testing

I can help implement whichever option you choose!

---

## Other Environment Variables to Set

Don't forget to also set these in Render:

```
# Facebook Messenger (from your .env.example)
PAGE_ACCESS_TOKEN=<your-facebook-page-access-token>
VERIFY_TOKEN=my_secret_token

# Optional but recommended
SECRET_KEY=<generate-random-secret-key>
FLASK_ENV=production
```

---

## Quick Commands Reference

### To test database connection locally:
```bash
# Create .env file first
cp .env.example .env
# Edit .env with your database credentials

# Run locally
python app.py
```

### To view Render logs:
```bash
# From Render Dashboard > Your Service > Logs
# Or use Render CLI
render logs automation-bot-5bho
```

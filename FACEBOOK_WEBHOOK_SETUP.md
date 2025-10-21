# 🔗 Facebook Messenger Webhook Setup Guide

## Current Issue: Bot Not Responding
**Cause:** Facebook webhook is not properly configured or verified

---

## Step-by-Step Setup

### Step 1: Check Your Render URL

Your app is live at: **https://automation-bot-xn9m.onrender.com**

Test it works:
```
Open browser: https://automation-bot-xn9m.onrender.com/health

Should show:
{
  "status": "healthy",
  "bot": "running",
  "database": "not_configured"
}
```

---

### Step 2: Get Your Facebook Page Access Token

1. **Go to Facebook Developer Console**
   - https://developers.facebook.com/apps/

2. **Select Your App** (or create one if you don't have it)

3. **Add Messenger Product** (if not added)
   - Left sidebar → **Add Product** → Find **Messenger** → Click **Set Up**

4. **Generate Page Access Token**
   - Scroll to **Access Tokens** section
   - Select your Facebook Page from dropdown
   - Click **Generate Token**
   - **COPY THIS TOKEN** - you'll need it

5. **Save Token to Render**
   - Go to Render Dashboard: https://dashboard.render.com/
   - Select service: `automation-bot-xn9m`
   - Click **Environment** tab
   - Add new variable:
     ```
     Key: PAGE_ACCESS_TOKEN
     Value: <paste your token here>
     ```
   - Click **Save Changes** (Render will redeploy - wait 2 minutes)

---

### Step 3: Configure Webhook on Facebook

1. **Still in Facebook Developer Console**
   - Your App → Messenger → Settings

2. **Scroll to "Webhooks" section**

3. **Click "Add Callback URL"** or **"Edit"** if already exists

4. **Enter Details:**
   ```
   Callback URL: https://automation-bot-xn9m.onrender.com/webhook
   Verify Token: my_secret_token
   ```
   ⚠️ **IMPORTANT:** Make sure URL has `/webhook` at the end!

5. **Click "Verify and Save"**
   - Should see green checkmark ✅
   - If it fails, check:
     - URL is exactly: `https://automation-bot-xn9m.onrender.com/webhook`
     - Verify token is exactly: `my_secret_token`
     - Your Render app is running (check logs)

6. **Subscribe to Webhook Fields**
   - After verification, you'll see subscription fields
   - Check these boxes:
     - ✅ **messages**
     - ✅ **messaging_postbacks**
     - ✅ **messaging_optins** (optional)
     - ✅ **message_deliveries** (optional)
   - Click **Save**

---

### Step 4: Subscribe Your Page

1. **Still in Webhooks section**
   - Scroll down to **"Select a Page"**
   - Choose your Facebook Page from dropdown
   - Click **Subscribe**
   - Should see "Subscribed" ✅

---

### Step 5: Test Your Bot!

1. **Go to Your Facebook Page**

2. **Click "Send Message"** button

3. **Type "hi"** and send

4. **Bot should respond!**

---

## 🐛 Troubleshooting

### Webhook Verification Fails (❌ Red X)

**Possible causes:**

1. **Wrong URL**
   - Make sure: `https://automation-bot-xn9m.onrender.com/webhook`
   - Don't forget `/webhook` at the end
   - No trailing slash after webhook

2. **Wrong Verify Token**
   - Must be exactly: `my_secret_token`
   - Case-sensitive
   - No extra spaces

3. **App Not Running**
   - Check Render logs
   - Make sure app deployed successfully

4. **Timeout**
   - Render free tier may sleep after inactivity
   - Visit the URL first to wake it up: https://automation-bot-xn9m.onrender.com/
   - Then try verification again

**Test verification manually:**
```bash
# In PowerShell or browser:
https://automation-bot-xn9m.onrender.com/webhook?hub.mode=subscribe&hub.verify_token=my_secret_token&hub.challenge=test123

# Should return: test123
```

---

### Bot Doesn't Respond to Messages

**Check these:**

1. **Webhook Verified?**
   - Green checkmark in Facebook Developer Console ✅

2. **Page Subscribed?**
   - Shows "Subscribed" next to your page name

3. **Access Token Set?**
   - Check Render Environment variables
   - `PAGE_ACCESS_TOKEN` should be set

4. **Check Render Logs**
   - Go to Render Dashboard → Your service → Logs
   - Send a test message
   - Look for: `📩 Received webhook data`
   - If you see this, webhook is working!

5. **Test with curl:**
   ```bash
   curl -X POST https://automation-bot-xn9m.onrender.com/webhook \
     -H "Content-Type: application/json" \
     -d '{
       "object": "page",
       "entry": [{
         "messaging": [{
           "sender": {"id": "test123"},
           "message": {"text": "hello"}
         }]
       }]
     }'
   ```

---

### Error: "PAGE_ACCESS_TOKEN not set"

**Solution:**
1. Generate token in Facebook Developer Console
2. Add to Render Environment variables
3. Wait for Render to redeploy

---

### Messages Received But No Response

**Check:**
1. **Access Token Valid?**
   - Tokens can expire
   - Regenerate in Facebook Developer Console

2. **Page Permissions?**
   - Make sure your app has permission to send messages

3. **Check Logs for Errors**
   - Look for API errors in Render logs

---

## ✅ Success Checklist

- [ ] Render app deployed and running
- [ ] PAGE_ACCESS_TOKEN added to Render environment
- [ ] Webhook URL verified in Facebook (green ✅)
- [ ] Webhook fields subscribed (messages, messaging_postbacks)
- [ ] Facebook Page subscribed to webhook
- [ ] Test message sent from Facebook Page
- [ ] Bot responds to test message
- [ ] Render logs show: `📩 Received webhook data`

---

## 🎯 Quick Test

**Send this message to your bot:**
```
hi
```

**Expected response:**
```
🎉 Welcome to QuickSell!

I'm your personal shopping assistant. I can help you with:
• Browse products
• Place orders
• Track your orders
• Answer your questions

Type 'menu' to see all options or just tell me what you need!
```

---

## 📝 Important Notes

1. **Access Token Security**
   - Never commit tokens to GitHub
   - Only store in Render Environment variables
   - Tokens are sensitive - treat like passwords

2. **Webhook URL**
   - Must be HTTPS (HTTP won't work)
   - Must be publicly accessible
   - Render provides HTTPS automatically

3. **Free Tier Limitations**
   - Render free tier sleeps after inactivity
   - First message may take 30 seconds
   - Subsequent messages are fast

---

Need help? Check Render logs for detailed error messages!

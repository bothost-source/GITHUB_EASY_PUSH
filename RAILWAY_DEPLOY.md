# 🚂 Railway Deployment Guide

## Step-by-Step Deployment

### Step 1: Push Code to GitHub

```bash
# Create a new GitHub repo (e.g., tarrific-host-bot)
# Then push your code:

git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/tarrific-host-bot.git
git push -u origin main
```

### Step 2: Create Railway Account

1. Go to [railway.com](https://railway.com)
2. Sign up with GitHub (easiest)
3. Verify your account

### Step 3: Deploy from GitHub

1. In Railway dashboard, click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your `tarrific-host-bot` repository
4. Railway will auto-detect it's a Python project

### Step 4: Add Environment Variables

Go to your service → **Variables** tab → Add these:

| Variable | Value | Required |
|----------|-------|----------|
| `BOT_TOKEN` | Your Telegram bot token | ✅ Yes |
| `VERCEL_TOKEN` | Your Vercel API token | ⚠️ For Vercel deploy |
| `GITHUB_CLIENT_ID` | GitHub OAuth app ID | ⚠️ For GitHub hosting |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth secret | ⚠️ For GitHub hosting |
| `GITHUB_REDIRECT_URI` | Your callback URL | ⚠️ For GitHub hosting |

**How to add:**
1. Click **"New Variable"**
2. Enter name and value
3. Click **"Add"**
4. Railway auto-redeploys when you add variables

### Step 5: Deploy

Railway automatically deploys when you:
- Push to GitHub
- Add/change variables
- Click "Redeploy"

**Check logs:** Service → Deployments → Click latest deployment → Logs

---

## 📋 Railway Free Tier Limits

| Resource | Free Tier |
|----------|-----------|
| CPU | 1 vCPU |
| RAM | 0.5 GB |
| Disk | 1 GB ephemeral |
| Storage | 0.5 GB volume |
| Uptime | 24/7 (no sleep!) |
| Cost | $0 (30-day trial, then $1/month) |

**Note:** Railway free tier stays on 24/7 unlike Render/Heroku. Perfect for bots!

---

## 🔧 Troubleshooting on Railway

| Problem | Solution |
|---------|----------|
| Bot not responding | Check `BOT_TOKEN` is correct in Variables |
| Playwright not working | Check `railway.json` build command includes playwright install |
| Out of memory | Railway free tier has 0.5GB RAM. Consider upgrading to Hobby ($5/mo) |
| Build fails | Check logs for missing dependencies |
| Database lost | Use Railway's built-in PostgreSQL or SQLite persists in volume |

---

## 🚀 Railway CLI (Optional)

Install Railway CLI for local development:

```bash
# Install
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# Deploy from local
railway up

# View logs
railway logs

# Add variables
railway variables set BOT_TOKEN=your_token_here
```

---

## 🎯 Quick Commands Reference

```bash
# Local testing
python bot.py

# Deploy to Railway
railway up

# View logs
railway logs -f

# SSH into container
railway ssh

# Restart service
railway restart
```

---

## 📸 Screenshots on Railway

Since Railway uses containers, screenshots are saved to ephemeral storage by default. To persist them:

1. **Option A:** Use Railway Volumes (add in dashboard)
2. **Option B:** Upload screenshots to external storage (S3, Supabase Storage)
3. **Option C:** Send screenshots directly via Telegram (already implemented)

The bot already sends screenshots via Telegram messages, so users get them instantly!

---

## 🔄 Auto-Deploy Setup

Railway auto-deploys on every GitHub push. To enable:

1. Go to Project Settings
2. Enable "Auto-deploy on push"
3. Done! Every `git push` triggers a new deployment

---

## 💡 Pro Tips

1. **Use Railway's built-in database** instead of SQLite for production
   - Go to "New" → Database → PostgreSQL or MySQL
   - Railway provides connection string automatically

2. **Monitor usage** in Railway dashboard
   - CPU, RAM, disk usage visible in real-time

3. **Set up alerts** for when bot goes down
   - Railway can send Discord/Slack notifications

4. **Custom domain** (optional)
   - Railway gives you a free `*.railway.app` domain
   - Or add your own custom domain in Settings

---

## 🎉 You're Done!

Your bot should now be running 24/7 on Railway. Test it by messaging your bot on Telegram!

**Next steps:**
- Test all commands: `/start`, `/help`, `/getid`
- Try security tools: `/hash`, `/jwt`, `/scan`
- Set up GitHub/Vercel tokens for hosting features

**Happy deploying! 🚀**

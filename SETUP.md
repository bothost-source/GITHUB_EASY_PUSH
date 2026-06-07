# 🚀 TARRIFIC HOST BOT - Setup Guide

## Quick Start (5 minutes)

### Step 1: Get Telegram Bot Token
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot`
3. Follow prompts to name your bot
4. **Save the token** - you'll need it!

### Step 2: Get Vercel Token (Optional, for deployments)
1. Go to [vercel.com/account/tokens](https://vercel.com/account/tokens)
2. Click "Create Token"
3. Name it "Tarrific Host Bot"
4. **Save the token**

### Step 3: Install Dependencies
```bash
# Clone or download the project
cd tarrific-host

# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers (for screenshots)
playwright install chromium
```

### Step 4: Configure
```bash
# Copy example config
cp .env.example .env

# Edit .env with your tokens
nano .env
```

### Step 5: Run
```bash
python bot.py
```

You should see: `🤖 TARRIFIC HOST Bot started!`

---

## 📸 Screenshot Feature Setup

The screenshot feature uses **Playwright** with Chromium:

```bash
# Install Playwright
pip install playwright

# Download Chromium browser
playwright install chromium
```

**System requirements:**
- Linux: `sudo apt-get install libglib2.0-0 libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2`
- Windows: Works out of the box
- macOS: Works out of the box

---

## 🚀 Vercel Deployment Setup

### Get Vercel Token
1. Log in to [vercel.com](https://vercel.com)
2. Go to Account Settings → Tokens
3. Create new token with scope: `All Projects` or `Specific Projects`

### How Vercel Deployment Works
1. User sends GitHub repo URL to bot
2. Bot creates Vercel project linked to GitHub repo
3. Vercel auto-deploys from GitHub
4. Bot takes screenshot of deployed site
5. Bot sends back:
   - Vercel deployment URL
   - Screenshot image
   - Project details

---

## 🎨 Menu Navigation

```
/start → Main Menu
    ├── 🚀 Host New Site (GitHub Pages)
    ├── 📁 My Hosted Sites
    ├── 🚀 Deploy to Vercel
    ├── 📸 Capture Screenshot
    ├── #️⃣ Hash Tools
    │   ├── Identify Hash
    │   ├── Crack Hash
    │   ├── Generate Hashes
    │   └── Base64 Encode/Decode
    ├── 🔐 JWT Decoder
    ├── 🔌 Port Scanner
    ├── 📡 Header Analyzer
    ├── 🌍 WHOIS & DNS
    │   ├── WHOIS Lookup
    │   ├── DNS Records
    │   └── Subdomain Finder
    ├── 📧 Breach Checker
    ├── 🔑 Password Generator
    ├── 🆔 Get My ID
    ├── ⚙️ Settings
    └── ❓ Help
```

---

## ⚠️ Important Notes

### GitHub Pages Hosting
- Requires GitHub OAuth App setup
- Free tier: 5 sites per user
- Max file size: 25 MB per file
- ZIP must contain `index.html` at root

### Vercel Deployment
- Requires Vercel API token
- Free tier: 100 deployments/day
- Auto-deploys on GitHub push
- Custom domains supported

### Screenshots
- Full-page captures (not just viewport)
- Waits 5 seconds for dynamic content
- Supports JavaScript-heavy sites
- Saved to `screenshots/` folder

### Security Tools
- **For educational/ethical use only**
- Only scan targets you own/have permission to scan
- Port scanner has 2-second timeout per port
- Breach checker requires HIBP API key for full functionality

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Bot not responding | Check BOT_TOKEN is correct |
| Screenshots fail | Run `playwright install chromium` |
| Vercel deploy fails | Check VERCEL_TOKEN is valid |
| Database errors | Delete `tarrific_host.db` to reset |
| GitHub auth fails | Reconnect in Settings menu |

---

## 📝 File Structure

```
tarrific-host/
├── bot.py              ← Main bot (44KB)
├── config.py           ← Menus, constants
├── database.py         ← SQLite handler
├── progress.py         ← ASCII progress bars
├── error_handler.py    ← Error formatting
├── vercel_deploy.py    ← Vercel API
├── screenshot_tool.py  ← Playwright screenshots
├── github_client.py    ← GitHub API (implement)
├── uploader.py         ← ZIP processing (implement)
├── tools/
│   ├── hash_tools.py     ← Hash identify/crack/generate
│   ├── jwt_decoder.py    ← JWT decode/analyze
│   ├── port_scanner.py   ← Port scanning
│   ├── header_analyzer.py← Security headers
│   ├── whois_dns.py      ← WHOIS/DNS/subdomains
│   ├── breach_checker.py ← HIBP breach check
│   └── password_gen.py   ← Secure password gen
├── .env.example        ← Config template
├── requirements.txt    ← Dependencies
└── README.md           ← Documentation
```

---

## 🎯 Next Steps

1. **Test basic commands**: `/start`, `/help`, `/getid`
2. **Try security tools**: `/hash`, `/jwt`, `/scan`
3. **Set up GitHub**: Connect in Settings for hosting
4. **Set up Vercel**: Add token for deployments
5. **Test screenshots**: `/screenshot https://example.com`

---

## 💡 Tips

- Use `/cancel` anytime to abort an operation
- Screenshots are saved locally in `screenshots/` folder
- Database is SQLite - zero setup, zero cost
- All tools log usage for statistics in Settings

**Happy hosting! 🚀**

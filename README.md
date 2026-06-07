# 🤖 TARRIFIC HOST BOT

A Telegram bot for hosting static websites, deploying to Vercel, taking screenshots, and ethical cybersecurity tools.

## Features

### 🚀 Hosting
- Host static websites via GitHub Pages
- Upload ZIP files (preserves folder structure)
- Upload single HTML files
- Real-time progress tracking with ASCII graphics
- Error handling with exact location and messages

### 🚀 Vercel Deployment
- Deploy GitHub repositories directly to Vercel
- Automatic screenshot after deployment
- Get instant Vercel.app URL

### 📸 Screenshots
- Capture full-page screenshots of any website
- Screenshot GitHub repositories
- Screenshot deployed sites (GitHub Pages or Vercel)
- Powered by Playwright (Chromium headless)

### 🛡️ Security Tools
- **#️⃣ Hash Tools**: Identify, crack, generate, Base64
- **🔐 JWT Decoder**: Decode and analyze JWT tokens
- **🔌 Port Scanner**: Scan common ports on targets
- **📡 Header Analyzer**: Check website security headers
- **🌍 WHOIS & DNS**: Domain lookups and subdomain discovery
- **📧 Breach Checker**: Check email against Have I Been Pwned
- **🔑 Password Generator**: Secure passwords with entropy analysis

### 📋 Utilities
- **🆔 Get My ID**: Show your Telegram user info

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure environment variables
Create a `.env` file or set these variables:
```bash
BOT_TOKEN=your_telegram_bot_token
GITHUB_CLIENT_ID=your_github_oauth_client_id
GITHUB_CLIENT_SECRET=your_github_oauth_client_secret
GITHUB_REDIRECT_URI=https://your-domain.com/github/callback
VERCEL_TOKEN=your_vercel_api_token
```

### 3. Run the bot
```bash
python bot.py
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Main menu |
| `/host` | Start new deployment (GitHub Pages) |
| `/sites` | List your sites |
| `/vercel` | Deploy to Vercel |
| `/screenshot` | Capture screenshot |
| `/hash` | Hash tools menu |
| `/jwt` | Decode JWT token |
| `/scan` | Port scanner |
| `/headers` | Analyze headers |
| `/whois` | WHOIS & DNS tools |
| `/breach` | Check email breach |
| `/pass` | Generate password |
| `/getid` | Show your Telegram ID |
| `/settings` | Bot settings |
| `/help` | Help menu |
| `/cancel` | Cancel operation |

## Vercel Deployment

To deploy to Vercel:
1. Get a Vercel token from [vercel.com/account/tokens](https://vercel.com/account/tokens)
2. Add `VERCEL_TOKEN` to your config
3. Send a GitHub repo URL to the bot
4. Bot will deploy and send screenshot

## Screenshot Tool

The bot uses Playwright to capture screenshots:
- Full-page captures (not just viewport)
- Waits for dynamic content to load
- Supports dark mode
- Works with JavaScript-heavy sites

## Progress Display (Option 5 Style)

```
┌─────────────────────────────┐
│  🚀 NEW SITE DEPLOYMENT     │
│                             │
│  Step 3/5                   │
│  [Authenticating]████████████ DONE
│  [Creating Repo ]████████████ DONE
│  [Uploading     ]██████░░░░░░ IN PROGRESS
│  [Enabling Pages]░░░░░░░░░░░░ WAITING
│  [Finalizing    ]░░░░░░░░░░░░ WAITING
│                             │
│  ▰▰▰▱▱▱▱▱▱▱  30%           │
│                             │
│  Current: 📤 Uploading      │
│  12/47 — css/style.css      │
│  (2.4 MB / 18.7 MB total)   │
└─────────────────────────────┘
```

## Error Display

```
┌─────────────────────────────┐
│  ❌ DEPLOYMENT FAILED       │
│                             │
│  ▰▰▰▰▰▰▰▱▱▱  60%           │
│                             │
│  [Authenticating]████████████ DONE
│  [Creating Repo ]████████████ DONE
│  [Uploading     ]██████░░░░░░ FAILED ←
│  [Enabling Pages]░░░░░░░░░░░░ BLOCKED
│  [Finalizing    ]░░░░░░░░░░░░ BLOCKED
│                             │
│  🔴 ERROR at Step 3/5       │
│  Location: Uploading        │
│  File: 12/47 — js/app.js    │
│                             │
│  Message:                   │
│  "File too large (28.5 MB). │
│  GitHub limit is 25 MB."    │
│                             │
│  [🔁 Retry] [⬅️ Back]        │
└─────────────────────────────┘
```

## Database

Uses SQLite (local file) — zero external dependencies, zero cost.

## File Structure

```
tarrific-host/
├── bot.py              # Main entry point
├── config.py           # Configuration
├── database.py         # SQLite handler
├── github_client.py    # GitHub API (to implement)
├── uploader.py         # ZIP processing (to implement)
├── progress.py         # Progress display
├── error_handler.py    # Error formatting
├── vercel_deploy.py    # Vercel deployment
├── screenshot_tool.py  # Screenshot capture
├── tools/
│   ├── hash_tools.py     # Hash tools
│   ├── jwt_decoder.py    # JWT decoder
│   ├── port_scanner.py   # Port scanner
│   ├── header_analyzer.py# Header analyzer
│   ├── whois_dns.py      # WHOIS & DNS
│   ├── breach_checker.py # Breach checker
│   └── password_gen.py   # Password generator
└── requirements.txt
```

## Notes

- **GitHub Pages hosting**: Requires GitHub OAuth setup
- **Vercel deployment**: Requires Vercel API token
- **Screenshots**: Requires Playwright + Chromium
- **ZIP handling**: Preserves exact folder structure, validates `index.html`, checks file sizes
- **Security tools**: For educational/ethical use only

## License

MIT

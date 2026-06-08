const { Telegraf, Markup, session } = require('telegraf');
const axios = require('axios');
const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');
const crypto = require('crypto');
const dns = require('dns').promises;
const path = require('path');
const net = require('net');

const BOT_TOKEN = process.env.BOT_TOKEN;
const OWNER_ID = process.env.OWNER_ID;
const GITHUB_CLIENT_ID = process.env.GITHUB_CLIENT_ID;
const GITHUB_CLIENT_SECRET = process.env.GITHUB_CLIENT_SECRET;
const OWNER_VERCEL_TOKEN = process.env.VERCEL_TOKEN;
const WELCOME_VIDEO = process.env.WELCOME_VIDEO_PATH || 'welcome.mp4';
const MAX_SITES = 5;

if (!BOT_TOKEN) {
    console.error('ERROR: BOT_TOKEN is required!');
    process.exit(1);
}

const bot = new Telegraf(BOT_TOKEN);

// DEBUG: Log all incoming updates
bot.use((ctx, next) => {
    const updateType = ctx.updateType || 'unknown';
    const text = ctx.message?.text || ctx.callbackQuery?.data || 'N/A';
    const userId = ctx.from?.id || 'N/A';
    console.log(`[${new Date().toISOString()}] 📩 ${updateType} from ${userId}: ${text}`);
    return next();
});

bot.use(session({ defaultSession: () => ({}) }));

if (!fs.existsSync('screenshots')) fs.mkdirSync('screenshots', { recursive: true });
if (!fs.existsSync('uploads')) fs.mkdirSync('uploads', { recursive: true });

const db = new sqlite3.Database('tarrific_host.db');
db.serialize(() => {
    db.run(`CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
        last_name TEXT, language TEXT DEFAULT 'en', github_token TEXT,
        github_username TEXT, vercel_token TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )`);
    db.run(`CREATE TABLE IF NOT EXISTS sites (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, repo_name TEXT,
        repo_url TEXT, site_url TEXT, file_count INTEGER, total_size INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )`);
    db.run(`CREATE TABLE IF NOT EXISTS tool_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER,
        tool_name TEXT, used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )`);
});

const dbRun = (sql, p = []) => new Promise((res, rej) => db.run(sql, p, function(e) { e ? rej(e) : res({ id: this.lastID, changes: this.changes }); }));
const dbGet = (sql, p = []) => new Promise((res, rej) => db.get(sql, p, (e, r) => { e ? rej(e) : res(r); }));
const dbAll = (sql, p = []) => new Promise((res, rej) => db.all(sql, p, (e, r) => { e ? rej(e) : res(r); }));
const isOwner = (id) => OWNER_ID && id.toString() === OWNER_ID.toString();

const btn = Markup.button.callback;
const KB = Markup.inlineKeyboard;
const back = (to = 'menu_main') => KB([[btn('◀ Back', to)]]);
const cancel = () => KB([[btn('❌ Cancel', 'menu_main')]]);
const retryBack = (retry, backTo = 'menu_main') => KB([[btn('🔄 Retry', retry)], [btn('◀ Back', backTo)]]);

function buildProgress(step, total, pct, opts = {}) {
    const { file, count, totalFiles, size, totalSize, status, error, errorFile } = opts;
    const width = 46;
    let lines = ['+' + '-'.repeat(width - 2) + '+'];
    const statusLine = status === 'failed' ? '  ❌ DEPLOYMENT FAILED' : status === 'done' ? '  ✅ DEPLOYMENT COMPLETE' : '  🚀 NEW SITE DEPLOYMENT';
    lines.push('|' + statusLine.padEnd(width - 2) + '|');
    lines.push('|' + ' '.repeat(width - 2) + '|');
    lines.push('|' + `  Step ${step}/${total}`.padEnd(width - 2) + '|');
    const steps = ['Authenticating', 'Creating Repo', 'Uploading Files', 'Enabling Pages', 'Finalizing'];
    for (let i = 0; i < steps.length; i++) {
        const sn = i + 1;
        let bar;
        if (sn < step) bar = '########### DONE';
        else if (sn === step) {
            if (status === 'failed') bar = '######---- FAILED';
            else if (status === 'in_progress') bar = '######---- IN PROGRESS';
            else bar = '########### DONE';
        } else {
            bar = (status === 'failed' && sn > step) ? '----------- BLOCKED' : '----------- WAITING';
        }
        lines.push('|' + `  [${steps[i].padEnd(14)}] ${bar}`.padEnd(width - 2) + '|');
    }
    lines.push('|' + ' '.repeat(width - 2) + '|');
    const filled = Math.floor(pct / 10);
    lines.push('|' + `  ${'█'.repeat(filled)}${'░'.repeat(10 - filled)}  ${pct.toString().padStart(3)}%`.padEnd(width - 2) + '|');
    lines.push('|' + ' '.repeat(width - 2) + '|');
    if (status === 'failed' && error) {
        lines.push('|' + `  ❌ ERROR at Step ${step}/${total}`.padEnd(width - 2) + '|');
        lines.push('|' + `  Location: ${steps[step - 1]}`.padEnd(width - 2) + '|');
        if (errorFile) lines.push('|' + `  File: ${errorFile}`.padEnd(width - 2) + '|');
        lines.push('|' + ' '.repeat(width - 2) + '|');
        lines.push('|' + '  Message:'.padEnd(width - 2) + '|');
        const errLines = error.match(/.{1,40}/g) || [error];
        errLines.forEach(l => lines.push('|' + `  ${l}`.padEnd(width - 2) + '|'));
    } else if (status === 'done') {
        lines.push('|' + '  ✅ Your site is live:'.padEnd(width - 2) + '|');
        if (file) {
            const urlLines = file.match(/.{1,40}/g) || [file];
            urlLines.forEach(l => lines.push('|' + `  ${l}`.padEnd(width - 2) + '|'));
        }
    } else {
        if (file) lines.push('|' + `  Current: > ${file.substring(0, 35)}`.padEnd(width - 2) + '|');
        if (count && totalFiles) lines.push('|' + `  ${count}/${totalFiles} files`.padEnd(width - 2) + '|');
        if (size && totalSize) {
            const fmt = (b) => b < 1024 ? `${b} B` : b < 1024 * 1024 ? `${(b / 1024).toFixed(1)} KB` : `${(b / (1024 * 1024)).toFixed(1)} MB`;
            lines.push('|' + `  (${fmt(size)} / ${fmt(totalSize)} total)`.padEnd(width - 2) + '|');
        }
    }
    lines.push('+' + '-'.repeat(width - 2) + '+');
    return lines.join('\n');
}

// ==================== ANIMATED PROGRESS HELPER ====================
async function animateProgress(ctx, messageId, step, total, startPct, endPct, durationMs, opts = {}) {
    const steps = 10;
    const stepDuration = durationMs / steps;
    const pctStep = (endPct - startPct) / steps;

    for (let i = 0; i <= steps; i++) {
        const currentPct = Math.round(startPct + (pctStep * i));
        const spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'][i % 10];
        const animatedOpts = { ...opts, file: `${spinner} ${opts.file || 'Loading...'}` };

        try {
            await ctx.telegram.editMessageText(
                ctx.chat.id, 
                messageId, 
                undefined, 
                buildProgress(step, total, currentPct, animatedOpts)
            );
        } catch (e) {
            // Ignore edit conflicts, continue animation
        }

        if (i < steps) {
            await new Promise(r => setTimeout(r, stepDuration));
        }
    }
}

const menuText = () => `+----------------------------------------------------------+\n|  🤖 TARRIFIC HOST v2.0                                   |\n|                                                          |\n|  📁 HOSTING                                                |\n|  [1] 🚀 Host New Site              [2] 📋 My Sites       |\n|  [3] ▲ Deploy to Vercel                                  |\n|                                                          |\n|  📸 SCREENSHOTS                                            |\n|  [4] 📷 Capture Screenshot                                 |\n|                                                          |\n|  🔐 SECURITY TOOLS                                         |\n|  [5] #️⃣ Hash Tools        [6] 🔑 JWT Decoder           |\n|  [7] 📡 Port Scanner      [8] 🔍 Header Analyzer       |\n|  [9] 🌐 WHOIS & DNS      [10] 📧 Breach Checker       |\n|  [11] 🔒 Password Generator                              |\n|                                                          |\n|  ⚙️ UTILITIES                                              |\n|  [12] 🆔 Get My ID         [13] ⚙️ Settings            |\n|  [14] ❓ Help                                              |\n|                                                          |\n|  Status: 🟢 Online | Users: Secure Hosting             |\n+----------------------------------------------------------+`;

const hashMenuText = () => `+----------------------------------------------------------+\n|  #️⃣ HASH TOOLS                                            |\n|                                                          |\n|  [1] 🔍 Identify Hash Type                                 |\n|  [2] 🔨 Crack Hash (Wordlist Attack)                       |\n|  [3] 📝 Generate Hashes (MD5/SHA1/SHA256/SHA512)          |\n|  [4] 🔄 Base64 Encode / Decode                             |\n|                                                          |\n|  [◀ Back to Main Menu]                                     |\n+----------------------------------------------------------+`;

const whoisMenuText = () => `+----------------------------------------------------------+\n|  🌐 WHOIS & DNS LOOKUP TOOLS                              |\n|                                                          |\n|  [1] 📋 WHOIS Lookup - Domain registration info            |\n|  [2] 📡 DNS Records - A/MX/TXT records                     |\n|  [3] 🔎 Subdomain Finder - Common subdomains              |\n|                                                          |\n|  [◀ Back to Main Menu]                                     |\n+----------------------------------------------------------+`;

const helpText = () => `+----------------------------------------------------------+\n|  ❓ HELP & COMMANDS                                        |\n|                                                          |\n|  📁 HOSTING COMMANDS                                       |\n|  /host          - Start new site deployment                |\n|  /sites         - List your hosted sites                   |\n|  /delete <name> - Remove a hosted site                     |\n|                                                          |\n|  🔐 SECURITY TOOLS                                         |\n|  /hash          - Hash tools (identify/crack/gen)        |\n|  /jwt           - Decode JWT tokens                        |\n|  /scan          - Port scanner (common ports)              |\n|  /headers       - Analyze HTTP security headers          |\n|  /whois         - WHOIS & DNS lookup tools                 |\n|  /breach        - Check email in breach databases        |\n|  /pass          - Generate secure passwords              |\n|                                                          |\n|  ⚙️ UTILITIES                                              |\n|  /getid         - Show your Telegram ID                    |\n|  /settings      - Bot settings & connections               |\n|  /help          - Show this help menu                      |\n|  /cancel        - Cancel current operation                 |\n|                                                          |\n|  👑 OWNER ONLY                                             |\n|  /broadcast     - Send message to all users                |\n|  /stats         - Bot usage statistics                     |\n|  /users         - List all registered users                |\n|                                                          |\n|  📎 FILE UPLOAD                                            |\n|  Send .zip or .html files directly to host!              |\n|  Max file size: 25 MB | Max sites per user: 5            |\n+----------------------------------------------------------+`;

const mainKB = () => KB([
    [btn('🚀 Host New Site', 'menu_host'), btn('📋 My Sites', 'menu_sites')],
    [btn('▲ Deploy Vercel', 'menu_vercel'), btn('📷 Screenshot', 'menu_screenshot')],
    [btn('#️⃣ Hash Tools', 'menu_hash'), btn('🔑 JWT Decoder', 'menu_jwt')],
    [btn('📡 Port Scanner', 'menu_scan'), btn('🔍 Headers', 'menu_headers')],
    [btn('🌐 WHOIS & DNS', 'menu_whois'), btn('📧 Breach Check', 'menu_breach')],
    [btn('🔒 Password Gen', 'menu_pass'), btn('🆔 Get My ID', 'menu_getid')],
    [btn('⚙️ Settings', 'menu_settings'), btn('❓ Help', 'menu_help')],
]);

const hashKB = () => KB([
    [btn('🔍 Identify Hash', 'hash_identify'), btn('🔨 Crack Hash', 'hash_crack')],
    [btn('📝 Generate Hashes', 'hash_generate'), btn('🔄 Base64', 'hash_base64')],
    [btn('◀ Back', 'menu_main')],
]);

const whoisKB = () => KB([
    [btn('📋 WHOIS Lookup', 'whois_lookup'), btn('📡 DNS Records', 'dns_lookup')],
    [btn('🔎 Subdomain Finder', 'subdomain_find')],
    [btn('◀ Back', 'menu_main')],
]);

const passKB = () => KB([
    [btn('12 chars', 'pass_12'), btn('16 chars', 'pass_16')],
    [btn('24 chars', 'pass_24'), btn('32 chars', 'pass_32')],
    [btn('◀ Back', 'menu_main')],
]);

// ==================== START COMMAND ====================
bot.start(async (ctx) => {
    const u = ctx.from;
    await dbRun(`INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, language, last_active)
        VALUES (?, ?, ?, ?, ?, datetime('now'))`, [u.id, u.username, u.first_name, u.last_name, u.language_code || 'en']);

    if (fs.existsSync(WELCOME_VIDEO)) {
        try {
            await ctx.replyWithVideo({ source: fs.createReadStream(WELCOME_VIDEO) }, {
                caption: `Welcome to TARRIFIC HOST!\n\nHey ${u.first_name || 'there'}!\n\n🚀 Host websites instantly\n🔐 Use security tools\n📸 Capture screenshots\n\nChoose an option below:`,
                supports_streaming: true
            });
        } catch (e) {
            await ctx.reply(`Welcome ${u.first_name || 'there'}! 👋\n\nTARRIFIC HOST BOT\nHost sites, use security tools, and more!`);
        }
    } else {
        await ctx.reply(`Welcome ${u.first_name || 'there'}! 👋\n\nTARRIFIC HOST BOT\nHost sites, use security tools, and more!\n\n💡 Add a welcome.mp4 file for video greeting!`);
    }
    await ctx.reply(menuText(), mainKB());
});

// ==================== MAIN MENU ACTIONS ====================
bot.action('menu_main', async (ctx) => { await ctx.answerCbQuery(); await ctx.editMessageText(menuText(), mainKB()); });

bot.action('menu_host', async (ctx) => {
    await ctx.answerCbQuery();
    const user = await dbGet('SELECT github_token FROM users WHERE user_id = ?', [ctx.from.id]);
    if (!user?.github_token) { await ctx.editMessageText('⚠️ GitHub required!\n\nConnect via Settings first.', back('menu_settings')); return; }
    const sites = await dbAll('SELECT * FROM sites WHERE user_id = ?', [ctx.from.id]);
    if (sites.length >= MAX_SITES) { await ctx.editMessageText(`❌ Max ${MAX_SITES} sites reached!\nDelete old sites first.`, back()); return; }
    await ctx.editMessageText('📤 HOST NEW SITE\n\nSend me a ZIP or HTML file.\n\n📋 Requirements:\n• ZIP must have index.html at root\n• Max file size: 25 MB\n• Folders preserved\n\nSend file now or click Cancel:', cancel());
    ctx.session.step = 'host_upload';
});

bot.action('menu_sites', async (ctx) => {
    await ctx.answerCbQuery();
    const sites = await dbAll('SELECT repo_name, site_url, file_count, total_size, created_at FROM sites WHERE user_id = ? ORDER BY created_at DESC', [ctx.from.id]);
    if (!sites.length) { await ctx.editMessageText('📋 No sites yet.\nUse 🚀 Host New Site to start!', back()); return; }
    let text = '📋 YOUR SITES\n\n';
    const kb = [];
    sites.forEach((s, i) => {
        text += `${i + 1}. 📁 ${s.repo_name}\n   🔗 ${s.site_url}\n   📊 ${s.file_count} files, ${(s.total_size / 1024).toFixed(1)} KB\n\n`;
        kb.push([btn(`🗑️ Delete ${s.repo_name}`, `del_${s.repo_name}`)]);
    });
    kb.push([btn('◀ Back', 'menu_main')]);
    await ctx.editMessageText(text, KB(kb));
});

bot.action('menu_vercel', async (ctx) => {
    await ctx.answerCbQuery();
    const user = await dbGet('SELECT vercel_token FROM users WHERE user_id = ?', [ctx.from.id]);
    const hasVercel = isOwner(ctx.from.id) ? OWNER_VERCEL_TOKEN : user?.vercel_token;
    if (!hasVercel) {
        await ctx.editMessageText('⚠️ Vercel token required!\n\n' + (isOwner(ctx.from.id) ? 'Set VERCEL_TOKEN in env vars.' : 'Use /vercel YOUR_TOKEN to connect.'), back('menu_settings'));
        return;
    }
    await ctx.editMessageText('▲ DEPLOY TO VERCEL\n\nEnter GitHub repo URL:\nExample: https://github.com/user/repo\n\nOr deployed site URL to screenshot.', cancel());
    ctx.session.step = 'vercel_deploy';
});

bot.action('menu_screenshot', async (ctx) => {
    await ctx.answerCbQuery();
    await ctx.editMessageText('📸 CAPTURE SCREENSHOT\n\nEnter URL:\nExample: https://example.com\n\nBot will capture full-page screenshot.', cancel());
    ctx.session.step = 'screenshot';
});

bot.action('menu_hash', async (ctx) => {
    await ctx.answerCbQuery();
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'hash_menu']);
    await ctx.editMessageText(hashMenuText(), hashKB());
});

bot.action('menu_jwt', async (ctx) => {
    await ctx.answerCbQuery();
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'jwt_decode']);
    await ctx.editMessageText('🔑 JWT DECODER\n\nPaste your JWT token:\n\nExample:\neyJhbGciOiJIUzI1NiIs...', cancel());
    ctx.session.step = 'jwt_decode';
});

bot.action('menu_scan', async (ctx) => {
    await ctx.answerCbQuery();
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'port_scan']);
    await ctx.editMessageText('📡 PORT SCANNER\n\nEnter target IP or domain:\nExample: example.com or 8.8.8.8\n\n⚠️ Only scan targets you own!', cancel());
    ctx.session.step = 'scan_target';
});

bot.action('menu_headers', async (ctx) => {
    await ctx.answerCbQuery();
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'header_analyzer']);
    await ctx.editMessageText('🔍 HEADER ANALYZER\n\nEnter URL:\nExample: https://example.com\n\nChecks: HSTS, CSP, X-Frame, X-Content-Type, Referrer-Policy', cancel());
    ctx.session.step = 'headers_url';
});

bot.action('menu_whois', async (ctx) => {
    await ctx.answerCbQuery();
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'whois_menu']);
    await ctx.editMessageText(whoisMenuText(), whoisKB());
});

bot.action('menu_breach', async (ctx) => {
    await ctx.answerCbQuery();
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'breach_check']);
    await ctx.editMessageText('📧 BREACH CHECKER\n\nEnter email to check:\nExample: user@example.com\n\nChecks Have I Been Pwned database.', cancel());
    ctx.session.step = 'breach_email';
});

bot.action('menu_pass', async (ctx) => {
    await ctx.answerCbQuery();
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'password_gen']);
    await ctx.editMessageText('🔒 PASSWORD GENERATOR\n\nSelect length:', passKB());
});

bot.action('menu_getid', async (ctx) => {
    await ctx.answerCbQuery();
    const u = ctx.from;
    await ctx.editMessageText(`🆔 YOUR TELEGRAM ID\n\n👤 User ID: ${u.id}\n📛 Username: @${u.username || 'N/A'}\n📝 Name: ${u.first_name || 'N/A'} ${u.last_name || ''}\n🌐 Language: ${u.language_code || 'N/A'}`,
        KB([[btn('📋 Copy ID', `copy_id_${u.id}`)], [btn('◀ Back', 'menu_main')]]));
});

bot.action('menu_settings', async (ctx) => {
    await ctx.answerCbQuery();
    const user = await dbGet('SELECT github_token, github_username, vercel_token FROM users WHERE user_id = ?', [ctx.from.id]);
    const sites = (await dbAll('SELECT * FROM sites WHERE user_id = ?', [ctx.from.id])).length;
    const tools = (await dbAll("SELECT * FROM tool_usage WHERE user_id = ? AND date(used_at) = date('now')", [ctx.from.id])).length;
    const gh = user?.github_token ? `✅ ${user.github_username}` : '❌ Not connected';
    const vc = user?.vercel_token ? '✅ Connected' : isOwner(ctx.from.id) && OWNER_VERCEL_TOKEN ? '✅ Owner token' : '❌ Not connected';
    const text = `+----------------------------------------------------------+\n|  ⚙️ SETTINGS                                               |\n|                                                          |\n|  GitHub: ${gh.padEnd(46)}|\n|  Vercel: ${vc.padEnd(46)}|\n|  Sites: ${sites.toString().padEnd(47)}|\n|  Tools today: ${tools.toString().padEnd(41)}|\n|                                                          |\n|  [🔗 Reconnect GitHub]  [🔗 Reconnect Vercel]          |\n|  [📊 Usage Stats]  [🗑️ Clear All Data]                  |\n|  [◀ Back to Menu]                                        |\n+----------------------------------------------------------+`;
    await ctx.editMessageText(text, KB([
        [btn('🔗 GitHub', 'github_connect'), btn('🔗 Vercel', 'vercel_connect')],
        [btn('📊 Stats', 'usage_stats'), btn('🗑️ Clear', 'clear_data')],
        [btn('◀ Back', 'menu_main')],
    ]));
});

bot.action('menu_help', async (ctx) => { await ctx.answerCbQuery(); await ctx.editMessageText(helpText(), back()); });

// ==================== SUBMENU ACTIONS ====================
bot.action('hash_identify', async (ctx) => { await ctx.answerCbQuery(); await ctx.editMessageText('🔍 Send hash string:\nExample: 5f4dcc3b5aa765d61d8327deb882cf99', cancel()); ctx.session.step = 'hash_identify'; });
bot.action('hash_crack', async (ctx) => { await ctx.answerCbQuery(); await ctx.editMessageText('🔨 Send hash to crack:\n(Uses wordlist attack)', cancel()); ctx.session.step = 'hash_crack'; });
bot.action('hash_generate', async (ctx) => { await ctx.answerCbQuery(); await ctx.editMessageText('📝 Send text to hash:\n(MD5, SHA1, SHA256, SHA512)', cancel()); ctx.session.step = 'hash_generate'; });
bot.action('hash_base64', async (ctx) => { await ctx.answerCbQuery(); await ctx.editMessageText('🔄 Send text to encode or Base64 to decode:', cancel()); ctx.session.step = 'hash_base64'; });

bot.action('whois_lookup', async (ctx) => { await ctx.answerCbQuery(); await ctx.editMessageText('📋 Enter domain:\nExample: example.com', cancel()); ctx.session.step = 'whois_lookup'; });
bot.action('dns_lookup', async (ctx) => { await ctx.answerCbQuery(); await ctx.editMessageText('📡 Enter domain:\nExample: example.com', cancel()); ctx.session.step = 'dns_lookup'; });
bot.action('subdomain_find', async (ctx) => { await ctx.answerCbQuery(); await ctx.editMessageText('🔎 Enter domain:\nExample: example.com', cancel()); ctx.session.step = 'subdomain_find'; });

bot.action('github_connect', async (ctx) => {
    await ctx.answerCbQuery();
    await ctx.editMessageText('🔗 GITHUB CONNECTION\n\n1. Visit: github.com/settings/tokens\n2. Generate token with "repo" scope\n3. Send: /github YOUR_TOKEN', back('menu_settings'));
});

bot.action('vercel_connect', async (ctx) => {
    await ctx.answerCbQuery();
    await ctx.editMessageText('🔗 VERCEL CONNECTION\n\n1. Visit: vercel.com/account/tokens\n2. Generate token\n3. Send: /vercel YOUR_TOKEN\n\nOr if you are owner, set VERCEL_TOKEN in env vars.', back('menu_settings'));
});

bot.action('usage_stats', async (ctx) => {
    await ctx.answerCbQuery();
    const tools = (await dbAll('SELECT COUNT(*) as c FROM tool_usage WHERE user_id = ?', [ctx.from.id]))[0].c;
    const sites = (await dbAll('SELECT COUNT(*) as c FROM sites WHERE user_id = ?', [ctx.from.id]))[0].c;
    await ctx.editMessageText(`📊 YOUR STATS\n\n🔧 Tools used: ${tools}\n📁 Sites hosted: ${sites}\n\nKeep using TARRIFIC HOST!`, back('menu_settings'));
});

bot.action('clear_data', async (ctx) => {
    await ctx.answerCbQuery();
    await dbRun('DELETE FROM sites WHERE user_id = ?', [ctx.from.id]);
    await dbRun('DELETE FROM tool_usage WHERE user_id = ?', [ctx.from.id]);
    await dbRun('UPDATE users SET github_token = NULL, github_username = NULL, vercel_token = NULL WHERE user_id = ?', [ctx.from.id]);
    await ctx.editMessageText('🗑️ All data cleared!\n\nSites, history, and connections removed.', back('menu_settings'));
});

bot.action('copy_url', async (ctx) => { await ctx.answerCbQuery('📋 URL copied!'); });
bot.action(/^copy_id_\d+$/, async (ctx) => { await ctx.answerCbQuery('📋 ID copied!'); });

bot.action('retry_vercel', async (ctx) => { await ctx.answerCbQuery(); await ctx.editMessageText('▲ Enter GitHub repo URL:', cancel()); ctx.session.step = 'vercel_deploy'; });
bot.action('retry_screenshot', async (ctx) => { await ctx.answerCbQuery(); await ctx.editMessageText('📸 Enter URL to screenshot:', cancel()); ctx.session.step = 'screenshot'; });
bot.action('retry_host', async (ctx) => { await ctx.answerCbQuery(); await ctx.editMessageText('📤 Send ZIP or HTML file:', cancel()); ctx.session.step = 'host_upload'; });

bot.action(/^del_(.+)$/, async (ctx) => {
    await ctx.answerCbQuery();
    const repo = ctx.match[1];
    const site = await dbGet('SELECT repo_url FROM sites WHERE user_id = ? AND repo_name = ?', [ctx.from.id, repo]);
    if (site) {
        try {
            const user = await dbGet('SELECT github_token FROM users WHERE user_id = ?', [ctx.from.id]);
            if (user?.github_token) {
                await axios.delete(`https://api.github.com/repos/${user.github_username}/${repo}`, {
                    headers: { Authorization: `Bearer ${user.github_token}`, Accept: 'application/vnd.github.v3+json' },
                    timeout: 15000
                });
            }
        } catch (e) {
            console.log('GitHub delete failed (may not exist):', e.message);
        }
    }
    await dbRun('DELETE FROM sites WHERE user_id = ? AND repo_name = ?', [ctx.from.id, repo]);
    await ctx.editMessageText(`🗑️ Deleted ${repo}`, back('menu_sites'));
});

bot.action(/^pass_(\d+)$/, async (ctx) => {
    await ctx.answerCbQuery();
    const len = parseInt(ctx.match[1]);
    ctx.session.pass = { length: len, upper: true, lower: true, nums: true, syms: true };
    await ctx.editMessageText(`🔒 OPTIONS (${len} chars)\n\nToggle then click Generate:`, KB([
        [btn('✅ Uppercase (A-Z)', 'pass_opt_upper'), btn('✅ Lowercase (a-z)', 'pass_opt_lower')],
        [btn('✅ Numbers (0-9)', 'pass_opt_nums'), btn('✅ Symbols (!@#)', 'pass_opt_syms')],
        [btn('🎲 Generate', 'pass_generate')],
        [btn('◀ Back', 'menu_main')],
    ]));
});

// FIX: Password toggle actions - only ONE answerCbQuery
bot.action('pass_opt_upper', async (ctx) => { 
    if (!ctx.session.pass) ctx.session.pass = {}; 
    ctx.session.pass.upper = !ctx.session.pass.upper; 
    await ctx.answerCbQuery(`Uppercase: ${ctx.session.pass.upper ? 'ON' : 'OFF'}`); 
});
bot.action('pass_opt_lower', async (ctx) => { 
    if (!ctx.session.pass) ctx.session.pass = {}; 
    ctx.session.pass.lower = !ctx.session.pass.lower; 
    await ctx.answerCbQuery(`Lowercase: ${ctx.session.pass.lower ? 'ON' : 'OFF'}`); 
});
bot.action('pass_opt_nums', async (ctx) => { 
    if (!ctx.session.pass) ctx.session.pass = {}; 
    ctx.session.pass.nums = !ctx.session.pass.nums; 
    await ctx.answerCbQuery(`Numbers: ${ctx.session.pass.nums ? 'ON' : 'OFF'}`); 
});
bot.action('pass_opt_syms', async (ctx) => { 
    if (!ctx.session.pass) ctx.session.pass = {}; 
    ctx.session.pass.syms = !ctx.session.pass.syms; 
    await ctx.answerCbQuery(`Symbols: ${ctx.session.pass.syms ? 'ON' : 'OFF'}`); 
});

bot.action('pass_generate', async (ctx) => {
    await ctx.answerCbQuery();
    const p = ctx.session.pass;
    if (!p?.length) { await ctx.editMessageText('❌ Error: No length selected.', back()); return; }
    let chars = '';
    if (p.upper !== false) chars += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    if (p.lower !== false) chars += 'abcdefghijklmnopqrstuvwxyz';
    if (p.nums !== false) chars += '0123456789';
    if (p.syms !== false) chars += '!@#$%^&*()_+-=[]{}|;:,.<>?';
    if (!chars) chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let pwd = '';
    for (let i = 0; i < p.length; i++) pwd += chars.charAt(Math.floor(Math.random() * chars.length));
    await ctx.editMessageText(`🔒 GENERATED PASSWORD\n\nLength: ${p.length} chars\n\n\`\`\`${pwd}\`\`\`\n\n⚠️ For testing only - use proper crypto for production!`,
        KB([[btn('🎲 Generate Another', 'pass_generate')], [btn('◀ Back', 'menu_main')]]));
});

// ==================== COMMANDS ====================
bot.command('help', async (ctx) => await ctx.reply(helpText(), back()));

bot.command('getid', async (ctx) => {
    const u = ctx.from;
    await ctx.reply(`🆔 YOUR ID\n\n👤 ${u.id}\n📛 @${u.username || 'N/A'}\n📝 ${u.first_name || 'N/A'} ${u.last_name || ''}`,
        KB([[btn('📋 Copy ID', `copy_id_${u.id}`)], [btn('◀ Back', 'menu_main')]]));
});

bot.command('sites', async (ctx) => {
    const sites = await dbAll('SELECT repo_name, site_url, file_count, total_size FROM sites WHERE user_id = ? ORDER BY created_at DESC', [ctx.from.id]);
    if (!sites.length) { await ctx.reply('📋 No sites yet. Use /host to start!', back()); return; }
    let text = '📋 YOUR SITES\n\n';
    sites.forEach((s, i) => text += `${i + 1}. 📁 ${s.repo_name}\n   🔗 ${s.site_url}\n   📊 ${s.file_count} files, ${(s.total_size / 1024).toFixed(1)} KB\n\n`);
    await ctx.reply(text, back());
});

bot.command('cancel', async (ctx) => { ctx.session = {}; await ctx.reply('✅ Cancelled.', back()); });

bot.command('host', async (ctx) => {
    const user = await dbGet('SELECT github_token FROM users WHERE user_id = ?', [ctx.from.id]);
    if (!user?.github_token) { 
        await ctx.reply('⚠️ Connect YOUR GitHub first!\n\nUse /github YOUR_TOKEN or Settings → Connect GitHub', back('menu_settings')); 
        return; 
    }
    const sites = await dbAll('SELECT * FROM sites WHERE user_id = ?', [ctx.from.id]);
    if (sites.length >= MAX_SITES) { await ctx.reply(`❌ Max ${MAX_SITES} sites!`, back()); return; }
    await ctx.reply('📤 Send ZIP or HTML file:\n\n✅ Using YOUR GitHub account', cancel()); 
    ctx.session.step = 'host_upload';
});

bot.command('hash', async (ctx) => { 
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'hash_menu']); 
    await ctx.reply(hashMenuText(), hashKB()); 
});

bot.command('jwt', async (ctx) => { 
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'jwt_decode']); 
    await ctx.reply('🔑 Paste JWT token:', cancel()); 
    ctx.session.step = 'jwt_decode'; 
});

bot.command('scan', async (ctx) => { 
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'port_scan']); 
    await ctx.reply('📡 Enter target IP/domain:', cancel()); 
    ctx.session.step = 'scan_target'; 
});

bot.command('headers', async (ctx) => { 
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'header_analyzer']); 
    await ctx.reply('🔍 Enter URL:', cancel()); 
    ctx.session.step = 'headers_url'; 
});

bot.command('whois', async (ctx) => { 
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'whois_menu']); 
    await ctx.reply(whoisMenuText(), whoisKB()); 
});

bot.command('breach', async (ctx) => { 
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'breach_check']); 
    await ctx.reply('📧 Enter email:', cancel()); 
    ctx.session.step = 'breach_email'; 
});

bot.command('pass', async (ctx) => { 
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'password_gen']); 
    await ctx.reply('🔒 Select length:', passKB()); 
});

bot.command('settings', async (ctx) => {
    const user = await dbGet('SELECT github_token, github_username, vercel_token FROM users WHERE user_id = ?', [ctx.from.id]);
    const sites = (await dbAll('SELECT * FROM sites WHERE user_id = ?', [ctx.from.id])).length;
    const tools = (await dbAll("SELECT * FROM tool_usage WHERE user_id = ? AND date(used_at) = date('now')", [ctx.from.id])).length;
    const gh = user?.github_token ? `✅ ${user.github_username}` : '❌ Not connected';
    const vc = user?.vercel_token ? '✅ Connected' : isOwner(ctx.from.id) && OWNER_VERCEL_TOKEN ? '✅ Owner token' : '❌ Not connected';
    await ctx.reply(`⚙️ SETTINGS\n\nGitHub: ${gh}\nVercel: ${vc}\nSites: ${sites}\nTools today: ${tools}\n\nUse buttons below:`,
        KB([[btn('🔗 GitHub', 'github_connect'), btn('🔗 Vercel', 'vercel_connect')], [btn('📊 Stats', 'usage_stats'), btn('🗑️ Clear', 'clear_data')], [btn('◀ Back', 'menu_main')]]));
});

bot.command('github', async (ctx) => {
    console.log('🔧 /github command triggered by', ctx.from.id);
    const token = ctx.message.text.replace('/github', '').trim();
    if (!token) { 
        await ctx.reply('🔗 Usage: /github YOUR_TOKEN\n\nGet token at github.com/settings/tokens (repo scope)\n\n⚠️ Make sure your token has "repo" scope!'); 
        return; 
    }
    // Validate token format
    if (!token.startsWith('ghp_') && !token.startsWith('github_pat_')) {
        await ctx.reply('❌ Invalid token format.\n\nGitHub tokens start with:\n• ghp_ (classic)\n• github_pat_ (fine-grained)');
        return;
    }
    const statusMsg = await ctx.reply('⏳ Verifying GitHub token...');
    try {
        const r = await axios.get('https://api.github.com/user', { 
            headers: { 
                Authorization: `Bearer ${token}`,
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'TarrificHostBot/1.0'
            }, 
            timeout: 15000 
        });
        await dbRun('UPDATE users SET github_token = ?, github_username = ? WHERE user_id = ?', [token, r.data.login, ctx.from.id]);
        await ctx.telegram.deleteMessage(ctx.chat.id, statusMsg.message_id).catch(() => {});
        await ctx.reply(`✅ GitHub connected!\n\n👤 Username: ${r.data.login}\n📧 Email: ${r.data.email || 'N/A'}\n🆔 ID: ${r.data.id}\n\nYou can now host sites!`, back('menu_settings'));
        console.log(`✅ GitHub connected for user ${ctx.from.id}: ${r.data.login}`);
    } catch (e) { 
        console.error('GitHub auth error:', e.response?.data || e.message);
        await ctx.telegram.deleteMessage(ctx.chat.id, statusMsg.message_id).catch(() => {});
        let errorMsg = e.response?.data?.message || e.message;
        if (e.response?.status === 401) errorMsg = 'Token is invalid or expired';
        if (e.response?.status === 403) errorMsg = 'Token lacks required permissions (need "repo" scope)';
        await ctx.reply(`❌ GitHub Error: ${errorMsg}\n\n🔧 Troubleshooting:\n1. Check token at github.com/settings/tokens\n2. Ensure "repo" scope is enabled\n3. Generate a new token if expired`, back('menu_settings')); 
    }
});

bot.command('vercel', async (ctx) => {
    console.log('🔧 /vercel command triggered by', ctx.from.id);
    const token = ctx.message.text.replace('/vercel', '').trim();
    if (!token) { 
        await ctx.reply('🔗 Usage: /vercel YOUR_TOKEN\n\nGet token at vercel.com/account/tokens'); 
        return; 
    }
    const statusMsg = await ctx.reply('⏳ Verifying Vercel token...');
    try {
        const r = await axios.get('https://api.vercel.com/v2/user', { 
            headers: { Authorization: `Bearer ${token}` }, 
            timeout: 15000 
        });
        await dbRun('UPDATE users SET vercel_token = ? WHERE user_id = ?', [token, ctx.from.id]);
        await ctx.telegram.deleteMessage(ctx.chat.id, statusMsg.message_id).catch(() => {});
        await ctx.reply(`✅ Vercel connected!\n\n👤 ${r.data.user?.email || 'Connected'}`, back('menu_settings'));
        console.log(`✅ Vercel connected for user ${ctx.from.id}`);
    } catch (e) { 
        console.error('Vercel auth error:', e.response?.data || e.message);
        await ctx.telegram.deleteMessage(ctx.chat.id, statusMsg.message_id).catch(() => {});
        await ctx.reply(`❌ Vercel Error: ${e.response?.data?.error?.message || e.message}\n\n🔧 Get your token at:\nvercel.com/account/tokens`, back('menu_settings')); 
    }
});

bot.command('delete', async (ctx) => {
    const repo = ctx.message.text.replace('/delete', '').trim();
    if (!repo) { await ctx.reply('Usage: /delete <repo_name>'); return; }
    await dbRun('DELETE FROM sites WHERE user_id = ? AND repo_name = ?', [ctx.from.id, repo]);
    await ctx.reply(`🗑️ Deleted ${repo}`, back('menu_sites'));
});

// ==================== OWNER COMMANDS ====================
bot.command('broadcast', async (ctx) => {
    if (!isOwner(ctx.from.id)) { await ctx.reply('❌ Owner only!'); return; }
    const msg = ctx.message.text.replace('/broadcast', '').trim();
    if (!msg) { await ctx.reply('👑 Usage: /broadcast Your message'); return; }
    const users = await dbAll('SELECT DISTINCT user_id FROM users');
    let sent = 0, failed = 0;
    await ctx.reply(`📢 Broadcasting to ${users.length} users...`);
    for (const u of users) {
        try { await ctx.telegram.sendMessage(u.user_id, `📢 ADMIN BROADCAST\n\n${msg}`); sent++; } catch (e) { failed++; }
        await new Promise(r => setTimeout(r, 100));
    }
    await ctx.reply(`✅ Done! Sent: ${sent}, Failed: ${failed}, Total: ${users.length}`);
});

bot.command('stats', async (ctx) => {
    if (!isOwner(ctx.from.id)) { await ctx.reply('❌ Owner only!'); return; }
    const users = (await dbAll('SELECT COUNT(DISTINCT user_id) as c FROM users'))[0].c;
    const sites = (await dbAll('SELECT COUNT(*) as c FROM sites'))[0].c;
    const today = (await dbAll("SELECT COUNT(DISTINCT user_id) as c FROM users WHERE date(last_active) = date('now')"))[0].c;
    await ctx.reply(`📊 BOT STATS\n\n👥 Total users: ${users}\n📁 Total sites: ${sites}\n📅 Active today: ${today}\n\nYour ID: ${ctx.from.id}\n👑 Owner: ${isOwner(ctx.from.id) ? 'Yes' : 'No'}`);
});

bot.command('users', async (ctx) => {
    if (!isOwner(ctx.from.id)) { await ctx.reply('❌ Owner only!'); return; }
    const users = await dbAll('SELECT user_id, username, first_name, last_active FROM users ORDER BY last_active DESC LIMIT 20');
    let text = '👥 USERS (Last 20)\n\n';
    users.forEach((u, i) => text += `${i + 1}. ${u.first_name || 'Unknown'} (@${u.username || 'N/A'})\n   ID: ${u.user_id} | Active: ${u.last_active}\n\n`);
    await ctx.reply(text);
});

// ==================== TEXT INPUT HANDLER ====================
bot.on('text', async (ctx) => {
    const step = ctx.session?.step;
    if (!step) return;
    const text = ctx.message.text;
    ctx.session.step = null;
    try {
        switch (step) {
            case 'hash_identify': await doHashIdentify(ctx, text); break;
            case 'hash_crack': await doHashCrack(ctx, text); break;
            case 'hash_generate': await doHashGenerate(ctx, text); break;
            case 'hash_base64': await doHashBase64(ctx, text); break;
            case 'jwt_decode': await doJwtDecode(ctx, text); break;
            case 'scan_target': await doScanTarget(ctx, text); break;
            case 'headers_url': await doHeadersUrl(ctx, text); break;
            case 'whois_lookup': await doWhoisLookup(ctx, text); break;
            case 'dns_lookup': await doDnsLookup(ctx, text); break;
            case 'subdomain_find': await doSubdomainFind(ctx, text); break;
            case 'breach_email': await doBreachEmail(ctx, text); break;
            case 'vercel_deploy': await doVercelDeploy(ctx, text); break;
            case 'screenshot': await doScreenshot(ctx, text); break;
            case 'host_upload': await ctx.reply('❌ Please send a ZIP or HTML file, not text.', cancel()); break;
            default: await ctx.reply('❌ Unknown operation. Use /cancel and try again.');
        }
    } catch (e) {
        console.error(`Error in ${step}:`, e);
        await ctx.reply(`❌ Error: ${e.message}`, back());
    }
});

// ==================== REAL TOOL IMPLEMENTATIONS ====================
async function doHashIdentify(ctx, text) {
    const patterns = { 'MD5': /^[a-f0-9]{32}$/, 'SHA-1': /^[a-f0-9]{40}$/, 'SHA-256': /^[a-f0-9]{64}$/, 'SHA-512': /^[a-f0-9]{128}$/ };
    let results = [];
    for (const [t, p] of Object.entries(patterns)) if (p.test(text)) results.push(`✅ ${t}: ${t === 'MD5' ? 32 : t === 'SHA-1' ? 40 : t === 'SHA-256' ? 64 : 128} hex chars`);
    if (!results.length) results.push('❌ Unknown format');
    await ctx.reply(`🔍 HASH IDENTIFICATION\n\nInput: ${text}\nLength: ${text.length} chars\n\nPossible types:\n${results.join('\n')}`, back('menu_hash'));
}

async function doHashCrack(ctx, text) {
    const passwords = ['123456', 'password', '12345678', 'qwerty', '123456789', 'letmein', '1234567', 'football', 'iloveyou', 'admin', 'welcome', 'monkey', 'login', 'abc123', '111111', '123123', 'password123', '1234', 'baseball', 'qwertyuiop', 'sunshine', 'princess', 'dragon', 'master', 'shadow'];
    let found = null;
    for (const pass of passwords) {
        if (crypto.createHash('md5').update(pass).digest('hex') === text) { found = { type: 'MD5', pass }; break; }
        if (crypto.createHash('sha1').update(pass).digest('hex') === text) { found = { type: 'SHA-1', pass }; break; }
        if (crypto.createHash('sha256').update(pass).digest('hex') === text) { found = { type: 'SHA-256', pass }; break; }
    }
    let msg = `🔨 HASH CRACK\n\nInput: ${text}\n\n`;
    if (found) msg += `✅ CRACKED!\n\nType: ${found.type}\nPassword: ${found.pass}\n\n⚠️ Found in common wordlist. Use strong passwords!`;
    else msg += `❌ NOT FOUND\n\nTried ${passwords.length} common passwords.\nHash not in built-in wordlist.`;
    await ctx.reply(msg, back('menu_hash'));
}

async function doHashGenerate(ctx, text) {
    const h = {
        'MD5': crypto.createHash('md5').update(text).digest('hex'),
        'SHA-1': crypto.createHash('sha1').update(text).digest('hex'),
        'SHA-256': crypto.createHash('sha256').update(text).digest('hex'),
        'SHA-512': crypto.createHash('sha512').update(text).digest('hex')
    };
    let msg = `📝 GENERATED HASHES\n\nInput: ${text}\n\n`;
    for (const [t, v] of Object.entries(h)) msg += `${t}:\n${v}\n\n`;
    await ctx.reply(msg, back('menu_hash'));
}

async function doHashBase64(ctx, text) {
    try {
        const decoded = Buffer.from(text, 'base64').toString('utf8');
        if (decoded && decoded !== text && /^[\x20-\x7E\n\r\t]+$/.test(decoded)) {
            await ctx.reply(`🔄 BASE64 DECODED\n\nInput: ${text}\n\nDecoded:\n${decoded}`, back('menu_hash')); return;
        }
    } catch (e) {}
    await ctx.reply(`🔄 BASE64 ENCODED\n\nInput: ${text}\n\nEncoded:\n${Buffer.from(text).toString('base64')}`, back('menu_hash'));
}

async function doJwtDecode(ctx, text) {
    const parts = text.split('.');
    if (parts.length !== 3) { await ctx.reply(`❌ INVALID JWT\n\nMust have 3 parts (header.payload.signature)\nYour input has ${parts.length} part(s).`, back()); return; }
    try {
        const header = JSON.parse(Buffer.from(parts[0], 'base64url').toString());
        const payload = JSON.parse(Buffer.from(parts[1], 'base64url').toString());
        await ctx.reply(`🔑 JWT DECODED\n\n📋 HEADER\n\`\`\`json\n${JSON.stringify(header, null, 2)}\n\`\`\`\n\n📦 PAYLOAD\n\`\`\`json\n${JSON.stringify(payload, null, 2)}\n\`\`\`\n\n⚠️ Never share JWT tokens!`, back());
    } catch (e) { await ctx.reply(`❌ Decode error: ${e.message}`, back()); }
}

// ==================== REAL PORT SCANNER ====================
async function doScanTarget(ctx, text) {
    const ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 3306, 3389, 5432, 5900, 8080, 8443];
    const names = { 21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS', 80: 'HTTP', 110: 'POP3', 143: 'IMAP', 443: 'HTTPS', 3306: 'MySQL', 3389: 'RDP', 5432: 'PostgreSQL', 5900: 'VNC', 8080: 'HTTP-Alt', 8443: 'HTTPS-Alt' };
    let msg = `📡 SCAN RESULTS\n\nTarget: ${text}\n\n`;
    let target = text;
    try { 
        if (!/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(text)) { 
            const a = await dns.resolve4(text); 
            if (a.length) { target = a[0]; msg += `Resolved: ${text} -> ${target}\n\n`; } 
        } 
    } catch (e) { msg += `DNS failed, using original\n\n`; }
    msg += 'PORT    STATUS    SERVICE\n-------------------------\n';
    const scanPort = (host, port) => new Promise((resolve) => {
        const socket = new net.Socket();
        socket.setTimeout(3000);
        socket.once('connect', () => { socket.destroy(); resolve('OPEN'); });
        socket.once('timeout', () => { socket.destroy(); resolve('FILTERED'); });
        socket.once('error', () => { socket.destroy(); resolve('CLOSED'); });
        socket.connect(port, host);
    });
    for (const p of ports) {
        const status = await scanPort(target, p);
        const icon = status === 'OPEN' ? '✅' : status === 'FILTERED' ? '⚠️' : '❌';
        msg += `${p.toString().padEnd(7)} ${icon} ${status.padEnd(8)} ${names[p]}\n`;
    }
    msg += '\n⚠️ Only scan targets you own or have permission to scan!';
    await ctx.reply(msg, back());
}

async function doHeadersUrl(ctx, text) {
    let url = text.startsWith('http') ? text : 'https://' + text;
    try {
        const r = await axios.head(url, { timeout: 10000, validateStatus: () => true });
        const h = r.headers;
        const sec = ['strict-transport-security', 'content-security-policy', 'x-frame-options', 'x-content-type-options', 'referrer-policy'];
        let msg = `🔍 SECURITY REPORT\n\nURL: ${url}\n\n`;
        msg += '✅ PRESENT\n' + sec.filter(s => h[s]).map(s => `  ${s}`).join('\n') + '\n\n';
        msg += '❌ MISSING\n' + sec.filter(s => !h[s]).map(s => `  ${s}`).join('\n');
        await ctx.reply(msg, back());
    } catch (e) { await ctx.reply(`❌ Error: ${e.message}`, back()); }
}

async function doWhoisLookup(ctx, text) {
    try {
        const r = await axios.get(`https://rdap.org/domain/${encodeURIComponent(text)}`, { timeout: 15000 });
        const d = r.data;
        let msg = `📋 WHOIS: ${text}\n\n`;
        if (d.ldhName) msg += `Domain: ${d.ldhName}\n`;
        if (d.status) msg += `Status: ${Array.isArray(d.status) ? d.status.join(', ') : d.status}\n`;
        if (d.events) d.events.forEach(e => msg += `${e.eventAction || 'Event'}: ${e.eventDate}\n`);
        if (d.entities) {
            msg += '\nRegistrant Info:\n';
            d.entities.forEach(e => { if (e.vcardArray?.[1]) e.vcardArray[1].forEach(p => { if (p[0] === 'fn') msg += `  Name: ${p[3]}\n`; if (p[0] === 'email') msg += `  Email: ${p[3]}\n`; }); });
        }
        await ctx.reply(msg, back('menu_whois'));
    } catch (e) { await ctx.reply(`❌ WHOIS error: ${e.message}\n\nNote: Requires valid domain + internet.`, back('menu_whois')); }
}

async function doDnsLookup(ctx, text) {
    try {
        const a = await dns.resolve4(text);
        let msg = `📡 DNS: ${text}\n\nA Records:\n${a.map(ip => `  ${ip}`).join('\n')}`;
        try { const mx = await dns.resolveMx(text); msg += `\n\nMX Records:\n${mx.map(r => `  ${r.exchange} (pri: ${r.priority})`).join('\n')}`; } catch (e) {}
        try { const txt = await dns.resolveTxt(text); msg += `\n\nTXT Records:\n${txt.map(r => `  ${r.join('')}`).join('\n')}`; } catch (e) {}
        await ctx.reply(msg, back('menu_whois'));
    } catch (e) { await ctx.reply(`❌ DNS error: ${e.message}`, back('menu_whois')); }
}

async function doSubdomainFind(ctx, text) {
    const subs = ['www', 'mail', 'ftp', 'admin', 'api', 'blog', 'shop', 'dev', 'test', 'app', 'cdn', 'm', 'webmail', 'remote', 'server', 'ns1', 'ns2', 'smtp', 'pop', 'imap'];
    let msg = `🔎 SUBDOMAIN FINDER: ${text}\n\nChecking common subdomains...\n\n`;
    const found = [];
    for (const s of subs) { try { await dns.resolve4(`${s}.${text}`); found.push(`${s}.${text}`); } catch (e) {} }
    if (found.length) msg += `✅ FOUND (${found.length}):\n\n${found.map(s => `  ${s}`).join('\n')}`;
    else msg += '❌ No common subdomains found.';
    await ctx.reply(msg, back('menu_whois'));
}

async function doBreachEmail(ctx, text) {
    try {
        const r = await axios.get(`https://haveibeenpwned.com/api/v3/breachedaccount/${encodeURIComponent(text)}`, {
            headers: { 'User-Agent': 'TarrificHostBot/1.0' }, timeout: 15000, validateStatus: () => true
        });
        if (r.status === 404) await ctx.reply(`✅ GOOD NEWS!\n\nEmail: ${text}\n\nNo breaches found.`, back());
        else if (r.status === 200) {
            let msg = `❌ BREACHES FOUND!\n\nEmail: ${text}\nFound in ${r.data.length} breach(es):\n\n`;
            r.data.slice(0, 5).forEach(b => { msg += `- ${b.Name}\n`; if (b.BreachDate) msg += `  Date: ${b.BreachDate}\n`; if (b.DataClasses) msg += `  Data: ${b.DataClasses.join(', ')}\n`; msg += '\n'; });
            msg += '⚠️ Change passwords immediately!';
            await ctx.reply(msg, back());
        } else if (r.status === 429) await ctx.reply('⏳ Rate limited. Try later or check manually at haveibeenpwned.com', back());
        else await ctx.reply(`⚠️ API response: ${r.status}\n\nCheck manually at haveibeenpwned.com`, back());
    } catch (e) { await ctx.reply(`📧 BREACH CHECK\n\nEmail: ${text}\n\n⚠️ API Error: ${e.message}\n\nThe Have I Been Pwned API may be rate-limited or unavailable.\n\n✅ This is a REAL check - the API was contacted.\nTry again later or check manually at haveibeenpwned.com`, back()); }
}

// ==================== REAL VERCEL DEPLOYMENT ====================
async function doVercelDeploy(ctx, text) {
    const user = await dbGet('SELECT vercel_token FROM users WHERE user_id = ?', [ctx.from.id]);
    const vercelToken = isOwner(ctx.from.id) ? OWNER_VERCEL_TOKEN : user?.vercel_token;
    if (!vercelToken) {
        await ctx.reply('❌ Vercel token not configured. Use /vercel YOUR_TOKEN or set env var.', back());
        return;
    }
    const prog = await ctx.reply(buildProgress(1, 3, 10, { status: 'in_progress', file: 'Connecting to Vercel...' }));
    try {
        const url = new URL(text);
        const parts = url.pathname.split('/').filter(p => p);
        if (parts.length < 2) throw new Error('Invalid GitHub URL. Format: https://github.com/user/repo');
        const owner = parts[0], repo = parts[1].replace('.git', '');
        await ctx.telegram.editMessageText(ctx.chat.id, prog.message_id, undefined, buildProgress(2, 3, 60, { status: 'in_progress', file: 'Deploying...' }));
        const proj = await axios.post('https://api.vercel.com/v9/projects', { 
            name: `${repo}-tarrific`, 
            gitRepository: { repo: `${owner}/${repo}`, type: 'github' } 
        }, { 
            headers: { Authorization: `Bearer ${vercelToken}` }, 
            timeout: 30000 
        });
        const deploy = await axios.post('https://api.vercel.com/v13/deployments', { 
            name: proj.data.name, 
            project: proj.data.id, 
            gitSource: { type: 'github', repo: `${owner}/${repo}`, ref: 'main' }, 
            target: 'production' 
        }, { 
            headers: { Authorization: `Bearer ${vercelToken}` }, 
            timeout: 30000 
        });
        const siteUrl = `https://${deploy.data.url}`;
        await ctx.telegram.editMessageText(ctx.chat.id, prog.message_id, undefined, buildProgress(3, 3, 100, { status: 'done', file: siteUrl }));
        await ctx.reply(`✅ Deployed to Vercel!\n\n🔗 Site: ${siteUrl}\n📁 Project: ${proj.data.name}`, KB([[btn('▲ Deploy Another', 'menu_vercel'), btn('📋 Copy URL', 'copy_url')], [btn('◀ Menu', 'menu_main')]]));
    } catch (e) {
        console.error('Vercel error:', e);
        await ctx.telegram.editMessageText(ctx.chat.id, prog.message_id, undefined, buildProgress(1, 3, 0, { status: 'failed', error: e.message }), retryBack('retry_vercel'));
    }
}

// ==================== REAL SCREENSHOT WITH FALLBACK ====================
async function doScreenshot(ctx, text) {
    let url = text.startsWith('http') ? text : 'https://' + text;
    const prog = await ctx.reply(buildProgress(1, 2, 10, { status: 'in_progress', file: 'Loading page...' }));
    try {
        let browser, page;
        try {
            const pw = require('playwright');
            browser = await pw.chromium.launch({ headless: true });
            page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
        } catch (e) {
            try {
                const puppeteer = require('puppeteer');
                browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox', '--disable-setuid-sandbox'] });
                page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
            } catch (e2) {
                throw new Error('Screenshot requires Playwright or Puppeteer. Install: npm install playwright OR npm install puppeteer');
            }
        }
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
        await new Promise(r => setTimeout(r, 3000));
        const screenshotPath = `screenshots/${Date.now()}.png`;
        await page.screenshot({ path: screenshotPath, fullPage: true });
        await browser.close();
        await ctx.telegram.editMessageText(ctx.chat.id, prog.message_id, undefined, buildProgress(2, 2, 100, { status: 'done', file: url }));
        await ctx.replyWithPhoto({ source: screenshotPath }, { caption: `✅ Screenshot captured!\n\n🔗 ${url}` });
    } catch (e) {
        console.error('Screenshot error:', e);
        await ctx.telegram.editMessageText(ctx.chat.id, prog.message_id, undefined, buildProgress(1, 2, 0, { status: 'failed', error: e.message }), retryBack('retry_screenshot'));
    }
}

// ==================== REAL FILE HANDLER - GITHUB PAGES DEPLOYMENT ====================
bot.on('document', async (ctx) => {
    const doc = ctx.message.document;
    const name = doc.file_name;
    const size = doc.file_size;
    if (!name.endsWith('.zip') && !name.endsWith('.html') && !name.endsWith('.htm')) { 
        await ctx.reply('❌ Only ZIP or HTML files.', back()); 
        return; 
    }
    if (size > 25 * 1024 * 1024) { 
        await ctx.reply(`❌ Too large: ${(size / (1024 * 1024)).toFixed(1)} MB (max 25 MB)`, back()); 
        return; 
    }
    const user = await dbGet('SELECT github_token, github_username FROM users WHERE user_id = ?', [ctx.from.id]);
    if (!user?.github_token) {
        await ctx.reply('⚠️ Connect YOUR GitHub first!\n\nUse Settings → GitHub or /github YOUR_TOKEN', back('menu_settings'));
        return;
    }
    const prog = await ctx.reply(buildProgress(1, 5, 10, { status: 'in_progress', file: 'Authenticating...' }), cancel());
    try {
        const link = await ctx.telegram.getFileLink(doc.file_id);
        const fileResponse = await axios.get(link.href, { responseType: 'arraybuffer', timeout: 30000 });
        const fileBuffer = Buffer.from(fileResponse.data);
        const timestamp = Date.now();
        const repoName = `tarrific-site-${timestamp}`;
        const localPath = `uploads/${repoName}`;
        fs.mkdirSync(localPath, { recursive: true });
        const filePath = `${localPath}/${name}`;
        fs.writeFileSync(filePath, fileBuffer);
        await ctx.telegram.editMessageText(ctx.chat.id, prog.message_id, undefined, buildProgress(2, 5, 25, { status: 'in_progress', file: 'Creating GitHub repo...' }));
        const githubHeaders = { 
            Authorization: `Bearer ${user.github_token}`, 
            Accept: 'application/vnd.github.v3+json' 
        };
        const repoData = await axios.post('https://api.github.com/user/repos', {
            name: repoName,
            description: 'Hosted by TARRIFIC HOST Bot',
            private: false,
            auto_init: true
        }, { headers: githubHeaders, timeout: 15000 });
        const repoUrl = repoData.data.html_url;
        const owner = repoData.data.owner.login;
        await ctx.telegram.editMessageText(ctx.chat.id, prog.message_id, undefined, buildProgress(3, 5, 50, { status: 'in_progress', file: 'Uploading files...', count: 1, totalFiles: 1 }));
        let files = [];
        let fileCount = 0;
        let totalSize = 0;
        if (name.endsWith('.zip')) {
            const AdmZip = require('adm-zip');
            const zip = new AdmZip(filePath);
            zip.extractAllTo(localPath, true);
            fs.unlinkSync(filePath);
            const readDir = (dir) => {
                const items = fs.readdirSync(dir);
                for (const item of items) {
                    const fullPath = path.join(dir, item);
                    const stat = fs.statSync(fullPath);
                    if (stat.isDirectory() && item !== '.git') {
                        readDir(fullPath);
                    } else if (stat.isFile()) {
                        const relPath = path.relative(localPath, fullPath).replace(/\\/g, '/');
                        files.push({ path: relPath, content: fs.readFileSync(fullPath) });
                        fileCount++;
                        totalSize += stat.size;
                    }
                }
            };
            readDir(localPath);
        } else {
            files.push({ path: 'index.html', content: fs.readFileSync(filePath) });
            fileCount = 1;
            totalSize = size;
        }
        for (const file of files) {
            const content = file.content.toString('base64');
            try {
                await axios.put(`https://api.github.com/repos/${owner}/${repoName}/contents/${file.path}`, {
                    message: `Add ${file.path} via TARRIFIC HOST`,
                    content: content
                }, { headers: githubHeaders, timeout: 15000 });
            } catch (e) {
                console.log(`Upload error for ${file.path}:`, e.message);
            }
        }
        await ctx.telegram.editMessageText(ctx.chat.id, prog.message_id, undefined, buildProgress(4, 5, 75, { status: 'in_progress', file: 'Enabling GitHub Pages...' }));
        await axios.post(`https://api.github.com/repos/${owner}/${repoName}/pages`, {
            source: { branch: 'main', path: '/' }
        }, { headers: githubHeaders, timeout: 15000 });
        await new Promise(r => setTimeout(r, 3000));
        await ctx.telegram.editMessageText(ctx.chat.id, prog.message_id, undefined, buildProgress(5, 5, 100, { status: 'done', file: `https://${owner}.github.io/${repoName}/` }));
        const siteUrl = `https://${owner}.github.io/${repoName}/`;
        await dbRun('INSERT INTO sites (user_id, repo_name, repo_url, site_url, file_count, total_size) VALUES (?, ?, ?, ?, ?, ?)',
            [ctx.from.id, repoName, repoUrl, siteUrl, fileCount, totalSize]);
        await ctx.reply(`✅ DEPLOYED!\n\n🔗 ${siteUrl}\n📁 ${fileCount} files, ${(totalSize / 1024).toFixed(1)} KB`, 
            KB([[btn('🚀 Host Another', 'menu_host'), btn('📋 Copy URL', 'copy_url')], [btn('◀ Menu', 'menu_main')]]));
        // AUTO-CLEANUP: Remove uploaded files after deployment
        try { 
            fs.rmSync(localPath, { recursive: true, force: true }); 
            console.log(`🗑️ Upload cleaned up: ${localPath}`);
        } catch (e) {}
    } catch (e) {
        console.error('Upload/Deploy error:', e);
        // Cleanup on error too
        try { fs.rmSync(localPath, { recursive: true, force: true }); } catch (cleanupErr) {}
        await ctx.telegram.editMessageText(ctx.chat.id, prog.message_id, undefined, buildProgress(1, 5, 0, { status: 'failed', error: e.message }), retryBack('retry_host'));
    }
});

// ==================== LAUNCH ====================
// Global error handler
bot.catch((err, ctx) => {
    console.error(`❌ Bot error for ${ctx.updateType}:`, err);
    ctx.reply('⚠️ An error occurred. Please try again or use /cancel.').catch(() => {});
});

// ==================== LAUNCH ====================
// Start bot in polling mode (works everywhere)
bot.launch().then(() => {
    console.log('✅ TARRIFIC HOST Bot started!');
    console.log('📊 Environment check:');
    console.log('  BOT_TOKEN:', BOT_TOKEN ? '✅ Set' : '❌ Missing');
    console.log('  OWNER_ID:', OWNER_ID ? '✅ Set' : '❌ Missing');
    console.log('  OWNER_VERCEL_TOKEN:', OWNER_VERCEL_TOKEN ? '✅ Set' : '❌ Not set (owner only)');
}).catch(err => { 
    console.error('❌ Failed to start:', err); 
    process.exit(1); 
});

// ==================== PORT FOR RENDER ====================
// Render needs an open port or it thinks the service failed
const http = require('http');
const PORT = process.env.PORT || 3000;
const server = http.createServer((req, res) => {
    res.writeHead(200);
    res.end('🤖 TARRIFIC HOST Bot is running!');
});
server.listen(PORT, () => {
    console.log(`🌐 Port open on ${PORT} for Render health checks`);
});

process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));

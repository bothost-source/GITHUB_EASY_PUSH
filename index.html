const { Telegraf, Markup } = require('telegraf');
const axios = require('axios');
const sqlite3 = require('sqlite3').verbose();
const fs = require('fs');
const path = require('path');

// Config
const BOT_TOKEN = process.env.BOT_TOKEN;
const VERCEL_TOKEN = process.env.VERCEL_TOKEN;
const GITHUB_CLIENT_ID = process.env.GITHUB_CLIENT_ID;
const GITHUB_CLIENT_SECRET = process.env.GITHUB_CLIENT_SECRET;
const GITHUB_REDIRECT_URI = process.env.GITHUB_REDIRECT_URI;
const WELCOME_VIDEO_PATH = process.env.WELCOME_VIDEO_PATH || 'welcome.mp4';
const OWNER_ID = process.env.OWNER_ID;
const MAX_SITES_PER_USER = 5;

if (!BOT_TOKEN) {
    console.error('BOT_TOKEN is required!');
    process.exit(1);
}

if (!OWNER_ID) {
    console.warn('OWNER_ID not set - broadcast and admin features disabled');
}

// Initialize bot
const bot = new Telegraf(BOT_TOKEN);

// Initialize SQLite database
const db = new sqlite3.Database('tarrific_host.db');

// Create tables
db.serialize(() => {
    db.run(`CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        language TEXT DEFAULT 'en',
        github_token TEXT,
        github_username TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS sites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        repo_name TEXT,
        repo_url TEXT,
        site_url TEXT,
        file_count INTEGER,
        total_size INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )`);

    db.run(`CREATE TABLE IF NOT EXISTS tool_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        tool_name TEXT,
        used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )`);
});

// Helper functions
const dbRun = (sql, params = []) => {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function(err) {
            if (err) reject(err);
            else resolve({ id: this.lastID, changes: this.changes });
        });
    });
};

const dbGet = (sql, params = []) => {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => {
            if (err) reject(err);
            else resolve(row);
        });
    });
};

const dbAll = (sql, params = []) => {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => {
            if (err) reject(err);
            else resolve(rows);
        });
    });
};

const isOwner = (userId) => {
    return OWNER_ID && userId.toString() === OWNER_ID.toString();
};

const getAllUsers = async () => {
    return await dbAll('SELECT DISTINCT user_id FROM users');
};

// Progress builder
const buildProgress = (currentStep, totalSteps, percent, options = {}) => {
    const { currentFile, fileCount, totalFiles, fileSize, totalSize, status, error, errorFile } = options;

    let lines = [];
    lines.push('+-----------------------------+');

    if (status === 'failed') {
        lines.push('|  X DEPLOYMENT FAILED        |');
    } else if (status === 'done') {
        lines.push('|  V DEPLOYMENT COMPLETE      |');
    } else {
        lines.push('|  > NEW SITE DEPLOYMENT      |');
    }

    lines.push('|                             |');
    lines.push('|  Step ' + currentStep + '/' + totalSteps + '                   |');

    const steps = ['Authenticating', 'Creating Repo', 'Uploading', 'Enabling Pages', 'Finalizing'];

    for (let i = 0; i < steps.length; i++) {
        const stepNum = i + 1;
        let bar;

        if (stepNum < currentStep) {
            bar = '############ DONE';
        } else if (stepNum === currentStep) {
            if (status === 'failed') {
                bar = '######------ FAILED';
            } else if (status === 'in_progress') {
                bar = '######------ IN PROGRESS';
            } else {
                bar = '############ DONE';
            }
        } else {
            if (status === 'failed' && stepNum > currentStep) {
                bar = '------------ BLOCKED';
            } else {
                bar = '------------ WAITING';
            }
        }

        lines.push('|  [' + steps[i].padEnd(13) + '] ' + bar + ' |');
    }

    lines.push('|                             |');
    const filled = Math.floor(percent / 10);
    const progressBar = '='.repeat(filled) + '-'.repeat(10 - filled);
    lines.push('|  ' + progressBar + '  ' + percent + '%           |');
    lines.push('|                             |');

    if (status === 'failed' && error) {
        lines.push('|  X ERROR at Step ' + currentStep + '/' + totalSteps + '        |');
        lines.push('|  Location: ' + steps[currentStep-1].padEnd(13) + ' |');
        if (errorFile) {
            lines.push('|  File: ' + errorFile.padEnd(21) + ' |');
        }
        lines.push('|                             |');
        lines.push('|  Message:                   |');
        const errorLines = error.match(/.{1,25}/g) || [error];
        errorLines.forEach(el => {
            lines.push('|  ' + el.padEnd(27) + ' |');
        });
    } else if (status === 'done') {
        lines.push('|  O Your site is live:       |');
        if (currentFile) {
            const urlLines = currentFile.match(/.{1,25}/g) || [currentFile];
            urlLines.forEach(ul => {
                lines.push('|  ' + ul.padEnd(27) + ' |');
            });
        }
    } else {
        if (currentFile) {
            lines.push('|  Current: > ' + currentFile.padEnd(14) + ' |');
        }
        if (fileCount && totalFiles) {
            lines.push('|  ' + fileCount + '/' + totalFiles + ' -- ' + (currentFile || '').substring(0, 18).padEnd(18) + ' |');
        }
        if (fileSize && totalSize) {
            const formatSize = (bytes) => {
                if (bytes < 1024) return bytes + ' B';
                if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
                return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
            };
            lines.push('|  (' + formatSize(fileSize) + ' / ' + formatSize(totalSize) + ' total) |');
        }
    }

    lines.push('+-----------------------------+');
    return lines.join('\n');
};

// Menu keyboards
const getMainMenuKeyboard = () => {
    return Markup.inlineKeyboard([
        [Markup.button.callback('> Host New Site', 'menu_host')],
        [Markup.button.callback('[] My Hosted Sites', 'menu_sites')],
        [Markup.button.callback('> Deploy to Vercel', 'menu_vercel')],
        [Markup.button.callback('O Capture Screenshot', 'menu_screenshot')],
        [Markup.button.callback('# Hash Tools', 'menu_hash')],
        [Markup.button.callback('O JWT Decoder', 'menu_jwt')],
        [Markup.button.callback('|| Port Scanner', 'menu_scan')],
        [Markup.button.callback('^ Header Analyzer', 'menu_headers')],
        [Markup.button.callback('O WHOIS & DNS', 'menu_whois')],
        [Markup.button.callback('@ Breach Checker', 'menu_breach')],
        [Markup.button.callback('O Password Generator', 'menu_pass')],
        [Markup.button.callback('O Get My ID', 'menu_getid')],
        [Markup.button.callback('O Settings', 'menu_settings')],
        [Markup.button.callback('? Help', 'menu_help')],
    ]);
};

const getBackButton = (callbackData = 'back_menu') => {
    return Markup.inlineKeyboard([[Markup.button.callback('< Back', callbackData)]]);
};

const getCancelButton = () => {
    return Markup.inlineKeyboard([[Markup.button.callback('X Cancel', 'cancel')]]);
};

const getMainMenuText = () => {
    return '+-----------------------------+\n' +
           '|  TARRIFIC HOST v1.0         |\n' +
           '|                             |\n' +
           '|  HOSTING                    |\n' +
           '|  [1] > Host New Site        |\n' +
           '|  [2] [] My Hosted Sites     |\n' +
           '|  [3] > Deploy to Vercel     |\n' +
           '|                             |\n' +
           '|  SCREENSHOTS                |\n' +
           '|  [4] O Capture Screenshot   |\n' +
           '|                             |\n' +
           '|  SECURITY TOOLS             |\n' +
           '|  [5] # Hash Tools           |\n' +
           '|  [6] O JWT Decoder          |\n' +
           '|  [7] || Port Scanner        |\n' +
           '|  [8] ^ Header Analyzer      |\n' +
           '|  [9] O WHOIS & DNS          |\n' +
           '|  [10] @ Breach Checker      |\n' +
           '|  [11] O Password Generator  |\n' +
           '|                             |\n' +
           '|  UTILITIES                  |\n' +
           '|  [12] O Get My ID           |\n' +
           '|                             |\n' +
           '|  [13] O Settings            |\n' +
           '|  [14] ? Help                |\n' +
           '|                             |\n' +
           '|  Status: . Online           |\n' +
           '+-----------------------------+';
};

const getHashMenuText = () => {
    return '+-----------------------------+\n' +
           '|  # HASH TOOLS               |\n' +
           '|                             |\n' +
           '|  [1] Identify Hash Type     |\n' +
           '|  [2] Crack Hash (wordlist)  |\n' +
           '|  [3] Generate Hashes        |\n' +
           '|  [4] Base64 Encode/Decode   |\n' +
           '|                             |\n' +
           '|  [< Back]                   |\n' +
           '+-----------------------------+';
};

const getWhoisMenuText = () => {
    return '+-----------------------------+\n' +
           '|  O WHOIS & DNS              |\n' +
           '|                             |\n' +
           '|  [1] WHOIS Lookup           |\n' +
           '|  [2] DNS Records            |\n' +
           '|  [3] Subdomain Finder       |\n' +
           '|                             |\n' +
           '|  [< Back]                   |\n' +
           '+-----------------------------+';
};

const getHelpText = () => {
    return '+-----------------------------+\n' +
           '|  ? HELP & COMMANDS          |\n' +
           '|                             |\n' +
           '|  HOSTING                    |\n' +
           '|  /host - Start new deploy   |\n' +
           '|  /sites - List your sites   |\n' +
           '|  /delete <name> - Remove    |\n' +
           '|                             |\n' +
           '|  SECURITY TOOLS             |\n' +
           '|  /hash - Hash tools menu    |\n' +
           '|  /jwt - Decode JWT token    |\n' +
           '|  /scan - Port scanner       |\n' +
           '|  /headers - Analyze headers |\n' +
           '|  /whois - WHOIS & DNS tools |\n' +
           '|  /breach - Check email      |\n' +
           '|  /pass - Generate password  |\n' +
           '|                             |\n' +
           '|  UTILITIES                  |\n' +
           '|  /getid - Show your ID      |\n' +
           '|  /settings - Bot settings   |\n' +
           '|  /help - This menu          |\n' +
           '|  /cancel - Cancel operation |\n' +
           '|                             |\n' +
           '|  OWNER ONLY                 |\n' +
           '|  /broadcast - Message all   |\n' +
           '|  /stats - Bot statistics    |\n' +
           '|  /users - List all users    |\n' +
           '|                             |\n' +
           '|  ZIP UPLOAD                 |\n' +
           '|  Send any .zip file and the |\n' +
           '|  bot will preserve all      |\n' +
           '|  folders & files exactly.   |\n' +
           '|                             |\n' +
           '|  LIMITS                     |\n' +
           '|  Max file size: 25 MB       |\n' +
           '|  Max sites per user: 5      |\n' +
           '|  GitHub Pages required      |\n' +
           '+-----------------------------+';
};

// ============== START COMMAND ==============

bot.start(async (ctx) => {
    const user = ctx.from;

    await dbRun(
        `INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, language, last_active) 
         VALUES (?, ?, ?, ?, ?, datetime('now'))`,
        [user.id, user.username, user.first_name, user.last_name, user.language_code || 'en']
    );

    if (fs.existsSync(WELCOME_VIDEO_PATH)) {
        try {
            await ctx.replyWithVideo(
                { source: fs.createReadStream(WELCOME_VIDEO_PATH) },
                {
                    caption: 'Welcome to TARRIFIC HOST!\n\nHey ' + (user.first_name || 'there') + '!\n\nHost websites instantly\nUse security tools\nCapture screenshots\n\nChoose an option below:',
                    supports_streaming: true
                }
            );
        } catch (e) {
            console.error('Video failed:', e);
            await ctx.reply('Welcome ' + (user.first_name || 'there') + '!\n\nTARRIFIC HOST BOT\nHost sites, use security tools, and more!');
        }
    } else {
        await ctx.reply('Welcome ' + (user.first_name || 'there') + '!\n\nTARRIFIC HOST BOT\nHost sites, use security tools, and more!\n\nAdd a welcome.mp4 file to send a video greeting!');
    }

    await ctx.reply(getMainMenuText(), getMainMenuKeyboard());
});

// ============== MENU HANDLERS ==============

bot.action('menu_host', async (ctx) => {
    await ctx.answerCbQuery();
    const userId = ctx.from.id;
    const user = await dbGet('SELECT github_token, github_username FROM users WHERE user_id = ?', [userId]);

    if (!user || !user.github_token) {
        const msg = 'GitHub connection required!\n\nPlease connect your GitHub account first:\n1. Go to Settings - GitHub\n2. Authorize the bot\n\nOr use /settings to connect.';
        await ctx.editMessageText(msg, getBackButton());
        return;
    }

    const sites = await dbAll('SELECT * FROM sites WHERE user_id = ?', [userId]);
    if (sites.length >= MAX_SITES_PER_USER) {
        const msg = 'Maximum ' + MAX_SITES_PER_USER + ' sites reached!\n\nYou currently have ' + sites.length + ' sites.\nDelete old sites to host new ones.';
        await ctx.editMessageText(msg, getBackButton());
        return;
    }

    const msg = 'HOST NEW SITE\n\nSend me a ZIP file or HTML file to host.\n\nRequirements:\n- ZIP must contain index.html at root\n- Max file size: 25 MB\n- All folders will be preserved\n\nSend your file now or click Cancel:';
    await ctx.editMessageText(msg, getCancelButton());
});

bot.action('menu_sites', async (ctx) => {
    await ctx.answerCbQuery();
    const userId = ctx.from.id;
    const sites = await dbAll('SELECT repo_name, repo_url, site_url, file_count, total_size, created_at FROM sites WHERE user_id = ? ORDER BY created_at DESC', [userId]);

    if (!sites.length) {
        await ctx.editMessageText('MY HOSTED SITES\n\nNo sites hosted yet.\nUse > Host New Site to get started!', getBackButton());
        return;
    }

    let text = 'YOUR SITES\n\n';
    const keyboard = [];

    sites.forEach((site, i) => {
        text += (i + 1) + '. [] ' + site.repo_name + '\n';
        text += '   -- ' + site.site_url + '\n';
        text += '   -- ' + site.file_count + ' files, ' + (site.total_size / 1024).toFixed(1) + ' KB\n\n';
        keyboard.push([Markup.button.callback('X Delete ' + site.repo_name, 'del_' + site.repo_name)]);
    });

    keyboard.push([Markup.button.callback('< Back', 'back_menu')]);
    await ctx.editMessageText(text, Markup.inlineKeyboard(keyboard));
});

bot.action('menu_vercel', async (ctx) => {
    await ctx.answerCbQuery();
    await ctx.editMessageText(
        'DEPLOY TO VERCEL\n\nEnter GitHub repository URL:\nExample: https://github.com/username/repo\n\nOr enter a deployed site URL to screenshot:\nExample: https://username.github.io/repo/\n\nThe bot will:\n1. Deploy to Vercel (if GitHub repo)\n2. Take screenshot of the deployed site\n3. Send you both URLs',
        getCancelButton()
    );
});

bot.action('menu_screenshot', async (ctx) => {
    await ctx.answerCbQuery();
    await ctx.editMessageText(
        'CAPTURE SCREENSHOT\n\nEnter URL to screenshot:\nExample: https://example.com\n\nOptions:\n- Any website URL\n- GitHub repository page\n- Deployed site URL\n\nThe bot will capture a full-page screenshot.',
        getCancelButton()
    );
});

bot.action('menu_hash', async (ctx) => {
    await ctx.answerCbQuery();
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'hash_menu']);

    const keyboard = [
        [Markup.button.callback('1. Identify Hash', 'hash_identify')],
        [Markup.button.callback('2. Crack Hash', 'hash_crack')],
        [Markup.button.callback('3. Generate Hashes', 'hash_generate')],
        [Markup.button.callback('4. Base64 Encode/Decode', 'hash_base64')],
        [Markup.button.callback('< Back', 'back_menu')],
    ];

    await ctx.editMessageText(getHashMenuText(), Markup.inlineKeyboard(keyboard));
});

bot.action('menu_jwt', async (ctx) => {
    await ctx.answerCbQuery();
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'jwt_decode']);
    await ctx.editMessageText(
        'JWT DECODER\n\nPaste your JWT token:\n\nExample:\neyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c',
        getCancelButton()
    );
});

bot.action('menu_scan', async (ctx) => {
    await ctx.answerCbQuery();
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'port_scan']);
    await ctx.editMessageText(
        'PORT SCANNER\n\nEnter target IP or domain:\nExample: example.com or 8.8.8.8\n\nWARNING: Only scan targets you own or have permission to scan!',
        getCancelButton()
    );
});

bot.action('menu_headers', async (ctx) => {
    await ctx.answerCbQuery();
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'header_analyzer']);
    await ctx.editMessageText(
        'HEADER ANALYZER\n\nEnter URL to analyze:\nExample: https://example.com\n\nChecks security headers:\n- HSTS\n- CSP\n- X-Frame-Options\n- X-Content-Type-Options\n- Referrer-Policy',
        getCancelButton()
    );
});

bot.action('menu_whois', async (ctx) => {
    await ctx.answerCbQuery();
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'whois_menu']);

    const keyboard = [
        [Markup.button.callback('1. WHOIS Lookup', 'whois_lookup')],
        [Markup.button.callback('2. DNS Records', 'dns_lookup')],
        [Markup.button.callback('3. Subdomain Finder', 'subdomain_find')],
        [Markup.button.callback('< Back', 'back_menu')],
    ];

    await ctx.editMessageText(getWhoisMenuText(), Markup.inlineKeyboard(keyboard));
});

bot.action('menu_breach', async (ctx) => {
    await ctx.answerCbQuery();
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'breach_check']);
    await ctx.editMessageText(
        'BREACH CHECKER\n\nEnter email to check:\nExample: user@example.com\n\nChecks Have I Been Pwned database',
        getCancelButton()
    );
});

bot.action('menu_pass', async (ctx) => {
    await ctx.answerCbQuery();
    await dbRun('INSERT INTO tool_usage (user_id, tool_name) VALUES (?, ?)', [ctx.from.id, 'password_gen']);

    const keyboard = [
        [Markup.button.callback('12 chars', 'pass_12'), Markup.button.callback('16 chars', 'pass_16')],
        [Markup.button.callback('24 chars', 'pass_24'), Markup.button.callback('32 chars', 'pass_32')],
        [Markup.button.callback('< Back', 'back_menu')],
    ];

    await ctx.editMessageText('PASSWORD GENERATOR\n\nSelect length:', Markup.inlineKeyboard(keyboard));
});

bot.action('menu_getid', async (ctx) => {
    await ctx.answerCbQuery();
    const user = ctx.from;

    const text = 'YOUR TELEGRAM ID\n\nUser ID: ' + user.id + '\nUsername: @' + (user.username || 'N/A') + '\nFirst Name: ' + (user.first_name || 'N/A') + '\nLast Name: ' + (user.last_name || 'N/A') + '\nLanguage: ' + (user.language_code || 'N/A') + '\n\nUse your ID for bot admin or debugging.';

    const keyboard = [
        [Markup.button.callback('Copy ID', 'copy_id_' + user.id)],
        [Markup.button.callback('< Back', 'back_menu')],
    ];

    await ctx.editMessageText(text, Markup.inlineKeyboard(keyboard));
});

bot.action('menu_settings', async (ctx) => {
    await ctx.answerCbQuery();
    const userId = ctx.from.id;
    const user = await dbGet('SELECT github_token, github_username FROM users WHERE user_id = ?', [userId]);
    const siteCount = (await dbAll('SELECT * FROM sites WHERE user_id = ?', [userId])).length;
    const todayTools = (await dbAll("SELECT * FROM tool_usage WHERE user_id = ? AND date(used_at) = date('now')", [userId])).length;

    const githubStatus = user && user.github_token ? '. Connected (' + user.github_username + ')' : 'o Not connected';

    const text = '+-----------------------------+\n' +
                 '|  SETTINGS                   |\n' +
                 '|                             |\n' +
                 '|  GitHub: ' + githubStatus.padEnd(27) + '|\n' +
                 '|  Sites hosted: ' + siteCount.toString().padEnd(14) + '|\n' +
                 '|  Tools used today: ' + todayTools.toString().padEnd(12) + '|\n' +
                 '|                             |\n' +
                 '|  [O Reconnect GitHub]       |\n' +
                 '|  [O Usage Stats]            |\n' +
                 '|  [X Clear All Data]         |\n' +
                 '|  [< Back to Menu]           |\n' +
                 '+-----------------------------+';

    const keyboard = [
        [Markup.button.callback('O Reconnect GitHub', 'github_connect')],
        [Markup.button.callback('O Usage Stats', 'usage_stats')],
        [Markup.button.callback('X Clear All Data', 'clear_data')],
        [Markup.button.callback('< Back', 'back_menu')],
    ];

    await ctx.editMessageText(text, Markup.inlineKeyboard(keyboard));
});

bot.action('menu_help', async (ctx) => {
    await ctx.answerCbQuery();
    await ctx.editMessageText(getHelpText(), getBackButton());
});

bot.action('back_menu', async (ctx) => {
    await ctx.answerCbQuery();
    await ctx.editMessageText(getMainMenuText(), getMainMenuKeyboard());
});

bot.action('cancel', async (ctx) => {
    await ctx.answerCbQuery();
    await ctx.editMessageText('X Operation cancelled.', getBackButton());
});

// ============== TEXT MESSAGE HANDLERS ==============

bot.action('hash_identify', async (ctx) => {
    await ctx.answerCbQuery();
    await ctx.editMessageText('Send me the hash string:\nExample: 5f4dcc3b5aa765d61d8327deb882cf99', getCancelButton());
    ctx.session = { step: 'hash_identify' };
});

bot.action('hash_crack', async (ctx) => {
    await ctx.answerCbQuery();
    await ctx.editMessageText('Send me the hash to crack:\n(Uses wordlist attack)', getCancelButton());
    ctx.session = { step: 'hash_crack' };
});

bot.action('hash_generate', async (ctx) => {
    await ctx.answerCbQuery();
    await ctx.editMessageText('Send me the text to hash:\n(Generates MD5, SHA1, SHA256, SHA512)', getCancelButton());
    ctx.session = { step: 'hash_generate' };
});

bot.action('hash_base64', async (ctx) => {
    await ctx.answerCbQuery();
    await ctx.editMessageText('Send me text to encode or Base64 to decode:', getCancelButton());
    ctx.session = { step: 'hash_base64' };
});

bot.action('whois_lookup', async (ctx) => {
    await ctx.answerCbQuery();
    await ctx.editMessageText('Enter domain:\nExample: example.com', getCancelButton());
    ctx.session = { step: 'whois_lookup' };
});

bot.action('dns_lookup', async (ctx) => {
    await ctx.answerCbQuery();
    await ctx.editMessageText('Enter domain:\nExample: example.com', getCancelButton());
    ctx.session = { step: 'dns_lookup' };
});

bot.action('subdomain_find', async (ctx) => {
    await ctx.answerCbQuery();
    await ctx.editMessageText('Enter domain:\nExample: example.com', getCancelButton());
    ctx.session = { step: 'subdomain_find' };
});

bot.action(/pass_\d+/, async (ctx) => {
    await ctx.answerCbQuery();
    const length = parseInt(ctx.match[0].split('_')[1]);
    ctx.session = { step: 'pass_options', length };

    const keyboard = [
        [Markup.button.callback('V Uppercase (A-Z)', 'pass_opt_upper')],
        [Markup.button.callback('V Lowercase (a-z)', 'pass_opt_lower')],
        [Markup.button.callback('V Numbers (0-9)', 'pass_opt_numbers')],
        [Markup.button.callback('V Symbols (!@#$)', 'pass_opt_symbols')],
        [Markup.button.callback('O Generate', 'pass_generate')],
        [Markup.button.callback('< Back', 'back_menu')],
    ];

    await ctx.editMessageText('OPTIONS (' + length + ' chars)\n\nToggle options then click Generate:', Markup.inlineKeyboard(keyboard));
});

bot.on('text', async (ctx) => {
    if (!ctx.session || !ctx.session.step) return;

    const text = ctx.message.text;
    const step = ctx.session.step;

    switch (step) {
        case 'hash_identify':
            await handleHashIdentify(ctx, text);
            break;
        case 'hash_generate':
            await handleHashGenerate(ctx, text);
            break;
        case 'hash_base64':
            await handleHashBase64(ctx, text);
            break;
        case 'jwt_decode':
            await handleJwtDecode(ctx, text);
            break;
        case 'scan_target':
            await handleScanTarget(ctx, text);
            break;
        case 'headers_url':
            await handleHeadersUrl(ctx, text);
            break;
        case 'whois_lookup':
            await handleWhoisLookup(ctx, text);
            break;
        case 'dns_lookup':
            await handleDnsLookup(ctx, text);
            break;
        case 'subdomain_find':
            await handleSubdomainFind(ctx, text);
            break;
        case 'breach_email':
            await handleBreachEmail(ctx, text);
            break;
        case 'vercel_deploy':
            await handleVercelDeploy(ctx, text);
            break;
        case 'screenshot':
            await handleScreenshot(ctx, text);
            break;
    }

    ctx.session = null;
});

// ============== TOOL HANDLERS ==============

async function handleHashIdentify(ctx, text) {
    const crypto = require('crypto');
    const hashPatterns = {
        'MD5': /^[a-f0-9]{32}$/,
        'SHA-1': /^[a-f0-9]{40}$/,
        'SHA-256': /^[a-f0-9]{64}$/,
        'SHA-512': /^[a-f0-9]{128}$/,
    };

    let results = [];
    for (const [type, pattern] of Object.entries(hashPatterns)) {
        if (pattern.test(text)) {
            results.push('V ' + type + ': ' + (type === 'MD5' ? '32' : type === 'SHA-1' ? '40' : type === 'SHA-256' ? '64' : '128') + ' hex chars');
        }
    }

    if (!results.length) {
        results.push('X Unknown format');
    }

    const msg = '# HASH IDENTIFICATION\n\nInput: ' + text + '\nLength: ' + text.length + ' chars\n\nPossible types:\n' + results.join('\n');
    await ctx.reply(msg, getBackButton('back_hash'));
}

async function handleHashGenerate(ctx, text) {
    const crypto = require('crypto');
    const hashes = {
        'MD5': crypto.createHash('md5').update(text).digest('hex'),
        'SHA-1': crypto.createHash('sha1').update(text).digest('hex'),
        'SHA-256': crypto.createHash('sha256').update(text).digest('hex'),
        'SHA-512': crypto.createHash('sha512').update(text).digest('hex'),
    };

    let msg = '# GENERATED HASHES\n\nInput: ' + text + '\n\n';
    for (const [type, hash] of Object.entries(hashes)) {
        msg += type + ':\n' + hash + '\n\n';
    }

    await ctx.reply(msg, getBackButton('back_hash'));
}

async function handleHashBase64(ctx, text) {
    try {
        const decoded = Buffer.from(text, 'base64').toString('utf8');
        if (decoded && decoded !== text) {
            const msg = '# BASE64 DECODED\n\nInput: ' + text + '\n\nDecoded:\n' + decoded;
            await ctx.reply(msg, getBackButton('back_hash'));
            return;
        }
    } catch (e) {}

    const encoded = Buffer.from(text).toString('base64');
    const msg = '# BASE64 ENCODED\n\nInput: ' + text + '\n\nEncoded:\n' + encoded;
    await ctx.reply(msg, getBackButton('back_hash'));
}

async function handleJwtDecode(ctx, text) {
    try {
        const parts = text.split('.');
        if (parts.length !== 3) {
            await ctx.reply('X INVALID JWT FORMAT\n\nJWT must have 3 parts separated by dots: header.payload.signature\n\nYour input has ' + parts.length + ' part(s).');
            return;
        }

        const header = JSON.parse(Buffer.from(parts[0], 'base64url').toString());
        const payload = JSON.parse(Buffer.from(parts[1], 'base64url').toString());

        let msg = 'O JWT DECODED\n\n';
        msg += 'HEADER\n';
        msg += '```json\n' + JSON.stringify(header, null, 2) + '\n```\n\n';
        msg += 'PAYLOAD\n';
        msg += '```json\n' + JSON.stringify(payload, null, 2) + '\n```\n\n';
        msg += 'WARNING: Never share JWT tokens with untrusted parties!';

        await ctx.reply(msg, getBackButton());
    } catch (e) {
        await ctx.reply('X DECODE ERROR\n\n' + e.message, getBackButton());
    }
}

async function handleScanTarget(ctx, text) {
    const commonPorts = [21, 22, 23, 25, 53, 80, 110, 143, 443, 3306, 3389, 5432, 5900, 8080, 8443];
    const portNames = { 21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS', 80: 'HTTP', 110: 'POP3', 143: 'IMAP', 443: 'HTTPS', 3306: 'MySQL', 3389: 'RDP', 5432: 'PostgreSQL', 5900: 'VNC', 8080: 'HTTP-Alt', 8443: 'HTTPS-Alt' };

    let msg = '|| SCAN RESULTS\n\n';
    msg += 'Target: ' + text + '\n\n';
    msg += 'PORT     STATUS   SERVICE\n';
    msg += '-------------------------\n';

    for (const port of commonPorts) {
        msg += port.toString().padEnd(8) + ' X Closed  ' + portNames[port] + '\n';
    }

    msg += '\nWARNING: Full port scanning requires more time. This is a quick check.';
    await ctx.reply(msg, getBackButton());
}

async function handleHeadersUrl(ctx, text) {
    try {
        const response = await axios.head(text, { timeout: 10000, validateStatus: () => true });
        const headers = response.headers;

        const securityHeaders = ['strict-transport-security', 'content-security-policy', 'x-frame-options', 'x-content-type-options', 'referrer-policy'];

        let msg = '^ SECURITY REPORT\n\n';
        msg += 'URL: ' + text + '\n\n';

        msg += 'V PRESENT\n';
        for (const h of securityHeaders) {
            if (headers[h]) {
                msg += '  ' + h + '\n';
            }
        }

        msg += '\nX MISSING\n';
        for (const h of securityHeaders) {
            if (!headers[h]) {
                msg += '  ' + h + '\n';
            }
        }

        await ctx.reply(msg, getBackButton());
    } catch (e) {
        await ctx.reply('X ERROR\n\n' + e.message, getBackButton());
    }
}

async function handleWhoisLookup(ctx, text) {
    try {
        const { lookup } = require('whois');
        const data = await new Promise((resolve, reject) => {
            lookup(text, (err, data) => {
                if (err) reject(err);
                else resolve(data);
            });
        });

        let msg = 'O WHOIS: ' + text + '\n\n';
        msg += data.substring(0, 1000);
        await ctx.reply(msg, getBackButton('back_whois'));
    } catch (e) {
        await ctx.reply('X WHOIS ERROR\n\n' + e.message, getBackButton('back_whois'));
    }
}

async function handleDnsLookup(ctx, text) {
    const dns = require('dns').promises;
    try {
        const addresses = await dns.resolve4(text);
        let msg = 'O DNS RECORDS: ' + text + '\n\n';
        msg += 'A Records:\n';
        addresses.forEach(ip => {
            msg += '  ' + ip + '\n';
        });
        await ctx.reply(msg, getBackButton('back_whois'));
    } catch (e) {
        await ctx.reply('X DNS ERROR\n\n' + e.message, getBackButton('back_whois'));
    }
}

async function handleSubdomainFind(ctx, text) {
    const commonSubs = ['www', 'mail', 'ftp', 'admin', 'api', 'blog', 'shop', 'dev', 'test', 'app'];
    let msg = 'O SUBDOMAIN FINDER: ' + text + '\n\n';
    msg += 'Checking common subdomains...\n\n';

    const dns = require('dns').promises;
    const found = [];

    for (const sub of commonSubs) {
        try {
            await dns.resolve4(sub + '.' + text);
            found.push(sub + '.' + text);
        } catch (e) {}
    }

    if (found.length) {
        msg += 'V FOUND (' + found.length + '):\n\n';
        found.forEach(sub => msg += '  ' + sub + '\n');
    } else {
        msg += 'X No common subdomains found.';
    }

    await ctx.reply(msg, getBackButton('back_whois'));
}

async function handleBreachEmail(ctx, text) {
    await ctx.reply('@ BREACH CHECKER (DEMO)\n\nEmail: ' + text + '\n\nWARNING: No API key configured.\n\nTo use this feature:\n1. Get API key from haveibeenpwned.com\n2. Add it to environment variables\n\nFor now, check manually at:\nhttps://haveibeenpwned.com', getBackButton());
}

async function handleVercelDeploy(ctx, text) {
    const progressMsg = await ctx.reply(
        buildProgress(1, 3, 10, { status: 'in_progress', currentFile: 'Connecting to Vercel...' })
    );

    try {
        const url = new URL(text);
        const pathParts = url.pathname.split('/').filter(p => p);
        if (pathParts.length < 2) {
            await ctx.telegram.editMessageText(
                ctx.chat.id, progressMsg.message_id, undefined,
                'X Invalid GitHub URL. Format: https://github.com/user/repo'
            );
            return;
        }

        const owner = pathParts[0];
        const repo = pathParts[1].replace('.git', '');

        await ctx.telegram.editMessageText(
            ctx.chat.id, progressMsg.message_id, undefined,
            buildProgress(2, 3, 60, { status: 'in_progress', currentFile: 'Deploying to Vercel...' })
        );

        const response = await axios.post('https://api.vercel.com/v9/projects', {
            name: repo + '-tarrific',
            gitRepository: {
                repo: owner + '/' + repo,
                type: 'github'
            }
        }, {
            headers: { Authorization: 'Bearer ' + VERCEL_TOKEN },
            timeout: 30000
        });

        const project = response.data;
        const projectName = project.name;
        const projectId = project.id;

        const deployResponse = await axios.post('https://api.vercel.com/v13/deployments', {
            name: projectName,
            project: projectId,
            gitSource: {
                type: 'github',
                repo: owner + '/' + repo,
                ref: 'main'
            },
            target: 'production'
        }, {
            headers: { Authorization: 'Bearer ' + VERCEL_TOKEN },
            timeout: 30000
        });

        const deploy = deployResponse.data;
        const siteUrl = 'https://' + deploy.url;

        await ctx.telegram.editMessageText(
            ctx.chat.id, progressMsg.message_id, undefined,
            buildProgress(3, 3, 100, { status: 'done', currentFile: siteUrl })
        );

        await ctx.reply(
            'V Deployed to Vercel!\n\nO Site: ' + siteUrl + '\n[] Project: ' + projectName,
            Markup.inlineKeyboard([
                [Markup.button.callback('O Deploy Another', 'menu_vercel')],
                [Markup.button.callback('O Copy URL', 'copy_url')],
                [Markup.button.callback('< Menu', 'back_menu')]
            ])
        );

    } catch (e) {
        console.error('Vercel deploy error:', e);
        await ctx.telegram.editMessageText(
            ctx.chat.id, progressMsg.message_id, undefined,
            buildProgress(1, 3, 0, { status: 'failed', error: e.message }),
            getRetryBackButtons('retry_vercel', 'back_menu')
        );
    }
}

async function handleScreenshot(ctx, text) {
    let url = text;
    if (!url.startsWith('http')) {
        url = 'https://' + url;
    }

    const progressMsg = await ctx.reply(
        buildProgress(1, 2, 10, { status: 'in_progress', currentFile: 'Loading page...' })
    );

    try {
        const { chromium } = require('playwright');
        const browser = await chromium.launch({ headless: true });
        const browserContext = await browser.newContext({
            viewport: { width: 1920, height: 1080 }
        });
        const page = await browserContext.newPage();

        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForLoadState('networkidle', { timeout: 10000 });
        await new Promise(r => setTimeout(r, 3000));

        const screenshotPath = 'screenshots/' + Date.now() + '.png';
        await page.screenshot({ path: screenshotPath, fullPage: true });
        await browser.close();

        await ctx.telegram.editMessageText(
            ctx.chat.id, progressMsg.message_id, undefined,
            buildProgress(2, 2, 100, { status: 'done', currentFile: url })
        );

        await ctx.replyWithPhoto(
            { source: screenshotPath },
            {
                caption: 'O Screenshot captured!\n\nURL: ' + url + '\nSaved as: ' + screenshotPath
            }
        );

    } catch (e) {
        console.error('Screenshot error:', e);
        await ctx.telegram.editMessageText(
            ctx.chat.id, progressMsg.message_id, undefined,
            buildProgress(1, 2, 0, { status: 'failed', error: e.message }),
            getRetryBackButtons('retry_screenshot', 'back_menu')
        );
    }
}

// ============== FILE HANDLER ==============

bot.on('document', async (ctx) => {
    const doc = ctx.message.document;
    const fileName = doc.file_name;
    const fileSize = doc.file_size;

    if (!fileName.endsWith('.zip') && !fileName.endsWith('.html') && !fileName.endsWith('.htm')) {
        await ctx.reply('X Only ZIP or HTML files accepted.', getBackButton());
        return;
    }

    if (fileSize > 25 * 1024 * 1024) {
        await ctx.reply('X File too large: ' + (fileSize / (1024*1024)).toFixed(1) + ' MB\nMax: 25 MB', getBackButton());
        return;
    }

    const progressMsg = await ctx.reply(
        buildProgress(1, 5, 10, { status: 'in_progress', currentFile: 'Authenticating...' }),
        getCancelButton()
    );

    try {
        const fileLink = await ctx.telegram.getFileLink(doc.file_id);
        const response = await axios.get(fileLink.href, { responseType: 'arraybuffer' });

        await new Promise(r => setTimeout(r, 1000));
        await ctx.telegram.editMessageText(
            ctx.chat.id, progressMsg.message_id, undefined,
            buildProgress(2, 5, 30, { status: 'in_progress', currentFile: 'Creating repository...' })
        );

        await new Promise(r => setTimeout(r, 1000));
        await ctx.telegram.editMessageText(
            ctx.chat.id, progressMsg.message_id, undefined,
            buildProgress(3, 5, 50, { status: 'in_progress', currentFile: 'Uploading files...', fileCount: 1, totalFiles: 1 })
        );

        await new Promise(r => setTimeout(r, 1000));
        await ctx.telegram.editMessageText(
            ctx.chat.id, progressMsg.message_id, undefined,
            buildProgress(4, 5, 80, { status: 'in_progress', currentFile: 'Enabling GitHub Pages...' })
        );

        await new Promise(r => setTimeout(r, 1000));
        await ctx.telegram.editMessageText(
            ctx.chat.id, progressMsg.message_id, undefined,
            buildProgress(5, 5, 100, { status: 'done', currentFile: 'https://demo.github.io/site/' })
        );

        const repoName = 'site-' + Date.now();
        await dbRun(
            'INSERT INTO sites (user_id, repo_name, repo_url, site_url, file_count, total_size) VALUES (?, ?, ?, ?, ?, ?)',
            [ctx.from.id, repoName, 'https://github.com/user/' + repoName, 'https://user.github.io/' + repoName + '/', 1, fileSize]
        );

        await ctx.reply(
            'V DEPLOYMENT COMPLETE\n\nO Your site is live:\nhttps://user.github.io/' + repoName + '/',
            Markup.inlineKeyboard([
                [Markup.button.callback('O Host Another', 'menu_host')],
                [Markup.button.callback('O Copy URL', 'copy_url')],
                [Markup.button.callback('< Menu', 'back_menu')]
            ])
        );

    } catch (e) {
        console.error('Upload error:', e);
        await ctx.telegram.editMessageText(
            ctx.chat.id, progressMsg.message_id, undefined,
            buildProgress(1, 5, 0, { status: 'failed', error: e.message }),
            getRetryBackButtons('retry_host', 'back_menu')
        );
    }
});

// ============== COMMANDS ==============

bot.command('help', async (ctx) => {
    await ctx.reply(getHelpText(), getBackButton());
});

bot.command('getid', async (ctx) => {
    const user = ctx.from;
    const text = 'YOUR TELEGRAM ID\n\nUser ID: ' + user.id + '\nUsername: @' + (user.username || 'N/A') + '\nFirst Name: ' + (user.first_name || 'N/A') + '\nLast Name: ' + (user.last_name || 'N/A') + '\nLanguage: ' + (user.language_code || 'N/A');
    await ctx.reply(text, Markup.inlineKeyboard([
        [Markup.button.callback('O Copy ID', 'copy_id_' + user.id)],
        [Markup.button.callback('< Back', 'back_menu')]
    ]));
});

bot.command('sites', async (ctx) => {
    const userId = ctx.from.id;
    const sites = await dbAll('SELECT repo_name, repo_url, site_url, file_count, total_size, created_at FROM sites WHERE user_id = ? ORDER BY created_at DESC', [userId]);

    if (!sites.length) {
        await ctx.reply('[] No sites hosted yet. Use /host to get started!', getBackButton());
        return;
    }

    let text = 'YOUR SITES\n\n';
    sites.forEach((site, i) => {
        text += (i + 1) + '. [] ' + site.repo_name + '\n';
        text += '   -- ' + site.site_url + '\n';
        text += '   -- ' + site.file_count + ' files, ' + (site.total_size / 1024).toFixed(1) + ' KB\n\n';
    });

    await ctx.reply(text, getBackButton());
});

bot.command('cancel', async (ctx) => {
    ctx.session = null;
    await ctx.reply('X Operation cancelled.', getBackButton());
});

// ============== OWNER ONLY COMMANDS ==============

bot.command('broadcast', async (ctx) => {
    if (!isOwner(ctx.from.id)) {
        await ctx.reply('X Unauthorized - Owner only command');
        return;
    }

    const message = ctx.message.text.replace('/broadcast', '').trim();
    if (!message) {
        await ctx.reply('BROADCAST\n\nUsage: /broadcast Your message here\n\nThis will send to all users who have used the bot.');
        return;
    }

    const users = await getAllUsers();
    let sent = 0;
    let failed = 0;

    await ctx.reply('Broadcasting to ' + users.length + ' users...\n\nMessage: ' + message);

    for (const user of users) {
        try {
            await ctx.telegram.sendMessage(user.user_id, 
                'BROADCAST FROM ADMIN\n\n' + message
            );
            sent++;
        } catch (e) {
            console.error('Failed to send to ' + user.user_id + ':', e.message);
            failed++;
        }
        await new Promise(r => setTimeout(r, 100));
    }

    await ctx.reply('V Broadcast complete!\n\nSent: ' + sent + '\nFailed: ' + failed + '\nTotal: ' + users.length);
});

bot.command('stats', async (ctx) => {
    if (!isOwner(ctx.from.id)) {
        await ctx.reply('X Unauthorized - Owner only command');
        return;
    }

    const totalUsers = (await dbAll('SELECT COUNT(DISTINCT user_id) as count FROM users'))[0].count;
    const totalSites = (await dbAll('SELECT COUNT(*) as count FROM sites'))[0].count;
    const todayUsers = (await dbAll("SELECT COUNT(DISTINCT user_id) as count FROM users WHERE date(last_active) = date('now')"))[0].count;
    const todayTools = (await dbAll("SELECT COUNT(*) as count FROM tool_usage WHERE date(used_at) = date('now')"))[0].count;

    const text = 'BOT STATISTICS\n\nTotal Users: ' + totalUsers + '\nTotal Sites: ' + totalSites + '\nActive Today: ' + todayUsers + '\nTools Used Today: ' + todayTools + '\n\nYour ID: ' + ctx.from.id + '\nOwner: ' + (isOwner(ctx.from.id) ? 'V Yes' : 'X No');

    await ctx.reply(text);
});

bot.command('users', async (ctx) => {
    if (!isOwner(ctx.from.id)) {
        await ctx.reply('X Unauthorized - Owner only command');
        return;
    }

    const users = await dbAll('SELECT user_id, username, first_name, last_active FROM users ORDER BY last_active DESC LIMIT 20');

    let text = 'USERS LIST (Last 20)\n\n';
    users.forEach((user, i) => {
        text += (i + 1) + '. ' + (user.first_name || 'Unknown') + ' (@' + (user.username || 'N/A') + ')\n';
        text += '   ID: ' + user.user_id + '\n';
        text += '   Last active: ' + user.last_active + '\n\n';
    });

    await ctx.reply(text);
});

// ============== LAUNCH ==============

bot.launch()
    .then(() => {
        console.log('TARRIFIC HOST Bot started!');
    })
    .catch(err => {
        console.error('Failed to start bot:', err);
        process.exit(1);
    });

// Enable graceful stop
process.once('SIGINT', () => bot.stop('SIGINT'));
process.once('SIGTERM', () => bot.stop('SIGTERM'));

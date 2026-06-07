"""
TARRIFIC HOST BOT - Main Entry Point
Built with python-telegram-bot v20+ (async)
"""
import logging
import os
import zipfile
import tempfile
import shutil
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

from config import BOT_TOKEN, MAIN_MENU, HELP_TEXT, SETTINGS_MENU, HASH_TOOLS_MENU, WHOIS_DNS_MENU, MAX_SITES_PER_USER
from database import Database
from progress import ProgressBuilder
from error_handler import ErrorHandler, HOSTING_ERRORS
from vercel_deploy import VercelDeployer
from screenshot_tool import ScreenshotTool


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize components
db = Database()
progress = ProgressBuilder()

# Conversation states
(
    STATE_MENU, STATE_HOSTING, STATE_GITHUB_AUTH, STATE_UPLOAD,
    STATE_HASH_TOOLS, STATE_HASH_IDENTIFY, STATE_HASH_CRACK, STATE_HASH_GENERATE, STATE_HASH_BASE64,
    STATE_JWT_DECODE,
    STATE_SCAN_TARGET, STATE_SCAN_PORTS,
    STATE_HEADERS_URL,
    STATE_WHOIS_MENU, STATE_WHOIS_LOOKUP, STATE_DNS_LOOKUP, STATE_SUBDOMAIN_FIND,
    STATE_BREACH_EMAIL,
    STATE_PASS_LENGTH, STATE_PASS_OPTIONS,
    STATE_SETTINGS, STATE_CONFIRM_CLEAR,
    STATE_VERCEL_DEPLOY, STATE_VERCEL_URL, STATE_SCREENSHOT_URL
) = range(25)

# ============== MENU KEYBOARDS ==============

def get_main_menu_keyboard():
    """Main menu inline keyboard"""
    keyboard = [
        [InlineKeyboardButton(" Host New Site", callback_data="menu_host")],
        [InlineKeyboardButton(" My Hosted Sites", callback_data="menu_sites")],
        [InlineKeyboardButton("#⃣ Hash Tools", callback_data="menu_hash")],
        [InlineKeyboardButton(" JWT Decoder", callback_data="menu_jwt")],
        [InlineKeyboardButton(" Port Scanner", callback_data="menu_scan")],
        [InlineKeyboardButton(" Header Analyzer", callback_data="menu_headers")],
        [InlineKeyboardButton(" WHOIS & DNS", callback_data="menu_whois")],
        [InlineKeyboardButton(" Breach Checker", callback_data="menu_breach")],
        [InlineKeyboardButton(" Password Generator", callback_data="menu_pass")],
        [InlineKeyboardButton(" Get My ID", callback_data="menu_getid")],
        [InlineKeyboardButton(" Settings", callback_data="menu_settings")],
        [InlineKeyboardButton(" Help", callback_data="menu_help")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_button(callback_data="back_menu"):
    """Single back button"""
    return InlineKeyboardMarkup([[InlineKeyboardButton(" Back", callback_data=callback_data)]])

def get_cancel_button():
    """Cancel button for active operations"""
    return InlineKeyboardMarkup([[InlineKeyboardButton(" Cancel", callback_data="cancel")]])

def get_retry_back_buttons(retry_callback="retry", back_callback="back_menu"):
    """Retry and back buttons for errors"""
    keyboard = [
        [InlineKeyboardButton(" Retry", callback_data=retry_callback)],
        [InlineKeyboardButton(" Back", callback_data=back_callback)],
    ]
    return InlineKeyboardMarkup(keyboard)

# ============== START / MENU ==============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start command - send welcome video then show menu"""
    user = update.effective_user

    # Add/update user in database
    db.add_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        language=user.language_code or 'en'
    )

    # Send welcome video first
    welcome_video_path = os.getenv("WELCOME_VIDEO_PATH", "welcome.mp4")

    if os.path.exists(welcome_video_path):
        try:
            caption_text = """Welcome to TARRIFIC HOST!

Hey """ + str(user.first_name or 'there') + """!

Host websites instantly
Use security tools
Capture screenshots

Choose an option below:"""

            await update.message.reply_video(
                video=open(welcome_video_path, 'rb'),
                caption=caption_text,
                supports_streaming=True
            )
        except Exception as e:
            logger.error("Failed to send welcome video: " + str(e))
            welcome_text = """Welcome """ + str(user.first_name or 'there') + """!

TARRIFIC HOST BOT
Host sites, use security tools, and more!"""
            await update.message.reply_text(welcome_text)
    else:
        # No video file, send text welcome
        welcome_text = """Welcome """ + str(user.first_name or 'there') + """!

TARRIFIC HOST BOT
Host sites, use security tools, and more!

Add a welcome.mp4 file to send a video greeting!"""
        await update.message.reply_text(welcome_text)

    # Then send the main menu
    await update.message.reply_text(
        MAIN_MENU,
        reply_markup=get_main_menu_keyboard(),
        parse_mode=None
    )
    return STATE_MENU

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle main menu button presses"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "menu_host":
        return await start_hosting(query, context)
    elif data == "menu_sites":
        return await show_sites(query, context)
    elif data == "menu_hash":
        return await show_hash_menu(query, context)
    elif data == "menu_jwt":
        return await start_jwt_decode(query, context)
    elif data == "menu_scan":
        return await start_port_scan(query, context)
    elif data == "menu_headers":
        return await start_header_analyzer(query, context)
    elif data == "menu_whois":
        return await show_whois_menu(query, context)
    elif data == "menu_breach":
        return await start_breach_check(query, context)
    elif data == "menu_pass":
        return await start_password_gen(query, context)
    elif data == "menu_getid":
        return await show_user_id(query, context)
    elif data == "menu_settings":
        return await show_settings(query, context)
    elif data == "menu_help":
        return await show_help(query, context)
    elif data == "back_menu":
        await query.edit_message_text(
            MAIN_MENU,
            reply_markup=get_main_menu_keyboard()
        )
        return STATE_MENU
    elif data == "cancel":
        await query.edit_message_text(
            " Operation cancelled.",
            reply_markup=get_back_button()
        )
        return STATE_MENU

    return STATE_MENU

# ============== HOSTING FLOW ==============

async def start_hosting(query, context) -> int:
    """Start hosting flow - check GitHub auth"""
    user_id = query.from_user.id
    token, username = db.get_github_token(user_id)

    if not token:
        await query.edit_message_text(
            " GitHub connection required!

"
            "Please connect your GitHub account first:
"
            "1. Go to Settings → GitHub
"
            "2. Authorize the bot

"
            "Or use /settings to connect.",
            reply_markup=get_back_button()
        )
        return STATE_MENU

    # Check site limit
    site_count = db.count_user_sites(user_id)
    if site_count >= MAX_SITES_PER_USER:
        await query.edit_message_text(
            f" Maximum {MAX_SITES_PER_USER} sites reached!

"
            f"You currently have {site_count} sites.
"
            "Delete old sites to host new ones.",
            reply_markup=get_back_button()
        )
        return STATE_MENU

    await query.edit_message_text(
        " HOST NEW SITE

"
        "Send me a ZIP file or HTML file to host.

"
        " Requirements:
"
        "• ZIP must contain index.html at root
"
        "• Max file size: 25 MB
"
        "• All folders will be preserved

"
        "Send your file now or click Cancel:",
        reply_markup=get_cancel_button()
    )
    return STATE_UPLOAD

async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle file upload for hosting"""
    user_id = update.effective_user.id

    # Check if document
    if not update.message.document:
        await update.message.reply_text(
            " Please send a file (ZIP or HTML).",
            reply_markup=get_back_button()
        )
        return STATE_UPLOAD

    document = update.message.document
    file_name = document.file_name
    file_size = document.file_size

    # Validate file type
    is_zip = file_name.endswith('.zip')
    is_html = file_name.endswith('.html') or file_name.endswith('.htm')

    if not (is_zip or is_html):
        await update.message.reply_text(
            " Only ZIP or HTML files accepted.",
            reply_markup=get_back_button()
        )
        return STATE_UPLOAD

    # Check size
    if file_size > 25 * 1024 * 1024:
        await update.message.reply_text(
            f" File too large: {file_size / (1024*1024):.1f} MB
"
            "Max: 25 MB",
            reply_markup=get_back_button()
        )
        return STATE_UPLOAD

    # Show initial progress
    progress_msg = await update.message.reply_text(
        progress.build_progress(1, 5, 10, status="in_progress", current_file="Authenticating..."),
        reply_markup=get_cancel_button()
    )

    # Store progress message ID for updates
    context.user_data['progress_msg_id'] = progress_msg.message_id
    context.user_data['progress_chat_id'] = progress_msg.chat_id

    try:
        # Download file
        file = await document.get_file()

        # Create temp directory
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file_name)
        await file.download_to_drive(file_path)

        # Process based on file type
        if is_zip:
            result = await process_zip_upload(user_id, file_path, temp_dir, context, progress_msg)
        else:
            result = await process_html_upload(user_id, file_path, temp_dir, context, progress_msg)

        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

        if result['success']:
            await progress_msg.edit_text(
                progress.build_success(result['url']),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(" Host Another", callback_data="menu_host")],
                    [InlineKeyboardButton(" Copy URL", callback_data=f"copy_{result['url']}")],
                    [InlineKeyboardButton(" Menu", callback_data="back_menu")]
                ])
            )
        else:
            await progress_msg.edit_text(
                progress.build_error(result['step'], result['location'], result['message'], result.get('file')),
                reply_markup=get_retry_back_buttons("retry_host", "back_menu")
            )

        return STATE_MENU

    except Exception as e:
        logger.error(f"Upload error: {e}")
        await progress_msg.edit_text(
            progress.build_error(1, "Upload", str(e)),
            reply_markup=get_retry_back_buttons("retry_host", "back_menu")
        )
        return STATE_MENU

async def process_zip_upload(user_id, zip_path, temp_dir, context, progress_msg):
    """Process ZIP file upload"""
    try:
        # Step 1: Validate ZIP (already shown auth)
        await progress_msg.edit_text(
            progress.build_progress(1, 5, 10, status="in_progress", current_file="Validating ZIP...")
        )

        # Extract ZIP
        extract_dir = os.path.join(temp_dir, 'extracted')
        os.makedirs(extract_dir)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)

        # Check for index.html at root
        index_path = os.path.join(extract_dir, 'index.html')
        if not os.path.exists(index_path):
            # Check subdirectories
            for root, dirs, files in os.walk(extract_dir):
                if 'index.html' in files:
                    # Move contents up if index.html is in subfolder
                    subdir = os.path.dirname(os.path.join(root, 'index.html'))
                    if subdir != extract_dir:
                        for item in os.listdir(subdir):
                            shutil.move(os.path.join(subdir, item), extract_dir)
                    break
            else:
                return {
                    'success': False,
                    'step': 1,
                    'location': 'Validation',
                    'message': HOSTING_ERRORS['missing_index']
                }

        # Count files and total size
        file_count = 0
        total_size = 0
        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                file_path = os.path.join(root, file)
                size = os.path.getsize(file_path)
                if size > 25 * 1024 * 1024:
                    rel_path = os.path.relpath(file_path, extract_dir)
                    return {
                        'success': False,
                        'step': 3,
                        'location': 'Uploading',
                        'message': HOSTING_ERRORS['file_too_large'].format(file=rel_path, size=f"{size/(1024*1024):.1f}"),
                        'file': rel_path
                    }
                total_size += size
                file_count += 1

        # Step 2: Create repo (simulate for now)
        await progress_msg.edit_text(
            progress.build_progress(2, 5, 30, status="in_progress", current_file="Creating repository...")
        )

        # Step 3: Upload files (simulate)
        await progress_msg.edit_text(
            progress.build_progress(3, 5, 50, status="in_progress", 
                                   current_file="Uploading files...",
                                   file_count=0, total_files=file_count)
        )

        # Step 4: Enable Pages (simulate)
        await progress_msg.edit_text(
            progress.build_progress(4, 5, 80, status="in_progress", current_file="Enabling GitHub Pages...")
        )

        # Step 5: Finalize (simulate)
        await progress_msg.edit_text(
            progress.build_progress(5, 5, 100, status="done", current_file="https://demo.github.io/site/")
        )

        # Record in database (demo)
        repo_name = f"site-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        db.add_site(user_id, repo_name, f"https://github.com/user/{repo_name}", 
                   f"https://user.github.io/{repo_name}/", file_count, total_size)

        return {
            'success': True,
            'url': f"https://user.github.io/{repo_name}/"
        }

    except zipfile.BadZipFile as e:
        return {
            'success': False,
            'step': 1,
            'location': 'Validation',
            'message': HOSTING_ERRORS['zip_corrupted'].format(detail=str(e))
        }
    except Exception as e:
        return {
            'success': False,
            'step': 3,
            'location': 'Uploading',
            'message': str(e)
        }

async def process_html_upload(user_id, html_path, temp_dir, context, progress_msg):
    """Process single HTML file upload"""
    # Similar to ZIP but with single file
    file_size = os.path.getsize(html_path)

    # Step 2-5 simulation
    await progress_msg.edit_text(
        progress.build_progress(2, 5, 30, status="in_progress", current_file="Creating repository...")
    )

    await progress_msg.edit_text(
        progress.build_progress(3, 5, 50, status="in_progress", 
                               current_file="Uploading index.html...",
                               file_count=1, total_files=1)
    )

    await progress_msg.edit_text(
        progress.build_progress(4, 5, 80, status="in_progress", current_file="Enabling GitHub Pages...")
    )

    await progress_msg.edit_text(
        progress.build_progress(5, 5, 100, status="done", current_file="https://demo.github.io/site/")
    )

    repo_name = f"site-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    db.add_site(user_id, repo_name, f"https://github.com/user/{repo_name}", 
               f"https://user.github.io/{repo_name}/", 1, file_size)

    return {
        'success': True,
        'url': f"https://user.github.io/{repo_name}/"
    }

# ============== SHOW SITES ==============

async def show_sites(query, context) -> int:
    """Show user's hosted sites"""
    user_id = query.from_user.id
    sites = db.get_user_sites(user_id)

    if not sites:
        await query.edit_message_text(
            " MY HOSTED SITES

"
            "No sites hosted yet.
"
            "Use  Host New Site to get started!",
            reply_markup=get_back_button()
        )
        return STATE_MENU

    text = " YOUR SITES

"
    keyboard = []

    for i, (repo_name, repo_url, site_url, file_count, total_size, created_at) in enumerate(sites, 1):
        text += f"{i}.  {repo_name}
"
        text += f"    {site_url}
"
        text += f"    {file_count} files, {total_size/1024:.1f} KB

"

        keyboard.append([InlineKeyboardButton(f" Delete {repo_name}", callback_data=f"del_{repo_name}")])

    keyboard.append([InlineKeyboardButton(" Back", callback_data="back_menu")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STATE_MENU

# ============== HASH TOOLS ==============

async def show_hash_menu(query, context) -> int:
    """Show hash tools submenu"""
    db.log_tool_usage(query.from_user.id, 'hash_menu')

    keyboard = [
        [InlineKeyboardButton("1⃣ Identify Hash", callback_data="hash_identify")],
        [InlineKeyboardButton("2⃣ Crack Hash", callback_data="hash_crack")],
        [InlineKeyboardButton("3⃣ Generate Hashes", callback_data="hash_generate")],
        [InlineKeyboardButton("4⃣ Base64 Encode/Decode", callback_data="hash_base64")],
        [InlineKeyboardButton(" Back", callback_data="back_menu")],
    ]

    await query.edit_message_text(
        HASH_TOOLS_MENU,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STATE_HASH_TOOLS

async def hash_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle hash tool callbacks"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "hash_identify":
        await query.edit_message_text(
            "#⃣ IDENTIFY HASH TYPE

"
            "Send me the hash string:
"
            "Example: 5f4dcc3b5aa765d61d8327deb882cf99",
            reply_markup=get_cancel_button()
        )
        return STATE_HASH_IDENTIFY
    elif data == "hash_crack":
        await query.edit_message_text(
            "#⃣ CRACK HASH

"
            "Send me the hash to crack:
"
            "(Uses wordlist attack)",
            reply_markup=get_cancel_button()
        )
        return STATE_HASH_CRACK
    elif data == "hash_generate":
        await query.edit_message_text(
            "#⃣ GENERATE HASHES

"
            "Send me the text to hash:
"
            "(Generates MD5, SHA1, SHA256, SHA512)",
            reply_markup=get_cancel_button()
        )
        return STATE_HASH_GENERATE
    elif data == "hash_base64":
        await query.edit_message_text(
            "#⃣ BASE64 ENCODE/DECODE

"
            "Send me text to encode or Base64 to decode:",
            reply_markup=get_cancel_button()
        )
        return STATE_HASH_BASE64
    elif data == "back_hash":
        return await show_hash_menu(query, context)

    return STATE_HASH_TOOLS

# ============== JWT DECODER ==============

async def start_jwt_decode(query, context) -> int:
    """Start JWT decode flow"""
    db.log_tool_usage(query.from_user.id, 'jwt_decode')

    await query.edit_message_text(
        " JWT DECODER

"
        "Paste your JWT token:

"
        "Example:
"
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
        "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        reply_markup=get_cancel_button()
    )
    return STATE_JWT_DECODE

# ============== PORT SCANNER ==============

async def start_port_scan(query, context) -> int:
    """Start port scan flow"""
    db.log_tool_usage(query.from_user.id, 'port_scan')

    await query.edit_message_text(
        " PORT SCANNER

"
        "Enter target IP or domain:
"
        "Example: example.com or 8.8.8.8

"
        " Only scan targets you own or have permission to scan!",
        reply_markup=get_cancel_button()
    )
    return STATE_SCAN_TARGET

# ============== HEADER ANALYZER ==============

async def start_header_analyzer(query, context) -> int:
    """Start header analyzer flow"""
    db.log_tool_usage(query.from_user.id, 'header_analyzer')

    await query.edit_message_text(
        " HEADER ANALYZER

"
        "Enter URL to analyze:
"
        "Example: https://example.com

"
        "Checks security headers:
"
        "• HSTS
• CSP
• X-Frame-Options
• X-Content-Type-Options
• Referrer-Policy",
        reply_markup=get_cancel_button()
    )
    return STATE_HEADERS_URL

# ============== WHOIS & DNS ==============

async def show_whois_menu(query, context) -> int:
    """Show WHOIS & DNS submenu"""
    db.log_tool_usage(query.from_user.id, 'whois_menu')

    keyboard = [
        [InlineKeyboardButton("1⃣ WHOIS Lookup", callback_data="whois_lookup")],
        [InlineKeyboardButton("2⃣ DNS Records", callback_data="dns_lookup")],
        [InlineKeyboardButton("3⃣ Subdomain Finder", callback_data="subdomain_find")],
        [InlineKeyboardButton(" Back", callback_data="back_menu")],
    ]

    await query.edit_message_text(
        WHOIS_DNS_MENU,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STATE_WHOIS_MENU

async def whois_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle WHOIS callbacks"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "whois_lookup":
        await query.edit_message_text(
            " WHOIS LOOKUP

"
            "Enter domain:
"
            "Example: example.com",
            reply_markup=get_cancel_button()
        )
        return STATE_WHOIS_LOOKUP
    elif data == "dns_lookup":
        await query.edit_message_text(
            " DNS RECORDS

"
            "Enter domain:
"
            "Example: example.com",
            reply_markup=get_cancel_button()
        )
        return STATE_DNS_LOOKUP
    elif data == "subdomain_find":
        await query.edit_message_text(
            " SUBDOMAIN FINDER

"
            "Enter domain:
"
            "Example: example.com",
            reply_markup=get_cancel_button()
        )
        return STATE_SUBDOMAIN_FIND
    elif data == "back_whois":
        return await show_whois_menu(query, context)

    return STATE_WHOIS_MENU

# ============== BREACH CHECKER ==============

async def start_breach_check(query, context) -> int:
    """Start breach check flow"""
    db.log_tool_usage(query.from_user.id, 'breach_check')

    await query.edit_message_text(
        " BREACH CHECKER

"
        "Enter email to check:
"
        "Example: user@example.com

"
        "Checks Have I Been Pwned database",
        reply_markup=get_cancel_button()
    )
    return STATE_BREACH_EMAIL

# ============== PASSWORD GENERATOR ==============

async def start_password_gen(query, context) -> int:
    """Start password generator"""
    db.log_tool_usage(query.from_user.id, 'password_gen')

    keyboard = [
        [InlineKeyboardButton("12 chars", callback_data="pass_12"),
         InlineKeyboardButton("16 chars", callback_data="pass_16")],
        [InlineKeyboardButton("24 chars", callback_data="pass_24"),
         InlineKeyboardButton("32 chars", callback_data="pass_32")],
        [InlineKeyboardButton(" Back", callback_data="back_menu")],
    ]

    await query.edit_message_text(
        " PASSWORD GENERATOR

"
        "Select length:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return STATE_PASS_LENGTH

async def pass_length_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle password length selection"""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("pass_"):
        length = int(data.split("_")[1])
        context.user_data['pass_length'] = length

        keyboard = [
            [InlineKeyboardButton(" Uppercase (A-Z)", callback_data="pass_opt_upper")],
            [InlineKeyboardButton(" Lowercase (a-z)", callback_data="pass_opt_lower")],
            [InlineKeyboardButton(" Numbers (0-9)", callback_data="pass_opt_numbers")],
            [InlineKeyboardButton(" Symbols (!@#$)", callback_data="pass_opt_symbols")],
            [InlineKeyboardButton(" Generate", callback_data="pass_generate")],
            [InlineKeyboardButton(" Back", callback_data="back_menu")],
        ]

        await query.edit_message_text(
            f" OPTIONS ({length} chars)

"
            "Toggle options then click Generate:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return STATE_PASS_OPTIONS
    elif data == "back_menu":
        await query.edit_message_text(
            MAIN_MENU,
            reply_markup=get_main_menu_keyboard()
        )
        return STATE_MENU

    return STATE_PASS_LENGTH

# ============== GET MY ID ==============

async def show_user_id(query, context) -> int:
    """Show user's Telegram ID"""
    user = query.from_user

    text = (
        " YOUR TELEGRAM ID

"
        f"User ID: `{user.id}`
"
        f"Username: @{user.username or 'N/A'}
"
        f"First Name: {user.first_name or 'N/A'}
"
        f"Last Name: {user.last_name or 'N/A'}
"
        f"Language: {user.language_code or 'N/A'}

"
        "Use your ID for bot admin or debugging."
    )

    keyboard = [
        [InlineKeyboardButton(" Copy ID", callback_data=f"copy_id_{user.id}")],
        [InlineKeyboardButton(" Back", callback_data="back_menu")],
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return STATE_MENU

# ============== SETTINGS ==============

async def show_settings(query, context) -> int:
    """Show settings menu"""
    user_id = query.from_user.id
    token, username = db.get_github_token(user_id)
    site_count = db.count_user_sites(user_id)
    tool_count = db.get_today_tool_usage(user_id)

    github_status = f" Connected ({username})" if token else " Not connected"

    text = SETTINGS_MENU.format(
        github_status=github_status,
        site_count=site_count,
        tool_count=tool_count
    )

    keyboard = [
        [InlineKeyboardButton(" Reconnect GitHub", callback_data="github_connect")],
        [InlineKeyboardButton(" Usage Stats", callback_data="usage_stats")],
        [InlineKeyboardButton(" Clear All Data", callback_data="clear_data")],
        [InlineKeyboardButton(" Back", callback_data="back_menu")],
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return STATE_SETTINGS

async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle settings callbacks"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    if data == "github_connect":
        await query.edit_message_text(
            " GITHUB CONNECTION

"
            "To connect your GitHub:

"
            "1. Visit: https://github.com/settings/developers
"
            "2. Create OAuth App
"
            "3. Set callback URL
"
            "4. Send me your Personal Access Token

"
            "Or use this direct link:
"
            "[Authorize GitHub](https://github.com/login/oauth/authorize?client_id=YOUR_CLIENT_ID)

"
            "Send token or click Back:",
            reply_markup=get_back_button("back_settings"),
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        return STATE_GITHUB_AUTH
    elif data == "usage_stats":
        total_sites = db.count_user_sites(user_id)
        today_tools = db.get_today_tool_usage(user_id)
        await query.edit_message_text(
            f" USAGE STATS

"
            f"Total sites hosted: {total_sites}
"
            f"Tools used today: {today_tools}
"
            f"Max sites allowed: {MAX_SITES_PER_USER}
",
            reply_markup=get_back_button("back_settings")
        )
        return STATE_SETTINGS
    elif data == "clear_data":
        await query.edit_message_text(
            " CLEAR ALL DATA

"
            " This will delete:
"
            "• All hosted site records
"
            "• Tool usage history
"
            "• GitHub connection

"
            "This cannot be undone!

"
            "Are you sure?",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(" Yes, delete everything", callback_data="confirm_clear")],
                [InlineKeyboardButton(" No, cancel", callback_data="back_settings")]
            ])
        )
        return STATE_CONFIRM_CLEAR
    elif data == "confirm_clear":
        db.clear_user_data(user_id)
        await query.edit_message_text(
            " All data cleared!

"
            "Your account has been reset.",
            reply_markup=get_back_button()
        )
        return STATE_MENU
    elif data == "back_settings":
        return await show_settings(query, context)
    elif data == "back_menu":
        await query.edit_message_text(
            MAIN_MENU,
            reply_markup=get_main_menu_keyboard()
        )
        return STATE_MENU

    return STATE_SETTINGS

# ============== HELP ==============

async def show_help(query, context) -> int:
    """Show help text"""
    await query.edit_message_text(
        HELP_TEXT,
        reply_markup=get_back_button()
    )
    return STATE_MENU

# ============== TEXT INPUT HANDLERS ==============

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle text inputs based on current state"""
    text = update.message.text
    user_id = update.effective_user.id

    # Get current state from user_data or default
    current_state = context.user_data.get('state', STATE_MENU)

    # Route to appropriate handler
    if current_state == STATE_HASH_IDENTIFY:
        return await handle_hash_identify(update, context, text)
    elif current_state == STATE_HASH_CRACK:
        return await handle_hash_crack(update, context, text)
    elif current_state == STATE_HASH_GENERATE:
        return await handle_hash_generate(update, context, text)
    elif current_state == STATE_HASH_BASE64:
        return await handle_hash_base64(update, context, text)
    elif current_state == STATE_JWT_DECODE:
        return await handle_jwt_decode(update, context, text)
    elif current_state == STATE_SCAN_TARGET:
        return await handle_scan_target(update, context, text)
    elif current_state == STATE_HEADERS_URL:
        return await handle_headers_url(update, context, text)
    elif current_state == STATE_WHOIS_LOOKUP:
        return await handle_whois_lookup(update, context, text)
    elif current_state == STATE_DNS_LOOKUP:
        return await handle_dns_lookup(update, context, text)
    elif current_state == STATE_SUBDOMAIN_FIND:
        return await handle_subdomain_find(update, context, text)
    elif current_state == STATE_BREACH_EMAIL:
        return await handle_breach_email(update, context, text)
    elif current_state == STATE_GITHUB_AUTH:
        return await handle_github_token(update, context, text)
    else:
        await update.message.reply_text(
            " I didn't understand that.
"
            "Use /start to see the menu.",
            reply_markup=get_back_button()
        )
        return STATE_MENU

# Tool handlers (stubs - will be implemented in tools/)
async def handle_hash_identify(update, context, text):
    from tools.hash_tools import identify_hash
    result = identify_hash(text)
    await update.message.reply_text(result, reply_markup=get_back_button("back_hash"))
    return STATE_HASH_TOOLS

async def handle_hash_crack(update, context, text):
    await update.message.reply_text(
        "#⃣ CRACKING...

"
        "This would attempt wordlist attack.
"
        "(Implementation in tools/hash_tools.py)",
        reply_markup=get_back_button("back_hash")
    )
    return STATE_HASH_TOOLS

async def handle_hash_generate(update, context, text):
    from tools.hash_tools import generate_hashes
    result = generate_hashes(text)
    await update.message.reply_text(result, reply_markup=get_back_button("back_hash"))
    return STATE_HASH_TOOLS

async def handle_hash_base64(update, context, text):
    from tools.hash_tools import base64_convert
    result = base64_convert(text)
    await update.message.reply_text(result, reply_markup=get_back_button("back_hash"))
    return STATE_HASH_TOOLS

async def handle_jwt_decode(update, context, text):
    from tools.jwt_decoder import decode_jwt
    result = decode_jwt(text)
    await update.message.reply_text(result, reply_markup=get_back_button())
    return STATE_MENU

async def handle_scan_target(update, context, text):
    from tools.port_scanner import scan_ports
    result = scan_ports(text)
    await update.message.reply_text(result, reply_markup=get_back_button())
    return STATE_MENU

async def handle_headers_url(update, context, text):
    from tools.header_analyzer import analyze_headers
    result = analyze_headers(text)
    await update.message.reply_text(result, reply_markup=get_back_button())
    return STATE_MENU

async def handle_whois_lookup(update, context, text):
    from tools.whois_dns import whois_lookup
    result = whois_lookup(text)
    await update.message.reply_text(result, reply_markup=get_back_button("back_whois"))
    return STATE_WHOIS_MENU

async def handle_dns_lookup(update, context, text):
    from tools.whois_dns import dns_lookup
    result = dns_lookup(text)
    await update.message.reply_text(result, reply_markup=get_back_button("back_whois"))
    return STATE_WHOIS_MENU

async def handle_subdomain_find(update, context, text):
    from tools.whois_dns import find_subdomains
    result = find_subdomains(text)
    await update.message.reply_text(result, reply_markup=get_back_button("back_whois"))
    return STATE_WHOIS_MENU

async def handle_breach_email(update, context, text):
    from tools.breach_checker import check_breach
    result = check_breach(text)
    await update.message.reply_text(result, reply_markup=get_back_button())
    return STATE_MENU

async def handle_github_token(update, context, text):
    """Handle GitHub token input"""
    user_id = update.effective_user.id
    # Validate token format (ghp_... or classic)
    if text.startswith('ghp_') or text.startswith('github_pat_'):
        # Store token (in real app, validate with GitHub API first)
        db.update_github_token(user_id, text, "user")
        await update.message.reply_text(
            " GitHub connected!

"
            "You can now host sites.",
            reply_markup=get_back_button("back_settings")
        )
        return STATE_SETTINGS
    else:
        await update.message.reply_text(
            " Invalid token format.
"
            "Should start with 'ghp_' or 'github_pat_'

"
            "Try again or click Back:",
            reply_markup=get_back_button("back_settings")
        )
        return STATE_GITHUB_AUTH

# ============== MAIN ==============


# ============== VERCEL DEPLOYMENT ==============

async def start_vercel_deploy(query, context) -> int:
    """Start Vercel deployment flow"""
    db.log_tool_usage(query.from_user.id, 'vercel_deploy')

    await query.edit_message_text(
        " DEPLOY TO VERCEL

"
        "Enter GitHub repository URL:
"
        "Example: https://github.com/username/repo

"
        "Or enter a deployed site URL to screenshot:
"
        "Example: https://username.github.io/repo/

"
        "The bot will:
"
        "1. Deploy to Vercel (if GitHub repo)
"
        "2. Take screenshot of the deployed site
"
        "3. Send you both URLs",
        reply_markup=get_cancel_button()
    )
    return STATE_VERCEL_DEPLOY

async def handle_vercel_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle Vercel deployment URL input"""
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # Check if it's a GitHub repo URL
    if 'github.com' in text and '/blob/' not in text:
        # Show progress
        progress_msg = await update.message.reply_text(
            progress.build_progress(1, 3, 10, status="in_progress", current_file="Connecting to Vercel...")
        )

        # Deploy to Vercel
        deployer = VercelDeployer()
        result = deployer.deploy_from_github(text)

        if result['success']:
            await progress_msg.edit_text(
                progress.build_progress(2, 3, 60, status="in_progress", current_file="Deploying to Vercel...")
            )

            # Wait a bit for deployment to start
            import asyncio
            await asyncio.sleep(3)

            # Take screenshot of the deployed site
            await progress_msg.edit_text(
                progress.build_progress(3, 3, 90, status="in_progress", current_file="Taking screenshot...")
            )

            screenshot_tool = ScreenshotTool()
            screenshot_result = await screenshot_tool.capture_deployment_preview(
                result['url'],
                filename=f"vercel_{result['project_name']}.png"
            )

            if screenshot_result['success']:
                # Send screenshot
                await update.message.reply_photo(
                    photo=open(screenshot_result['path'], 'rb'),
                    caption=f" Deployed to Vercel!

"
                           f" Site: {result['url']}
"
                           f" Project: {result['project_name']}
"
                           f" Inspector: {result.get('inspector_url', 'N/A')}

"
                           f"Screenshot saved!"
                )
            else:
                await update.message.reply_text(
                    f" Deployed to Vercel!

"
                    f" Site: {result['url']}
"
                    f" Project: {result['project_name']}

"
                    f" Screenshot failed: {screenshot_result.get('error', 'Unknown error')}"
                )

            await progress_msg.edit_text(
                progress.build_progress(3, 3, 100, status="done", current_file=result['url'])
            )
        else:
            await progress_msg.edit_text(
                progress.build_error(1, "Vercel Deploy", result['error']),
                reply_markup=get_retry_back_buttons("retry_vercel", "back_menu")
            )

        return STATE_MENU

    # If not GitHub, treat as URL to screenshot
    else:
        return await handle_screenshot_url(update, context)

# ============== SCREENSHOT TOOL ==============

async def start_screenshot(query, context) -> int:
    """Start screenshot capture flow"""
    db.log_tool_usage(query.from_user.id, 'screenshot')

    await query.edit_message_text(
        " CAPTURE SCREENSHOT

"
        "Enter URL to screenshot:
"
        "Example: https://example.com

"
        "Options:
"
        "• Any website URL
"
        "• GitHub repository page
"
        "• Deployed site URL

"
        "The bot will capture a full-page screenshot.",
        reply_markup=get_cancel_button()
    )
    return STATE_SCREENSHOT_URL

async def handle_screenshot_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle screenshot URL input"""
    text = update.message.text.strip()

    if not text.startswith('http'):
        text = 'https://' + text

    # Show progress
    progress_msg = await update.message.reply_text(
        progress.build_progress(1, 2, 10, status="in_progress", current_file="Loading page...")
    )

    try:
        screenshot_tool = ScreenshotTool()

        # Check if it's a GitHub repo
        if 'github.com' in text:
            result = await screenshot_tool.capture_github_repo(text)
        else:
            result = await screenshot_tool.capture_deployment_preview(text)

        if result['success']:
            await progress_msg.edit_text(
                progress.build_progress(2, 2, 100, status="done", current_file=text)
            )

            # Send screenshot
            await update.message.reply_photo(
                photo=open(result['path'], 'rb'),
                caption=f" Screenshot captured!

"
                       f"URL: {text}
"
                       f"Size: {result['size'] / 1024:.1f} KB
"
                       f"Saved as: {result['filename']}"
            )
        else:
            await progress_msg.edit_text(
                progress.build_error(1, "Screenshot", result.get('error', 'Unknown error')),
                reply_markup=get_retry_back_buttons("retry_screenshot", "back_menu")
            )

    except Exception as e:
        await progress_msg.edit_text(
            progress.build_error(1, "Screenshot", str(e)),
            reply_markup=get_retry_back_buttons("retry_screenshot", "back_menu")
        )

    return STATE_MENU

def main():
    """Start the bot"""
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )

    # Conversation handler for hosting flow
    hosting_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(menu_callback, pattern="^menu_"),
            CommandHandler("host", lambda u, c: menu_callback(u, c)),
        ],
        states={
            STATE_MENU: [CallbackQueryHandler(menu_callback)],
            STATE_UPLOAD: [
                MessageHandler(filters.Document.ALL, handle_file_upload),
                CallbackQueryHandler(menu_callback, pattern="^cancel$")
            ],
            STATE_HASH_TOOLS: [CallbackQueryHandler(hash_callback)],
            STATE_HASH_IDENTIFY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            STATE_HASH_CRACK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            STATE_HASH_GENERATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            STATE_HASH_BASE64: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            STATE_JWT_DECODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            STATE_SCAN_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            STATE_HEADERS_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            STATE_WHOIS_MENU: [CallbackQueryHandler(whois_callback)],
            STATE_WHOIS_LOOKUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            STATE_DNS_LOOKUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            STATE_SUBDOMAIN_FIND: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            STATE_BREACH_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            STATE_PASS_LENGTH: [CallbackQueryHandler(pass_length_callback)],
            STATE_PASS_OPTIONS: [CallbackQueryHandler(pass_length_callback)],
            STATE_SETTINGS: [CallbackQueryHandler(settings_callback)],
            STATE_GITHUB_AUTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            STATE_CONFIRM_CLEAR: [CallbackQueryHandler(settings_callback)],
            STATE_VERCEL_DEPLOY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_vercel_url)],
            STATE_VERCEL_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_vercel_url)],
            STATE_SCREENSHOT_URL: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_screenshot_url)],
        },
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("cancel", lambda u, c: menu_callback(u, c)),
            CallbackQueryHandler(menu_callback, pattern="^back_"),
        ],
        allow_reentry=True
    )

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", lambda u, c: show_help(u.callback_query or u, c)))
    application.add_handler(CommandHandler("getid", lambda u, c: show_user_id(u.callback_query or u, c)))
    application.add_handler(CommandHandler("sites", lambda u, c: show_sites(u.callback_query or u, c)))
    application.add_handler(CommandHandler("vercel", lambda u, c: start_vercel_deploy(u.callback_query or u, c)))
    application.add_handler(CommandHandler("screenshot", lambda u, c: start_screenshot(u.callback_query or u, c)))
    application.add_handler(hosting_conv)

    # Start bot
    print(" TARRIFIC HOST Bot started!")
    application.run_polling()

if __name__ == "__main__":
    main()

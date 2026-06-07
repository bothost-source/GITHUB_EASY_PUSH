"""
TARRIFIC HOST BOT - Configuration
"""
import os

# Telegram Bot Token (from @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# GitHub OAuth App Credentials
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "YOUR_GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "YOUR_GITHUB_CLIENT_SECRET")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "https://your-domain.com/github/callback")
# Vercel API
VERCEL_TOKEN = os.getenv("VERCEL_TOKEN", "YOUR_VERCEL_TOKEN")
VERCEL_API_BASE = "https://api.vercel.com"

# Screenshot Settings
SCREENSHOT_DIR = "screenshots"
SCREENSHOT_DEFAULT_WIDTH = 1920
SCREENSHOT_DEFAULT_HEIGHT = 1080
SCREENSHOT_WAIT_TIME = 5000  # ms


# GitHub API
GITHUB_API_BASE = "https://api.github.com"
GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"

# Database
DB_FILE = "tarrific_host.db"

# Hosting Config
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB GitHub limit
MAX_SITES_PER_USER = 5
SUPPORTED_ARCHIVE_TYPES = ['.zip', '.tar', '.tar.gz', '.tgz']

# Progress Steps
HOSTING_STEPS = [
    "Authenticating",
    "Creating Repo", 
    "Uploading",
    "Enabling Pages",
    "Finalizing"
]

# ASCII Progress Bars
PROGRESS_BLOCKS = {
    "empty": "",
    "filled": "",
    "current": "",
    "done": "",
    "waiting": "",
    "failed": "",
    "in_progress": ""
}

# Menu Text
MAIN_MENU = """

   TARRIFIC HOST v1.0      
                             
   HOSTING                 
  [1]  Host New Site       
  [2]  My Hosted Sites     
  [3]  Deploy to Vercel    
                             
   SCREENSHOTS             
  [4]  Capture Screenshot  
                             
   SECURITY TOOLS          
  [5] #⃣ Hash Tools          
  [6]  JWT Decoder         
  [7]  Port Scanner        
  [8]  Header Analyzer     
  [9]  WHOIS & DNS         
  [10]  Breach Checker     
  [11]  Password Generator 
                             
   UTILITIES               
  [12]  Get My ID          
                             
   [13] Settings           
   [14] Help               
                             
  Status:  Online           

"""

SETTINGS_MENU = """

   SETTINGS                
                             
  GitHub: {github_status}    
  Sites hosted: {site_count} 
  Tools used today: {tool_count}
                             
  [ Reconnect GitHub]      
  [ Usage Stats]           
  [ Clear All Data]        
  [ Back to Menu]          

"""

HASH_TOOLS_MENU = """

  #⃣ HASH TOOLS              
                             
  [1] Identify Hash Type     
  [2] Crack Hash (wordlist)  
  [3] Generate Hashes        
  [4] Base64 Encode/Decode   
                             
  [ Back]                  

"""

WHOIS_DNS_MENU = """

   WHOIS & DNS             
                             
  [1] WHOIS Lookup           
  [2] DNS Records            
  [3] Subdomain Finder       
                             
  [ Back]                  

"""

HELP_TEXT = """

   HELP & COMMANDS          
                             
   HOSTING                 
  /host - Start new deployment
  /sites - List your sites   
  /delete <name> - Remove site
                             
   SECURITY TOOLS          
  /hash - Hash tools menu    
  /jwt - Decode JWT token    
  /scan - Port scanner       
  /headers - Analyze headers 
  /whois - WHOIS & DNS tools 
  /breach - Check email breach
  /pass - Generate password  
                             
   UTILITIES               
  /getid - Show your Telegram ID
  /settings - Bot settings   
  /help - This menu          
  /cancel - Cancel operation 
                             
   ZIP UPLOAD              
  Send any .zip file and the 
  bot will preserve all      
  folders & files exactly.   
                             
   LIMITS                  
  Max file size: 25 MB       
  Max sites per user: 5      
  GitHub Pages required      

"""

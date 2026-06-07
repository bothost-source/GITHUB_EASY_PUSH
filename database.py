"""
TARRIFIC HOST BOT - Database Handler
SQLite for zero external dependencies
"""
import sqlite3
import json
from datetime import datetime
from config import DB_FILE

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self._init_tables()

    def _init_tables(self):
        """Create tables if not exist"""
        cursor = self.conn.cursor()

        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                language TEXT DEFAULT 'en',
                github_token TEXT,
                github_username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Hosted sites table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                repo_name TEXT,
                repo_url TEXT,
                site_url TEXT,
                file_count INTEGER,
                total_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        # Tool usage stats
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                tool_name TEXT,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)

        self.conn.commit()

    def get_user(self, user_id):
        """Get user by ID"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        )
        return cursor.fetchone()

    def add_user(self, user_id, username, first_name, last_name, language='en'):
        """Add new user"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO users 
            (user_id, username, first_name, last_name, language, last_active)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, username, first_name, last_name, language))
        self.conn.commit()

    def update_github_token(self, user_id, token, username):
        """Update GitHub OAuth token"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE users SET github_token = ?, github_username = ?
            WHERE user_id = ?
        """, (token, username, user_id))
        self.conn.commit()

    def get_github_token(self, user_id):
        """Get GitHub token for user"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT github_token, github_username FROM users WHERE user_id = ?",
            (user_id,)
        )
        result = cursor.fetchone()
        return result if result else (None, None)

    def add_site(self, user_id, repo_name, repo_url, site_url, file_count, total_size):
        """Record new hosted site"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO sites (user_id, repo_name, repo_url, site_url, file_count, total_size)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, repo_name, repo_url, site_url, file_count, total_size))
        self.conn.commit()

    def get_user_sites(self, user_id):
        """Get all sites for user"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT repo_name, repo_url, site_url, file_count, total_size, created_at
            FROM sites WHERE user_id = ? ORDER BY created_at DESC
        """, (user_id,))
        return cursor.fetchall()

    def delete_site(self, user_id, repo_name):
        """Delete site record"""
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM sites WHERE user_id = ? AND repo_name = ?",
            (user_id, repo_name)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def count_user_sites(self, user_id):
        """Count sites for user"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM sites WHERE user_id = ?", (user_id,)
        )
        return cursor.fetchone()[0]

    def log_tool_usage(self, user_id, tool_name):
        """Log tool usage"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO tool_usage (user_id, tool_name)
            VALUES (?, ?)
        """, (user_id, tool_name))
        self.conn.commit()

    def get_today_tool_usage(self, user_id):
        """Get today's tool usage count"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM tool_usage 
            WHERE user_id = ? AND date(used_at) = date('now')
        """, (user_id,))
        return cursor.fetchone()[0]

    def clear_user_data(self, user_id):
        """Delete all user data"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM sites WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM tool_usage WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        self.conn.commit()

    def close(self):
        self.conn.close()

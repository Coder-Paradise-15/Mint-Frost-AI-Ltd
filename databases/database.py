import sqlite3
from datetime import datetime
import os


DATABASE_PATH = os.environ.get('DATABASE_PATH')
if DATABASE_PATH:
    DATABASE_PATH = os.path.abspath(DATABASE_PATH)
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
else:
    DATABASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'chat.db'))

class CoercedConnection(sqlite3.Connection):
    def __enter__(self):
        return super().__enter__()
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            super().__exit__(exc_type, exc_val, exc_tb)
        finally:
            self.close()

def connect_db():
    """Get an optimized SQLite connection with WAL mode and synchronous tuning"""
    conn = sqlite3.connect(DATABASE_PATH, timeout=10.0, factory=CoercedConnection)
    try:
        conn.execute('PRAGMA journal_mode=WAL;')
        conn.execute('PRAGMA synchronous=NORMAL;')
        conn.execute('PRAGMA cache_size=2000;')
        conn.execute('PRAGMA temp_store=MEMORY;')
    except Exception:
        pass
    return conn


def init_db():
    """Initialize the database with required tables"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            
            # Create chat_sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    user_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sender TEXT NOT NULL CHECK (sender IN ('user', 'ai')),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions (id)
                )
            ''')
            
            # Create user_settings table for theme persistence
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    id TEXT PRIMARY KEY,
                    current_theme TEXT DEFAULT 'dark',
                    auto_theme INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create custom_themes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS custom_themes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    colors TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create oauth_accounts table for storing provider tokens
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS oauth_accounts (
                    provider TEXT NOT NULL,
                    account_id TEXT PRIMARY KEY,
                    access_token TEXT,
                    refresh_token TEXT,
                    expires_at INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    password_hash TEXT,
                    display_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create linked_accounts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS linked_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(provider, account_id),
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')

            # Create indices for instant O(1) query lookups (avoids full-table scans on load)
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_linked_accounts_user_id ON linked_accounts(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id)')

            # Dynamic migrations to ensure schema is fully upgraded for existing databases safely
            try:
                cursor.execute("PRAGMA table_info(user_settings)")
                info = cursor.fetchall()
                id_column = [col for col in info if col[1] == 'id']
                if id_column and 'INTEGER' in id_column[0][2].upper():
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings_old'")
                    if not cursor.fetchone():
                        cursor.execute('ALTER TABLE user_settings RENAME TO user_settings_old')
                        cursor.execute('''
                            CREATE TABLE IF NOT EXISTS user_settings (
                                id TEXT PRIMARY KEY,
                                current_theme TEXT DEFAULT 'dark',
                                auto_theme INTEGER DEFAULT 0,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        ''')
                        cursor.execute('''
                            INSERT INTO user_settings (id, current_theme, auto_theme, created_at, updated_at)
                            SELECT CAST(id AS TEXT), current_theme, auto_theme, created_at, updated_at FROM user_settings_old
                        ''')
                        cursor.execute('DROP TABLE user_settings_old')
            except Exception as e:
                import logging
                logging.error(f"Migration error for user_settings: {e}")

            try:
                cursor.execute('ALTER TABLE users ADD COLUMN password_hash TEXT')
            except sqlite3.OperationalError:
                pass
            
            try:
                cursor.execute('ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0')
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute('ALTER TABLE users ADD COLUMN is_online INTEGER DEFAULT 0')
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute('ALTER TABLE users ADD COLUMN last_seen TIMESTAMP DEFAULT NULL')
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'")
            except sqlite3.OperationalError:
                pass

            # Capturing IP, Geo-location, Age and Home Address telemetry columns
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN last_login_ip TEXT DEFAULT '127.0.0.1'")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE users ADD COLUMN last_login_location TEXT DEFAULT 'Localhost Network'")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE users ADD COLUMN home_address TEXT DEFAULT 'Not Provided'")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE users ADD COLUMN birth_date TEXT DEFAULT 'Not Verified'")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute('ALTER TABLE chat_sessions ADD COLUMN user_id TEXT REFERENCES users(id)')
            except sqlite3.OperationalError:
                pass

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON chat_sessions(user_id)')

            # Add API settings columns to user_settings
            for col in ['api_provider TEXT', 'api_key TEXT', 'api_model TEXT']:
                try:
                    cursor.execute(f'ALTER TABLE user_settings ADD COLUMN {col}')
                except sqlite3.OperationalError:
                    pass

            # Create announcements table for history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    user_id TEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            try:
                cursor.execute('ALTER TABLE announcements ADD COLUMN user_id TEXT DEFAULT NULL')
            except sqlite3.OperationalError:
                pass

            # Create system_config table for admin configurations & announcements
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')

            # Create admin_audit_logs table for tracking administrator actions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    target_user TEXT,
                    details TEXT,
                    ip_address TEXT DEFAULT '127.0.0.1',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create user_passkeys table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_passkeys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    key_name TEXT NOT NULL,
                    credential_id TEXT UNIQUE NOT NULL,
                    public_key TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')

            # Create user_authenticators table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_authenticators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    device_name TEXT NOT NULL,
                    secret_key TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')

            # Dynamic migrations for audit logs
            try:
                cursor.execute("ALTER TABLE admin_audit_logs ADD COLUMN ip_address TEXT DEFAULT '127.0.0.1'")
            except sqlite3.OperationalError:
                pass

            # Create active_sessions table for session tracking and revocation
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS active_sessions (
                    session_token TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')

            # Create support_tickets table for admin Support Inbox
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS support_tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    subject TEXT,
                    message TEXT NOT NULL,
                    category TEXT,
                    priority TEXT,
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create tasks table for AI Deadline Detection Engine
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT,
                    deadline TEXT,
                    duration TEXT,
                    confidence REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')

            # Create subtasks table for AI Task Breakdown Engine
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS subtasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    duration TEXT,
                    difficulty TEXT,
                    priority TEXT,
                    completed INTEGER DEFAULT 0,
                    subtask_order INTEGER DEFAULT 0,
                    dependency TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
                )
            ''')

            # Create daily_plans table for AI Smart Daily Planner
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS daily_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    generated_plan TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE(user_id, date)
                )
            ''')
            # Create recent_activity table for AI Productivity Dashboard
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS recent_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    activity_type TEXT NOT NULL,
                    details TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            # Create user_gamification table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_gamification (
                    user_id TEXT PRIMARY KEY,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    streak INTEGER DEFAULT 0,
                    last_activity_date TEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            # Create user_badges table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_badges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    badge_id TEXT NOT NULL,
                    badge_name TEXT NOT NULL,
                    badge_description TEXT NOT NULL,
                    icon TEXT NOT NULL,
                    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, badge_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            try:
                cursor.execute("ALTER TABLE subtasks ADD COLUMN dependency TEXT")
            except Exception:
                pass

            # Safe database migrations for tasks table
            for col_name, col_type in [
                ("description", "TEXT"),
                ("estimated_duration", "TEXT"),
                ("priority", "TEXT"),
                ("risk_level", "TEXT"),
                ("status", "TEXT"),
                ("progress", "INTEGER DEFAULT 0"),
                ("updated_at", "TIMESTAMP"),
                ("completed_at", "TEXT"),
                ("ai_generated", "INTEGER DEFAULT 0"),
                ("source_chat_message", "TEXT"),
                ("priority_score", "INTEGER DEFAULT 50"),
                ("completion_probability", "INTEGER DEFAULT 100"),
                ("suggested_action", "TEXT"),
                ("risk_reason", "TEXT")
            ]:
                try:
                    cursor.execute(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}")
                except Exception:
                    pass

            # Populate system default settings if they do not exist
            default_configs = [
                ('enable_registration', 'true'),
                ('allow_guests', 'true'),
                ('enable_music', 'true'),
                ('enforce_passwords', 'false'),
                ('site_announcement', ''),
                ('rule_admin_delete_coadmin', 'true'),
                ('rule_admin_delete_user', 'true'),
                ('rule_admin_reset_coadmin', 'true'),
                ('rule_admin_reset_user', 'true'),
                ('rule_admin_manage_config', 'true'),
                ('rule_admin_execute_commands', 'true'),
                ('rule_admin_publish_announcement', 'true'),
                ('rule_admin_export_data', 'true'),
                ('rule_coadmin_delete_user', 'true'),
                ('rule_coadmin_reset_user', 'true'),
                ('rule_coadmin_deactivate_user', 'true'),
                ('rule_coadmin_view_logs', 'true'),
                ('rule_coadmin_publish_announcement', 'true'),
                ('rule_coadmin_execute_commands', 'false'),
                ('rule_coadmin_export_data', 'true'),
                ('rule_user_view_logs', 'false')
            ]
            for key, val in default_configs:
                cursor.execute('INSERT OR IGNORE INTO system_config (key, value) VALUES (?, ?)', (key, val))

            # Initialize default user settings if not exists
            cursor.execute('SELECT COUNT(*) FROM user_settings')
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO user_settings (id, current_theme, auto_theme)
                    VALUES (1, 'dark', 0)
                ''')
            
            # Seed default administrator account if not exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_admin = 2")
            if cursor.fetchone()[0] == 0:
                from werkzeug.security import generate_password_hash
                admin_username = 'admin'
                admin_pass_hash = generate_password_hash('admin123')
                admin_display = 'Administrator'
                cursor.execute('''
                    INSERT OR IGNORE INTO users (id, password_hash, display_name, is_admin, status, last_login_ip, last_login_location, home_address)
                    VALUES (?, ?, ?, 2, 'active', '127.0.0.1', 'Mumbai, Maharashtra, India', '1, Admin Boulevard, Silicon Valley, CA')
                ''', (admin_username, admin_pass_hash, admin_display))

            # Role migration: upgrade legacy is_admin=1 to superadmin level 2
            cursor.execute("SELECT value FROM system_config WHERE key = 'role_migration_v2'")
            if not cursor.fetchone():
                cursor.execute("UPDATE users SET is_admin = 2 WHERE is_admin = 1")
                cursor.execute("INSERT INTO system_config (key, value) VALUES ('role_migration_v2', 'done')")

            # Clean up mock locations to comply with "City, State, Country" actual formatting requirement
            cursor.execute("""
                UPDATE users 
                SET last_login_location = 'Mumbai, Maharashtra, India' 
                WHERE last_login_location IN ('Localhost Network', 'Localhost Command Center', 'Localhost', 'Mumbai, India') OR last_login_location IS NULL
            """)

            # Create AvailableModels table for Dynamic AI Model Discovery
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS AvailableModels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    model_id TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    description TEXT,
                    supports_chat INTEGER DEFAULT 1,
                    supports_reasoning INTEGER DEFAULT 0,
                    supports_vision INTEGER DEFAULT 0,
                    supports_audio INTEGER DEFAULT 0,
                    supports_image_generation INTEGER DEFAULT 0,
                    supports_function_calling INTEGER DEFAULT 0,
                    supports_streaming INTEGER DEFAULT 1,
                    context_window INTEGER,
                    status TEXT DEFAULT 'active',
                    is_available INTEGER DEFAULT 1,
                    last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    api_owner TEXT
                )
            ''')

            conn.commit()
    except Exception as e:
        import logging
        logging.error(f"Database initialization error: {e}")
        raise

def create_session(session_id, title, user_id=None):
    """Create a new chat session"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO chat_sessions (id, title, user_id, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (session_id, title, user_id))
            conn.commit()
    except Exception as e:
        import logging
        logging.error(f"Error creating session: {e}")
        raise

def add_message(session_id, content, sender):
    """Add a message to a session"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO messages (session_id, content, sender)
                VALUES (?, ?, ?)
            ''', (session_id, content, sender))
            
            # Update session timestamp
            cursor.execute('''
                UPDATE chat_sessions 
                SET updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (session_id,))
            
            conn.commit()
    except Exception as e:
        import logging
        logging.error(f"Error adding message: {e}")
        raise

def get_recent_sessions(limit=20, user_id=None):
    """Get recent chat sessions"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.id, s.title, s.updated_at,
                       (SELECT content FROM messages 
                        WHERE session_id = s.id 
                        ORDER BY timestamp DESC LIMIT 1) as last_message
                FROM chat_sessions s
                WHERE s.user_id = ? OR (? IS NULL AND s.user_id IS NULL)
                ORDER BY s.updated_at DESC
                LIMIT ?
            ''', (user_id, user_id, limit))
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'id': row[0],
                    'title': row[1],
                    'timestamp': row[2],
                    'preview': row[3][:60] + '...' if row[3] and len(row[3]) > 60 else row[3] or 'Empty chat'
                })
            
            return sessions
    except Exception as e:
        import logging
        logging.error(f"Error getting sessions: {e}")
        return []

def get_session_messages(session_id):
    """Get all messages for a session"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, content, sender, timestamp
                FROM messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
            ''', (session_id,))
            
            messages = []
            for row in cursor.fetchall():
                messages.append({
                    'id': row[0],
                    'text': row[1],
                    'who': row[2],
                    'timestamp': row[3]
                })
            
            return messages
    except Exception as e:
        import logging
        logging.error(f"Error getting session messages: {e}")
        return []

def delete_session(session_id):
    """Delete a chat session and its messages"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
            cursor.execute('DELETE FROM chat_sessions WHERE id = ?', (session_id,))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        import logging
        logging.error(f"Error deleting session: {e}")
        return False

def update_session_title(session_id, new_title):
    """Update session title"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE chat_sessions 
                SET title = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (new_title, session_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        import logging
        logging.error(f"Error updating session title: {e}")
        return False

def delete_last_ai_message(session_id):
    """Delete the last AI message from a session"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM messages 
                WHERE session_id = ? AND sender = 'ai' 
                AND id = (
                    SELECT id FROM messages 
                    WHERE session_id = ? AND sender = 'ai' 
                    ORDER BY timestamp DESC LIMIT 1
                )
            ''', (session_id, session_id))
            conn.commit()
    except Exception as e:
        import logging
        logging.error(f"Error deleting last AI message: {e}")
        raise

def update_message(session_id, message_id, new_content):
    """Update a message content"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE messages 
                SET content = ?, timestamp = CURRENT_TIMESTAMP
                WHERE id = ? AND session_id = ?
            ''', (new_content, message_id, session_id))
            conn.commit()
    except Exception as e:
        import logging
        logging.error(f"Error updating message: {e}")
        raise

def clear_all_sessions(user_id=None):
    """Clear all chat sessions and messages for the user"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute('DELETE FROM messages WHERE session_id IN (SELECT id FROM chat_sessions WHERE user_id = ?)', (user_id,))
                cursor.execute('DELETE FROM chat_sessions WHERE user_id = ?', (user_id,))
            else:
                cursor.execute('DELETE FROM messages')
                cursor.execute('DELETE FROM chat_sessions')
            conn.commit()
    except Exception as e:
        import logging
        logging.error(f"Error clearing all sessions: {e}")
        raise

def get_all_sessions(user_id=None):
    """Get all chat sessions for modal system"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.id, s.title, s.updated_at,
                       (SELECT content FROM messages 
                        WHERE session_id = s.id 
                        ORDER BY timestamp DESC LIMIT 1) as last_message
                FROM chat_sessions s
                WHERE s.user_id = ? OR (? IS NULL AND s.user_id IS NULL)
                ORDER BY s.updated_at DESC
            ''', (user_id, user_id))
            
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'id': row[0],
                    'title': row[1],
                    'timestamp': row[2],
                    'preview': row[3][:60] + '...' if row[3] and len(row[3]) > 60 else row[3] or 'Empty chat'
                })
            
            return sessions
    except Exception as e:
        import logging
        logging.error(f"Error getting all sessions: {e}")
        return []

def get_session_data(session_id):
    """Get complete session data including messages"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            
            # Get session info
            cursor.execute('SELECT id, title, created_at, updated_at FROM chat_sessions WHERE id = ?', (session_id,))
            session_row = cursor.fetchone()
            
            if not session_row:
                return None
                
            # Get messages
            messages = get_session_messages(session_id)
            
            return {
                'id': session_row[0],
                'title': session_row[1],
                'created_at': session_row[2],
                'updated_at': session_row[3],
                'messages': messages
            }
    except Exception as e:
        import logging
        logging.error(f"Error getting session data: {e}")
        return None

def duplicate_session(session_id):
    """Duplicate a chat session"""
    try:
        import uuid
        new_session_id = str(uuid.uuid4())
        
        with connect_db() as conn:
            cursor = conn.cursor()
            
            # Get original session including user_id
            cursor.execute('SELECT title, user_id FROM chat_sessions WHERE id = ?', (session_id,))
            session_row = cursor.fetchone()
            
            if not session_row:
                return None
                
            # Create new session copying user_id
            new_title = f"{session_row[0]} (Copy)"
            cursor.execute('''
                INSERT INTO chat_sessions (id, title, user_id, created_at, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (new_session_id, new_title, session_row[1]))
            
            # Copy messages
            cursor.execute('''
                INSERT INTO messages (session_id, content, sender, timestamp)
                SELECT ?, content, sender, timestamp
                FROM messages
                WHERE session_id = ?
                ORDER BY timestamp ASC
            ''', (new_session_id, session_id))
            
            conn.commit()
            return new_session_id
            
    except Exception as e:
        import logging
        logging.error(f"Error duplicating session: {e}")
        return None

def clear_all_data(user_id=None):
    """Clear all data including sessions and messages for the user"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute('DELETE FROM messages WHERE session_id IN (SELECT id FROM chat_sessions WHERE user_id = ?)', (user_id,))
                cursor.execute('DELETE FROM chat_sessions WHERE user_id = ?', (user_id,))
            else:
                cursor.execute('DELETE FROM messages')
                cursor.execute('DELETE FROM chat_sessions')
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error clearing all data: {e}")
        return False

# Theme Management Functions
def get_user_theme(user_id=None):
    """Get current user theme settings"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute('SELECT current_theme, auto_theme FROM user_settings WHERE id = ?', (user_id,))
                row = cursor.fetchone()
                if row:
                    return {'theme': row[0], 'auto_theme': bool(row[1])}
            return {'theme': 'dark', 'auto_theme': False}
    except Exception as e:
        import logging
        logging.error(f"Error getting user theme: {e}")
        return {'theme': 'dark', 'auto_theme': False}

def set_user_theme(theme, auto_theme=None, user_id=None):
    """Set current user theme"""
    try:
        target_id = user_id if user_id else 1
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM user_settings WHERE id = ?', (target_id,))
            exists = cursor.fetchone()[0] > 0
            if exists:
                if auto_theme is not None:
                    cursor.execute('''
                        UPDATE user_settings 
                        SET current_theme = ?, auto_theme = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (theme, int(auto_theme), target_id))
                else:
                    cursor.execute('''
                        UPDATE user_settings 
                        SET current_theme = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (theme, target_id))
            else:
                at_val = int(auto_theme) if auto_theme is not None else 0
                cursor.execute('''
                    INSERT INTO user_settings (id, current_theme, auto_theme)
                    VALUES (?, ?, ?)
                ''', (target_id, theme, at_val))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error setting user theme: {e}")
        return False

def get_custom_themes():
    """Get all custom themes"""
    try:
        import json
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, colors, created_at FROM custom_themes ORDER BY created_at DESC')
            themes = {}
            for row in cursor.fetchall():
                themes[row[0]] = {
                    'name': row[1],
                    'colors': json.loads(row[2]),
                    'created': row[3]
                }
            return themes
    except Exception as e:
        import logging
        logging.error(f"Error getting custom themes: {e}")
        return {}

def save_custom_theme(theme_id, name, colors):
    """Save a custom theme"""
    try:
        import json
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO custom_themes (id, name, colors, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (theme_id, name, json.dumps(colors)))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error saving custom theme: {e}")
        return False

def delete_custom_theme(theme_id):
    """Delete a custom theme"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM custom_themes WHERE id = ?', (theme_id,))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        import logging
        logging.error(f"Error deleting custom theme: {e}")
        return False

def save_oauth_token(provider, account_id, access_token, refresh_token=None, expires_at=None):
    """Save or update OAuth token for a provider account."""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO oauth_accounts (provider, account_id, access_token, refresh_token, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (provider, account_id, access_token, refresh_token, expires_at))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error saving oauth token: {e}")
        return False


def get_oauth_token(provider, account_id):
    """Retrieve OAuth token record for provider/account_id."""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT access_token, refresh_token, expires_at FROM oauth_accounts WHERE provider = ? AND account_id = ?', (provider, account_id))
            row = cursor.fetchone()
            if not row:
                return None
            return {'access_token': row[0], 'refresh_token': row[1], 'expires_at': row[2]}
    except Exception as e:
        import logging
        logging.error(f"Error getting oauth token: {e}")
        return None


def delete_oauth_token(provider, account_id):
    """Delete OAuth token record."""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM oauth_accounts WHERE provider = ? AND account_id = ?', (provider, account_id))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        import logging
        logging.error(f"Error deleting oauth token: {e}")
        return False

# Helper functions for user/link management

def create_user(user_id, display_name=None):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO users (id, display_name) VALUES (?, ?)', (user_id, display_name))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error creating user: {e}")
        return False


def get_user_by_provider(provider, account_id):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM linked_accounts WHERE provider = ? AND account_id = ?', (provider, account_id))
            row = cursor.fetchone()
            return row[0] if row else None
    except Exception as e:
        import logging
        logging.error(f"Error getting user by provider: {e}")
        return None


def link_account_to_user(user_id, provider, account_id):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR IGNORE INTO linked_accounts (user_id, provider, account_id) VALUES (?, ?, ?)', (user_id, provider, account_id))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error linking account: {e}")
        return False


def get_linked_accounts(user_id):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT provider, account_id, created_at FROM linked_accounts WHERE user_id = ?', (user_id,))
            rows = cursor.fetchall()
            return [{'provider': r[0], 'account_id': r[1], 'created_at': r[2]} for r in rows]
    except Exception as e:
        import logging
        logging.error(f"Error getting linked accounts: {e}")
        return []


def unlink_account(user_id, provider):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM linked_accounts WHERE user_id = ? AND provider = ?', (user_id, provider))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        import logging
        logging.error(f"Error unlinking account: {e}")
        return False


def reset_database():
    """Drops all tables and runs init_db() to reinitialize the schema and default admin"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            tables = [
                'chat_sessions',
                'messages',
                'user_settings',
                'custom_themes',
                'oauth_accounts',
                'users',
                'linked_accounts',
                'announcements',
                'system_config',
                'admin_audit_logs',
                'active_sessions',
                'tasks',
                'subtasks',
                'daily_plans',
                'recent_activity',
                'user_gamification',
                'user_badges'
            ]
            cursor.execute('PRAGMA foreign_keys = OFF;')
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
            cursor.execute('PRAGMA foreign_keys = ON;')
            conn.commit()
        init_db()
        return True
    except Exception as e:
        import logging
        logging.error(f"Error resetting database: {e}")
        return False


# Initialize database on import
if __name__ == '__main__':
    init_db()
    print("Database initialized successfully!")
# --- Secure User Authentication Helpers ---

def create_user_secure(username, password_hash, display_name=None, is_admin=0):
    """Create a new user securely with a password hash and role"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (id, password_hash, display_name, is_admin)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, display_name, is_admin))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error creating user securely: {e}")
        return False

def get_user_secure(username):
    """Retrieve user secure context (details, password hash, status, is_admin)"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, password_hash, display_name, status, COALESCE(is_admin, 0) FROM users WHERE id = ?', (username,))
            row = cursor.fetchone()
            if row:
                return {
                    'id': row[0],
                    'password_hash': row[1],
                    'display_name': row[2],
                    'status': row[3] or 'active',
                    'is_admin': row[4]
                }
            return None
    except Exception as e:
        import logging
        logging.error(f"Error getting user secure context: {e}")
        return None

def verify_session_owner(session_id, user_id):
    """Verify if the session belongs to the user"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM chat_sessions WHERE id = ?', (session_id,))
            row = cursor.fetchone()
            if row:
                return row[0] == user_id
            return False
    except Exception as e:
        import logging
        logging.error(f"Error verifying session owner: {e}")
        return False


# --- Admin Panel Moderation Helper Functions ---

def get_all_users_admin(search=None, status=None, date_val=None, time_val=None, start_date=None, end_date=None, start_time=None, end_time=None):
    """Retrieve all users, statuses, and session counts for admin panel, optionally filtered"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            
            # Base query
            query = '''
                SELECT u.id, u.display_name, u.status, u.created_at,
                       (SELECT COUNT(*) FROM chat_sessions WHERE user_id = u.id) as session_count,
                       COALESCE(u.is_admin, 0) as is_admin,
                       COALESCE(u.last_login_ip, '127.0.0.1') as last_login_ip,
                       COALESCE(u.last_login_location, 'Localhost Network') as last_login_location,
                       CASE WHEN COALESCE(u.is_online, 0) = 1 AND (strftime('%s', 'now') - strftime('%s', COALESCE(u.last_seen, u.created_at))) < 15 THEN 1 ELSE 0 END as is_online
                FROM users u
            '''
            
            where_clauses = []
            params = []
            
            # 1. Search Query
            if search:
                where_clauses.append('''
                    (u.id LIKE ? OR 
                     u.display_name LIKE ? OR 
                     u.last_login_location LIKE ? OR 
                     u.last_login_ip LIKE ?)
                ''')
                search_param = f"%{search}%"
                params.extend([search_param, search_param, search_param, search_param])
                
            # 2. Status Filter
            if status:
                if status == 'online':
                    where_clauses.append("COALESCE(u.is_online, 0) = 1 AND (strftime('%s', 'now') - strftime('%s', COALESCE(u.last_seen, u.created_at))) < 15")
                elif status == 'offline':
                    where_clauses.append("NOT (COALESCE(u.is_online, 0) = 1 AND (strftime('%s', 'now') - strftime('%s', COALESCE(u.last_seen, u.created_at))) < 15)")
                elif status == 'admin':
                    where_clauses.append("COALESCE(u.is_admin, 0) >= 2")
                elif status == 'coadmin':
                    where_clauses.append("COALESCE(u.is_admin, 0) = 1")
                elif status == 'user':
                    where_clauses.append("COALESCE(u.is_admin, 0) = 0")
                elif status != 'all':
                    where_clauses.append("u.status = ?")
                    params.append(status)
                    
            # 3. Date Filter (expected format: YYYY-MM-DD)
            if date_val:
                where_clauses.append("date(datetime(u.created_at, 'localtime')) = date(?)")
                params.append(date_val)
                
            # 4. Time Filter (expected format: HH, hour of the day 00-23)
            if time_val:
                where_clauses.append("strftime('%H', datetime(u.created_at, 'localtime')) = ?")
                params.append(time_val)

            # 5. Date Interval Filter
            if start_date and end_date:
                where_clauses.append("date(datetime(u.created_at, 'localtime')) BETWEEN date(?) AND date(?)")
                params.extend([start_date, end_date])
            elif start_date:
                where_clauses.append("date(datetime(u.created_at, 'localtime')) >= date(?)")
                params.append(start_date)
            elif end_date:
                where_clauses.append("date(datetime(u.created_at, 'localtime')) <= date(?)")
                params.append(end_date)

            # 6. Time Interval Filter (expected HH:MM format)
            if start_time and end_time:
                where_clauses.append("strftime('%H:%M', datetime(u.created_at, 'localtime')) BETWEEN ? AND ?")
                params.extend([start_time, end_time])
            elif start_time:
                where_clauses.append("strftime('%H:%M', datetime(u.created_at, 'localtime')) >= ?")
                params.append(start_time)
            elif end_time:
                where_clauses.append("strftime('%H:%M', datetime(u.created_at, 'localtime')) <= ?")
                params.append(end_time)
                
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
                
            query += " ORDER BY u.created_at DESC"
            
            cursor.execute(query, params)
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'username': row[0],
                    'display_name': row[1] or 'Not Set',
                    'status': row[2] or 'active',
                    'created_at': row[3],
                    'session_count': row[4],
                    'is_admin': row[5] or 0,
                    'last_login_ip': row[6],
                    'last_login_location': row[7],
                    'is_online': bool(row[8])
                })
            return users
    except Exception as e:
        import logging
        logging.error(f"Error getting users for admin panel: {e}")
        return []

def set_user_online_status(username, is_online):
    """Set the online status of a user (1 for online, 0 for offline)"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET is_online = ? WHERE id = ?', (int(is_online), username))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error setting user online status: {e}")
        return False

def update_user_last_seen(username):
    """Update last_seen timestamp and ensure user is online"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET last_seen = CURRENT_TIMESTAMP, is_online = 1
                WHERE id = ?
            ''', (username,))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error updating user last seen: {e}")
        return False

# --- System Configuration Getters/Setters ---

def get_config_value(key, default_value=''):
    """Retrieve a configuration value from the system_config table"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM system_config WHERE key = ?', (key,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return default_value
    except Exception as e:
        import logging
        logging.error(f"Error getting config value for {key}: {e}")
        return default_value

def set_config_value(key, value):
    """Insert or update a configuration setting in system_config"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO system_config (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
            ''', (key, str(value)))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error setting config value for {key}: {e}")
        return False

def get_all_configs():
    """Retrieve all configuration keys and values"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT key, value FROM system_config')
            configs = {}
            for row in cursor.fetchall():
                configs[row[0]] = row[1]
            return configs
    except Exception as e:
        import logging
        logging.error(f"Error getting all configs: {e}")
        return {}

def add_announcement(content, user_id=None):
    """Add a new announcement to the history table"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO announcements (content, user_id) VALUES (?, ?)', (content, user_id))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error adding announcement: {e}")
        return False

def get_announcements_history(user_id=None):
    """Retrieve all announcements from history sorted by created_at DESC, filtered by user_id"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute('''
                    SELECT id, content, created_at FROM announcements 
                    WHERE user_id IS NULL OR user_id = ?
                    ORDER BY created_at DESC
                ''', (user_id,))
            else:
                cursor.execute('SELECT id, content, created_at FROM announcements WHERE user_id IS NULL ORDER BY created_at DESC')
            rows = cursor.fetchall()
            return [{'id': r[0], 'content': r[1], 'created_at': r[2]} for r in rows]
    except Exception as e:
        import logging
        logging.error(f"Error getting announcements history: {e}")
        return []

def update_user_telemetry_admin(username, ip, location):
    """Record login IP address and geo-location for a user"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users 
                SET last_login_ip = ?, last_login_location = ?
                WHERE id = ?
            ''', (ip, location, username))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error updating telemetry for {username}: {e}")
        return False

def get_user_full_details_admin(username):
    """Retrieve complete profile biodata, telemetry and session titles for details drawer"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            
            # Fetch User Profile Columns
            cursor.execute('''
                SELECT id, display_name, status, created_at, COALESCE(is_admin, 0),
                       COALESCE(last_login_ip, '127.0.0.1'),
                       COALESCE(last_login_location, 'Localhost Network'),
                       COALESCE(home_address, 'Not Provided'),
                       COALESCE(birth_date, 'Not Verified')
                FROM users 
                WHERE id = ?
            ''', (username,))
            user_row = cursor.fetchone()
            if not user_row:
                return None
            
            # Fetch Recent Chat Sessions
            cursor.execute('''
                SELECT id, title, created_at 
                FROM chat_sessions 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            ''', (username,))
            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'id': row[0],
                    'title': row[1] or 'Untitled Chat',
                    'created_at': row[2]
                })
                
            return {
                'username': user_row[0],
                'display_name': user_row[1] or 'Not Set',
                'status': user_row[2] or 'active',
                'created_at': user_row[3],
                'is_admin': user_row[4] or 0,
                'last_login_ip': user_row[5],
                'last_login_location': user_row[6],
                'home_address': user_row[7],
                'birth_date': user_row[8],
                'sessions': sessions
            }
    except Exception as e:
        import logging
        logging.error(f"Error getting full user details for {username}: {e}")
        return None

def update_user_status_admin(username, status, caller_level=1):
    """Update status of a user securely checking caller hierarchy and rules"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT is_admin FROM users WHERE id = ?', (username,))
            row = cursor.fetchone()
            if not row:
                return False
            target_level = row[0] or 0
            
            # Tier protections:
            # 1. Target cannot be admin (level >= 2)
            if target_level >= 2:
                return False
            # 2. Caller level must be strictly greater than target level
            if caller_level <= target_level:
                return False
                
            # Rule protections:
            if caller_level == 1:  # Co-Admin
                if get_config_value('rule_coadmin_deactivate_user', 'true') != 'true':
                    return False
            
            cursor.execute('UPDATE users SET status = ? WHERE id = ?', (status, username))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        import logging
        logging.error(f"Error updating user status: {e}")
        return False

def reset_user_password_admin(username, password_hash, caller_level=1):
    """Reset a user's password securely from admin panel checking levels and rules"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT is_admin FROM users WHERE id = ?', (username,))
            row = cursor.fetchone()
            if not row:
                return False
            target_level = row[0] or 0
            
            # Protections:
            if target_level >= 2:
                return False
            if caller_level <= target_level:
                return False
                
            # Dynamic rules check:
            if caller_level >= 2:
                if target_level == 1:
                    if get_config_value('rule_admin_reset_coadmin', 'true') != 'true':
                        return False
                elif target_level == 0:
                    if get_config_value('rule_admin_reset_user', 'true') != 'true':
                        return False
            elif caller_level == 1:
                if target_level == 0:
                    if get_config_value('rule_coadmin_reset_user', 'true') != 'true':
                        return False
                else:
                    return False
            else:
                return False
                
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (password_hash, username))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        import logging
        logging.error(f"Error resetting user password: {e}")
        return False

def delete_user_admin(username, caller_level=1):
    """Recursively delete user profile, linked accounts, and session data checking rules & levels"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            
            # Check if user exists and get target level
            cursor.execute('SELECT is_admin FROM users WHERE id = ?', (username,))
            row = cursor.fetchone()
            if not row:
                return False
            target_level = row[0] or 0
            
            # Deletion authorization checks:
            # 1. No one can delete an Admin (level >= 2)
            if target_level >= 2:
                return False
            # 2. Caller level must be strictly greater than target level
            if caller_level <= target_level:
                return False
                
            # 3. Dynamic rules checks
            if caller_level >= 2: # Admin
                if target_level == 1: # Co-Admin
                    if get_config_value('rule_admin_delete_coadmin', 'true') != 'true':
                        return False
                elif target_level == 0: # User
                    if get_config_value('rule_admin_delete_user', 'true') != 'true':
                        return False
            elif caller_level == 1: # Co-Admin
                if target_level == 0: # User
                    if get_config_value('rule_coadmin_delete_user', 'true') != 'true':
                        return False
                else:
                    return False
            else:
                return False
                
            # Delete messages
            cursor.execute('''
                DELETE FROM messages 
                WHERE session_id IN (SELECT id FROM chat_sessions WHERE user_id = ?)
            ''', (username,))
            
            # Delete chat sessions
            cursor.execute('DELETE FROM chat_sessions WHERE user_id = ?', (username,))
            
            # Delete settings
            cursor.execute('DELETE FROM user_settings WHERE id = ?', (username,))
            
            # Delete linked OAuth accounts
            cursor.execute('DELETE FROM linked_accounts WHERE user_id = ?', (username,))
            
            # Delete user tasks manually to avoid orphaned records
            try:
                cursor.execute('DELETE FROM tasks WHERE user_id = ?', (username,))
            except Exception:
                pass

            # Delete user record
            cursor.execute('DELETE FROM users WHERE id = ?', (username,))
            
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error deleting user from admin panel: {e}")
        return False


def log_admin_action(admin_id, action_type, target_user=None, details=None, ip_address=None):
    """Log administrative actions for audit log compliance"""
    if not ip_address:
        try:
            from flask import request
            if request:
                ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
                if ip_address and ',' in ip_address:
                    ip_address = ip_address.split(',')[0].strip()
        except Exception:
            pass
    if not ip_address:
        ip_address = '127.0.0.1'

    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO admin_audit_logs (admin_id, action_type, target_user, details, ip_address)
                VALUES (?, ?, ?, ?, ?)
            ''', (admin_id, action_type, target_user, details, ip_address))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error logging admin action: {e}")
        return False


def get_admin_audit_logs(limit=100):
    """Retrieve recent administrative audit logs"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, admin_id, action_type, target_user, details, timestamp, COALESCE(ip_address, '127.0.0.1')
                FROM admin_audit_logs
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            return [{
                'id': r[0],
                'admin_id': r[1],
                'action_type': r[2],
                'target_user': r[3],
                'details': r[4],
                'timestamp': r[5],
                'ip_address': r[6]
            } for r in rows]
    except Exception as e:
        import logging
        logging.error(f"Error fetching audit logs: {e}")
        return []


def clear_admin_audit_logs():
    """Wipe all admin audit logs"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM admin_audit_logs")
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error clearing audit logs: {e}")
        return False


def create_active_session(session_token, user_id, ip_address, user_agent):
    """Register active session in active_sessions table on login"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO active_sessions (session_token, user_id, ip_address, user_agent)
                VALUES (?, ?, ?, ?)
            ''', (session_token, user_id, ip_address, user_agent))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error creating active session: {e}")
        return False


def update_active_session_activity(session_token):
    """Update last_activity timestamp for an active session"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE active_sessions 
                SET last_activity = CURRENT_TIMESTAMP
                WHERE session_token = ?
            ''', (session_token,))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error updating active session last activity: {e}")
        return False


def is_session_active(session_token):
    """Check if session token exists in active_sessions table"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM active_sessions WHERE session_token = ?', (session_token,))
            return cursor.fetchone() is not None
    except Exception as e:
        import logging
        logging.error(f"Error checking session active status: {e}")
        return False


def revoke_active_session(session_token):
    """Delete session token row from active_sessions table"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM active_sessions WHERE session_token = ?', (session_token,))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error revoking active session: {e}")
        return False


def revoke_all_user_sessions(user_id):
    """Terminate all active session tokens for a user"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM active_sessions WHERE user_id = ?', (user_id,))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error revoking all user sessions: {e}")
        return False


def get_active_sessions_admin():
    """Retrieve all active sessions joined with user name and is_admin details"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.session_token, s.user_id, u.display_name, u.is_admin, s.ip_address, s.user_agent, s.created_at, s.last_activity
                FROM active_sessions s
                LEFT JOIN users u ON s.user_id = u.id
                ORDER BY s.last_activity DESC
            ''')
            rows = cursor.fetchall()
            return [{
                'session_token': r[0],
                'user_id': r[1],
                'display_name': r[2] or r[1],
                'is_admin': r[3] or 0,
                'ip_address': r[4] or 'Unknown',
                'user_agent': r[5] or 'Unknown',
                'created_at': r[6],
                'last_activity': r[7]
            } for r in rows]
    except Exception as e:
        import logging
        logging.error(f"Error getting active sessions: {e}")
        return []


def delete_user_self(username):
    """Cleanly delete the user's own profile, settings, chat history, sessions, passkeys, and authenticators."""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            
            # Delete messages first
            cursor.execute('''
                DELETE FROM messages 
                WHERE session_id IN (SELECT id FROM chat_sessions WHERE user_id = ?)
            ''', (username,))
            
            # Delete chat sessions
            cursor.execute('DELETE FROM chat_sessions WHERE user_id = ?', (username,))
            
            # Delete settings
            cursor.execute('DELETE FROM user_settings WHERE id = ?', (username,))
            
            # Delete linked accounts
            cursor.execute('DELETE FROM linked_accounts WHERE user_id = ?', (username,))
            
            # Delete custom themes (if exists)
            try:
                cursor.execute('DELETE FROM custom_themes WHERE user_id = ?', (username,))
            except Exception:
                pass
                
            # Delete passkeys and authenticators
            cursor.execute('DELETE FROM user_passkeys WHERE user_id = ?', (username,))
            cursor.execute('DELETE FROM user_authenticators WHERE user_id = ?', (username,))
            
            # Delete user tasks
            try:
                cursor.execute('DELETE FROM tasks WHERE user_id = ?', (username,))
            except Exception:
                pass

            # Delete active sessions
            cursor.execute('DELETE FROM active_sessions WHERE user_id = ?', (username,))
            
            # Delete user record
            cursor.execute('DELETE FROM users WHERE id = ?', (username,))
            
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error self-deleting user: {e}")
        return False


def create_support_ticket(sender, subject, message, category, priority):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO support_tickets (sender, subject, message, category, priority, status)
                VALUES (?, ?, ?, ?, ?, 'open')
            ''', (sender, subject, message, category, priority))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error creating support ticket: {e}")
        return False


def get_support_tickets():
    try:
        with connect_db() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM support_tickets ORDER BY created_at DESC')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        import logging
        logging.error(f"Error fetching support tickets: {e}")
        return []


def update_support_ticket_status(ticket_id, status):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE support_tickets SET status = ? WHERE id = ?', (status, ticket_id))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error updating support ticket status: {e}")
        return False


def get_support_ticket(ticket_id):
    try:
        with connect_db() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM support_tickets WHERE id = ?', (ticket_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        import logging
        logging.error(f"Error fetching support ticket {ticket_id}: {e}")
        return None

def delete_support_ticket(ticket_id):
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM support_tickets WHERE id = ?', (ticket_id,))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        import logging
        logging.error(f"Error deleting support ticket {ticket_id}: {e}")
        return False

def delete_all_support_tickets():
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM support_tickets')
            conn.commit()
            return cursor.rowcount
    except Exception as e:
        import logging
        logging.error(f"Error deleting all support tickets: {e}")
        return 0

def create_task(user_id, title, category, deadline, duration, confidence):
    """Create a new user task in the tasks table"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tasks (user_id, title, category, deadline, duration, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, title, category, deadline, duration, confidence))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error creating task: {e}")
        return False

def create_task_with_subtasks(user_id, title, category, deadline, duration, confidence, subtasks_list):
    """Transaction to insert a task and its associated subtasks. Returns task_id if successful."""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            # 1. Insert the parent task
            cursor.execute('''
                INSERT INTO tasks (user_id, title, category, deadline, duration, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, title, category, deadline, duration, confidence))
            task_id = cursor.lastrowid
            
            # 2. Insert each subtask
            for idx, sub in enumerate(subtasks_list):
                cursor.execute('''
                    INSERT INTO subtasks (task_id, title, duration, difficulty, priority, completed, subtask_order, dependency)
                    VALUES (?, ?, ?, ?, ?, 0, ?, ?)
                ''', (task_id, sub.get('title'), sub.get('duration'), sub.get('difficulty', 'Easy'), sub.get('priority', 'Medium'), idx, sub.get('dependency')))
            
            conn.commit()
            return task_id
    except Exception as e:
        import logging
        logging.error(f"Error creating task with subtasks: {e}")
        return None

def toggle_subtask(subtask_id, completed):
    """Toggle a subtask completed status (0 or 1) and return parent task progress details"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE subtasks SET completed = ? WHERE id = ?', (int(completed), subtask_id))
            
            # Find parent task_id
            cursor.execute('SELECT task_id FROM subtasks WHERE id = ?', (subtask_id,))
            row = cursor.fetchone()
            if not row:
                conn.commit()
                return None
            task_id = row[0]
            
            # Compute progress
            cursor.execute('SELECT COUNT(*), SUM(completed) FROM subtasks WHERE task_id = ?', (task_id,))
            total, finished = cursor.fetchone()
            progress = int((finished / total) * 100) if total > 0 else 0
            
            # Update parent task progress
            cursor.execute('UPDATE tasks SET progress = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (progress, task_id))
            
            conn.commit()
            
            # Auto update status lifecycle
            update_task_status_auto(task_id)
            
            return {
                'task_id': task_id,
                'progress': progress,
                'is_completed': (progress == 100)
            }
    except Exception as e:
        import logging
        logging.error(f"Error toggling subtask: {e}")
        return None

def get_task_progress(task_id):
    """Get the current progress of a task based on subtasks completion"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*), SUM(completed) FROM subtasks WHERE task_id = ?', (task_id,))
            total, finished = cursor.fetchone()
            progress = int((finished / total) * 100) if total > 0 else 0
            return progress
    except Exception as e:
        import logging
        logging.error(f"Error getting task progress: {e}")
        return 0

def check_duplicate_task(user_id, title, deadline):
    """Check if a task with the same user, title, and deadline already exists"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM tasks WHERE user_id = ? AND title = ? AND deadline = ?', (user_id, title, deadline))
            return cursor.fetchone() is not None
    except Exception as e:
        import logging
        logging.error(f"Error checking duplicate task: {e}")
        return False

def create_task_complete(user_id, title, description, category, deadline, estimated_duration, duration, confidence, priority, risk_level, status, progress, ai_generated, source_chat_message):
    """Insert a complete task row with all enriched task metadata"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tasks (
                    user_id, title, description, category, deadline, estimated_duration, 
                    duration, confidence, priority, risk_level, status, progress, 
                    ai_generated, source_chat_message, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                user_id, title, description, category, deadline, estimated_duration, 
                duration, confidence, priority, risk_level, status, progress, 
                ai_generated, source_chat_message
            ))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error creating complete task: {e}")
        return False

def get_user_tasks_filtered(user_id, search_query=None, category=None, priority=None, status=None, risk=None):
    """Retrieve user tasks filtered by search keywords and metadata tags"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            query = "SELECT id, title, description, category, deadline, estimated_duration, duration, confidence, priority, risk_level, status, progress, created_at, updated_at, completed_at, ai_generated, source_chat_message, priority_score, completion_probability, suggested_action, risk_reason FROM tasks WHERE user_id = ?"
            params = [user_id]
            
            if search_query:
                query += " AND (title LIKE ? OR description LIKE ?)"
                params.extend([f"%{search_query}%", f"%{search_query}%"])
            if category:
                query += " AND category = ?"
                params.append(category)
            if priority:
                query += " AND priority = ?"
                params.append(priority)
            if status:
                query += " AND status = ?"
                params.append(status)
            if risk:
                query += " AND risk_level = ?"
                params.append(risk)
                
            query += " ORDER BY deadline ASC, created_at DESC"
            cursor.execute(query, params)
            
            tasks = []
            for row in cursor.fetchall():
                subtasks = []
                cursor.execute("SELECT id, title, duration, difficulty, priority, completed, dependency FROM subtasks WHERE task_id = ? ORDER BY subtask_order ASC", (row[0],))
                for s_row in cursor.fetchall():
                    subtasks.append({
                        "id": s_row[0],
                        "title": s_row[1],
                        "duration": s_row[2],
                        "difficulty": s_row[3],
                        "priority": s_row[4],
                        "completed": bool(s_row[5]),
                        "dependency": s_row[6]
                    })
                
                tasks.append({
                    "id": row[0],
                    "title": row[1],
                    "description": row[2],
                    "category": row[3],
                    "deadline": row[4],
                    "estimated_duration": row[5],
                    "duration": row[6],
                    "confidence": row[7],
                    "priority": row[8],
                    "risk_level": row[9],
                    "status": row[10],
                    "progress": row[11],
                    "created_at": row[12],
                    "updated_at": row[13],
                    "completed_at": row[14],
                    "ai_generated": bool(row[15]),
                    "source_chat_message": row[16],
                    "priority_score": row[17] if row[17] is not None else 50,
                    "completion_probability": row[18] if row[18] is not None else 100,
                    "suggested_action": row[19] or "",
                    "risk_reason": row[20] or "",
                    "subtasks": subtasks
                })
            return tasks
    except Exception as e:
        import logging
        logging.error(f"Error getting filtered tasks: {e}")
        return []

def verify_task_ownership(task_id, user_id):
    """Ensure the user owns the task before modifying it"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM tasks WHERE id = ? AND user_id = ?', (task_id, user_id))
            return cursor.fetchone() is not None
    except Exception as e:
        import logging
        logging.error(f"Error verifying task ownership: {e}")
        return False

def update_task_details(task_id, fields):
    """Update arbitrary fields of a task dynamically"""
    try:
        if not fields:
            return True
        with connect_db() as conn:
            cursor = conn.cursor()
            query = "UPDATE tasks SET "
            params = []
            updates = []
            for k, v in fields.items():
                updates.append(f"{k} = ?")
                params.append(v)
            query += ", ".join(updates) + ", updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            params.append(task_id)
            cursor.execute(query, params)
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error updating task details: {e}")
        return False

def delete_task(task_id):
    """Delete a task permanently from the database (subtasks will cascade delete)"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error deleting task: {e}")
        return False

def update_task_status_auto(task_id):
    """Automatically update the status of a task based on its progress and deadline"""
    from datetime import datetime
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT deadline, progress, status FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            if not row:
                return False
            
            deadline_str, progress, current_status = row
            if current_status == 'Cancelled':
                return True
                
            new_status = 'Pending'
            if progress == 100:
                new_status = 'Completed'
            else:
                if progress > 0:
                    new_status = 'In Progress'
                
                # Check for overdue
                if deadline_str:
                    try:
                        # try standard YYYY-MM-DD HH:MM
                        deadline_dt = datetime.strptime(deadline_str.strip(), '%Y-%m-%d %H:%M')
                        if deadline_dt < datetime.now():
                            new_status = 'Overdue'
                    except Exception:
                        try:
                            # try YYYY-MM-DD
                            deadline_dt = datetime.strptime(deadline_str.strip(), '%Y-%m-%d')
                            if deadline_dt.date() < datetime.now().date():
                                new_status = 'Overdue'
                        except Exception:
                            pass
            
            if new_status != current_status:
                completed_at_val = datetime.now().strftime('%Y-%m-%d %H:%M') if new_status == 'Completed' else None
                cursor.execute('''
                    UPDATE tasks 
                    SET status = ?, completed_at = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                ''', (new_status, completed_at_val, task_id))
                conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error updating task status automatically: {e}")
        return False

def save_daily_plan(user_id, date, plan_json):
    """Save or update the daily plan for a user on a specific date"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO daily_plans (user_id, date, generated_plan, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, date) DO UPDATE SET
                    generated_plan = excluded.generated_plan,
                    created_at = CURRENT_TIMESTAMP
            ''', (user_id, date, plan_json))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error saving daily plan: {e}")
        return False

def get_daily_plan(user_id, date):
    """Retrieve the daily plan for a user on a specific date"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT generated_plan FROM daily_plans
                WHERE user_id = ? AND date = ?
            ''', (user_id, date))
            row = cursor.fetchone()
            return row[0] if row else None
    except Exception as e:
        import logging
        logging.error(f"Error retrieving daily plan: {e}")
        return None

def log_user_activity(user_id, activity_type, details):
    """Log user activity for recent activity feed"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO recent_activity (user_id, activity_type, details, timestamp)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, activity_type, details))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error logging user activity: {e}")
        return False

def get_recent_activities(user_id, limit=10):
    """Get recent activities for the user dashboard"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT activity_type, details, timestamp FROM recent_activity
                WHERE user_id = ?
                ORDER BY timestamp DESC LIMIT ?
            ''', (user_id, limit))
            rows = cursor.fetchall()
            return [{
                'activity_type': r[0],
                'details': r[1],
                'timestamp': r[2]
            } for r in rows]
    except Exception as e:
        import logging
        logging.error(f"Error retrieving user activity: {e}")
        return []

def ensure_model_sync_state(provider):
    """Create a sync-status row for a provider if it does not exist yet."""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_sync_state (
                    provider TEXT PRIMARY KEY,
                    last_sync_at TIMESTAMP,
                    last_success_at TIMESTAMP,
                    status TEXT DEFAULT 'idle',
                    last_error TEXT,
                    failure_count INTEGER DEFAULT 0,
                    model_count INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('INSERT OR IGNORE INTO model_sync_state (provider, status) VALUES (?, ?)', (provider, 'idle'))
            conn.commit()
        return True
    except Exception as e:
        import logging
        logging.error(f"Error ensuring model sync state: {e}")
        return False


def update_model_sync_state(provider, status, error=None, model_count=None):
    """Record the latest provider synchronization status without clearing cached models."""
    try:
        ensure_model_sync_state(provider)
        with connect_db() as conn:
            cursor = conn.cursor()
            if error:
                cursor.execute('''
                    UPDATE model_sync_state
                    SET status = ?, last_error = ?, failure_count = failure_count + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE provider = ?
                ''', (status, str(error)[:1000], provider))
            else:
                cursor.execute('''
                    UPDATE model_sync_state
                    SET status = ?, last_error = NULL, last_sync_at = CURRENT_TIMESTAMP,
                        last_success_at = CURRENT_TIMESTAMP, failure_count = 0,
                        model_count = COALESCE(?, model_count), updated_at = CURRENT_TIMESTAMP
                    WHERE provider = ?
                ''', (status, model_count, provider))
            conn.commit()
        return True
    except Exception as e:
        import logging
        logging.error(f"Error updating model sync state: {e}")
        return False


def get_model_sync_state():
    """Retrieve provider sync metadata for the admin panel and diagnostics."""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT provider, last_sync_at, last_success_at, status, last_error, failure_count, model_count, updated_at
                FROM model_sync_state
                ORDER BY provider ASC
            ''')
            rows = cursor.fetchall()
            return [{
                'provider': row[0],
                'last_sync_at': row[1],
                'last_success_at': row[2],
                'status': row[3],
                'last_error': row[4],
                'failure_count': row[5],
                'model_count': row[6],
                'updated_at': row[7]
            } for row in rows]
    except Exception as e:
        import logging
        logging.error(f"Error retrieving model sync state: {e}")
        return []


def get_all_api_settings():
    """Retrieve saved provider API settings across users for admin refresh and discovery."""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, api_provider, api_key, api_model
                FROM user_settings
                WHERE TRIM(COALESCE(api_provider, '')) != ''
                  AND TRIM(COALESCE(api_key, '')) != ''
                ORDER BY id ASC
            ''')
            rows = cursor.fetchall()
            return [{
                'user_id': row[0],
                'api_provider': row[1],
                'api_key': row[2],
                'api_model': row[3]
            } for row in rows]
    except Exception as e:
        import logging
        logging.error(f"Error retrieving API settings: {e}")
        return []


def save_api_settings(user_id, provider, api_key, model):
    """Save user-specific API provider, key, and model settings to user_settings table"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            # Ensure settings record exists first
            cursor.execute('INSERT OR IGNORE INTO user_settings (id) VALUES (?)', (user_id,))
            # Update columns
            cursor.execute('''
                UPDATE user_settings 
                SET api_provider = ?, api_key = ?, api_model = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (provider, api_key, model, user_id))
            conn.commit()
            return True
    except Exception as e:
        import logging
        logging.error(f"Error saving API settings: {e}")
        return False

def get_api_settings(user_id):
    """Retrieve API settings for a specific user"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT api_provider, api_key, api_model FROM user_settings WHERE id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'api_provider': row[0],
                    'api_key': row[1],
                    'api_model': row[2]
                }
            return None
    except Exception as e:
        import logging
        logging.error(f"Error retrieving API settings: {e}")
        return None


def get_gamification_stats(user_id):
    """Retrieve gamification stats for a specific user, initializing if not present"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            
            # Ensure gamification record exists
            cursor.execute('INSERT OR IGNORE INTO user_gamification (user_id) VALUES (?)', (user_id,))
            conn.commit()
            
            # Fetch gamification stats
            cursor.execute('''
                SELECT xp, level, streak, last_activity_date 
                FROM user_gamification 
                WHERE user_id = ?
            ''', (user_id,))
            row = cursor.fetchone()
            
            xp, level, streak, last_activity_date = row if row else (0, 1, 0, None)
            
            # Calculate next level info
            current_level_min_xp = ((level - 1) ** 2) * 100
            next_level_xp = (level ** 2) * 100
            xp_in_level = xp - current_level_min_xp
            xp_needed = next_level_xp - current_level_min_xp
            progress_pct = int((xp_in_level / xp_needed) * 100) if xp_needed > 0 else 0
            
            # Fetch badges
            cursor.execute('''
                SELECT badge_id, badge_name, badge_description, icon, earned_at 
                FROM user_badges 
                WHERE user_id = ?
                ORDER BY earned_at DESC
            ''', (user_id,))
            badges_rows = cursor.fetchall()
            badges = []
            for b in badges_rows:
                badges.append({
                    'badge_id': b[0],
                    'badge_name': b[1],
                    'badge_description': b[2],
                    'icon': b[3],
                    'earned_at': b[4]
                })
                
            return {
                'xp': xp,
                'level': level,
                'streak': streak,
                'last_activity_date': last_activity_date,
                'current_level_min_xp': current_level_min_xp,
                'next_level_xp': next_level_xp,
                'xp_in_level': xp_in_level,
                'xp_needed': xp_needed,
                'progress_pct': progress_pct,
                'badges': badges
            }
    except Exception as e:
        import logging
        logging.error(f"Error getting gamification stats: {e}")
        return {
            'xp': 0,
            'level': 1,
            'streak': 0,
            'last_activity_date': None,
            'current_level_min_xp': 0,
            'next_level_xp': 100,
            'xp_in_level': 0,
            'xp_needed': 100,
            'progress_pct': 0,
            'badges': []
        }


def award_xp(user_id, xp_amount, reason):
    """
    Award XP to a user, recalculate levels, handle streaks,
    log activities, check for level ups, and return state changes.
    """
    import math
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            
            # Ensure gamification record exists
            cursor.execute('INSERT OR IGNORE INTO user_gamification (user_id) VALUES (?)', (user_id,))
            
            # Get current stats
            cursor.execute('SELECT xp, level, streak, last_activity_date FROM user_gamification WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            current_xp, current_level, streak, last_date_str = row
            
            new_xp = current_xp + xp_amount
            new_level = math.floor(math.sqrt(new_xp / 100)) + 1
            
            level_up = new_level > current_level
            
            # Handle streak update
            today_str = datetime.now().strftime('%Y-%m-%d')
            new_streak = streak
            if last_date_str != today_str:
                if last_date_str:
                    try:
                        last_date = datetime.strptime(last_date_str, '%Y-%m-%d').date()
                        today = datetime.now().date()
                        delta = (today - last_date).days
                        if delta == 1:
                            new_streak = streak + 1
                        elif delta > 1:
                            new_streak = 1
                    except Exception:
                        new_streak = 1
                else:
                    new_streak = 1
            
            # Update database
            cursor.execute('''
                UPDATE user_gamification 
                SET xp = ?, level = ?, streak = ?, last_activity_date = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE user_id = ?
            ''', (new_xp, new_level, new_streak, today_str, user_id))
            conn.commit()
            
        # Log activity
        log_user_activity(user_id, "XP_GAIN", f"Gained {xp_amount} XP for {reason}")
        if level_up:
            log_user_activity(user_id, "LEVEL_UP", f"Reached Level {new_level}!")
            
        # Check badges
        new_badges = check_and_award_badges(user_id)
        
        # Return state changes
        return {
            'xp_gained': xp_amount,
            'level_up': level_up,
            'new_level': new_level,
            'old_level': current_level,
            'current_xp': new_xp,
            'streak': new_streak,
            'reason': reason,
            'new_badges': new_badges
        }
    except Exception as e:
        import logging
        logging.error(f"Error awarding XP: {e}")
        return {
            'xp_gained': xp_amount,
            'level_up': False,
            'new_level': 1,
            'old_level': 1,
            'current_xp': 0,
            'streak': 0,
            'reason': reason,
            'new_badges': []
        }


def award_badge(user_id, badge_id, badge_name, badge_description, icon):
    """Award a badge to a user if they don't already have it"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            
            # Check if badge already exists for this user
            cursor.execute('SELECT id FROM user_badges WHERE user_id = ? AND badge_id = ?', (user_id, badge_id))
            if cursor.fetchone():
                return False
                
            cursor.execute('''
                INSERT INTO user_badges (user_id, badge_id, badge_name, badge_description, icon, earned_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, badge_id, badge_name, badge_description, icon))
            conn.commit()
            
        log_user_activity(user_id, "BADGE_EARNED", f"Earned badge: {badge_name} - {badge_description}")
        return True
    except Exception as e:
        import logging
        logging.error(f"Error awarding badge: {e}")
        return False


def check_and_award_badges(user_id):
    """Check user progress and award badges if criteria met. Returns a list of newly earned badge dicts."""
    newly_earned = []
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            
            # Fetch completed subtasks
            cursor.execute('SELECT COUNT(*) FROM subtasks s JOIN tasks t ON s.task_id = t.id WHERE t.user_id = ? AND s.completed = 1', (user_id,))
            subtasks_completed = cursor.fetchone()[0]
            
            # Fetch completed tasks
            cursor.execute("SELECT COUNT(*) FROM tasks WHERE user_id = ? AND status = 'Completed'", (user_id,))
            tasks_completed = cursor.fetchone()[0]
            
            # Fetch daily plans
            cursor.execute('SELECT COUNT(*) FROM daily_plans WHERE user_id = ?', (user_id,))
            plans_count = cursor.fetchone()[0]
            
            # Fetch gamification level & streak
            cursor.execute('SELECT level, streak FROM user_gamification WHERE user_id = ?', (user_id,))
            gam_row = cursor.fetchone()
            level, streak = gam_row if gam_row else (1, 0)
            
            # Fetch panic recoveries from recent activity
            cursor.execute("SELECT COUNT(*) FROM recent_activity WHERE user_id = ? AND activity_type = 'Panic Schedule Recovery'", (user_id,))
            panic_recoveries = cursor.fetchone()[0]

        # Define badge award helper
        def try_award(badge_id, badge_name, badge_description, icon):
            if award_badge(user_id, badge_id, badge_name, badge_description, icon):
                newly_earned.append({
                    'badge_id': badge_id,
                    'badge_name': badge_name,
                    'badge_description': badge_description,
                    'icon': icon
                })
                
        # Evaluate badges
        if subtasks_completed >= 1:
            try_award('first_step', 'First Step', 'Completed your first subtask!', '🎯')
            
        if tasks_completed >= 1:
            try_award('first_task', 'Initiator', 'Completed your first full task!', '🚀')
        if tasks_completed >= 5:
            try_award('task_master', 'Task Master', 'Completed 5 tasks!', '🏆')
        if tasks_completed >= 15:
            try_award('grandmaster', 'Grandmaster', 'Completed 15 tasks!', '👑')
            
        if plans_count >= 1:
            try_award('first_plan', 'Daily Architect', 'Generated your first daily plan!', '✍️')
        if plans_count >= 5:
            try_award('planner_pro', 'Planner Pro', 'Generated 5 daily plans!', '📅')
            
        if level >= 5:
            try_award('level_5', 'High Achiever', 'Reached level 5!', '⭐')
        if level >= 10:
            try_award('level_10', 'Elite Performer', 'Reached level 10!', '🌟')
            
        if streak >= 3:
            try_award('streak_3', 'Streak Starter', 'Maintained a 3-day activity streak!', '🔥')
        if streak >= 7:
            try_award('streak_7', 'Unstoppable', 'Maintained a 7-day activity streak!', '⚡')
            
        if panic_recoveries >= 1:
            try_award('survivor', 'Survivor', 'Successfully executed panic recovery!', '🛡️')
            
        return newly_earned
    except Exception as e:
        import logging
        logging.error(f"Error checking and awarding badges: {e}")
        return newly_earned


def sync_models_to_db(provider, models_list):
    """
    Synchronizes fetched models for a provider:
    - Inserts new models.
    - Updates attributes of existing ones.
    - Sets is_available=0 for models no longer returned by the provider.
    """
    try:
        ensure_model_sync_state(provider)
        with connect_db() as conn:
            cursor = conn.cursor()
            
            # Fetch existing model_ids for this provider (excluding custom ones)
            cursor.execute('SELECT model_id FROM AvailableModels WHERE provider = ? AND api_owner IS NULL', (provider,))
            existing_ids = {row[0] for row in cursor.fetchall()}
            
            incoming_ids = set()
            for m in models_list:
                model_id = m['model_id']
                incoming_ids.add(model_id)
                
                cursor.execute('''
                    INSERT INTO AvailableModels (
                        provider, model_id, display_name, description, 
                        supports_chat, supports_reasoning, supports_vision, supports_audio, 
                        supports_image_generation, supports_function_calling, supports_streaming, 
                        context_window, status, is_available, last_synced
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(model_id) DO UPDATE SET
                        display_name = excluded.display_name,
                        description = excluded.description,
                        supports_chat = excluded.supports_chat,
                        supports_reasoning = excluded.supports_reasoning,
                        supports_vision = excluded.supports_vision,
                        supports_audio = excluded.supports_audio,
                        supports_image_generation = excluded.supports_image_generation,
                        supports_function_calling = excluded.supports_function_calling,
                        supports_streaming = excluded.supports_streaming,
                        context_window = excluded.context_window,
                        status = excluded.status,
                        is_available = 1,
                        last_synced = CURRENT_TIMESTAMP
                ''', (
                    provider, model_id, m.get('display_name', model_id), m.get('description'),
                    m.get('supports_chat', 1), m.get('supports_reasoning', 0), m.get('supports_vision', 0),
                    m.get('supports_audio', 0), m.get('supports_image_generation', 0), m.get('supports_function_calling', 0),
                    m.get('supports_streaming', 1), m.get('context_window'), m.get('status', 'active')
                ))
            
            # Mark discontinued models as unavailable
            discontinued = existing_ids - incoming_ids
            for model_id in discontinued:
                cursor.execute('UPDATE AvailableModels SET is_available = 0, last_synced = CURRENT_TIMESTAMP WHERE model_id = ?', (model_id,))
                
            conn.commit()
        update_model_sync_state(provider, 'ready', model_count=len(models_list))
        return True
    except Exception as e:
        import logging
        logging.error(f"Error syncing models to db: {e}")
        update_model_sync_state(provider, 'error', error=str(e), model_count=0)
        return False


def get_available_models():
    """Retrieve all available models, grouped by provider (and admin custom models)"""
    try:
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, provider, model_id, display_name, description, 
                       supports_chat, supports_reasoning, supports_vision, supports_audio, 
                       supports_image_generation, supports_function_calling, supports_streaming, 
                       context_window, status, is_available, last_synced, api_owner
                FROM AvailableModels
                WHERE is_available = 1
                ORDER BY provider ASC, display_name ASC
            ''')
            columns = [col[0] for col in cursor.description]
            models = []
            for row in cursor.fetchall():
                models.append(dict(zip(columns, row)))
            return models
    except Exception as e:
        import logging
        logging.error(f"Error loading available models: {e}")
        return []


def register_custom_model_db(provider, model_id, display_name, description=None, context_window=None, features=None):
    """Allows administrators to manually register custom models"""
    try:
        features = features or {}
        with connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO AvailableModels (
                    provider, model_id, display_name, description, 
                    supports_chat, supports_reasoning, supports_vision, supports_audio, 
                    supports_image_generation, supports_function_calling, supports_streaming, 
                    context_window, status, is_available, last_synced, api_owner
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', 1, CURRENT_TIMESTAMP, 'admin')
                ON CONFLICT(model_id) DO UPDATE SET
                    provider = excluded.provider,
                    display_name = excluded.display_name,
                    description = excluded.description,
                    supports_chat = excluded.supports_chat,
                    supports_reasoning = excluded.supports_reasoning,
                    supports_vision = excluded.supports_vision,
                    supports_audio = excluded.supports_audio,
                    supports_image_generation = excluded.supports_image_generation,
                    supports_function_calling = excluded.supports_function_calling,
                    supports_streaming = excluded.supports_streaming,
                    context_window = excluded.context_window,
                    is_available = 1,
                    last_synced = CURRENT_TIMESTAMP
            ''', (
                provider, model_id, display_name, description,
                features.get('supports_chat', 1), features.get('supports_reasoning', 0),
                features.get('supports_vision', 0), features.get('supports_audio', 0),
                features.get('supports_image_generation', 0), features.get('supports_function_calling', 0),
                features.get('supports_streaming', 1), context_window
            ))
            conn.commit()
        return True
    except Exception as e:
        import logging
        logging.error(f"Error registering custom model: {e}")
        return False



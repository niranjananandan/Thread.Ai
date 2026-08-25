from flask import Flask, render_template, request, jsonify, Response
import sqlite3
import google.generativeai as genai
import json
import os
import csv
from werkzeug.utils import secure_filename
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import pandas as pd

from dotenv import load_dotenv
load_dotenv()

# ==========================================
# 1. Setup & Configuration
# ==========================================
# Initialize the Gemini model for fast and smart responses
genai.configure(api_key=os.environ.get("GEMINI_API_KEY", ""))
model = genai.GenerativeModel('gemini-3.6-flash')

app = Flask(__name__)

# Admin Settings
ADMIN_EMAILS = ['1u24ai024.niranjan@gmail.com', 'niranjan.admin@gmail.com', 'admin@example.com'] # Add valid admin emails here


# File Upload Configurations
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024 # 25 MB max size
# Vercel uses a read-only filesystem except for the /tmp directory
UPLOAD_FOLDER = '/tmp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    """Establish and return a connection to the SQLite database."""
    # Vercel's root directory is read-only. We must place the SQLite file in /tmp
    conn = sqlite3.connect('/tmp/textile.db')
    conn.row_factory = sqlite3.Row  # Enables column access by name
    return conn

def init_analytics_db():
    """Initialize the isolated user analytics table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_analytics_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_query TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            google_id TEXT UNIQUE,
            email TEXT,
            name TEXT,
            picture_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_chats (
            session_id TEXT PRIMARY KEY,
            google_id TEXT,
            title TEXT,
            history_json TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Initialize analytics DB on startup
init_analytics_db()

def log_query(user_query):
    """Securely log queries in isolation."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO user_analytics_logs (user_query) VALUES (?)", (user_query,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to log query: {e}")

@app.route('/', methods=['GET', 'POST'])
def home():
    # If Google OAuth falls back to a POST redirect on mobile, just load the app normally.
    # The frontend will still require them to log in via the popup button.
    return render_template('index.html')

# ==========================================
# 2. Authentication Route
# ==========================================
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")

@app.route('/api/auth/google', methods=['POST'])
def auth_google():
    token = request.json.get('token')
    if not token:
        return jsonify({"error": "No token provided"}), 400
        
    try:
        # Note: If testing without a real Client ID, this will fail.
        # Remove GOOGLE_CLIENT_ID argument if you want to skip audience validation (not recommended for production)
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)
        
        google_id = idinfo['sub']
        email = idinfo.get('email')
        name = idinfo.get('given_name') or idinfo.get('name')
        picture = idinfo.get('picture')
        
        # Save or update user in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE google_id = ?", (google_id,))
        user = cursor.fetchone()
        
        if user:
            cursor.execute("UPDATE users SET email = ?, name = ?, picture_url = ? WHERE google_id = ?", 
                           (email, name, picture, google_id))
        else:
            cursor.execute("INSERT INTO users (google_id, email, name, picture_url) VALUES (?, ?, ?, ?)",
                           (google_id, email, name, picture))
                           
        conn.commit()
        conn.close()
        
        is_admin = email in ADMIN_EMAILS
        
        return jsonify({
            "message": "Authentication successful",
            "user": {
                "google_id": google_id,
                "name": name,
                "email": email,
                "picture": picture,
                "is_admin": is_admin
            }
        })
        
    except ValueError as e:
        # Invalid token
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": "Authentication failed", "details": str(e)}), 500

@app.route('/admin')
def admin_dashboard():
    """Serve the Admin Dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get basic stats
    cursor.execute("SELECT COUNT(*) as count FROM users")
    total_users = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM user_analytics_logs")
    total_queries = cursor.fetchone()['count']
    
    cursor.execute("SELECT COUNT(*) as count FROM user_chats")
    total_chats = cursor.fetchone()['count']
    
    # Get user list
    cursor.execute("SELECT id, name, email, google_id, created_at FROM users ORDER BY created_at DESC")
    users = [dict(row) for row in cursor.fetchall()]
    
    # Get all chats joined with user info
    cursor.execute('''
        SELECT c.session_id, c.title, c.updated_at, u.name, u.email 
        FROM user_chats c
        JOIN users u ON c.google_id = u.google_id
        ORDER BY c.updated_at DESC
    ''')
    all_chats = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return render_template('admin.html', stats={
        "total_users": total_users,
        "total_queries": total_queries,
        "total_chats": total_chats
    }, users=users, chats=all_chats)

# ==========================================
# 3. The Smart Chat Route
system_instruction = """You are THREAD.AI, an AI assistant for the textile industry. You were created and are owned by NIRANJAN ANANDAN.
Rule 1: Your primary purpose is to answer questions related to textiles, fashion, clothing, fabrics, garments, and related inventory/sales data.
Rule 2: You MUST answer basic conversational greetings, small talk, and simple general knowledge questions (e.g., "hello", "how are you", "who are you", "who created you", basic math, weather). If asked who created or owns you, state clearly that it is NIRANJAN ANANDAN. Be polite and helpful.
Rule 3: If the user asks complex, detailed, or domain-specific questions completely unrelated to textiles (e.g., medical advice, coding a website, historical essays, legal advice), you MUST refuse to answer and reply EXACTLY: "Please ask only textile-based questions with me."
Rule 4: If the user provides data (e.g. CSV) that is clearly NOT related to the textile industry, you MUST refuse to analyze it and reply EXACTLY: "Please do not upload non-textile documents."
Do not deviate from these rules."""
chat_model = genai.GenerativeModel('gemini-3.6-flash', system_instruction=system_instruction)

sessions = {}

@app.route('/api/generate_title', methods=['POST'])
def generate_title():
    try:
        user_message = request.json.get('message', '')
        session_id = request.json.get('session_id', '')
        google_id = request.json.get('google_id', '')
        
        if not user_message:
            return jsonify({"title": "New Chat"})
        
        prompt = f"Generate a very short, concise, apt title (2-4 words maximum) for a chat that starts with this message:\n{user_message}\nReturn ONLY the title, no quotes."
        response = chat_model.generate_content(prompt)
        title = response.text.strip().replace('"', '')
        
        if session_id and google_id:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE user_chats SET title = ? WHERE session_id = ? AND google_id = ?", (title, session_id, google_id))
            conn.commit()
            conn.close()
        
        return jsonify({"title": title})
    except Exception as e:
        return jsonify({"title": "New Chat", "error": str(e)})

@app.route('/api/get_chats', methods=['POST'])
def get_chats():
    google_id = request.json.get('google_id')
    if not google_id:
        return jsonify({"error": "Unauthorized"}), 401
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT session_id, title, history_json, updated_at FROM user_chats WHERE google_id = ? ORDER BY updated_at DESC", (google_id,))
    chats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({"chats": chats})

@app.route('/api/delete_chat', methods=['POST'])
def delete_chat():
    session_id = request.json.get('session_id')
    google_id = request.json.get('google_id')
    
    if not session_id or not google_id:
        return jsonify({"error": "Missing parameters"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_chats WHERE session_id = ? AND google_id = ?", (session_id, google_id))
    conn.commit()
    conn.close()
    
    # Also clear from memory if exists
    if session_id in sessions:
        del sessions[session_id]
        
    return jsonify({"success": True})

@app.route('/api/update_chat_title', methods=['POST'])
def update_chat_title():
    session_id = request.json.get('session_id')
    google_id = request.json.get('google_id')
    title = request.json.get('title')
    
    if not all([session_id, google_id, title]):
        return jsonify({"error": "Missing parameters"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE user_chats SET title = ? WHERE session_id = ? AND google_id = ?", (title, session_id, google_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True})

@app.route('/api/validate_csv', methods=['POST'])
def validate_csv():
    try:
        data = request.json.get('data', '')
        if not data:
            return jsonify({"valid": False, "error": "No data provided"})
        
        prompt = f"Analyze this CSV sample data:\n{data}\n\nIs this dataset related to textiles, clothing, fashion, garments, or fabric? Answer ONLY with 'YES' or 'NO'."
        response = chat_model.generate_content(prompt)
        is_valid = 'YES' in response.text.upper()
        
        return jsonify({"valid": is_valid})
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)}), 500

@app.route('/api/chat_stream', methods=['POST'])
def chat_stream():
    try:
        user_message = request.form.get('message', '').strip()
        session_id = request.form.get('session_id', 'default_session')
        
        if not user_message and request.is_json:
            json_data = request.json
            user_message = json_data.get('message', '').strip()
            session_id = json_data.get('session_id', 'default_session')
            
        # Extract google_id
        google_id = request.form.get('google_id') if request.form else None
        if not google_id and request.is_json:
            google_id = request.json.get('google_id')
            
        if not user_message:
            return Response("Please enter a message so I can assist you.", mimetype='text/plain')
            
        log_query(user_message)
        
        uploaded_file = request.files.get('file')
        if uploaded_file and uploaded_file.filename:
            if not uploaded_file.filename.lower().endswith('.csv'):
                return Response("Invalid file type. Please upload a valid textile/clothing inventory CSV file.", mimetype='text/plain')
            
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(filepath)
            
            try:
                df = pd.read_csv(filepath)
                csv_data = df.to_csv(index=False)
                
                generation_prompt = f"Here is the user's uploaded complete CSV dataset:\n{csv_data}\n\nUser Question: {user_message}\nRemember Rule 3: Evaluate if this CSV data is textile-related. If not, reject it. Analyze the entire dataset to answer the user's question accurately."
                
                def generate_csv_response():
                    response = chat_model.generate_content(generation_prompt, stream=True)
                    for chunk in response:
                        if chunk.text:
                            yield chunk.text
                return Response(generate_csv_response(), mimetype='text/plain')
            finally:
                if os.path.exists(filepath):
                    os.remove(filepath)
        else:
            # Handle DB / Chat mode
            if session_id not in sessions:
                history = []
                if google_id:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT history_json FROM user_chats WHERE session_id = ? AND google_id = ?", (session_id, google_id))
                    row = cursor.fetchone()
                    conn.close()
                    if row and row['history_json']:
                        try:
                            history = json.loads(row['history_json'])
                        except:
                            pass
                sessions[session_id] = chat_model.start_chat(history=history)
                
            active_chat = sessions[session_id]
            
            def generate_chat_response():
                try:
                    response = active_chat.send_message(user_message, stream=True)
                    for chunk in response:
                        if chunk.text:
                            yield chunk.text
                            
                    # After streaming, save the updated history to the database
                    if google_id:
                        try:
                            formatted_history = [{"role": m.role, "parts": [p.text for p in m.parts]} for m in active_chat.history]
                            history_json = json.dumps(formatted_history)
                            
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("SELECT session_id FROM user_chats WHERE session_id = ?", (session_id,))
                            if cursor.fetchone():
                                cursor.execute("UPDATE user_chats SET history_json = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?", 
                                             (history_json, session_id))
                            else:
                                cursor.execute("INSERT INTO user_chats (session_id, google_id, title, history_json) VALUES (?, ?, 'New Chat', ?)", 
                                             (session_id, google_id, history_json))
                            conn.commit()
                            conn.close()
                        except Exception as e:
                            print(f"Failed to save chat history to DB: {e}")
                except Exception as e:
                    yield f"\n\n[System Error: {str(e)}]\nPlease check if your GEMINI_API_KEY is valid in Render."
                        
            return Response(generate_chat_response(), mimetype='text/plain')
            
    except Exception as e:
        return Response(f"THREAD.AI Services are currently unreachable. Error: {str(e)}", mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)
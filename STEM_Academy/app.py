from flask import Flask, request, jsonify, render_template
import os
import base64
from pdf_loader import PDFChatBot
from PIL import Image
import io
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import jwt
import datetime

app = Flask(__name__, static_folder='static')
chatbot = PDFChatBot()

# Configure upload folder
UPLOAD_FOLDER = 'uploads'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load all PDF files from the uploads folder
def load_pdfs_from_folder(folder):
    pdf_files = [f for f in os.listdir(folder) if f.endswith('.pdf')]
    for pdf_file in pdf_files:
        pdf_path = os.path.join(folder, pdf_file)
        result = chatbot.load_pdf(pdf_path)
        print(f"Loaded {pdf_file}: {result}")

# Load PDFs when the application starts
load_pdfs_from_folder(app.config['UPLOAD_FOLDER'])

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         email TEXT UNIQUE NOT NULL,
         password TEXT NOT NULL,
         name TEXT)
    ''')
    conn.commit()
    conn.close()

# Initialize the database
init_db()

# Add this secret key to your Flask app configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this to a secure secret key

@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Hash the password
        hashed_password = generate_password_hash(data['password'])
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        try:
            c.execute('INSERT INTO users (email, password, name) VALUES (?, ?, ?)',
                     (data['email'], hashed_password, data.get('name', '')))
            conn.commit()
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Email already exists'}), 409
        finally:
            conn.close()
            
        return jsonify({'message': 'User created successfully'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Missing required fields'}), 400
            
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        c.execute('SELECT * FROM users WHERE email = ?', (data['email'],))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], data['password']):
            # Generate JWT token
            token = jwt.encode({
                'user_id': user[0],
                'email': user[1],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'])
            
            return jsonify({
                'token': token,
                'user': {
                    'id': user[0],
                    'email': user[1],
                    'name': user[3]
                }
            }), 200
        
        return jsonify({'error': 'Invalid email or password'}), 401
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400
            
        answer = chatbot.ask_question(data['question'])
        return jsonify({'answer': answer}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload_image', methods=['POST'])
def upload_image():
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400
        
        # Decode the base64 image
        image_data = base64.b64decode(data['image'].split(',')[1])
        image = Image.open(io.BytesIO(image_data))
        
        # Save the image to the uploads folder
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded_image.png')
        image.save(image_path)
        
        # Process the image (e.g., extract text using OCR)
        # For now, just return a success message
        return jsonify({'message': 'Image uploaded successfully!'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def auth():
    return render_template('auth.html')

@app.route('/chat')
def index():
    return render_template('index.html')

@app.route("/home")
def home():
    return render_template("home.html")

@app.route("/menu")
def menu():
    return render_template("menu.html")

@app.route("/aboutus")
def aboutus():
    return render_template("aboutus.html")

if __name__ == '__main__':
    app.run(debug=True)
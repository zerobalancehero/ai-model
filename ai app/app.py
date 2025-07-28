from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from diffusers import StableDiffusionPipeline
import torch
import json
import os
from datetime import datetime
from PIL import Image
from flask import send_from_directory
from utils import generate_image, save_metadata, get_history, setup_database
import sqlite3

app = Flask(__name__, static_url_path="/static")
UPLOAD_FOLDER = os.path.join('static', 'images')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


CORS(app, resources={r"/*": {"origins": "http://localhost:5500"}})

CORS(app)


model = StableDiffusionPipeline.from_pretrained("CompVis/stable-diffusion-v1-4")
model.to("cuda" if torch.cuda.is_available() else "cpu")

IMAGE_DATA_FILE = "static/image_data.json"
IMAGES_FOLDER = "static/images"


def save_metadata(prompt, filename):
    if os.path.exists(IMAGE_DATA_FILE):
        with open(IMAGE_DATA_FILE, "r") as file:
            image_data = json.load(file)
    else:
        image_data = []

    image_data.append({
        "prompt": prompt,
        "filename": filename,
        "url": f"/static/images/{filename}"  # Correct URL
    })

    with open(IMAGE_DATA_FILE, "w") as file:
        json.dump(image_data, file)


@app.route("/generate", methods=["POST"])
def generate():
    try:
        data = request.json
        prompt = data.get("prompt", None)
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_only = f"generated_image_{timestamp}.png"
        full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename_only)  # Save to static/images/

        print(f"Generating image for: {prompt}")
        image = model(prompt).images[0]
        image.save(full_path)

        save_metadata(prompt, filename_only)
        print(f"Image saved as '{full_path}'")

        return jsonify({"filename": filename_only, "url": f"/static/images/{filename_only}"})

    except Exception as e:
        print("Error generating image:", e)
        return jsonify({"error": str(e)}), 500

from utils import get_history

@app.route('/images')
def get_images():
    # Try to load metadata (prompt + filename)
    if os.path.exists(IMAGE_DATA_FILE):
        with open(IMAGE_DATA_FILE, "r") as f:
            image_data = json.load(f)
    else:
        image_data = []

    # Get all image files in static/images
    files = set(os.listdir(IMAGES_FOLDER))
    # Add any images not in metadata (for backward compatibility)
    filenames_in_metadata = set(img['filename'] for img in image_data)
    for fname in files:
        if fname.lower().endswith(('.png', '.jpg', '.jpeg')) and fname not in filenames_in_metadata:
            image_data.append({"filename": fname, "prompt": "(unknown prompt)"})

    # Optionally, sort by creation time or filename
    image_data.sort(key=lambda x: x['filename'])

    return jsonify(image_data)

@app.route('/download/<filename>')
def download_image(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    return "File not found", 404



@app.route("/delete", methods=["POST"])
def delete_image():
    try:
        data = request.json
        filename_to_delete = data.get("filename", None)

        if not filename_to_delete:
            return jsonify({"error": "No filename provided"}), 400

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename_to_delete)
        if os.path.exists(file_path):
            os.remove(file_path)

            if os.path.exists(IMAGE_DATA_FILE):
                with open(IMAGE_DATA_FILE, "r") as file:
                    image_data = json.load(file)
                    image_data = [img for img in image_data if img["filename"] != filename_to_delete]

                with open(IMAGE_DATA_FILE, "w") as file:
                    json.dump(image_data, file)

            return jsonify({"message": "Image deleted successfully"})

        return jsonify({"error": "Image file not found"}), 404

    except Exception as e:
        print("Error deleting image:", e)
        return jsonify({"error": str(e)}), 500

USER_DB = 'users.db'

def init_user_db():
    conn = sqlite3.connect(USER_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

init_user_db()

@app.route("/about")
def about():
    return render_template("about.html")

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    conn = sqlite3.connect(USER_DB)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    user = c.fetchone()
    conn.close()
    if user:
        return jsonify({"success": True})
    else:
        return jsonify({"success": False})

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    conn = sqlite3.connect(USER_DB)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "error": "Username already exists"})

@app.route("/")
def home():
    return render_template("about.html")

@app.route("/login.html")
def login_page():
    return render_template("login.html")

@app.route("/index.html")
def index_html():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import urllib.request
from werkzeug.utils import secure_filename
import numpy as np
import cv2
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip

app = Flask(__name__)

# Folders set-up
UPLOAD_FOLDER = 'static/uploads'
PROCESSED_FOLDER = 'static/processed'
MUSIC_FOLDER = 'static/music'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER
app.config['MUSIC_FOLDER'] = MUSIC_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)
os.makedirs(MUSIC_FOLDER, exist_ok=True)

# Free royalty-free background music track (Lofi Hip Hop)
BG_MUSIC_URL = "https://pub-c5e31b5cdafb419a86a69d5d341b024c.r2.dev/lofi_loop.mp3"
BG_MUSIC_PATH = os.path.join(MUSIC_FOLDER, 'bg_music.mp3')

def download_default_music():
    """Server par ek default copyright-free background music download karna"""
    if not os.path.exists(BG_MUSIC_PATH):
        try:
            print("Downloading background music track...")
            urllib.request.urlretrieve(BG_MUSIC_URL, BG_MUSIC_PATH)
            print("Music download complete!")
        except Exception as e:
            print(f"Music download failed: {str(e)}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- CUSTOM FREE VIDEO FILTERS (OPENCV & NUMPY) ---

def apply_cinematic_bars(frame):
    """Video ke top aur bottom mein cinematic black bars add karna"""
    h, w, c = frame.shape
    bar_h = int(h * 0.12)  # 12% black bars
    frame_copy = frame.copy()
    frame_copy[0:bar_h, :, :] = 0
    frame_copy[h-bar_h:h, :, :] = 0
    
    # Warm cinematic color grading
    img = frame_copy.astype(np.float32)
    img[:, :, 0] = np.clip(img[:, :, 0] * 1.15, 0, 255) # Red (Warmth)
    img[:, :, 1] = np.clip(img[:, :, 1] * 1.05, 0, 255) # Green
    img[:, :, 2] = np.clip(img[:, :, 2] * 0.95, 0, 255) # Blue
    return img.astype(np.uint8)

def apply_cyberpunk_filter(frame):
    """Neon Purple and Cyberpunk Blue look filter"""
    img = frame.astype(np.float32)
    r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]
    
    r_new = np.clip(r * 1.3 + b * 0.2, 0, 255)
    g_new = np.clip(g * 0.25 + b * 0.25, 0, 255)
    b_new = np.clip(b * 1.7, 0, 255)
    
    cyber = np.stack([r_new, g_new, b_new], axis=2).astype(np.uint8)
    return cyber

def apply_anime_filter(frame):
    """Anime/Cartoon look"""
    img_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 9)
    color = cv2.bilateralFilter(img_bgr, 9, 250, 250)
    cartoon_bgr = cv2.bitwise_and(color, color, mask=edges)
    return cv2.cvtColor(cartoon_bgr, cv2.COLOR_BGR2RGB)

@app.route('/')
def home():
    download_default_music()
    return render_template('index.html')

@app.route('/generate-video', methods=['POST'])
def generate_video():
    if 'video' not in request.files:
        file = request.files.get('file')
    else:
        file = request.files['video']

    prompt = request.form.get('prompt', '')
    effect = request.form.get('effect', '')

    if not file or file.filename == '':
        return jsonify({"success": False, "error": "Bhai, video upload karna zaroori hai!"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)

        output_filename = "edited_" + filename
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)

        try:
            clip = VideoFileClip(input_path)
            if clip.w > 480: clip = clip.resize(width=480)
            if clip.duration > 8: clip = clip.subclip(0, 8)

            chosen_effect = effect.lower() if effect else prompt.lower()

            if "cinematic" in chosen_effect or "4k" in chosen_effect:
                clip = clip.fl_image(apply_cinematic_bars)
            elif "cyber" in chosen_effect or "neon" in chosen_effect:
                clip = clip.fl_image(apply_cyberpunk_filter)
            elif "anime" in chosen_effect or "cartoon" in chosen_effect:
                clip = clip.fl_image(apply_anime_filter)
            elif "music" in chosen_effect or "bg" in chosen_effect:
                download_default_music()
                if os.path.exists(BG_MUSIC_PATH):
                    bg_audio = AudioFileClip(BG_MUSIC_PATH).subclip(0, clip.duration)
                    if clip.audio:
                        mixed_audio = CompositeAudioClip([clip.audio.volumex(0.3), bg_audio.volumex(0.8)])
                    else:
                        mixed_audio = bg_audio
                    clip = clip.set_audio(mixed_audio)

            clip.write_videofile(output_path, codec='libx264', audio_codec='aac', preset='ultrafast', threads=1, logger=None)
            clip.close()
            return jsonify({"success": True, "video_url": f"/static/processed/{output_filename}"})

        except Exception as e:
            if 'clip' in locals(): clip.close()
            return jsonify({"success": False, "error": f"Editing fail ho gayi: {str(e)}"}), 500

    return jsonify({"success": False, "error": "Invalid video format!"}), 400

@app.route('/static/processed/<filename>')
def send_processed_video(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

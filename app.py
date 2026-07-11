from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/generate-video', methods=['POST'])
def generate_video():
    prompt = request.form.get('prompt')
    if not prompt:
        return jsonify({"error": "Prompt missing!"}), 400

    # Test video link
    return jsonify({
        "success": True,
        "video_url": "https://www.w3schools.com/html/mov_bbb.mp4"
    })

if __name__ == '__main__':
    # Yeh internet server (Render) ke liye zaroori hai
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
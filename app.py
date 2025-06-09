from flask import Flask, request, jsonify, render_template
import os
from datetime import datetime, timedelta
import subprocess
from werkzeug.utils import secure_filename
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)

# ================== Cấu hình ==================
UPLOAD_FOLDER = 'uploaded_videos'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.force-ssl"
]

# ================== Hàm phụ ==================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_youtube_service():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    return build("youtube", "v3", credentials=creds)

# ================== Livestream YouTube ==================
def create_livestream(youtube):
    start_time = (datetime.utcnow() + timedelta(minutes=1)).isoformat("T") + "Z"

    broadcast = youtube.liveBroadcasts().insert(
        part="snippet,status,contentDetails",
        body={
            "snippet": {
                "title": "📺 Fake Livestream 24/7",
                "scheduledStartTime": start_time
            },
            "status": {"privacyStatus": "public"},
            "contentDetails": {"monitorStream": {"enableMonitorStream": False}}
        }
    ).execute()

    stream = youtube.liveStreams().insert(
        part="snippet,cdn",
        body={
            "snippet": {"title": "24/7 Stream"},
            "cdn": {
                "frameRate": "30fps",
                "resolution": "720p",
                "ingestionType": "rtmp"
            }
        }
    ).execute()

    youtube.liveBroadcasts().bind(
        part="id,contentDetails",
        id=broadcast["id"],
        streamId=stream["id"]
    ).execute()

    ingest = stream["cdn"]["ingestionInfo"]
    return f"{ingest['ingestionAddress']}/{ingest['streamName']}"

# ================== FFmpeg Stream ==================
def stream_looped_video(video_path, rtmp_url):
    command = [
        "ffmpeg",
        "-stream_loop", "-1",
        "-re", "-i", video_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-maxrate", "3000k",
        "-bufsize", "6000k",
        "-pix_fmt", "yuv420p",
        "-g", "50",
        "-c:a", "aac",
        "-b:a", "128k",
        "-ar", "44100",
        "-f", "flv",
        rtmp_url
    ]
    subprocess.Popen(command)

# ================== Route giao diện web ==================
@app.route('/upload', methods=['GET'])
def upload_page():
    return render_template("index.html")

# ================== Route kiểm tra ==================
@app.route('/')
def home():
    return "✅ A1Host đang hoạt động. Truy cập /upload để gửi video livestream."

# ================== API Upload & Stream ==================
@app.route('/upload-and-stream', methods=['POST'])
def upload_and_stream():
    if 'video' not in request.files:
        return jsonify({'error': 'Không tìm thấy video'}), 400

    file = request.files['video']
    if not allowed_file(file.filename):
        return jsonify({'error': 'Định dạng không hợp lệ'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    youtube = get_youtube_service()
    rtmp_url = create_livestream(youtube)
    stream_looped_video(filepath, rtmp_url)

    return jsonify({'message': '✅ Đã bắt đầu phát livestream 24/7', 'video': filename}), 200

# ================== Khởi chạy ==================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)

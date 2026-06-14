import os
import uuid
import subprocess
import threading
import requests as req
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "secret")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

MEDIA_DIR = "/app/media"
os.makedirs(MEDIA_DIR, exist_ok=True)

def download_and_convert(url, job_id, original_type, meta):
    try:
        r = req.get(url, timeout=30)
        ext = url.split("?")[0].split(".")[-1].lower()
        input_path = os.path.join(MEDIA_DIR, f"{job_id}_input.{ext}")
        with open(input_path, "wb") as f:
            f.write(r.content)

        if original_type == "video":
            output_path = os.path.join(MEDIA_DIR, f"{job_id}.mp4")
            result = subprocess.run([
                "ffmpeg", "-y",
                "-i", input_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-movflags", "faststart",
                output_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if result.returncode != 0:
                subprocess.run([
                    "ffmpeg", "-y",
                    "-i", input_path,
                    "-vcodec", "libx264",
                    "-acodec", "aac",
                    "-movflags", "faststart",
                    "-preset", "ultrafast",
                    "-crf", "28",
                    output_path
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            os.remove(input_path)
            socketio.emit("show_overlay", {
                "job_id": job_id,
                "username": meta["username"],
                "avatar": meta["avatar"],
                "text": meta["text"],
                "hide_user": meta.get("hide_user", False),
                "media": f"/media/{job_id}.mp4",
                "media_type": "video",
            })
        elif original_type == "audio":
            # Convertir les fichiers audio en MP3 si ce n'est pas déjà le cas
            output_path = os.path.join(MEDIA_DIR, f"{job_id}.mp3")
            if ext != "mp3":
                result = subprocess.run([
                    "ffmpeg", "-y",
                    "-i", input_path,
                    "-codec:a", "libmp3lame",
                    "-q:a", "2",
                    output_path
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                if result.returncode != 0:
                    # Si la conversion échoue, on essaie avec aac
                    subprocess.run([
                        "ffmpeg", "-y",
                        "-i", input_path,
                        "-codec:a", "aac",
                        output_path
                    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                os.remove(input_path)
            else:
                os.rename(input_path, output_path)
            
            socketio.emit("show_overlay", {
                "job_id": job_id,
                "username": meta["username"],
                "avatar": meta["avatar"],
                "text": meta["text"],
                "hide_user": meta.get("hide_user", False),
                "media": f"/media/{job_id}.mp3",
                "media_type": "audio",
            })
        else:
            output_path = os.path.join(MEDIA_DIR, f"{job_id}.{ext}")
            os.rename(input_path, output_path)
            socketio.emit("show_overlay", {
                "job_id": job_id,
                "username": meta["username"],
                "avatar": meta["avatar"],
                "text": meta["text"],
                "hide_user": meta.get("hide_user", False),
                "media": f"/media/{job_id}.{ext}",
                "media_type": "image",
            })

    except Exception as e:
        print(f"Erreur conversion : {e}")
        socketio.emit("show_overlay", {
            "job_id": job_id,
            "username": meta["username"],
            "avatar": meta["avatar"],
            "text": meta["text"],
            "media": None,
            "media_type": None,
        })

@app.route("/overlay")
def overlay():
    return render_template("overlay.html")

@app.route("/push", methods=["POST"])
def push():
    data = request.json
    job_id = str(uuid.uuid4())
    meta = {
        "username": data.get("username", ""),
        "avatar": data.get("avatar", ""),
        "text": data.get("text", ""),
    }

    # Récupérer hide_user s'il existe
    hide_user = data.get("hide_user", False)
    meta["hide_user"] = hide_user
    
    if data.get("media"):
        t = threading.Thread(
            target=download_and_convert,
            args=(data["media"], job_id, data.get("media_type", "image"), meta)
        )
        t.daemon = True
        t.start()
    else:
        socketio.emit("show_overlay", {
            "job_id": job_id,
            "username": meta["username"],
            "avatar": meta["avatar"],
            "text": meta["text"],
            "hide_user": meta["hide_user"],
            "media": None,
            "media_type": None,
        })

    return jsonify({"status": "ok"})

@app.route("/stop", methods=["POST"])
def stop():
    socketio.emit("hide_overlay")
    return jsonify({"status": "ok"})

@app.route("/media/<filename>")
def serve_media(filename):
    return send_from_directory(MEDIA_DIR, filename)

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, allow_unsafe_werkzeug=True)

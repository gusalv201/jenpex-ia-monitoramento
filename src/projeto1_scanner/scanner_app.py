"""
Projeto 1 - Servidor Web do Scanner de Objetos (Porta 5001)
"""

import os
import sys
import threading
from flask import Flask, render_template, Response, jsonify

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scanner_detector import ObjectScannerDetector

app = Flask(__name__, template_folder="templates")
detector = ObjectScannerDetector(camera_source=0)

camera_thread = threading.Thread(target=detector.start_camera_loop, daemon=True)
camera_thread.start()

@app.route("/")
def index():
    return render_template("scanner.html")

def generate_stream():
    while True:
        frame_bytes = detector.get_jpeg_frame()
        if frame_bytes is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        threading.Event().wait(0.04)

@app.route("/video_feed")
def video_feed():
    return Response(generate_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/api/scanner_status")
def api_scanner_status():
    return jsonify(detector.get_status())

if __name__ == "__main__":
    print("=" * 65)
    print("🚀 PROJETO 1: SCANNER INTELIGENTE DE OBJETOS INICIADO!")
    print("🌐 Interface do Scanner: http://localhost:5001")
    print("=" * 65)
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)

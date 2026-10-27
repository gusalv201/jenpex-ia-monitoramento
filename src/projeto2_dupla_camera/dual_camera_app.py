"""
Projeto 2 - Servidor Flask para o Sistema de Dupla Câmera (Porta 5002)
"""

import os
import sys
import threading
from flask import Flask, render_template, Response, jsonify

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dual_detector import DualCameraSystem

app = Flask(__name__, template_folder="templates")

# Inicializa sistema dual: cam1_source=0 (ou vídeo), cam2_source=1
dual_system = DualCameraSystem(cam1_source=0, cam2_source=1, capacity=30)
dual_system.run_camera_threads()

@app.route("/")
def index():
    return render_template("dual_monitor.html")

def generate_cam1_stream():
    while True:
        frame_bytes = dual_system.get_jpeg_cam1()
        if frame_bytes is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        threading.Event().wait(0.04)

def generate_cam2_stream():
    while True:
        frame_bytes = dual_system.get_jpeg_cam2()
        if frame_bytes is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        threading.Event().wait(0.04)

@app.route("/cam1_feed")
def cam1_feed():
    return Response(generate_cam1_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/cam2_feed")
def cam2_feed():
    return Response(generate_cam2_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/api/dual_status")
def api_dual_status():
    return jsonify(dual_system.get_status())

if __name__ == "__main__":
    print("=" * 65)
    print("🚀 PROJETO 2: SISTEMA DE DUPLA CÂMERA INICIADO!")
    print("🌐 Monitor de Entrada: http://localhost:5002")
    print("=" * 65)
    app.run(host="0.0.0.0", port=5002, debug=False, threaded=True)

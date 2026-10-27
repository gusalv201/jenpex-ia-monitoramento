"""
JENPEX Vision - Servidor Flask para Monitor de Ocupação em Tempo Real
"""

import os
import sys
import threading
from flask import Flask, render_template, Response, jsonify, request

# Adiciona o diretório atual ao sys.path para garantir imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from detector import PeopleCounterDetector

app = Flask(__name__, template_folder="templates", static_folder="static")

# Instância global do detector
detector = PeopleCounterDetector(config_path="config.json")

# Inicia a captura em thread separada
camera_thread = threading.Thread(target=detector.start_camera_loop, daemon=True)
camera_thread.start()

@app.route("/")
def index():
    return render_template("index.html")

def generate_video_stream():
    """Gera stream MJPEG para exibição no navegador."""
    while True:
        frame_bytes = detector.get_jpeg_frame()
        if frame_bytes is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        threading.Event().wait(0.04) # ~25 FPS

@app.route("/video_feed")
def video_feed():
    return Response(generate_video_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/api/status")
def api_status():
    """Retorna os dados em tempo real para o painel."""
    return jsonify(detector.get_status())

@app.route("/api/reset", methods=["POST"])
def api_reset():
    """Reseta a contagem da sala."""
    detector.reset_counts()
    return jsonify({"success": True, "message": "Contagem resetada com sucesso."})

@app.route("/api/adjust", methods=["POST"])
def api_adjust():
    """Ajuste manual da contagem (+1 ou -1)."""
    data = request.get_json() or {}
    delta = int(data.get("delta", 0))
    if delta != 0:
        detector.manual_adjust(delta)
    return jsonify(detector.get_status())

@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    """Obtém ou atualiza configurações em tempo real."""
    if request.method == "POST":
        data = request.get_json() or {}
        for key, value in data.items():
            if key in detector.config:
                detector.config[key] = value
        detector.save_config()
        return jsonify({"success": True, "config": detector.config})
    return jsonify(detector.config)

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 JENPEX Vision - Monitor de Ocupação Iniciado!")
    print("🌐 Painel do Monitor: http://localhost:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)

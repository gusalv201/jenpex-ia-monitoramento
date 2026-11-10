"""
Projeto 2 - Servidor Flask para o Monitor de Ocupação com Visão Panorâmica
IFMT - JENPEX (Porta 5002)
"""

import os
import sys
import threading
from flask import Flask, render_template, Response, jsonify, request, send_file
import io

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dual_detector import DualCameraSystem

app = Flask(__name__, template_folder="templates", static_folder="static")

# Inicializa o sistema de monitoramento panorâmico
dual_system = DualCameraSystem(cam1_source=0, cam2_source=1, capacity=25)
dual_system.run_camera_threads()

@app.route("/")
def index():
    return render_template("dual_monitor.html")

def generate_cam1_stream():
    """Gera o stream contínuo de vídeo MJPEG em alta taxa de quadros."""
    while True:
        frame_bytes = dual_system.get_jpeg_cam1()
        if frame_bytes is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        threading.Event().wait(0.04)

@app.route("/cam1_feed")
def cam1_feed():
    return Response(generate_cam1_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/video_feed")
def video_feed():
    """Alias para /cam1_feed."""
    return Response(generate_cam1_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/cam2_feed")
def cam2_feed():
    """Mantido para compatibilidade com outros módulos."""
    return Response(generate_cam1_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/api/record_snapshot")
def api_record_snapshot():
    """
    Retorna a fotografia do momento em que houve mais pessoas na sala (Recorde).
    """
    img_bytes = dual_system.get_peak_jpeg()
    if img_bytes is not None:
        response = Response(img_bytes, mimetype='image/jpeg')
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        return response

    # Se ainda não houver foto salva, retorna imagem de placeholder em SVG
    svg_placeholder = """<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480" viewBox="0 0 640 480">
      <rect width="100%" height="100%" fill="#0d1522"/>
      <circle cx="320" cy="210" r="48" fill="#182538" stroke="#00f0ff" stroke-width="2" stroke-dasharray="6 4"/>
      <text x="320" y="218" font-family="sans-serif" font-size="28" fill="#00f0ff" text-anchor="middle">🏆</text>
      <text x="320" y="290" font-family="sans-serif" font-size="16" font-weight="bold" fill="#8899aa" text-anchor="middle">AGUARDANDO PRIMEIRO RECORDE</text>
      <text x="320" y="315" font-family="sans-serif" font-size="13" fill="#556677" text-anchor="middle">A foto do pico maximo sera exibida aqui automaticamente</text>
    </svg>"""
    return Response(svg_placeholder, mimetype='image/svg+xml')

@app.route("/api/dual_status")
def api_dual_status():
    """Retorna os dados em tempo real para o painel."""
    return jsonify(dual_system.get_status())

@app.route("/api/status")
def api_status():
    """Alias para /api/dual_status."""
    return jsonify(dual_system.get_status())

@app.route("/api/reset_record", methods=["POST"])
def api_reset_record():
    """Zera o recorde de pessoas para iniciar uma nova medição."""
    dual_system.reset_peak_record()
    return jsonify({"success": True, "message": "Recorde zerado com sucesso!"})

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 PROJETO 2 (GRUPO 2) - MONITOR DE OCUPAÇÃO COM VISÃO PANORÂMICA")
    print("🏆 Detecção em Tempo Real + Registro Automático de Recorde")
    print("🌐 Acesse no Navegador: http://localhost:5002")
    print("=" * 70)
    app.run(host="0.0.0.0", port=5002, debug=False, threaded=True)

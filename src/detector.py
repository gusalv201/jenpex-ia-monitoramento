"""
JENPEX Vision - Módulo de Detecção e Rastreamento de Pessoas
Utiliza YOLOv8 (Ultralytics) com rastreamento persistente de IDs e detecção de cruzamento de linha virtual.
Possui fallback automático para OpenCV HOG caso necessário.
"""

import cv2
import numpy as np
import time
import json
import os
import threading
from datetime import datetime

class PeopleCounterDetector:
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.load_config()

        self.in_count = 0
        self.out_count = 0
        self.current_count = 0
        self.events_log = []
        self.max_events = 20

        # Histórico de rastreamento de IDs: {track_id: [(x, y), (x, y), ...]}
        self.track_history = {}
        # Status de contagem por ID para evitar contagens duplicadas: {track_id: 'counted_in' | 'counted_out' | None}
        self.counted_ids = {}

        self.fps = 0.0
        self._frame_count = 0
        self._fps_start_time = time.time()

        self.lock = threading.Lock()
        self.latest_frame = None
        self.is_running = False

        # Inicializa o modelo de IA
        self.init_model()

    def load_config(self):
        default_config = {
            "project_name": "JENPEX Vision - Monitor de Ocupação",
            "room_name": "Sala de Exposição JENPEX",
            "room_capacity": 25,
            "warning_threshold_pct": 80,
            "camera_source": 0,
            "camera_width": 640,
            "camera_height": 480,
            "model_type": "auto",
            "confidence_threshold": 0.45,
            "line_orientation": "horizontal",
            "line_position_pct": 0.50,
            "line_buffer_pixels": 25,
            "enable_audio_alerts": True,
            "alert_sound": True,
            "debug_view": True
        }

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            except Exception as e:
                print(f"[AVISO] Erro ao carregar config.json: {e}. Usando configuração padrão.")
                self.config = default_config
        else:
            self.config = default_config
            self.save_config()

    def save_config(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ERRO] Falha ao salvar config.json: {e}")

    def init_model(self):
        self.use_yolo = False
        try:
            from ultralytics import YOLO
            print("[INFO] Carregando modelo YOLOv8n (Nano) para detecção de pessoas...")
            self.model = YOLO("yolov8n.pt")
            self.use_yolo = True
            print("[INFO] YOLOv8n inicializado com sucesso!")
        except Exception as e:
            print(f"[AVISO] Não foi possível carregar YOLOv8 ({e}). Ativando fallback OpenCV HOG.")
            self.hog = cv2.HOGDescriptor()
            self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            self.use_yolo = False

    def reset_counts(self):
        with self.lock:
            self.in_count = 0
            self.out_count = 0
            self.current_count = 0
            self.track_history.clear()
            self.counted_ids.clear()
            self.events_log.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "type": "RESET",
                "message": "Contagem zerada manualmente",
                "current": 0
            })

    def manual_adjust(self, delta):
        with self.lock:
            self.current_count = max(0, self.current_count + delta)
            if delta > 0:
                self.in_count += delta
                tipo = "MANUAL_IN"
                msg = f"+{delta} pessoa(s) adicionada(s) manualmente"
            else:
                self.out_count += abs(delta)
                tipo = "MANUAL_OUT"
                msg = f"-{abs(delta)} pessoa(s) removida(s) manualmente"

            self.events_log.insert(0, {
                "time": datetime.now().strftime("%H:%M:%S"),
                "type": tipo,
                "message": msg,
                "current": self.current_count
            })
            if len(self.events_log) > self.max_events:
                self.events_log.pop()

    def process_frame(self, frame):
        h, w, _ = frame.shape
        line_pct = self.config.get("line_position_pct", 0.50)
        buffer_px = self.config.get("line_buffer_pixels", 25)
        orientation = self.config.get("line_orientation", "horizontal")

        # Posição da linha de contagem
        if orientation == "horizontal":
            line_coord = int(h * line_pct)
        else:
            line_coord = int(w * line_pct)

        detected_boxes = []

        if self.use_yolo:
            conf = self.config.get("confidence_threshold", 0.45)
            # Executa rastreamento persistente: classes=[0] filtra apenas 'person'
            results = self.model.track(frame, persist=True, classes=[0], conf=conf, verbose=False)
            if results and len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                for box in boxes:
                    xyxy = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = map(int, xyxy)
                    track_id = int(box.id[0]) if box.id is not None else None
                    confidence = float(box.conf[0])
                    detected_boxes.append((x1, y1, x2, y2, track_id, confidence))
        else:
            # Fallback HOG OpenCV
            rects, weights = self.hog.detectMultiScale(frame, winStride=(4, 4), padding=(8, 8), scale=1.05)
            for i, (x, y, bw, bh) in enumerate(rects):
                detected_boxes.append((x, y, x + bw, y + bh, i + 1, 0.70))

        # Desenhar linha guia
        line_color = (255, 200, 0) # Ciano/Azul claro padrão
        if orientation == "horizontal":
            cv2.line(frame, (0, line_coord), (w, line_coord), line_color, 2)
            # Zona de histerese
            cv2.line(frame, (0, line_coord - buffer_px), (w, line_coord - buffer_px), (80, 80, 80), 1)
            cv2.line(frame, (0, line_coord + buffer_px), (w, line_coord + buffer_px), (80, 80, 80), 1)
            cv2.putText(frame, "ENTRADA [DESCENDO]", (10, line_coord + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.putText(frame, "SAIDA [SUBINDO]", (10, line_coord - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 1)
        else:
            cv2.line(frame, (line_coord, 0), (line_coord, h), line_color, 2)
            cv2.line(frame, (line_coord - buffer_px, 0), (line_coord - buffer_px, h), (80, 80, 80), 1)
            cv2.line(frame, (line_coord + buffer_px, 0), (line_coord + buffer_px, h), (80, 80, 80), 1)

        # Atualiza posições e lógica de contagem
        for (x1, y1, x2, y2, track_id, conf) in detected_boxes:
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            # Desenha Bounding Box e Centróide
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 128), 2)
            cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

            label = f"Pessoa #{track_id} ({conf:.2f})" if track_id is not None else f"Pessoa ({conf:.2f})"
            cv2.putText(frame, label, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

            if track_id is not None:
                if track_id not in self.track_history:
                    self.track_history[track_id] = []
                self.track_history[track_id].append((cx, cy))
                if len(self.track_history[track_id]) > 30:
                    self.track_history[track_id].pop(0)

                # Desenha rastro de movimento
                points = self.track_history[track_id]
                for p_idx in range(1, len(points)):
                    cv2.line(frame, points[p_idx - 1], points[p_idx], (0, 255, 255), 2)

                # Verifica se cruzou a linha
                if len(points) >= 2:
                    prev_c = points[0]
                    curr_c = points[-1]

                    if orientation == "horizontal":
                        prev_pos = prev_c[1]
                        curr_pos = curr_c[1]
                    else:
                        prev_pos = prev_c[0]
                        curr_pos = curr_c[0]

                    # Cruzando de cima para baixo (ENTRADA)
                    if prev_pos < (line_coord - buffer_px) and curr_pos > (line_coord + buffer_px):
                        if self.counted_ids.get(track_id) != "IN":
                            with self.lock:
                                self.in_count += 1
                                self.current_count = max(0, self.in_count - self.out_count)
                                self.counted_ids[track_id] = "IN"
                                self.events_log.insert(0, {
                                    "time": datetime.now().strftime("%H:%M:%S"),
                                    "type": "ENTRADA",
                                    "message": f"Pessoa #{track_id} entrou na sala",
                                    "current": self.current_count
                                })
                                if len(self.events_log) > self.max_events:
                                    self.events_log.pop()
                            # Destaque visual temporário da linha
                            cv2.line(frame, (0, line_coord), (w, line_coord), (0, 255, 0), 4)

                    # Cruzando de baixo para cima (SAÍDA)
                    elif prev_pos > (line_coord + buffer_px) and curr_pos < (line_coord - buffer_px):
                        if self.counted_ids.get(track_id) != "OUT":
                            with self.lock:
                                self.out_count += 1
                                self.current_count = max(0, self.in_count - self.out_count)
                                self.counted_ids[track_id] = "OUT"
                                self.events_log.insert(0, {
                                    "time": datetime.now().strftime("%H:%M:%S"),
                                    "type": "SAIDA",
                                    "message": f"Pessoa #{track_id} saiu da sala",
                                    "current": self.current_count
                                })
                                if len(self.events_log) > self.max_events:
                                    self.events_log.pop()
                            # Destaque visual temporário da linha
                            cv2.line(frame, (0, line_coord), (w, line_coord), (0, 0, 255), 4)

        # Cálculo de FPS
        self._frame_count += 1
        elapsed = time.time() - self._fps_start_time
        if elapsed >= 1.0:
            self.fps = round(self._frame_count / elapsed, 1)
            self._frame_count = 0
            self._fps_start_time = time.time()

        # Overlay de status no próprio vídeo
        cv2.putText(frame, f"FPS: {self.fps} | IA: {'YOLOv8' if self.use_yolo else 'OpenCV HOG'}",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        cv2.putText(frame, f"NA SALA: {self.current_count} (IN: {self.in_count} | OUT: {self.out_count})",
                    (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        return frame

    def get_status(self):
        with self.lock:
            capacity = self.config.get("room_capacity", 25)
            pct = round((self.current_count / capacity * 100), 1) if capacity > 0 else 0

            if self.current_count >= capacity:
                status_label = "SALA LOTADA - AGUARDE"
                status_color = "danger"
            elif pct >= self.config.get("warning_threshold_pct", 80):
                status_label = "ATENÇÃO - QUASE CHEIA"
                status_color = "warning"
            else:
                status_label = "ENTRADA LIVRE"
                status_color = "success"

            return {
                "project_name": self.config.get("project_name", "JENPEX Vision"),
                "room_name": self.config.get("room_name", "Sala de Exposição JENPEX"),
                "current_count": self.current_count,
                "in_count": self.in_count,
                "out_count": self.out_count,
                "room_capacity": capacity,
                "occupancy_pct": min(100, pct),
                "status_label": status_label,
                "status_color": status_color,
                "fps": self.fps,
                "ai_model": "YOLOv8 Nano" if self.use_yolo else "OpenCV HOG",
                "recent_events": self.events_log[:10]
            }

    def start_camera_loop(self):
        """Loop contínuo em background para captura de câmera."""
        source = self.config.get("camera_source", 0)
        # Permite string numérica ou caminho de vídeo
        if isinstance(source, str) and source.isdigit():
            source = int(source)

        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            print(f"[ERRO] Não foi possível abrir a câmera índice/caminho: {source}")
            # Tenta índice 0 alternativo
            if source != 0:
                print("[INFO] Tentando câmera padrão índice 0...")
                cap = cv2.VideoCapture(0)

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.get("camera_width", 640))
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.get("camera_height", 480))

        self.is_running = True
        print("[INFO] Captura de vídeo iniciada.")

        # Fallback para caso não haja nenhuma câmera física conectada
        mock_frame = None

        while self.is_running:
            ret, frame = cap.read()
            if not ret or frame is None:
                # Cria frame simulado para demonstração se a webcam não estiver conectada
                if mock_frame is None:
                    mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(mock_frame, "CONECTE UMA WEBCAM OU VIDEO", (60, 240),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 165, 255), 2)
                    cv2.putText(mock_frame, "JENPEX Vision em Modo Demonstrativo", (80, 280),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
                processed = mock_frame.copy()
                time.sleep(0.05)
            else:
                processed = self.process_frame(frame)

            with self.lock:
                self.latest_frame = processed

        cap.release()
        print("[INFO] Captura de vídeo finalizada.")

    def get_jpeg_frame(self):
        with self.lock:
            if self.latest_frame is None:
                # Imagem preta de espera
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(placeholder, "Aguardando camera...", (180, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                ret, jpeg = cv2.imencode('.jpg', placeholder)
                return jpeg.tobytes() if ret else None

            ret, jpeg = cv2.imencode('.jpg', self.latest_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                return jpeg.tobytes()
            return None

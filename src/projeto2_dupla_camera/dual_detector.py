"""
Projeto 2 - Sistema de Dupla Câmera de Ocupação e Fluxo (YOLOv8)
Câmera 1 (Panorâmica): Contagem de pessoas presentes no salão.
Câmera 2 (Porta): Linha virtual bidirecional (Entrada / Saída).
"""

import cv2
import numpy as np
import time
import json
import os
import threading
from datetime import datetime

class DualCameraSystem:
    def __init__(self, cam1_source=0, cam2_source=1, capacity=30):
        self.cam1_source = cam1_source # Panorâmica
        self.cam2_source = cam2_source # Porta
        self.room_capacity = capacity

        self.lock = threading.Lock()
        self.is_running = False

        # Estado da Câmera 1 (Panorâmica)
        self.frame_panoramic = None
        self.count_panoramic = 0
        self.fps_cam1 = 0.0

        # Estado da Câmera 2 (Porta - Fluxo)
        self.frame_door = None
        self.in_count = 0
        self.out_count = 0
        self.count_gate = 0
        self.fps_cam2 = 0.0
        self.track_history = {}
        self.counted_ids = {}

        # Linha virtual de corte na porta (50% da altura da câmera 2)
        self.line_pct = 0.50
        self.buffer_px = 25

        # Log de eventos
        self.events_log = []

        # Modelo YOLOv8
        self.init_model()

    def init_model(self):
        from ultralytics import YOLO
        print("[PROJETO 2] Carregando modelo YOLOv8n para o Sistema de Dupla Câmera...")
        self.model = YOLO("yolov8n.pt")
        print("[PROJETO 2] Sistema de Dupla Câmera pronto!")

    def process_panoramic(self, frame):
        """Processa câmera panorâmica: conta quantas pessoas estão no salão."""
        results = self.model.predict(frame, classes=[0], conf=0.40, verbose=False)
        detected_count = 0

        if results and len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            detected_count = len(boxes)
            for box in boxes:
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = map(int, xyxy)
                conf = float(box.conf[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 128), 2)
                cv2.putText(frame, f"Pessoa ({conf*100:.0f}%)", (x1, max(20, y1 - 5)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 128), 1)

        cv2.putText(frame, f"CAM 1 [PANORAMICA] - PRESENTES NO SALAO: {detected_count}",
                    (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        return frame, detected_count

    def process_door(self, frame):
        """Processa câmera da porta com linha virtual de entrada e saída."""
        h, w, _ = frame.shape
        line_y = int(h * self.line_pct)

        results = self.model.track(frame, persist=True, classes=[0], conf=0.45, verbose=False)

        # Desenha a linha de corte
        cv2.line(frame, (0, line_y), (w, line_y), (255, 200, 0), 2)
        cv2.putText(frame, "ENTRADA [DESCENDO]", (10, line_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
        cv2.putText(frame, "SAIDA [SUBINDO]", (10, line_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 140, 255), 1)

        if results and len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for box in boxes:
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = map(int, xyxy)
                track_id = int(box.id[0]) if box.id is not None else None
                conf = float(box.conf[0])

                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 200, 255), 2)
                cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)

                if track_id is not None:
                    if track_id not in self.track_history:
                        self.track_history[track_id] = []
                    self.track_history[track_id].append((cx, cy))
                    if len(self.track_history[track_id]) > 25:
                        self.track_history[track_id].pop(0)

                    points = self.track_history[track_id]
                    if len(points) >= 2:
                        prev_y = points[0][1]
                        curr_y = points[-1][1]

                        # Entrando (cima para baixo)
                        if prev_y < (line_y - self.buffer_px) and curr_y > (line_y + self.buffer_px):
                            if self.counted_ids.get(track_id) != "IN":
                                with self.lock:
                                    self.in_count += 1
                                    self.count_gate = max(0, self.in_count - self.out_count)
                                    self.counted_ids[track_id] = "IN"
                                    self.events_log.insert(0, {
                                        "time": datetime.now().strftime("%H:%M:%S"),
                                        "type": "ENTRADA",
                                        "msg": f"Pessoa #{track_id} entrou pela porta"
                                    })
                                cv2.line(frame, (0, line_y), (w, line_y), (0, 255, 0), 4)

                        # Saindo (baixo para cima)
                        elif prev_y > (line_y + self.buffer_px) and curr_y < (line_y - self.buffer_px):
                            if self.counted_ids.get(track_id) != "OUT":
                                with self.lock:
                                    self.out_count += 1
                                    self.count_gate = max(0, self.in_count - self.out_count)
                                    self.counted_ids[track_id] = "OUT"
                                    self.events_log.insert(0, {
                                        "time": datetime.now().strftime("%H:%M:%S"),
                                        "type": "SAIDA",
                                        "msg": f"Pessoa #{track_id} saiu pela porta"
                                    })
                                cv2.line(frame, (0, line_y), (w, line_y), (0, 0, 255), 4)

        cv2.putText(frame, f"CAM 2 [PORTA] - IN: {self.in_count} | OUT: {self.out_count} (SALDO: {self.count_gate})",
                    (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2)

        return frame

    def run_camera_threads(self):
        """Inicia os loops das 2 câmeras em threads independentes."""
        t1 = threading.Thread(target=self._cam1_loop, daemon=True)
        t2 = threading.Thread(target=self._cam2_loop, daemon=True)
        self.is_running = True
        t1.start()
        t2.start()

    def _cam1_loop(self):
        """Loop da Câmera 1 (Panorâmica)."""
        cap1 = cv2.VideoCapture(self.cam1_source)
        if not cap1.isOpened():
            print(f"[DUAL CAM] Câmera 1 ({self.cam1_source}) não encontrada. Usando canal padrão 0...")
            cap1 = cv2.VideoCapture(0)

        while self.is_running:
            ret, frame = cap1.read()
            if not ret or frame is None:
                # Simulação para caso de apenas 1 câmera física estar conectada
                mock = np.zeros((360, 480, 3), dtype=np.uint8)
                cv2.putText(mock, "CAMERA 1: PANORAMICA (SALAO)", (30, 160),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                cv2.putText(mock, "Conecte a camera interna do teto", (50, 200),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
                with self.lock:
                    self.frame_panoramic = mock
                time.sleep(0.05)
                continue

            processed, p_count = self.process_panoramic(frame)
            with self.lock:
                self.frame_panoramic = processed
                self.count_panoramic = p_count

        cap1.release()

    def _cam2_loop(self):
        """Loop da Câmera 2 (Porta com Linha)."""
        cap2 = cv2.VideoCapture(self.cam2_source)
        if not cap2.isOpened():
            # Se a segunda câmera não existir, usa a primeira ou mock
            print(f"[DUAL CAM] Câmera 2 ({self.cam2_source}) não encontrada. Aguardando conexão...")
            cap2 = cv2.VideoCapture(0)

        while self.is_running:
            ret, frame = cap2.read()
            if not ret or frame is None:
                mock = np.zeros((360, 480, 3), dtype=np.uint8)
                cv2.putText(mock, "CAMERA 2: PORTA (FLUXO)", (50, 160),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
                cv2.putText(mock, "Conecte a webcam da portaria", (60, 200),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
                with self.lock:
                    self.frame_door = mock
                time.sleep(0.05)
                continue

            processed = self.process_door(frame)
            with self.lock:
                self.frame_door = processed

        cap2.release()

    def get_jpeg_cam1(self):
        with self.lock:
            if self.frame_panoramic is None: return None
            ret, jpeg = cv2.imencode('.jpg', self.frame_panoramic, [cv2.IMWRITE_JPEG_QUALITY, 75])
            return jpeg.tobytes() if ret else None

    def get_jpeg_cam2(self):
        with self.lock:
            if self.frame_door is None: return None
            ret, jpeg = cv2.imencode('.jpg', self.frame_door, [cv2.IMWRITE_JPEG_QUALITY, 75])
            return jpeg.tobytes() if ret else None

    def get_status(self):
        with self.lock:
            # Ocupação considerada para a porta: usa o maior entre a panorâmica e a catraca
            # para garantir máxima segurança contra superlotação!
            audited_occupancy = max(self.count_panoramic, self.count_gate)
            diff = abs(self.count_panoramic - self.count_gate)

            pct = round((audited_occupancy / self.room_capacity * 100), 1) if self.room_capacity > 0 else 0

            if audited_occupancy >= self.room_capacity:
                status_label = "SALA LOTADA - AGUARDE"
                status_color = "danger"
            elif pct >= 80:
                status_label = "ATENÇÃO - QUASE CHEIA"
                status_color = "warning"
            else:
                status_label = "ENTRADA PERMITIDA"
                status_color = "success"

            return {
                "count_panoramic": self.count_panoramic,
                "count_gate": self.count_gate,
                "in_count": self.in_count,
                "out_count": self.out_count,
                "audited_occupancy": audited_occupancy,
                "room_capacity": self.room_capacity,
                "occupancy_pct": min(100, pct),
                "discrepancy": diff,
                "audit_status": "CONVERGÊNCIA PERFEITA" if diff == 0 else f"DIVERGÊNCIA ({diff})",
                "status_label": status_label,
                "status_color": status_color,
                "events": self.events_log[:10]
            }

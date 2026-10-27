"""
Projeto 1 - Scanner de Objetos em Região de Interesse (ROI) com IA Local (YOLOv8)
Detecta objetos posicionados dentro de um quadrado imaginário e traduz para Português.
"""

import cv2
import numpy as np
import time
import json
import os
import threading
from datetime import datetime

# Dicionário de tradução dos 80 objetos do dataset COCO para Português com Categorias
COCO_PTBR = {
    "person": ("Pessoa / Mão", "Humano"),
    "bicycle": ("Bicicleta", "Veículo"),
    "car": ("Carro / Automóvel", "Veículo"),
    "motorcycle": ("Motocicleta", "Veículo"),
    "airplane": ("Avião", "Veículo"),
    "bus": ("Ônibus", "Veículo"),
    "train": ("Trem", "Veículo"),
    "truck": ("Caminhão", "Veículo"),
    "boat": ("Barco", "Veículo"),
    "traffic light": ("Semáforo", "Trânsito"),
    "fire hydrant": ("Hidrante", "Urbano"),
    "stop sign": ("Placa de Pare", "Trânsito"),
    "parking meter": ("Parquímetro", "Urbano"),
    "bench": ("Banco de Praça", "Mobiliário"),
    "bird": ("Pássaro", "Animal"),
    "cat": ("Gato", "Animal"),
    "dog": ("Cachorro", "Animal"),
    "horse": ("Cavalo", "Animal"),
    "sheep": ("Ovelha", "Animal"),
    "cow": ("Vaca", "Animal"),
    "elephant": ("Elefante", "Animal"),
    "bear": ("Urso", "Animal"),
    "zebra": ("Zebra", "Animal"),
    "giraffe": ("Girafa", "Animal"),
    "backpack": ("Mochila Escolar", "Acessório"),
    "umbrella": ("Guarda-chuva", "Acessório"),
    "handbag": ("Bolsa de Mão", "Acessório"),
    "tie": ("Gravata", "Vestuário"),
    "suitcase": ("Mala de Viagem", "Acessório"),
    "frisbee": ("Frisbee", "Brinquedo"),
    "skis": ("Esquis", "Esporte"),
    "snowboard": ("Prancha de Snowboard", "Esporte"),
    "sports ball": ("Bola de Esportes", "Esporte"),
    "kite": ("Pipa", "Brinquedo"),
    "baseball bat": ("Taco de Beisebol", "Esporte"),
    "baseball glove": ("Luva de Beisebol", "Esporte"),
    "skateboard": ("Skate", "Esporte"),
    "surfboard": ("Prancha de Surfe", "Esporte"),
    "tennis racket": ("Raquete de Tênis", "Esporte"),
    "bottle": ("Garrafa d'Água / Bebida", "Utensílio"),
    "wine glass": ("Taça de Vidro", "Louça"),
    "cup": ("Caneca / Copo", "Utensílio"),
    "fork": ("Garfo", "Talher"),
    "knife": ("Faca", "Talher"),
    "spoon": ("Colher", "Talher"),
    "bowl": ("Tigela / Pote", "Louça"),
    "banana": ("Banana", "Alimento"),
    "apple": ("Maçã", "Alimento"),
    "sandwich": ("Sanduíche", "Alimento"),
    "orange": ("Laranja", "Alimento"),
    "broccoli": ("Brócolis", "Alimento"),
    "carrot": ("Cenoura", "Alimento"),
    "hot dog": ("Cachorro-quente", "Alimento"),
    "pizza": ("Pizza", "Alimento"),
    "donut": ("Donut", "Alimento"),
    "cake": ("Bolo", "Alimento"),
    "chair": ("Cadeira", "Mobiliário"),
    "couch": ("Sofá", "Mobiliário"),
    "potted plant": ("Vaso de Planta", "Decoração"),
    "bed": ("Cama", "Mobiliário"),
    "dining table": ("Mesa", "Mobiliário"),
    "toilet": ("Vaso Sanitário", "Sanitário"),
    "tv": ("Televisão / Monitor", "Eletrônico"),
    "laptop": ("Notebook / Laptop", "Informática"),
    "mouse": ("Mouse de Computador", "Informática"),
    "remote": ("Controle Remoto", "Eletrônico"),
    "keyboard": ("Teclado de Computador", "Informática"),
    "cell phone": ("Celular / Smartphone", "Eletrônico"),
    "microwave": ("Micro-ondas", "Eletrodoméstico"),
    "oven": ("Forno", "Eletrodoméstico"),
    "toaster": ("Torradeira", "Eletrodoméstico"),
    "sink": ("Pia", "Sanitário"),
    "refrigerator": ("Geladeira", "Eletrodoméstico"),
    "book": ("Livro / Caderno", "Papelaria"),
    "clock": ("Relógio", "Acessório"),
    "vase": ("Vaso", "Decoração"),
    "scissors": ("Tesoura Escolar", "Ferramenta"),
    "teddy bear": ("Urso de Pelúcia", "Brinquedo"),
    "hair drier": ("Secador de Cabelo", "Aparelho"),
    "toothbrush": ("Escova de Dente", "Higiene")
}

class ObjectScannerDetector:
    def __init__(self, camera_source=0):
        self.camera_source = camera_source
        self.lock = threading.Lock()
        self.latest_frame = None
        self.is_running = False

        # Configurações da Região de Interesse (ROI - Quadrado Central)
        self.roi_margin_x = 0.25 # 25% de margem em cada lado horizontal
        self.roi_margin_y = 0.20 # 20% de margem em cada lado vertical
        self.confidence_threshold = 0.40

        # Estado do objeto detectado no quadrado
        self.current_object = None
        self.scan_history = []
        self.fps = 0.0
        self._frame_count = 0
        self._fps_start_time = time.time()

        # Carrega modelo YOLOv8
        self.init_model()

    def init_model(self):
        from ultralytics import YOLO
        print("[PROJETO 1] Carregando YOLOv8n para o Scanner de Objetos...")
        self.model = YOLO("yolov8n.pt")
        print("[PROJETO 1] Scanner pronto!")

    def process_frame(self, frame):
        # Modo Espelho Interativo: espelha horizontalmente para a pessoa se ver naturalmente
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Coordenadas do "Quadrado Imaginário" no software (Mira Cibernética Flutuante)
        # Posicionado para que a pessoa se veja ao lado ou levante o objeto na área de escaneamento
        roi_x1 = int(w * self.roi_margin_x)
        roi_y1 = int(h * self.roi_margin_y)
        roi_x2 = int(w * (1.0 - self.roi_margin_x))
        roi_y2 = int(h * (1.0 - self.roi_margin_y))

        # Executa inferência YOLO em todo o frame
        results = self.model.predict(frame, conf=self.confidence_threshold, verbose=False)

        best_object_in_roi = None
        best_conf = 0.0

        if results and len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for box in boxes:
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = map(int, xyxy)
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                class_name = self.model.names.get(cls_id, "unknown")

                # Centróide do objeto detectado
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)

                # Verifica se o centróide está dentro do quadrado imaginário no software
                inside_roi = (roi_x1 <= cx <= roi_x2) and (roi_y1 <= cy <= roi_y2)

                if inside_roi:
                    # Ignora a detecção da própria pessoa/corpo para focar no objeto segurado!
                    if class_name == "person":
                        continue

                    # Desenha caixa com destaque verde no objeto inspecionado
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)
                    pt_name, category = COCO_PTBR.get(class_name, (class_name.capitalize(), "Geral"))
                    label = f"{pt_name} ({conf*100:.0f}%)"
                    cv2.putText(frame, label, (x1, max(25, y1 - 8)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2)

                    if conf > best_conf:
                        best_conf = conf
                        best_object_in_roi = {
                            "raw_name": class_name,
                            "name_pt": pt_name,
                            "category": category,
                            "confidence": round(conf * 100, 1),
                            "time": datetime.now().strftime("%H:%M:%S")
                        }
                else:
                    # Objetos fora da mira ficam com caixa cinza sutil (exceto pessoa inteira)
                    if class_name != "person":
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (80, 80, 80), 1)

        # Desenhar o "Quadrado Imaginário no Software" estilo mira cibernética (HUD)
        hud_color = (0, 240, 255) if best_object_in_roi else (0, 200, 100)
        thickness = 2
        cv2.rectangle(frame, (roi_x1, roi_y1), (roi_x2, roi_y2), hud_color, thickness)

        # Cantos reforçados no quadrado estilo mira de escaneamento
        corner_len = 30
        # Canto Sup. Esq.
        cv2.line(frame, (roi_x1, roi_y1), (roi_x1 + corner_len, roi_y1), (0, 255, 255), 4)
        cv2.line(frame, (roi_x1, roi_y1), (roi_x1, roi_y1 + corner_len), (0, 255, 255), 4)
        # Canto Sup. Dir.
        cv2.line(frame, (roi_x2, roi_y1), (roi_x2 - corner_len, roi_y1), (0, 255, 255), 4)
        cv2.line(frame, (roi_x2, roi_y1), (roi_x2, roi_y1 + corner_len), (0, 255, 255), 4)
        # Canto Inf. Esq.
        cv2.line(frame, (roi_x1, roi_y2), (roi_x1 + corner_len, roi_y2), (0, 255, 255), 4)
        cv2.line(frame, (roi_x1, roi_y2), (roi_x1, roi_y2 - corner_len), (0, 255, 255), 4)
        # Canto Inf. Dir.
        cv2.line(frame, (roi_x2, roi_y2), (roi_x2 - corner_len, roi_y2), (0, 255, 255), 4)
        cv2.line(frame, (roi_x2, roi_y2), (roi_x2, roi_y2 - corner_len), (0, 255, 255), 4)

        # Mira central sutil (+)
        mid_x = int((roi_x1 + roi_x2) / 2)
        mid_y = int((roi_y1 + roi_y2) / 2)
        cv2.line(frame, (mid_x - 12, mid_y), (mid_x + 12, mid_y), (0, 240, 255), 1)
        cv2.line(frame, (mid_x, mid_y - 12), (mid_x, mid_y + 12), (0, 240, 255), 1)

        # Rótulo superior da mira
        tag_text = "[ QUADRADO IMAGINARIO - SEGURE O OBJETO AQUI ]"
        cv2.putText(frame, tag_text, (roi_x1 + 10, roi_y1 - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 240, 255), 2)

        # Atualiza o estado
        with self.lock:
            self.current_object = best_object_in_roi
            if best_object_in_roi:
                # Evita spam se for o mesmo objeto repetido em sequência
                if not self.scan_history or self.scan_history[0]["name_pt"] != best_object_in_roi["name_pt"]:
                    self.scan_history.insert(0, best_object_in_roi)
                    if len(self.scan_history) > 15:
                        self.scan_history.pop()

        # FPS
        self._frame_count += 1
        elapsed = time.time() - self._fps_start_time
        if elapsed >= 1.0:
            self.fps = round(self._frame_count / elapsed, 1)
            self._frame_count = 0
            self._fps_start_time = time.time()

        cv2.putText(frame, f"Scanner IA - FPS: {self.fps}", (15, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return frame

    def start_camera_loop(self):
        cap = cv2.VideoCapture(self.camera_source)
        if not cap.isOpened():
            print(f"[SCANNER] Câmera {self.camera_source} não encontrada. Tentando câmera padrão 0...")
            cap = cv2.VideoCapture(0)

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.is_running = True

        mock_frame = None

        while self.is_running:
            ret, frame = cap.read()
            if not ret or frame is None:
                if mock_frame is None:
                    mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
                    cv2.putText(mock_frame, "CONECTE A WEBCAM DO SCANNER", (100, 240),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
                processed = mock_frame.copy()
                time.sleep(0.05)
            else:
                processed = self.process_frame(frame)

            with self.lock:
                self.latest_frame = processed

        cap.release()

    def get_jpeg_frame(self):
        with self.lock:
            if self.latest_frame is None:
                placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(placeholder, "Aguardando camera...", (200, 240),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                ret, jpeg = cv2.imencode('.jpg', placeholder)
                return jpeg.tobytes() if ret else None
            ret, jpeg = cv2.imencode('.jpg', self.latest_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            return jpeg.tobytes() if ret else None

    def get_status(self):
        with self.lock:
            return {
                "current_object": self.current_object,
                "history": self.scan_history,
                "fps": self.fps,
                "total_scanned": len(self.scan_history)
            }

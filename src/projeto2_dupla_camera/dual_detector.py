"""
Projeto 2 - Sistema de Monitoramento com Visão Panorâmica e Detecção de Ocupação (YOLOv8)
IFMT - JENPEX

Recursos Principais:
1. Visão Panorâmica em Tempo Real: Câmera cobrindo o salão principal com detecção instantânea de pessoas.
2. Contagem Ao Vivo: Medição instantânea e taxa de ocupação da sala.
3. Registro de Recorde de Pessoas (Pico Histórico):
   - Identifica o momento exato em que houve a maior quantidade de pessoas simultâneas.
   - Captura e armazena automaticamente a fotografia (snapshot) do instante recorde.
   - Registra data, horário e quantidade de pessoas no momento recorde.
"""

import cv2
import numpy as np
import time
import json
import os
import threading
from datetime import datetime

class DualCameraSystem:
    def __init__(self, cam1_source=0, cam2_source=1, capacity=30, config_path="config.json"):
        self.config_path = config_path
        self.cam1_source = cam1_source  # Câmera Panorâmica (Salão)
        self.cam2_source = cam2_source  # Câmera secundária / reservada
        self.room_capacity = capacity

        self.lock = threading.Lock()
        self.is_running = False

        # Estado da Câmera Panorâmica
        self.frame_panoramic = None
        self.count_panoramic = 0
        self.fps_cam1 = 0.0
        self._frame_count = 0
        self._fps_start_time = time.time()

        # Registro de Recorde de Ocupação (Pico Histórico)
        self.peak_count = 0
        self.peak_timestamp = None
        self.peak_image_bytes = None
        self.peak_image_raw = None
        self.is_new_peak = False

        # Diretório para salvar snapshots dos recordes
        self.static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
        os.makedirs(self.static_dir, exist_ok=True)
        self.peak_file_path = os.path.join(self.static_dir, "record_snapshot.jpg")

        # Câmera 2 mantida para compatibilidade (caso desejado)
        self.frame_door = None
        self.in_count = 0
        self.out_count = 0
        self.count_gate = 0
        self.fps_cam2 = 0.0

        # Log de eventos
        self.events_log = []
        self._log_event("Sistema de Monitoramento Panorâmico Inicializado.", "info")

        # Carrega configurações personalizadas se existirem
        self.load_config()

        # Inicializa o modelo de IA YOLOv8
        self.init_model()

    def load_config(self):
        """Carrega configurações do arquivo config.json."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.room_capacity = cfg.get("room_capacity", self.room_capacity)
                    self.cam1_source = cfg.get("camera_source", self.cam1_source)
            except Exception as e:
                print(f"[DUAL DETECTOR] Erro ao carregar config.json: {e}")

    def init_model(self):
        """Inicializa o modelo YOLOv8 para detecção de pessoas."""
        self.use_yolo = False
        try:
            from ultralytics import YOLO
            model_path = "yolov8n.pt"
            if not os.path.exists(model_path):
                # Se não estiver no diretório atual, procura na raiz
                parent_model = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "yolov8n.pt")
                if os.path.exists(parent_model):
                    model_path = parent_model
            print(f"[PROJETO 2] Carregando modelo YOLOv8 ({model_path})...")
            self.model = YOLO(model_path)
            self.use_yolo = True
            print("[PROJETO 2] YOLOv8 carregado com sucesso para a Visão Panorâmica!")
        except Exception as e:
            print(f"[PROJETO 2] Aviso: Falha ao carregar YOLOv8 ({e}). Usando fallback OpenCV HOG.")
            self.hog = cv2.HOGDescriptor()
            self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            self.use_yolo = False

    def _log_event(self, text, event_type="info"):
        """Adiciona um evento ao histórico com timestamp."""
        now_str = datetime.now().strftime("%H:%M:%S")
        self.events_log.insert(0, {
            "time": now_str,
            "text": text,
            "type": event_type
        })
        if len(self.events_log) > 30:
            self.events_log.pop()

    def process_panoramic(self, frame):
        """
        Processa o quadro da visão panorâmica:
        1. Detecta pessoas no salão em tempo real.
        2. Desenha caixas delimitadoras e rótulos tecnológicos.
        3. Compara com o recorde histórico e captura o momento de pico.
        """
        h, w, _ = frame.shape
        detected_count = 0
        boxes_coords = []

        # Detecção de pessoas (Classe 0 = person no COCO dataset)
        if self.use_yolo:
            results = self.model.predict(frame, classes=[0], conf=0.40, verbose=False)
            if results and len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                detected_count = len(boxes)
                for box in boxes:
                    xyxy = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = map(int, xyxy)
                    conf = float(box.conf[0])
                    boxes_coords.append((x1, y1, x2, y2, conf))
        else:
            # Fallback HOG
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            boxes, _ = self.hog.detectMultiScale(gray, winStride=(8, 8), padding=(4, 4), scale=1.05)
            detected_count = len(boxes)
            for (x, y, bw, bh) in boxes:
                boxes_coords.append((x, y, x + bw, y + bh, 0.75))

        # Renderização visual sobre o frame
        display_frame = frame.copy()

        # Desenha caixas de detecção com estilo moderno
        for (x1, y1, x2, y2, conf) in boxes_coords:
            # Caixa retangular com cor ciano
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0, 240, 255), 2)

            # Rótulo com fundo semi-opaco
            label = f"Pessoa {conf*100:.0f}%"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(display_frame, (x1, max(0, y1 - 20)), (x1 + tw + 8, y1), (0, 240, 255), -1)
            cv2.putText(display_frame, label, (x1 + 4, max(14, y1 - 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)

            # Ponto central (centróide)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            cv2.circle(display_frame, (cx, cy), 3, (0, 255, 128), -1)

        # Barra de status superior no vídeo
        overlay = display_frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 42), (10, 15, 25), -1)
        cv2.addWeighted(overlay, 0.75, display_frame, 0.25, 0, display_frame)

        # Indicador AO VIVO
        cv2.circle(display_frame, (20, 21), 6, (0, 0, 255), -1)
        cv2.putText(display_frame, "AO VIVO", (32, 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

        # Título da Câmera
        cv2.putText(display_frame, "VISAO PANORAMICA (SALAO PRINCIPAL)", (120, 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 240, 255), 1, cv2.LINE_AA)

        # Contador no vídeo
        count_text = f"PESSOAS PRESENTES: {detected_count}"
        (cw, _), _ = cv2.getTextSize(count_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
        cv2.putText(display_frame, count_text, (w - cw - 20, 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 128), 2, cv2.LINE_AA)

        # =========================================================================
        # LÓGICA DE RECORDE HISTÓRICO DE OCUPAÇÃO (PICO MÁXIMO DE PESSOAS)
        # =========================================================================
        if detected_count > self.peak_count and detected_count > 0:
            self._update_peak_record(detected_count, display_frame)

        return display_frame, detected_count

    def _update_peak_record(self, new_peak, record_frame):
        """Salva e registra o novo recorde com fotografia e timestamp."""
        now_dt = datetime.now()
        timestamp_str = now_dt.strftime("%d/%m/%Y às %H:%M:%S")

        self.peak_count = new_peak
        self.peak_timestamp = timestamp_str
        self.is_new_peak = True

        # Cria uma cópia com marca d'água oficial do recorde
        snapshot = record_frame.copy()
        sh, sw, _ = snapshot.shape

        # Faixa inferior informativa na foto do recorde
        banner_h = 45
        sub_overlay = snapshot.copy()
        cv2.rectangle(sub_overlay, (0, sh - banner_h), (sw, sh), (0, 20, 40), -1)
        cv2.addWeighted(sub_overlay, 0.85, snapshot, 0.15, 0, snapshot)

        # Borda dourada de destaque
        cv2.rectangle(snapshot, (0, sh - banner_h), (sw, sh), (0, 215, 255), 2)

        watermark_text = f"RECORDE: {new_peak} PESSOAS  |  REGISTRADO EM: {timestamp_str}"
        cv2.putText(snapshot, watermark_text, (15, sh - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 240, 255), 2, cv2.LINE_AA)

        # Salva em memória (JPEG bytes)
        ret, jpeg = cv2.imencode('.jpg', snapshot, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if ret:
            self.peak_image_bytes = jpeg.tobytes()
            self.peak_image_raw = snapshot

        # Salva em arquivo físico
        try:
            cv2.imwrite(self.peak_file_path, snapshot)
        except Exception as e:
            print(f"[DUAL DETECTOR] Erro ao salvar snapshot no disco: {e}")

        # Registra no log de eventos
        self._log_event(f"🏆 NOVO RECORDE: {new_peak} pessoas simultâneas no salão!", "record")
        print(f"[RECORDE] Novo pico registrado: {new_peak} pessoas em {timestamp_str}")

    def reset_peak_record(self):
        """Zera o recorde atual para reiniciar o teste."""
        with self.lock:
            self.peak_count = 0
            self.peak_timestamp = None
            self.peak_image_bytes = None
            self.peak_image_raw = None
            self.is_new_peak = False
            if os.path.exists(self.peak_file_path):
                try:
                    os.remove(self.peak_file_path)
                except Exception:
                    pass
            self._log_event("Recorde de ocupação zerado pelo operador.", "warning")

    def run_camera_threads(self):
        """Inicia os loops de captura de vídeo em threads independentes."""
        self.is_running = True
        t1 = threading.Thread(target=self._cam1_loop, daemon=True)
        t1.start()

    def _create_mock_panoramic_frame(self, t):
        """
        Cria uma visualização simulada ultra-realista quando não há webcam física conectada,
        garantindo que o sistema funcione perfeitamente para apresentação e testes!
        """
        h, w = 480, 640
        mock = np.zeros((h, w, 3), dtype=np.uint8)

        # Gradiente suave de fundo simulando piso e paredes de um auditório/sala
        for y in range(h):
            val = int(30 + (y / h) * 45)
            mock[y, :] = (val - 10, val, val + 10)

        # Linhas de perspectiva (teto, paredes, chão)
        cv2.line(mock, (0, 100), (w // 2, 220), (55, 65, 80), 1)
        cv2.line(mock, (w, 100), (w // 2, 220), (55, 65, 80), 1)
        cv2.line(mock, (w // 2, 220), (w // 2, h), (45, 55, 70), 1)

        # Desenha pessoas simuladas se movendo suavemente
        # Simula entre 3 e 7 pessoas variando com o tempo
        cycle = int(t % 30)
        sim_count = 3 + (cycle % 5)

        for i in range(sim_count):
            base_x = int(120 + (i * 90) + np.sin(t * 0.8 + i) * 35)
            base_y = int(240 + (i % 3) * 60 + np.cos(t * 0.6 + i) * 20)

            # Silhueta de pessoa simulada
            # Cabeça
            cv2.circle(mock, (base_x, base_y - 45), 14, (120, 180, 240), -1)
            # Corpo
            cv2.ellipse(mock, (base_x, base_y), (18, 35), 0, 0, 360, (90, 140, 200), -1)

            # Caixa de detecção simulada (para YOLOv8 ou demonstração)
            x1, y1 = base_x - 22, base_y - 65
            x2, y2 = base_x + 22, base_y + 40
            cv2.rectangle(mock, (x1, y1), (x2, y2), (0, 240, 255), 2)
            cv2.putText(mock, f"Pessoa {85 + (i * 2)}%", (x1, y1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 240, 255), 1)

        # Rodapé com aviso pedagógico
        cv2.putText(mock, "[MODO DEMO/SIMULACAO ATIVO - CONECTE WEBCAM PARA VIDEO REAL]",
                    (30, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 200, 220), 1)

        return mock, sim_count

    def _cam1_loop(self):
        """Loop de captura e processamento da Câmera 1 (Panorâmica)."""
        cap1 = cv2.VideoCapture(self.cam1_source)

        # Se falhar ao abrir no índice configurado, tenta índice 0
        if not cap1.isOpened() and self.cam1_source != 0:
            print(f"[DUAL CAM] Tentando câmera alternativa índice 0...")
            cap1 = cv2.VideoCapture(0)

        is_camera_available = cap1.isOpened()
        if not is_camera_available:
            print("[DUAL CAM] Nenhuma webcam física detectada. Ativando Gerador de Visão Panorâmica Simulada...")

        while self.is_running:
            start_t = time.time()
            if is_camera_available:
                ret, frame = cap1.read()
                if not ret or frame is None:
                    # Em caso de desconexão momentânea, gera frame de standby
                    mock, p_count = self._create_mock_panoramic_frame(time.time())
                    with self.lock:
                        self.frame_panoramic = mock
                        self.count_panoramic = p_count
                    time.sleep(0.04)
                    continue

                processed, p_count = self.process_panoramic(frame)
                with self.lock:
                    self.frame_panoramic = processed
                    self.count_panoramic = p_count
            else:
                # Sem webcam: simulação interativa com contagem dinâmica
                mock, p_count = self._create_mock_panoramic_frame(time.time())

                # Adiciona barra de status e verifica recorde
                overlay = mock.copy()
                w = mock.shape[1]
                cv2.rectangle(overlay, (0, 0), (w, 42), (10, 15, 25), -1)
                cv2.addWeighted(overlay, 0.75, mock, 0.25, 0, mock)

                cv2.circle(mock, (20, 21), 6, (0, 200, 255), -1)
                cv2.putText(mock, "SIMULADOR PANORAMICO", (34, 26),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

                count_text = f"PESSOAS NA SALA: {p_count}"
                (cw, _), _ = cv2.getTextSize(count_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
                cv2.putText(mock, count_text, (w - cw - 20, 26),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 128), 2, cv2.LINE_AA)

                if p_count > self.peak_count and p_count > 0:
                    self._update_peak_record(p_count, mock)

                with self.lock:
                    self.frame_panoramic = mock
                    self.count_panoramic = p_count

                time.sleep(0.04)

            # Cálculo de FPS
            self._frame_count += 1
            elapsed = time.time() - self._fps_start_time
            if elapsed >= 1.0:
                self.fps_cam1 = round(self._frame_count / elapsed, 1)
                self._frame_count = 0
                self._fps_start_time = time.time()

        if cap1.isOpened():
            cap1.release()

    def get_jpeg_cam1(self):
        """Retorna os bytes em formato JPEG para transmissão MJPEG."""
        with self.lock:
            if self.frame_panoramic is None:
                return None
            ret, jpeg = cv2.imencode('.jpg', self.frame_panoramic, [cv2.IMWRITE_JPEG_QUALITY, 80])
            return jpeg.tobytes() if ret else None

    def get_jpeg_cam2(self):
        """Retorna stream da câmera 2 ou espelho da câmera 1."""
        return self.get_jpeg_cam1()

    def get_peak_jpeg(self):
        """Retorna os bytes da fotografia do momento recorde."""
        with self.lock:
            if self.peak_image_bytes is not None:
                return self.peak_image_bytes
            # Se já houver um arquivo salvo em disco de sessões anteriores
            if os.path.exists(self.peak_file_path):
                try:
                    with open(self.peak_file_path, "rb") as f:
                        self.peak_image_bytes = f.read()
                        return self.peak_image_bytes
                except Exception:
                    pass
            return None

    def get_status(self):
        """
        Retorna o dicionário de status em tempo real consumido pelo front-end:
        - Ocupação ao vivo no salão
        - Momento recorde (foto, horário, data, contagem)
        - Alertas e capacidade
        """
        with self.lock:
            current_occ = self.count_panoramic
            pct = round((current_occ / self.room_capacity * 100), 1) if self.room_capacity > 0 else 0

            if current_occ >= self.room_capacity:
                status_label = "SALA LOTADA - AGUARDE"
                status_color = "danger"
            elif pct >= 80:
                status_label = "ATENÇÃO - QUASE CHEIA"
                status_color = "warning"
            else:
                status_label = "ENTRADA PERMITIDA"
                status_color = "success"

            has_peak = self.peak_count > 0

            return {
                "count_panoramic": current_occ,
                "audited_occupancy": current_occ,
                "room_capacity": self.room_capacity,
                "occupancy_pct": min(100, pct),
                "fps": self.fps_cam1,
                "status_label": status_label,
                "status_color": status_color,
                "is_new_peak": self.is_new_peak,
                "peak_record": {
                    "count": self.peak_count,
                    "timestamp": self.peak_timestamp or "Nenhum recorde registrado ainda",
                    "has_record": has_peak,
                    "image_url": "/api/record_snapshot" if has_peak else None
                },
                "events": self.events_log[:8]
            }

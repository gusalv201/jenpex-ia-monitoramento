"""
Projeto 2 - Sistema de Monitoramento com Visão Panorâmica e Detecção de Ocupação (YOLOv8)
IFMT - JENPEX 2026 (Grupo 2)

Recursos Principais:
1. Visão Panorâmica Única em Tempo Real: Câmera cobrindo o salão principal com detecção instantânea de pessoas.
2. Contagem Ao Vivo com Estabilização: Mediana dos últimos 5 frames para evitar oscilações falsas.
3. Registro de Recorde de Pessoas (Pico Histórico):
   - Identifica o momento exato em que houve a maior quantidade de pessoas simultâneas.
   - Captura e armazena automaticamente a fotografia (snapshot com caixas delimitadoras) do instante recorde.
   - Registra data, horário e quantidade de pessoas no momento recorde.
   - Persistência permanente em disco (record_data.json e record_snapshot.jpg).
4. Suporte Robusto a Webcams Físicas (Microsoft Media Foundation / DirectShow) e Fallback Simulado.
"""

import cv2
import numpy as np
import time
import json
import os
import threading
from datetime import datetime
from collections import deque


class DualCameraSystem:
    def __init__(self, cam1_source=0, cam2_source=1, capacity=25, config_path="config.json"):
        self.config_path = config_path
        self.cam1_source = cam1_source  # Câmera Panorâmica (Salão)
        self.room_capacity = capacity

        self.lock = threading.Lock()
        self.is_running = False

        # Estado da Câmera Panorâmica
        self.frame_panoramic = None
        self.raw_count = 0
        self.count_panoramic = 0
        self.recent_counts = deque(maxlen=5)  # Mediana dos últimos 5 frames
        self.fps_cam1 = 0.0
        self._frame_count = 0
        self._fps_start_time = time.time()
        self.camera_online = False

        # Diretório estático para persistência do recorde
        self.static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
        os.makedirs(self.static_dir, exist_ok=True)
        self.peak_file_path = os.path.join(self.static_dir, "record_snapshot.jpg")
        self.record_json_path = os.path.join(self.static_dir, "record_data.json")

        # Registro de Recorde de Ocupação (Pico Histórico)
        self.peak_count = 0
        self.peak_date = "--/--/----"
        self.peak_time = "--:--:--"
        self.peak_timestamp = "Aguardando primeiro registro"
        self.peak_image_bytes = None
        self.is_new_peak = False

        # Carrega recorde persistente de sessões anteriores
        self.load_persisted_record()

        # Log de eventos
        self.events_log = []
        self._log_event("Sistema de Monitoramento Panorâmico Inicializado.", "info")

        # Carrega configurações personalizadas se existirem
        self.load_config()

        # Inicializa o modelo de IA YOLOv8
        self.init_model()

    def load_persisted_record(self):
        """Carrega o recorde salvo em disco para persistir entre reinicializações."""
        if os.path.exists(self.record_json_path):
            try:
                with open(self.record_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.peak_count = int(data.get("record_count", 0))
                    self.peak_date = data.get("record_date", "--/--/----")
                    self.peak_time = data.get("record_time", "--:--:--")
                    self.peak_timestamp = f"{self.peak_date} às {self.peak_time}"
                    print(f"[RECORDE] Recorde persistente carregado: {self.peak_count} pessoas ({self.peak_timestamp})")
            except Exception as e:
                print(f"[RECORDE] Erro ao carregar record_data.json: {e}")

        # Se já existir a foto salva fisicamente, carrega seus bytes
        if os.path.exists(self.peak_file_path):
            try:
                with open(self.peak_file_path, "rb") as f:
                    self.peak_image_bytes = f.read()
            except Exception:
                pass

    def save_persisted_record(self):
        """Salva os dados do recorde em arquivo JSON e fotografia em JPG."""
        record_data = {
            "record_count": self.peak_count,
            "record_date": self.peak_date,
            "record_time": self.peak_time,
            "record_timestamp": self.peak_timestamp
        }
        try:
            with open(self.record_json_path, "w", encoding="utf-8") as f:
                json.dump(record_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[RECORDE] Erro ao gravar record_data.json: {e}")

    def load_config(self):
        """Carrega configurações do arquivo config.json se existir."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.room_capacity = cfg.get("room_capacity", self.room_capacity)
                    self.cam1_source = cfg.get("camera_source", self.cam1_source)
            except Exception as e:
                print(f"[PROJETO 2] Erro ao carregar config.json: {e}")

    def init_model(self):
        """Inicializa o modelo YOLOv8 para detecção de pessoas."""
        self.use_yolo = False
        try:
            from ultralytics import YOLO
            # Procura o modelo no diretório local ou na raiz do projeto
            model_path = "yolov8n.pt"
            if not os.path.exists(model_path):
                parent_model = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                    "yolov8n.pt"
                )
                if os.path.exists(parent_model):
                    model_path = parent_model

            print(f"[PROJETO 2] Carregando YOLOv8n de {model_path}...")
            self.model = YOLO(model_path)
            self.use_yolo = True
            print("[PROJETO 2] YOLOv8n inicializado com sucesso!")
        except Exception as e:
            print(f"[PROJETO 2] Aviso ao carregar YOLOv8: {e}. Usando fallback HOG.")
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
        if len(self.events_log) > 20:
            self.events_log.pop()

    def process_panoramic(self, frame):
        """
        Processa o frame da câmera panorâmica:
        1. Detecta pessoas no salão em tempo real com YOLOv8n.
        2. Desenha caixas delimitadoras neon numeradas ("Pessoa 1, 2, 3...").
        3. Aplica estabilização da contagem pela mediana móvel dos últimos 5 frames.
        4. Compara com o recorde histórico e captura o momento de pico.
        """
        h, w, _ = frame.shape
        boxes_coords = []

        # Detecção de pessoas (Classe 0 = person no dataset COCO)
        if self.use_yolo:
            results = self.model.predict(frame, classes=[0], conf=0.40, verbose=False)
            if results and len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                for box in boxes:
                    xyxy = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = map(int, xyxy)
                    conf = float(box.conf[0])
                    boxes_coords.append((x1, y1, x2, y2, conf))
        else:
            # Fallback OpenCV HOG
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            boxes, _ = self.hog.detectMultiScale(gray, winStride=(8, 8), padding=(4, 4), scale=1.05)
            for (x, y, bw, bh) in boxes:
                boxes_coords.append((x, y, x + bw, y + bh, 0.75))

        raw_count = len(boxes_coords)
        self.raw_count = raw_count

        # Estabilização: mediana dos últimos 5 frames para evitar oscilações falsas
        self.recent_counts.append(raw_count)
        stable_count = int(np.median(list(self.recent_counts)))

        # Renderização visual sobre o frame
        display_frame = frame.copy()

        # Desenha caixas delimitadoras neon com rótulos numerados
        for idx, (x1, y1, x2, y2, conf) in enumerate(boxes_coords):
            # Caixa Ciano Neon
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (255, 240, 0), 2)

            # Cantos reforçados
            corner_len = min(16, (x2 - x1) // 3)
            cv2.line(display_frame, (x1, y1), (x1 + corner_len, y1), (0, 240, 255), 3)
            cv2.line(display_frame, (x1, y1), (x1, y1 + corner_len), (0, 240, 255), 3)
            cv2.line(display_frame, (x2, y1), (x2 - corner_len, y1), (0, 240, 255), 3)
            cv2.line(display_frame, (x2, y1), (x2, y1 + corner_len), (0, 240, 255), 3)
            cv2.line(display_frame, (x1, y2), (x1 + corner_len, y2), (0, 240, 255), 3)
            cv2.line(display_frame, (x1, y2), (x1, y2 - corner_len), (0, 240, 255), 3)
            cv2.line(display_frame, (x2, y2), (x2 - corner_len, y2), (0, 240, 255), 3)
            cv2.line(display_frame, (x2, y2), (x2, y2 - corner_len), (0, 240, 255), 3)

            # Rótulo exigido: "Pessoa 1, 2, 3..."
            label = f"Pessoa {idx + 1}"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.48, 1)
            cv2.rectangle(display_frame, (x1, max(0, y1 - 22)), (x1 + tw + 10, y1), (255, 240, 0), -1)
            cv2.putText(display_frame, label, (x1 + 5, max(14, y1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.48, (10, 15, 25), 2, cv2.LINE_AA)

        # Barra superior tecnológica no vídeo
        overlay = display_frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 42), (10, 15, 25), -1)
        cv2.addWeighted(overlay, 0.75, display_frame, 0.25, 0, display_frame)

        # Indicador AO VIVO pulsante
        cv2.circle(display_frame, (20, 21), 6, (0, 0, 255), -1)
        cv2.putText(display_frame, "AO VIVO", (34, 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

        # Título da Câmera
        cv2.putText(display_frame, "VISAO PANORAMICA (SALAO)", (125, 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 240, 255), 1, cv2.LINE_AA)

        # Contador de pessoas na barra
        count_text = f"PESSOAS: {stable_count}"
        (cw, _), _ = cv2.getTextSize(count_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
        cv2.putText(display_frame, count_text, (w - cw - 20, 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 128), 2, cv2.LINE_AA)

        # =========================================================================
        # LÓGICA DO RECORDE DE OCUPAÇÃO (PICO MÁXIMO)
        # =========================================================================
        if stable_count > self.peak_count and stable_count > 0:
            self._update_peak_record(stable_count, display_frame)

        return display_frame, stable_count

    def _update_peak_record(self, new_peak, record_frame):
        """Salva e registra o novo recorde com fotografia e timestamp oficial."""
        now_dt = datetime.now()
        date_str = now_dt.strftime("%d/%m/%Y")
        time_str = now_dt.strftime("%H:%M:%S")
        timestamp_str = f"{date_str} às {time_str}"

        self.peak_count = new_peak
        self.peak_date = date_str
        self.peak_time = time_str
        self.peak_timestamp = timestamp_str
        self.is_new_peak = True

        # Cria uma cópia com faixa dourada oficial de recorde
        snapshot = record_frame.copy()
        sh, sw, _ = snapshot.shape
        banner_h = 46

        sub_overlay = snapshot.copy()
        cv2.rectangle(sub_overlay, (0, sh - banner_h), (sw, sh), (0, 20, 40), -1)
        cv2.addWeighted(sub_overlay, 0.85, snapshot, 0.15, 0, snapshot)
        cv2.rectangle(snapshot, (0, sh - banner_h), (sw, sh), (0, 215, 255), 2)

        watermark_text = f"RECORDE: {new_peak} PESSOAS  |  REGISTRADO EM: {timestamp_str}"
        cv2.putText(snapshot, watermark_text, (15, sh - 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 240, 255), 2, cv2.LINE_AA)

        # Salva em memória (JPEG bytes)
        ret, jpeg = cv2.imencode('.jpg', snapshot, [cv2.IMWRITE_JPEG_QUALITY, 88])
        if ret:
            self.peak_image_bytes = jpeg.tobytes()

        # Salva a fotografia fisicamente em disco
        try:
            cv2.imwrite(self.peak_file_path, snapshot)
        except Exception as e:
            print(f"[RECORDE] Erro ao salvar snapshot no disco: {e}")

        # Salva o arquivo JSON com os dados do recorde
        self.save_persisted_record()

        self._log_event(f"🏆 NOVO RECORDE: {new_peak} pessoas simultâneas no salão!", "record")
        print(f"[RECORDE] 🏆 NOVO RECORDE: {new_peak} pessoas registradas em {timestamp_str}")

    def reset_peak_record(self):
        """Zera o recorde atual e remove os arquivos gravados."""
        with self.lock:
            self.peak_count = 0
            self.peak_date = "--/--/----"
            self.peak_time = "--:--:--"
            self.peak_timestamp = "Aguardando primeiro registro"
            self.peak_image_bytes = None
            self.is_new_peak = False

            if os.path.exists(self.peak_file_path):
                try:
                    os.remove(self.peak_file_path)
                except Exception:
                    pass

            if os.path.exists(self.record_json_path):
                try:
                    os.remove(self.record_json_path)
                except Exception:
                    pass

            self._log_event("Recorde de ocupação zerado pelo operador.", "warning")
            print("[RECORDE] Recorde zerado com sucesso.")

    def _open_camera_safely(self, index, timeout=5.0):
        """
        Tenta abrir a câmera testando backends compatíveis em threads com timeout:
        1. CAP_MSMF  - Microsoft Media Foundation (Logitech C920 e webcams modernas)
        2. CAP_DSHOW - DirectShow (fallback legado)
        3. CAP_ANY   - Automático
        """
        backends = [
            ("MSMF", cv2.CAP_MSMF),
            ("DSHOW", cv2.CAP_DSHOW),
            ("ANY", cv2.CAP_ANY)
        ]

        for name, backend_id in backends:
            result = [None]

            def _try():
                try:
                    cap = cv2.VideoCapture(index, backend_id)
                    if cap is not None and cap.isOpened():
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            result[0] = cap
                        else:
                            cap.release()
                except Exception:
                    pass

            t = threading.Thread(target=_try, daemon=True)
            t.start()
            t.join(timeout=timeout)

            if result[0] is not None:
                print(f"[CÂMERA] ✅ Câmera {index} aberta com sucesso via {name}!")
                # Ajusta resolução se suportado
                try:
                    result[0].set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    result[0].set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                except Exception:
                    pass
                return result[0]

        return None

    def _create_mock_panoramic_frame(self, t):
        """Frame de simulação de alta qualidade quando não há câmera conectada."""
        h, w = 480, 640
        mock = np.zeros((h, w, 3), dtype=np.uint8)

        # Fundo escuro com gradiente
        for y in range(h):
            val = int(24 + (y / h) * 35)
            mock[y, :] = (val - 5, val, val + 10)

        # Linhas de perspectiva arquitetural
        cv2.line(mock, (0, 80), (w // 2, 200), (50, 60, 75), 1)
        cv2.line(mock, (w, 80), (w // 2, 200), (50, 60, 75), 1)
        cv2.line(mock, (w // 2, 200), (w // 2, h), (40, 50, 65), 1)

        # Simula entre 3 e 6 pessoas virtuais em movimento
        cycle = int(t % 30)
        sim_count = 3 + (cycle % 4)

        for i in range(sim_count):
            bx = int(140 + (i * 95) + np.sin(t * 0.8 + i) * 35)
            by = int(250 + (i % 3) * 55 + np.cos(t * 0.6 + i) * 18)

            # Silhueta
            cv2.circle(mock, (bx, by - 45), 13, (140, 190, 240), -1)
            cv2.ellipse(mock, (bx, by), (18, 34), 0, 0, 360, (100, 150, 200), -1)

            # Caixa Neon
            x1, y1 = bx - 24, by - 65
            x2, y2 = bx + 24, by + 40
            cv2.rectangle(mock, (x1, y1), (x2, y2), (255, 240, 0), 2)
            cv2.putText(mock, f"Pessoa {i + 1}", (x1, y1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 240, 0), 1)

        # Rodapé pedagógico
        cv2.putText(mock, "[MODO DEMO: CONECTE UMA WEBCAM FISICA PARA DETECCAO REAL]",
                    (35, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (180, 200, 220), 1)

        return mock, sim_count

    def run_camera_threads(self):
        """Inicia o loop de captura e IA em thread desacoplada."""
        self.is_running = True
        t1 = threading.Thread(target=self._cam1_loop, daemon=True)
        t1.start()

    def _cam1_loop(self):
        """Loop contínuo de captura e processamento da Câmera Panorâmica Única."""
        cap1 = self._open_camera_safely(self.cam1_source)

        if cap1 is None and self.cam1_source != 0:
            print("[CÂMERA] Tentando índice alternativo 0...")
            cap1 = self._open_camera_safely(0)

        is_camera_available = (cap1 is not None and cap1.isOpened())
        self.camera_online = is_camera_available

        if not is_camera_available:
            print("[CÂMERA] Nenhuma webcam física detectada. Ativando Modo de Simulação Panorâmica.")

        last_reconnect_attempt = time.time()

        while self.is_running:
            now_t = time.time()

            # Se não estiver com câmera aberta, tenta reconectar a cada 5 segundos
            if not is_camera_available:
                if now_t - last_reconnect_attempt >= 5.0:
                    last_reconnect_attempt = now_t
                    new_cap = self._open_camera_safely(self.cam1_source, timeout=3.0)
                    if new_cap is not None:
                        cap1 = new_cap
                        is_camera_available = True
                        self.camera_online = True
                        print("[CÂMERA] Câmera física reconectada com sucesso!")

            if is_camera_available and cap1 is not None:
                ret, frame = cap1.read()
                if not ret or frame is None:
                    # Desconexão momentânea da câmera
                    self.camera_online = False
                    is_camera_available = False
                    if cap1 is not None:
                        cap1.release()
                        cap1 = None
                    continue

                self.camera_online = True
                processed, count = self.process_panoramic(frame)
                with self.lock:
                    self.frame_panoramic = processed
                    self.count_panoramic = count
                time.sleep(0.01)
            else:
                # Simulação contínua e suave
                mock, count = self._create_mock_panoramic_frame(now_t)

                # Barra no topo do frame simulado
                overlay = mock.copy()
                w = mock.shape[1]
                cv2.rectangle(overlay, (0, 0), (w, 42), (10, 15, 25), -1)
                cv2.addWeighted(overlay, 0.75, mock, 0.25, 0, mock)

                cv2.circle(mock, (20, 21), 6, (0, 200, 255), -1)
                cv2.putText(mock, "SIMULADOR PANORAMICO", (34, 26),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

                count_text = f"PESSOAS NA SALA: {count}"
                (cw, _), _ = cv2.getTextSize(count_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
                cv2.putText(mock, count_text, (w - cw - 20, 26),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 128), 2, cv2.LINE_AA)

                if count > self.peak_count and count > 0:
                    self._update_peak_record(count, mock)

                with self.lock:
                    self.frame_panoramic = mock
                    self.count_panoramic = count

                time.sleep(0.04)

            # Cálculo de FPS
            self._frame_count += 1
            elapsed = time.time() - self._fps_start_time
            if elapsed >= 1.0:
                self.fps_cam1 = round(self._frame_count / elapsed, 1)
                self._frame_count = 0
                self._fps_start_time = time.time()

        if cap1 is not None and cap1.isOpened():
            cap1.release()

    def get_jpeg_cam1(self):
        """Retorna os bytes em JPEG para o stream contínuo MJPEG."""
        with self.lock:
            if self.frame_panoramic is None:
                return None
            ret, jpeg = cv2.imencode('.jpg', self.frame_panoramic, [cv2.IMWRITE_JPEG_QUALITY, 82])
            return jpeg.tobytes() if ret else None

    def get_peak_jpeg(self):
        """Retorna os bytes da fotografia oficial do momento recorde."""
        with self.lock:
            if self.peak_image_bytes is not None:
                return self.peak_image_bytes
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
        Retorna o dicionário com os dados em tempo real consumidos pelo painel HTML:
        - current_count: contagem ao vivo estabilizada
        - record_count: maior pico de pessoas já registrado
        - record_photo: URL da foto do recorde
        - record_date e record_time: momento exato do recorde
        - fps: taxa de quadros
        - ai_model: identificação do modelo de IA
        """
        with self.lock:
            current = self.count_panoramic
            has_peak = (self.peak_count > 0 and self.peak_image_bytes is not None)
            photo_url = "/api/record_snapshot" if has_peak else None

            pct = round((current / self.room_capacity * 100), 1) if self.room_capacity > 0 else 0

            return {
                # Campos principais consumidos pelo dual_monitor.html
                "current_count": current,
                "record_count": self.peak_count,
                "record_photo": photo_url,
                "record_date": self.peak_date if self.peak_count > 0 else "Aguardando registro",
                "record_time": self.peak_time if self.peak_count > 0 else "--:--:--",
                "record_timestamp": self.peak_timestamp,
                "fps": self.fps_cam1,
                "ai_model": "YOLOv8n" if self.use_yolo else "OpenCV HOG",
                "room_capacity": self.room_capacity,
                "occupancy_pct": min(100, pct),
                "camera_online": self.camera_online,

                # Aliases e compatibilidade com interfaces e testes existentes
                "count_panoramic": current,
                "audited_occupancy": current,
                "peak_count": self.peak_count,
                "peak_photo": photo_url,
                "peak_date": self.peak_date,
                "peak_time": self.peak_time,
                "is_new_peak": self.is_new_peak,
                "events": self.events_log[:6]
            }

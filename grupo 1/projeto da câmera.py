# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════╗
║          ESPELHO INTERATIVO COM IA - SCANNER DE OBJETOS                ║
║          Identificação de Objetos em Tempo Real (YOLOv8)               ║
║          Projeto JENPEX - Visão Computacional                          ║
╚══════════════════════════════════════════════════════════════════════════╝

Descrição:
    Espelho interativo que usa câmera + YOLOv8 para detectar e identificar
    objetos segurados pelo visitante dentro de uma mira HUD cibernética.
    O corpo humano (classe "person") é filtrado automaticamente.

Requisitos:
    pip install opencv-python ultralytics numpy Pillow

Controles:
    ESC  - Sair do programa
    +/-  - Aumentar/diminuir tamanho da mira
    C    - Alternar exibição do painel de calibração
    S    - Salvar screenshot
    R    - Resetar mira para posição padrão
    F    - Alternar tela cheia

Autores: Equipe JENPEX - Frente 2
"""

import cv2
import numpy as np
import time
import math
import os
import csv
import sys
import sqlite3
import winsound
from datetime import datetime
from collections import deque

# ============================================================================
#  CONFIGURAÇÕES GLOBAIS
# ============================================================================

# --- Câmera ---
CAMERA_INDEX = 0                  # Índice da câmera (0 = webcam padrão)
CAMERA_WIDTH = 1280               # Largura da captura
CAMERA_HEIGHT = 720               # Altura da captura
FPS_TARGET = 30                   # FPS alvo

# --- Captura Automática & Banco de Dados ---
AUTO_FOTO_INTERVALO = 3.0         # Intervalo de estabilização contínua do objeto para disparar foto (3s)
PASTA_FOTOS = "capturas"          # Diretório onde as imagens serão salvas
BANCO_DADOS_PATH = "scanner_historico.db" # Banco de dados SQLite local
MAX_MINIATURAS_LATERAL = 4        # Quantidade de fotos recentes na galeria lateral direita

# --- Mira Virtual (Quadrado Imaginário) ---
MIRA_SIZE_PERCENT = 0.30          # Tamanho da mira como % da altura da tela
MIRA_CENTER_Y_OFFSET = -0.08     # Offset vertical da mira (-=sobe, +=desce)
MIRA_MIN_SIZE = 100               # Tamanho mínimo da mira em pixels
MIRA_MAX_SIZE = 500               # Tamanho máximo da mira em pixels

# --- Detecção (YOLOv8 & YOLO-World) ---
YOLO_MODEL = "yolov8s-worldv2.pt"  # Padrão: YOLO-World v2 (Detecta celulares angulares, boné, fone, etc.)
CONFIDENCE_THRESHOLD = 0.22        # Limiar de confiança calibrado (22% para máxima sensibilidade de ângulos)
IOU_THRESHOLD = 0.45               # Limiar de IoU para NMS
DETECTION_INTERVAL = 2             # Rodar detecção a cada N frames (performance)
MODO_ZOOM_MIRA = True              # Inspeciona a região da mira com alta resolução (aumenta precisão para mouse/pequenos)
IMGSZ_CROP = 800                   # Resolução ampliada de inferência no recorte da mira (HD)

# Lista de vocabulário aberto multimodal (Prompts enriquecidos para o YOLO-World com CLIP)
CLASSES_YOLO_WORLD = [
    # Celulares e smartphones (vários ângulos, tela, traseira e na mão)
    "cell phone", "smartphone", "mobile phone", "telephone",
    "black smartphone", "hand holding smartphone", "phone screen", "back of smartphone",
    
    # Bonés e coberturas de cabeça
    "cap", "baseball cap", "hat", "snapback cap", "trucker hat",
    
    # Fones de ouvido e áudio
    "headphones", "over-ear headphones", "earphones", "earbuds", "headset", "wireless earbuds",
    
    # Garrafas e copos
    "water bottle", "bottle", "plastic bottle", "reusable bottle", "tumbler",
    "cup", "mug", "coffee mug", "glass",
    
    # Papelaria e ferramentas
    "book", "notebook", "scissors", "pen", "pencil", "marker",
    
    # Acessórios
    "backpack", "watch", "wrist watch", "smartwatch",
    "glasses", "sunglasses", "eyeglasses",
    
    # Informática e alimentos
    "mouse", "computer mouse", "wireless mouse",
    "apple", "fruit", "banana"
]

# --- Áudio ---
BEEP_FREQUENCY = 1800             # Frequência do beep de escaneamento (Hz)
BEEP_DURATION = 120               # Duração do beep (ms)
BEEP_COOLDOWN = 2.0               # Tempo mínimo entre beeps (segundos)

# --- Visual HUD ---
COR_MIRA_IDLE = (0, 255, 255)        # Amarelo cibernético (BGR) - sem detecção
COR_MIRA_DETECTANDO = (0, 255, 0)    # Verde neon - objeto detectado
COR_MIRA_SCANNING = (255, 100, 0)    # Azul claro - escaneando
COR_TEXTO_PRINCIPAL = (0, 255, 0)    # Verde para textos principais
COR_FUNDO_PAINEL = (20, 20, 20)      # Fundo escuro dos painéis
COR_BORDA_PAINEL = (0, 200, 200)     # Borda dos painéis info
ESPESSURA_MIRA = 2                    # Espessura das linhas da mira
CANTO_LENGTH_RATIO = 0.25            # Comprimento dos cantos como % do lado


# ============================================================================
#  DICIONÁRIO DE TRADUÇÃO COCO → PORTUGUÊS
# ============================================================================

TRADUCAO_OBJETOS = {
    # Pessoas (filtrado, mas traduzido para log)
    "person": "Pessoa",

    # Veículos
    "bicycle": "Bicicleta",
    "car": "Carro",
    "motorcycle": "Motocicleta",
    "airplane": "Avião",
    "bus": "Ônibus",
    "train": "Trem",
    "truck": "Caminhão",
    "boat": "Barco",

    # Sinais e mobiliário urbano
    "traffic light": "Semáforo",
    "fire hydrant": "Hidrante",
    "stop sign": "Placa de Pare",
    "parking meter": "Parquímetro",
    "bench": "Banco",

    # Animais
    "bird": "Pássaro",
    "cat": "Gato",
    "dog": "Cachorro",
    "horse": "Cavalo",
    "sheep": "Ovelha",
    "cow": "Vaca",
    "elephant": "Elefante",
    "bear": "Urso",
    "zebra": "Zebra",
    "giraffe": "Girafa",

    # Acessórios pessoais
    "backpack": "Mochila",
    "umbrella": "Guarda-chuva",
    "handbag": "Bolsa",
    "tie": "Gravata",
    "suitcase": "Mala de Viagem",

    # Esportes
    "frisbee": "Frisbee",
    "skis": "Esquis",
    "snowboard": "Snowboard",
    "sports ball": "Bola Esportiva",
    "kite": "Pipa / Papagaio",
    "baseball bat": "Taco de Beisebol",
    "baseball glove": "Luva de Beisebol",
    "skateboard": "Skate",
    "surfboard": "Prancha de Surf",
    "tennis racket": "Raquete de Tênis",

    # Utensílios de cozinha
    "bottle": "Garrafa",
    "wine glass": "Taça de Vinho",
    "cup": "Copo / Caneca",
    "fork": "Garfo",
    "knife": "Faca",
    "spoon": "Colher",
    "bowl": "Tigela",

    # Alimentos
    "banana": "Banana",
    "apple": "Maçã",
    "sandwich": "Sanduíche",
    "orange": "Laranja",
    "broccoli": "Brócolis",
    "carrot": "Cenoura",
    "hot dog": "Cachorro-quente",
    "pizza": "Pizza",
    "donut": "Rosquinha / Donut",
    "cake": "Bolo",

    # Móveis
    "chair": "Cadeira",
    "couch": "Sofá",
    "potted plant": "Planta em Vaso",
    "bed": "Cama",
    "dining table": "Mesa de Jantar",
    "toilet": "Vaso Sanitário",

    # Eletrônicos
    "tv": "Televisão / Monitor",
    "laptop": "Notebook / Laptop",
    "mouse": "Mouse",
    "remote": "Controle Remoto",
    "keyboard": "Teclado",
    "cell phone": "Celular / Smartphone",

    # Objetos domésticos
    "microwave": "Micro-ondas",
    "oven": "Forno",
    "toaster": "Torradeira",
    "sink": "Pia",
    "refrigerator": "Geladeira",

    # Papelaria e ferramentas
    "book": "Livro / Caderno",
    "clock": "Relógio",
    "vase": "Vaso",
    "scissors": "Tesoura",
    "teddy bear": "Urso de Pelúcia",
    "hair drier": "Secador de Cabelo",
    "toothbrush": "Escova de Dentes",

    # Vocabulário Estendido (YOLO-World & Detecções Adicionais)
    "cap": "Boné",
    "hat": "Boné / Chapéu",
    "baseball cap": "Boné",
    "headphones": "Fones de Ouvido",
    "earphones": "Fones de Ouvido",
    "headset": "Headset / Fone",
    "glasses": "Óculos",
    "sunglasses": "Óculos de Sol",
    "pen": "Caneta",
    "pencil": "Lápis",
    "watch": "Relógio de Pulso",
    "wrist watch": "Relógio de Pulso",
    "smartphone": "Celular / Smartphone",
    "mobile phone": "Celular / Smartphone",
    "mug": "Caneca",
    "tumbler": "Copo Térmico",
}

# Categorias dos objetos para exibição
CATEGORIAS_OBJETOS = {
    "cell phone": "Eletrônico",
    "smartphone": "Eletrônico",
    "mobile phone": "Eletrônico",
    "headphones": "Eletrônico",
    "earphones": "Eletrônico",
    "headset": "Eletrônico",
    "cap": "Acessório",
    "hat": "Acessório",
    "baseball cap": "Acessório",
    "glasses": "Acessório",
    "sunglasses": "Acessório",
    "pen": "Papelaria",
    "pencil": "Papelaria",
    "watch": "Acessório",
    "wrist watch": "Acessório",
    "mug": "Louça",
    "tumbler": "Utensílio",
    "laptop": "Eletrônico",
    "keyboard": "Eletrônico",
    "mouse": "Eletrônico",
    "remote": "Eletrônico",
    "tv": "Eletrônico",
    "bottle": "Utensílio",
    "wine glass": "Utensílio",
    "cup": "Louça",
    "fork": "Utensílio",
    "knife": "Utensílio",
    "spoon": "Utensílio",
    "bowl": "Louça",
    "book": "Papelaria",
    "scissors": "Ferramenta",
    "apple": "Alimento",
    "banana": "Alimento",
    "orange": "Alimento",
    "sandwich": "Alimento",
    "pizza": "Alimento",
    "cake": "Alimento",
    "donut": "Alimento",
    "carrot": "Alimento",
    "broccoli": "Alimento",
    "hot dog": "Alimento",
    "backpack": "Acessório",
    "handbag": "Acessório",
    "umbrella": "Acessório",
    "tie": "Acessório",
    "suitcase": "Acessório",
    "clock": "Acessório",
    "chair": "Mobiliário",
    "couch": "Mobiliário",
    "bed": "Mobiliário",
    "dining table": "Mobiliário",
    "potted plant": "Decoração",
    "vase": "Decoração",
    "teddy bear": "Brinquedo",
    "toothbrush": "Higiene",
    "hair drier": "Higiene",
    "microwave": "Eletrodoméstico",
    "oven": "Eletrodoméstico",
    "toaster": "Eletrodoméstico",
    "refrigerator": "Eletrodoméstico",
    "sink": "Eletrodoméstico",
}


# ============================================================================
#  CLASSE: HUD CIBERNÉTICO (Mira Virtual)
# ============================================================================

class MiraHUD:
    """
    Desenha a mira flutuante estilo HUD cibernético na tela.
    A mira é o 'Quadrado Imaginário Virtual' onde o visitante posiciona objetos.
    """

    def __init__(self, frame_w, frame_h):
        self.frame_w = frame_w
        self.frame_h = frame_h
        self.tamanho = int(frame_h * MIRA_SIZE_PERCENT)
        self.tamanho = max(MIRA_MIN_SIZE, min(MIRA_MAX_SIZE, self.tamanho))
        self.cx = frame_w // 2
        self.cy = int(frame_h // 2 + frame_h * MIRA_CENTER_Y_OFFSET)
        self.animacao_angulo = 0.0
        self.animacao_pulso = 0.0
        self.cor_atual = COR_MIRA_IDLE
        self.scanning = False
        self.scan_progress = 0.0

    def get_rect(self):
        """Retorna (x1, y1, x2, y2) da região da mira."""
        half = self.tamanho // 2
        x1 = self.cx - half
        y1 = self.cy - half
        x2 = self.cx + half
        y2 = self.cy + half
        return (x1, y1, x2, y2)

    def ajustar_tamanho(self, delta):
        """Ajusta o tamanho da mira (+/-)."""
        self.tamanho = max(MIRA_MIN_SIZE, min(MIRA_MAX_SIZE, self.tamanho + delta))

    def resetar(self):
        """Reseta a mira para posição e tamanho padrão."""
        self.tamanho = int(self.frame_h * MIRA_SIZE_PERCENT)
        self.tamanho = max(MIRA_MIN_SIZE, min(MIRA_MAX_SIZE, self.tamanho))
        self.cx = self.frame_w // 2
        self.cy = int(self.frame_h // 2 + self.frame_h * MIRA_CENTER_Y_OFFSET)

    def desenhar(self, frame, detectou_objeto=False, tempo=0.0, progresso_estabilizacao=0.0):
        """Desenha a mira HUD cibernética completa no frame com indicador de estabilização."""
        # Atualizar animação
        self.animacao_angulo = (tempo * 30) % 360
        self.animacao_pulso = 0.5 + 0.5 * math.sin(tempo * 3)

        if detectou_objeto:
            self.cor_atual = COR_MIRA_DETECTANDO
        else:
            self.cor_atual = COR_MIRA_IDLE

        x1, y1, x2, y2 = self.get_rect()
        lado = self.tamanho
        canto = int(lado * CANTO_LENGTH_RATIO)
        esp = ESPESSURA_MIRA

        # Overlay semi-transparente fora da mira (escurece o fundo)
        overlay = frame.copy()
        mask = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)
        mask[y1:y2, x1:x2] = 255
        overlay[mask == 0] = (overlay[mask == 0] * 0.6).astype(np.uint8)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

        cor = self.cor_atual

        # --- Cantos estilo mira cibernética ---
        # Canto superior esquerdo
        cv2.line(frame, (x1, y1), (x1 + canto, y1), cor, esp + 1)
        cv2.line(frame, (x1, y1), (x1, y1 + canto), cor, esp + 1)

        # Canto superior direito
        cv2.line(frame, (x2, y1), (x2 - canto, y1), cor, esp + 1)
        cv2.line(frame, (x2, y1), (x2, y1 - canto * 0 + canto), cor, esp + 1)

        # Canto inferior esquerdo
        cv2.line(frame, (x1, y2), (x1 + canto, y2), cor, esp + 1)
        cv2.line(frame, (x1, y2), (x1, y2 - canto), cor, esp + 1)

        # Canto inferior direito
        cv2.line(frame, (x2, y2), (x2 - canto, y2), cor, esp + 1)
        cv2.line(frame, (x2, y2), (x2, y2 - canto), cor, esp + 1)

        # --- Linhas tracejadas nas bordas ---
        dash_len = 8
        gap = 12
        # Borda superior (entre cantos)
        for px in range(x1 + canto + gap, x2 - canto, dash_len + gap):
            cv2.line(frame, (px, y1), (min(px + dash_len, x2 - canto), y1), cor, 1)
        # Borda inferior
        for px in range(x1 + canto + gap, x2 - canto, dash_len + gap):
            cv2.line(frame, (px, y2), (min(px + dash_len, x2 - canto), y2), cor, 1)
        # Borda esquerda
        for py in range(y1 + canto + gap, y2 - canto, dash_len + gap):
            cv2.line(frame, (x1, py), (x1, min(py + dash_len, y2 - canto)), cor, 1)
        # Borda direita
        for py in range(y1 + canto + gap, y2 - canto, dash_len + gap):
            cv2.line(frame, (x2, py), (x2, min(py + dash_len, y2 - canto)), cor, 1)

        # --- Cruz central (crosshair) ---
        cross_size = 12
        cross_gap = 4
        cx, cy = self.cx, self.cy
        cv2.line(frame, (cx - cross_size, cy), (cx - cross_gap, cy), cor, 1)
        cv2.line(frame, (cx + cross_gap, cy), (cx + cross_size, cy), cor, 1)
        cv2.line(frame, (cx, cy - cross_size), (cx, cy - cross_gap), cor, 1)
        cv2.line(frame, (cx, cy + cross_gap), (cx, cy + cross_size), cor, 1)

        # --- Círculos decorativos girando nos cantos ---
        raio_deco = 6
        angulo_rad = math.radians(self.animacao_angulo)
        offsets = [
            (x1, y1, -1, -1),
            (x2, y1, 1, -1),
            (x1, y2, -1, 1),
            (x2, y2, 1, 1),
        ]
        for ox, oy, dx, dy in offsets:
            px = int(ox + dx * 15 * math.cos(angulo_rad))
            py = int(oy + dy * 15 * math.sin(angulo_rad))
            cv2.circle(frame, (px, py), raio_deco, cor, 1)

        # --- Texto "SCAN AREA" acima da mira ---
        font = cv2.FONT_HERSHEY_SIMPLEX
        if detectou_objeto:
            label = "[ ESCANEANDO OBJETO ]"
        else:
            label = "[ POSICIONE O ITEM NA MIRA ]"

        font_scale = 0.48
        (tw, th), _ = cv2.getTextSize(label, font, font_scale, 1)
        tx = cx - tw // 2
        ty = y1 - 14
        cv2.putText(frame, label, (tx, ty), font, font_scale, cor, 1, cv2.LINE_AA)

        # --- Barra de scan animada (quando detectando) ---
        if detectou_objeto:
            self.scan_progress = (self.scan_progress + 0.03) % 1.0
            scan_y = int(y1 + self.scan_progress * lado)
            alpha = 0.3
            scan_overlay = frame.copy()
            cv2.line(scan_overlay, (x1 + 5, scan_y), (x2 - 5, scan_y),
                     COR_MIRA_SCANNING, 2)
            cv2.addWeighted(scan_overlay, alpha, frame, 1 - alpha, 0, frame)

            # --- Barra e indicador de Estabilização (3 segundos) ---
            if progresso_estabilizacao > 0.0:
                bar_h = 6
                bar_y = y2 + 12
                # Fundo da barra
                cv2.rectangle(frame, (x1, bar_y), (x2, bar_y + bar_h), (40, 40, 40), -1)
                # Preenchimento em verde neon brilhante
                fill_w = int(lado * min(1.0, progresso_estabilizacao))
                cor_prog = (0, 255, 0) if progresso_estabilizacao < 0.9 else (0, 255, 255)
                cv2.rectangle(frame, (x1, bar_y), (x1 + fill_w, bar_y + bar_h), cor_prog, -1)

                # Texto de contagem regressiva de estabilização
                tempo_falta = max(0.0, AUTO_FOTO_INTERVALO * (1.0 - progresso_estabilizacao))
                txt_estavel = f"SEGURE FIRME: FOTO EM {tempo_falta:.1f}s"
                (tw_e, th_e), _ = cv2.getTextSize(txt_estavel, font, 0.40, 1)
                cv2.putText(frame, txt_estavel, (cx - tw_e // 2, bar_y + bar_h + 16),
                            font, 0.40, cor_prog, 1, cv2.LINE_AA)

        return frame


# ============================================================================
#  CLASSE: PAINEL DE INFORMAÇÕES (HUD lateral)
# ============================================================================

class PainelInfo:
    """Desenha painéis de informação estilo HUD sobre objetos detectados."""

    @staticmethod
    def desenhar_painel_objeto(frame, nome_en, nome_pt, categoria, confianca,
                                tempo_ms, x_pos, y_pos):
        """Desenha painel informativo sobre o objeto detectado."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_small = 0.45
        font_med = 0.55
        font_big = 0.7

        # Dimensões do painel
        painel_w = 320
        painel_h = 180
        margem = 12

        # Garantir que o painel não saia da tela
        fw, fh = frame.shape[1], frame.shape[0]
        if x_pos + painel_w > fw:
            x_pos = fw - painel_w - 10
        if y_pos + painel_h > fh:
            y_pos = fh - painel_h - 10
        if x_pos < 10:
            x_pos = 10
        if y_pos < 10:
            y_pos = 10

        # Fundo semi-transparente do painel
        overlay = frame.copy()
        cv2.rectangle(overlay, (x_pos, y_pos),
                      (x_pos + painel_w, y_pos + painel_h),
                      COR_FUNDO_PAINEL, -1)
        cv2.addWeighted(overlay, 0.85, frame, 0.15, 0, frame)

        # Borda do painel
        cv2.rectangle(frame, (x_pos, y_pos),
                      (x_pos + painel_w, y_pos + painel_h),
                      COR_BORDA_PAINEL, 1)

        # Linha decorativa no topo
        cv2.line(frame, (x_pos, y_pos + 30),
                 (x_pos + painel_w, y_pos + 30), COR_BORDA_PAINEL, 1)

        # Título
        cv2.putText(frame, "OBJETO IDENTIFICADO",
                    (x_pos + margem, y_pos + 22),
                    font, font_small, COR_BORDA_PAINEL, 1, cv2.LINE_AA)

        # Nome do objeto em português (destaque)
        cv2.putText(frame, nome_pt.upper(),
                    (x_pos + margem, y_pos + 60),
                    font, font_big, COR_MIRA_DETECTANDO, 2, cv2.LINE_AA)

        # Nome original em inglês
        cv2.putText(frame, f"EN: {nome_en}",
                    (x_pos + margem, y_pos + 82),
                    font, font_small, (180, 180, 180), 1, cv2.LINE_AA)

        # Categoria
        cv2.putText(frame, f"Categoria: {categoria}",
                    (x_pos + margem, y_pos + 105),
                    font, font_small, (200, 200, 200), 1, cv2.LINE_AA)

        # Confiança com barra visual
        conf_text = f"Confianca IA: {confianca:.1f}%"
        cv2.putText(frame, conf_text,
                    (x_pos + margem, y_pos + 128),
                    font, font_small, (200, 200, 200), 1, cv2.LINE_AA)

        # Barra de confiança
        barra_x = x_pos + margem
        barra_y = y_pos + 135
        barra_w = painel_w - 2 * margem
        barra_h = 8
        cv2.rectangle(frame, (barra_x, barra_y),
                      (barra_x + barra_w, barra_y + barra_h),
                      (60, 60, 60), -1)
        fill_w = int(barra_w * confianca / 100)
        cor_barra = COR_MIRA_DETECTANDO if confianca > 60 else (0, 200, 255)
        cv2.rectangle(frame, (barra_x, barra_y),
                      (barra_x + fill_w, barra_y + barra_h),
                      cor_barra, -1)

        # Tempo de resposta
        cv2.putText(frame, f"Tempo: {tempo_ms:.0f} ms",
                    (x_pos + margem, y_pos + 168),
                    font, font_small, (180, 180, 180), 1, cv2.LINE_AA)

        return frame

    @staticmethod
    def desenhar_hud_superior(frame, fps, total_detectados, modelo_nome):
        """Desenha barra superior com informações do sistema."""
        fh, fw = frame.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Fundo superior
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (fw, 35), (10, 10, 10), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Data e hora
        agora = datetime.now().strftime("%d/%m/%Y  %H:%M:%S")
        cv2.putText(frame, agora, (10, 24),
                    font, 0.5, (150, 150, 150), 1, cv2.LINE_AA)

        # FPS
        cor_fps = (0, 255, 0) if fps > 20 else (0, 165, 255) if fps > 10 else (0, 0, 255)
        cv2.putText(frame, f"FPS: {fps:.0f}", (fw - 120, 24),
                    font, 0.5, cor_fps, 1, cv2.LINE_AA)

        # Modelo
        cv2.putText(frame, f"Modelo: {modelo_nome}", (fw // 2 - 80, 24),
                    font, 0.45, (150, 150, 150), 1, cv2.LINE_AA)

        # Status
        status = "ESCANEANDO..." if total_detectados > 0 else "AGUARDANDO OBJETO..."
        cor_status = COR_MIRA_DETECTANDO if total_detectados > 0 else COR_MIRA_IDLE
        cv2.putText(frame, status, (200, 24),
                    font, 0.45, cor_status, 1, cv2.LINE_AA)

        return frame

    @staticmethod
    def desenhar_instrucoes(frame):
        """Desenha instruções na parte inferior da tela."""
        fh, fw = frame.shape[:2]
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Fundo inferior
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, fh - 40), (fw, fh), (10, 10, 10), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        instrucoes = "ESC: Sair | ESPACO: Foto | P: Pausa 3s | [ / ]: Conf | 1-4: Modelos | Z: Zoom | C: Painel"
        cv2.putText(frame, instrucoes, (10, fh - 14),
                    font, 0.36, (140, 140, 140), 1, cv2.LINE_AA)

        # Marca d'água
        cv2.putText(frame, "ESPELHO INTERATIVO IA - JENPEX",
                    (fw - 310, fh - 14),
                    font, 0.4, (80, 80, 80), 1, cv2.LINE_AA)

        return frame


# ============================================================================
#  CLASSE: LOG DE TESTES (Tabela de Acurácia JENPEX)
# ============================================================================

class LogTestes:
    """Gerencia o log de detecções para a tabela de acurácia JENPEX."""

    def __init__(self, pasta_saida="resultados"):
        self.pasta = pasta_saida
        os.makedirs(self.pasta, exist_ok=True)
        self.arquivo = os.path.join(
            self.pasta,
            f"log_deteccoes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        self.deteccoes = []
        self._criar_arquivo()

    def _criar_arquivo(self):
        """Cria o arquivo CSV com cabeçalho."""
        with open(self.arquivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Timestamp",
                "Objeto (EN)",
                "Objeto (PT)",
                "Categoria",
                "Confianca (%)",
                "Tempo Resposta (ms)",
            ])

    def registrar(self, nome_en, nome_pt, categoria, confianca, tempo_ms):
        """Registra uma detecção no log."""
        registro = {
            "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
            "nome_en": nome_en,
            "nome_pt": nome_pt,
            "categoria": categoria,
            "confianca": round(confianca, 1),
            "tempo_ms": round(tempo_ms, 1),
        }
        self.deteccoes.append(registro)

        with open(self.arquivo, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                registro["timestamp"],
                registro["nome_en"],
                registro["nome_pt"],
                registro["categoria"],
                registro["confianca"],
                registro["tempo_ms"],
            ])

    def get_estatisticas(self):
        """Retorna estatísticas gerais das detecções."""
        if not self.deteccoes:
            return None
        total = len(self.deteccoes)
        confianca_media = sum(d["confianca"] for d in self.deteccoes) / total
        tempo_medio = sum(d["tempo_ms"] for d in self.deteccoes) / total
        return {
            "total": total,
            "confianca_media": round(confianca_media, 1),
            "tempo_medio": round(tempo_medio, 1),
        }


# ============================================================================
#  CLASSE: BANCO DE DADOS DE CAPTURAS (SQLite)
# ============================================================================

class BancoDeDadosCapturas:
    """
    Gerencia o banco de dados SQLite para armazenamento permanente
    das capturas fotográficas periódicas e dos metadados de identificação.
    """

    def __init__(self, db_path=BANCO_DADOS_PATH, pasta_fotos=PASTA_FOTOS):
        self.db_path = db_path
        self.pasta_fotos = pasta_fotos
        os.makedirs(self.pasta_fotos, exist_ok=True)
        self._inicializar_banco()

    def _inicializar_banco(self):
        """Cria a tabela de capturas se ela ainda não existir."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS capturas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    caminho_imagem TEXT NOT NULL,
                    objeto_en TEXT,
                    objeto_pt TEXT,
                    categoria TEXT,
                    confianca REAL,
                    modelo_ia TEXT
                )
            """)
            conn.commit()

    def inserir(self, caminho_imagem, objeto_en, objeto_pt, categoria, confianca, modelo_ia):
        """Insere um novo registro de captura no banco de dados."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO capturas (
                    timestamp, caminho_imagem, objeto_en, objeto_pt,
                    categoria, confianca, modelo_ia
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, caminho_imagem, objeto_en, objeto_pt, categoria, float(confianca), modelo_ia))
            conn.commit()
            return cursor.lastrowid

    def carregar_ultimas(self, limite=4):
        """Recupera as últimas N capturas para inicializar a galeria lateral."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, caminho_imagem, objeto_en, objeto_pt, confianca
                FROM capturas
                ORDER BY id DESC
                LIMIT ?
            """, (limite,))
            return cursor.fetchall()


# ============================================================================
#  CLASSE: GALERIA LATERAL HUD (Feed de Fotos a cada 5s)
# ============================================================================

class GaleriaLateralHUD:
    """
    Desenha o feed visual de fotos no canto direito da tela.
    Conforme novas fotos são tiradas a cada 5 segundos, elas entram
    no topo da lista empurrando as anteriores para baixo.
    """

    def __init__(self, frame_w, frame_h, max_itens=MAX_MINIATURAS_LATERAL):
        self.frame_w = frame_w
        self.frame_h = frame_h
        self.max_itens = max_itens
        # Cada item: {"img": thumb_bgr, "hora": str, "label": str, "tem_obj": bool, "id": int}
        self.fotos = deque(maxlen=max_itens)
        self.largura_painel = 165
        self.thumb_w = 145
        self.thumb_h = 85
        self.flash_contador = 0

    def carregar_historico_inicial(self, registros_bd):
        """Carrega fotos anteriores do banco de dados na inicialização."""
        # registros_bd vem do mais novo para o mais velho
        for reg in reversed(registros_bd):
            reg_id, ts, caminho, obj_en, obj_pt, conf = reg
            if os.path.exists(caminho):
                img_disco = cv2.imread(caminho)
                if img_disco is not None:
                    thumb = cv2.resize(img_disco, (self.thumb_w, self.thumb_h))
                    hora = ts.split(" ")[1] if " " in ts else ts
                    tem_obj = bool(obj_pt and obj_pt != "Ambiente")
                    label = f"{obj_pt[:10]} {conf:.0f}%" if tem_obj else "Registro"
                    self.fotos.appendleft({
                        "img": thumb,
                        "hora": hora,
                        "label": label,
                        "tem_obj": tem_obj,
                        "id": reg_id
                    })

    def adicionar_foto(self, frame_puro, label_pt, confianca, tem_obj, id_bd):
        """Adiciona uma nova foto no topo da galeria lateral."""
        thumb = cv2.resize(frame_puro, (self.thumb_w, self.thumb_h))
        hora = datetime.now().strftime("%H:%M:%S")
        label = f"{label_pt[:10]} {confianca:.0f}%" if tem_obj else "Registro"

        self.fotos.appendleft({
            "img": thumb,
            "hora": hora,
            "label": label,
            "tem_obj": tem_obj,
            "id": id_bd
        })
        self.flash_contador = 6  # Efeito de brilho por 6 frames

    def desenhar(self, frame, tempo_estavel=0.0, tem_objeto=False, auto_ativa=True):
        """Renderiza o painel da galeria e as miniaturas na extrema direita."""
        fh, fw = frame.shape[:2]
        x_painel = fw - self.largura_painel - 10
        y_painel = 42
        altura_painel = fh - 90
        font = cv2.FONT_HERSHEY_SIMPLEX

        # Fundo translúcido do painel lateral direito
        overlay = frame.copy()
        cv2.rectangle(overlay, (x_painel, y_painel),
                      (fw - 8, y_painel + altura_painel),
                      COR_FUNDO_PAINEL, -1)
        cv2.addWeighted(overlay, 0.82, frame, 0.18, 0, frame)

        # Borda do painel
        cor_borda = (0, 200, 200)
        cv2.rectangle(frame, (x_painel, y_painel),
                      (fw - 8, y_painel + altura_painel),
                      cor_borda, 1)

        # Cabeçalho do painel
        cv2.putText(frame, "BANCO DE FOTOS",
                    (x_painel + 12, y_painel + 18),
                    font, 0.42, (0, 255, 255), 1, cv2.LINE_AA)

        # Indicador de estabilização de 3s
        bar_w = self.largura_painel - 24
        bar_h = 5
        bx = x_painel + 12
        by = y_painel + 38

        if not auto_ativa:
            cv2.putText(frame, "[PAUSADO (P)]",
                        (x_painel + 12, y_painel + 32),
                        font, 0.34, (0, 165, 255), 1, cv2.LINE_AA)
            cv2.rectangle(frame, (bx, by), (bx + bar_w, by + bar_h), (50, 50, 50), -1)
        elif not tem_objeto:
            cv2.putText(frame, "Aguardando Item...",
                        (x_painel + 12, y_painel + 32),
                        font, 0.33, (140, 140, 140), 1, cv2.LINE_AA)
            cv2.rectangle(frame, (bx, by), (bx + bar_w, by + bar_h), (40, 40, 40), -1)
        else:
            progresso = min(1.0, tempo_estavel / AUTO_FOTO_INTERVALO)
            falta = max(0.0, AUTO_FOTO_INTERVALO - tempo_estavel)
            txt_timer = f"Estavel: {tempo_estavel:.1f}s / {AUTO_FOTO_INTERVALO:.0f}s"
            cor_prog = (0, 255, 0) if progresso < 0.9 else (0, 255, 255)
            cv2.putText(frame, txt_timer,
                        (x_painel + 12, y_painel + 32),
                        font, 0.33, cor_prog, 1, cv2.LINE_AA)

            # Barra de progresso do timer
            cv2.rectangle(frame, (bx, by), (bx + bar_w, by + bar_h), (40, 40, 40), -1)
            fill_w = int(bar_w * progresso)
            cv2.rectangle(frame, (bx, by), (bx + fill_w, by + bar_h), cor_prog, -1)

        # Linha separadora
        cv2.line(frame, (x_painel + 6, y_painel + 48),
                 (fw - 14, y_painel + 48), (70, 70, 70), 1)

        # Desenhar cada miniatura empilhada verticalmente
        y_thumb_atual = y_painel + 56
        espaco_entre = 10

        for idx, foto in enumerate(self.fotos):
            if y_thumb_atual + self.thumb_h + 30 > y_painel + altura_painel:
                break

            x_thumb = x_painel + (self.largura_painel - self.thumb_w) // 2
            y_thumb = y_thumb_atual

            # Inserir imagem da miniatura no frame
            frame[y_thumb:y_thumb + self.thumb_h, x_thumb:x_thumb + self.thumb_w] = foto["img"]

            # Cor da moldura da foto (verde se achou objeto, azul se sem objeto)
            cor_moldura = COR_MIRA_DETECTANDO if foto["tem_obj"] else (255, 180, 0)
            if idx == 0 and self.flash_contador > 0:
                cor_moldura = (255, 255, 255)  # Efeito flash no item mais recente

            # Borda ao redor da foto
            cv2.rectangle(frame, (x_thumb, y_thumb),
                          (x_thumb + self.thumb_w, y_thumb + self.thumb_h),
                          cor_moldura, 1)

            # Tarja com dados da foto embaixo da miniatura
            tarja_h = 22
            tarja_y = y_thumb + self.thumb_h - tarja_h
            tarja_overlay = frame.copy()
            cv2.rectangle(tarja_overlay, (x_thumb, tarja_y),
                          (x_thumb + self.thumb_w, y_thumb + self.thumb_h),
                          (10, 10, 10), -1)
            cv2.addWeighted(tarja_overlay, 0.75, frame, 0.25, 0, frame)

            # Texto do ID e Objeto
            id_txt = f"#{foto['id']}"
            cv2.putText(frame, id_txt, (x_thumb + 4, tarja_y + 10),
                        font, 0.32, (150, 150, 150), 1, cv2.LINE_AA)
            cv2.putText(frame, foto["hora"], (x_thumb + self.thumb_w - 48, tarja_y + 10),
                        font, 0.30, (180, 180, 180), 1, cv2.LINE_AA)
            cv2.putText(frame, foto["label"], (x_thumb + 4, tarja_y + 20),
                        font, 0.34, cor_moldura, 1, cv2.LINE_AA)

            y_thumb_atual += self.thumb_h + espaco_entre + 4

        # Reduz contador de flash
        if self.flash_contador > 0:
            self.flash_contador -= 1

        return frame


# ============================================================================
#  CLASSE PRINCIPAL: ESPELHO INTERATIVO
# ============================================================================

class EspelhoInterativo:
    """
    Aplicação principal do Espelho Interativo com IA.
    Gerencia câmera, detecção YOLOv8, HUD cibernético e interação.
    """

    def __init__(self):
        print("\n" + "=" * 60)
        print("  ESPELHO INTERATIVO COM IA - SCANNER DE OBJETOS")
        print("  YOLOv8 | Visão Computacional | JENPEX")
        print("=" * 60)

        # Estado
        self.rodando = False
        self.fullscreen = False
        self.mostrar_calibracao = False
        self.ultimo_beep = 0
        self.frame_count = 0
        self.fps_atual = 0
        self.fps_historico = deque(maxlen=30)
        self.tempo_inicio = time.time()
        self.objeto_anterior = None
        self.deteccao_cache = []
        self.conf_threshold = CONFIDENCE_THRESHOLD
        self.modo_zoom = MODO_ZOOM_MIRA
        self.modelo_nome = YOLO_MODEL

        # Captura periódica (após 3s de estabilização do objeto) e Banco de Dados
        self.ultimo_tempo_foto = time.time()
        self.tempo_inicio_estabilizacao = None
        self.objeto_estabilizando = None
        self.auto_foto_ativa = True
        self.banco = BancoDeDadosCapturas()

        # Filtro de persistência temporal anti-flicker
        self.ultimo_objeto_valido = None
        self.frames_sem_objeto = 0

        # Inicializar componentes
        self._init_camera()
        self._init_yolo()

        # Componentes visuais
        self.mira = MiraHUD(self.cam_w, self.cam_h)
        self.painel = PainelInfo()
        self.log = LogTestes()
        self.galeria = GaleriaLateralHUD(self.cam_w, self.cam_h, MAX_MINIATURAS_LATERAL)

        # Carregar histórico existente do banco de dados na galeria
        ultimas_capturas = self.banco.carregar_ultimas(MAX_MINIATURAS_LATERAL)
        self.galeria.carregar_historico_inicial(ultimas_capturas)

        print(f"\n[OK] Sistema inicializado com sucesso!")
        print(f"[INFO] Resolucao: {self.cam_w}x{self.cam_h}")
        print(f"[INFO] Modelo: {self.modelo_nome} | Confianca min: {self.conf_threshold*100:.0f}% | Zoom ROI: {self.modo_zoom}")
        print(f"[INFO] Banco de Dados: {BANCO_DADOS_PATH} | Fotos a cada {AUTO_FOTO_INTERVALO:.0f}s")
        print(f"[INFO] Log: {self.log.arquivo}")
        print(f"\nPressione ESC para sair.\n")

    def _init_camera(self):
        """Inicializa a câmera."""
        print(f"\n[...] Abrindo camera (indice {CAMERA_INDEX})...")
        self.cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)

        if not self.cap.isOpened():
            # Tentar sem DirectShow
            print("[AVISO] Tentando abrir camera sem DirectShow...")
            self.cap = cv2.VideoCapture(CAMERA_INDEX)

        if not self.cap.isOpened():
            print("[ERRO] Nao foi possivel abrir a camera!")
            print("       Verifique se a webcam esta conectada.")
            sys.exit(1)

        # Configurar resolução
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, FPS_TARGET)

        # Ler resolução real
        self.cam_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.cam_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        print(f"[OK] Camera aberta: {self.cam_w}x{self.cam_h}")

    def _init_yolo(self):
        """Inicializa o modelo YOLOv8 ou YOLO-World."""
        print(f"\n[...] Carregando modelo YOLO ({self.modelo_nome})...")
        try:
            from ultralytics import YOLO
            self.modelo = YOLO(self.modelo_nome)
            # Se for modelo de vocabulário aberto (YOLO-World), configura as classes customizadas
            if "world" in self.modelo_nome.lower():
                print("[INFO] Configurando classes personalizadas no YOLO-World...")
                self.modelo.set_classes(CLASSES_YOLO_WORLD)
            # Warm-up: uma inferência com imagem preta para carregar na memória
            dummy = np.zeros((640, 640, 3), dtype=np.uint8)
            self.modelo.predict(dummy, verbose=False)
            print(f"[OK] Modelo {self.modelo_nome} carregado com sucesso!")
        except ImportError:
            print("[ERRO] Biblioteca 'ultralytics' nao encontrada!")
            print("       Execute: pip install ultralytics")
            sys.exit(1)
        except Exception as e:
            print(f"[ERRO] Falha ao carregar modelo: {e}")
            sys.exit(1)

    def _trocar_modelo(self, novo_nome):
        """Permite alternar entre yolov8n, yolov8s, yolov8m e yolov8s-worldv2 dinamicamente."""
        if novo_nome == self.modelo_nome:
            return
        print(f"\n[...] Alternando modelo de {self.modelo_nome} para {novo_nome}...")
        try:
            from ultralytics import YOLO
            novo_modelo = YOLO(novo_nome)
            if "world" in novo_nome.lower():
                print("[INFO] Configurando vocabulário aberto (boné, fone, smartphone) no YOLO-World...")
                novo_modelo.set_classes(CLASSES_YOLO_WORLD)
            dummy = np.zeros((640, 640, 3), dtype=np.uint8)
            novo_modelo.predict(dummy, verbose=False)
            self.modelo = novo_modelo
            self.modelo_nome = novo_nome
            print(f"[OK] Modelo alternado com sucesso para {novo_nome}!")
        except Exception as e:
            print(f"[ERRO] Nao foi possivel carregar {novo_nome}: {e}")

    def _emitir_beep(self):
        """Emite sinal sonoro de escaneamento (com cooldown)."""
        agora = time.time()
        if agora - self.ultimo_beep >= BEEP_COOLDOWN:
            self.ultimo_beep = agora
            try:
                winsound.Beep(BEEP_FREQUENCY, BEEP_DURATION)
            except Exception:
                pass  # Ignorar se não conseguir emitir som

    def _capturar_foto_e_salvar(self, frame_puro, objeto_atual=None):
        """
        Tira uma foto, salva no disco (pasta capturas/), insere no SQLite
        e adiciona a miniatura no topo da galeria lateral direita.
        """
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        nome_arquivo = f"foto_{timestamp_str}.jpg"
        caminho_completo = os.path.join(PASTA_FOTOS, nome_arquivo)

        # Salvar a imagem com qualidade
        cv2.imwrite(caminho_completo, frame_puro)

        # Dados do objeto detectado no momento do disparo
        tem_obj = objeto_atual is not None
        nome_en = objeto_atual["nome_en"] if tem_obj else "none"
        nome_pt = objeto_atual["nome_pt"] if tem_obj else "Ambiente"
        categoria = objeto_atual["categoria"] if tem_obj else "Nenhum"
        confianca = float(objeto_atual["confianca"]) if tem_obj else 0.0

        # Gravar no banco de dados SQLite
        id_bd = self.banco.inserir(
            caminho_imagem=caminho_completo,
            objeto_en=nome_en,
            objeto_pt=nome_pt,
            categoria=categoria,
            confianca=confianca,
            modelo_ia=self.modelo_nome
        )

        # Atualizar a galeria lateral direita
        self.galeria.adicionar_foto(frame_puro, nome_pt, confianca, tem_obj, id_bd)

        # Som sutil de obturador de câmera fotográfica
        try:
            winsound.Beep(2400, 50)
            winsound.Beep(3000, 40)
        except Exception:
            pass

        print(f"[BD FOTO #{id_bd}] Gravada no SQLite e disco: {nome_arquivo} | Objeto: {nome_pt} ({confianca:.1f}%)")
        return id_bd

    def _objeto_dentro_da_mira(self, box_x1, box_y1, box_x2, box_y2):
        """
        Verifica se o centro do bounding box do objeto está dentro da mira.
        Usa o centro do bbox para determinar se o objeto está na área de scan.
        """
        mx1, my1, mx2, my2 = self.mira.get_rect()
        obj_cx = (box_x1 + box_x2) / 2
        obj_cy = (box_y1 + box_y2) / 2
        return mx1 <= obj_cx <= mx2 and my1 <= obj_cy <= my2

    def _calcular_iou_mira(self, box_x1, box_y1, box_x2, box_y2):
        """Calcula a porcentagem de sobreposição do bbox com a mira."""
        mx1, my1, mx2, my2 = self.mira.get_rect()
        inter_x1 = max(box_x1, mx1)
        inter_y1 = max(box_y1, my1)
        inter_x2 = min(box_x2, mx2)
        inter_y2 = min(box_y2, my2)

        if inter_x1 >= inter_x2 or inter_y1 >= inter_y2:
            return 0.0

        inter_area = (inter_x2 - inter_x1) * (inter_y2 - inter_y1)
        box_area = (box_x2 - box_x1) * (box_y2 - box_y1)

        if box_area == 0:
            return 0.0

        return inter_area / box_area

    @staticmethod
    def aprimorar_contraste_clahe(imagem_bgr):
        """
        Aplica equalização adaptativa de histograma (CLAHE) no canal L (luminosidade).
        Realça texturas, bordas finas e detalhes escuros (celular/mouse/fone) contra reflexos.
        """
        lab = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        l_eq = clahe.apply(l)
        lab_melhorado = cv2.merge((l_eq, a, b))
        return cv2.cvtColor(lab_melhorado, cv2.COLOR_LAB2BGR)

    def _extrair_objetos_de_results(self, results, offset_x=0, offset_y=0, tempo_ms=0.0):
        """Extrai objetos filtrando 'person' e mapeando coordenadas se houver offset."""
        objetos = []
        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0]) * 100
                    nome_en = self.modelo.names[cls_id].lower()

                    # FILTRO: IGNORAR CORPO HUMANO (person)
                    if nome_en == "person":
                        continue

                    # Normalização semântica flexível de sinônimos e termos compostos
                    if any(p in nome_en for p in ["phone", "smartphone", "cellular"]):
                        nome_en = "cell phone"
                    elif any(p in nome_en for p in ["cap", "hat"]):
                        nome_en = "cap"
                    elif any(p in nome_en for p in ["headphone", "earphone", "earbud", "headset"]):
                        nome_en = "headphones"
                    elif any(p in nome_en for p in ["glasses"]):
                        nome_en = "glasses"
                    elif any(p in nome_en for p in ["watch"]):
                        nome_en = "watch"
                    elif any(p in nome_en for p in ["bottle", "tumbler"]):
                        nome_en = "bottle"
                    elif any(p in nome_en for p in ["cup", "mug"]):
                        nome_en = "cup"
                    elif any(p in nome_en for p in ["mouse"]):
                        nome_en = "mouse"
                    elif any(p in nome_en for p in ["pen", "pencil", "marker"]):
                        nome_en = "pen"

                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    x1 = int(x1) + offset_x
                    y1 = int(y1) + offset_y
                    x2 = int(x2) + offset_x
                    y2 = int(y2) + offset_y

                    # Verificar se objeto está dentro da mira
                    if self._objeto_dentro_da_mira(x1, y1, x2, y2):
                        nome_pt = TRADUCAO_OBJETOS.get(nome_en, nome_en.capitalize())
                        categoria = CATEGORIAS_OBJETOS.get(nome_en, "Outro")
                        objetos.append({
                            "nome_en": nome_en,
                            "nome_pt": nome_pt,
                            "categoria": categoria,
                            "confianca": conf,
                            "tempo_ms": tempo_ms,
                            "bbox": (x1, y1, x2, y2),
                        })
        return objetos

    def _detectar_objetos(self, frame):
        """
        Executa a detecção com:
        1. Inferência de alta resolução (imgsz=800) focada na mira.
        2. Dual-Pass com CLAHE (realce adaptativo de contraste para celulares pretos/fones/garrafas).
        3. Fallback no frame completo caso necessário.
        """
        inicio = time.time()
        objetos = []

        # Se o Modo Zoom na Mira estiver ativado, recorta a mira com margem para inferência de alta resolução
        if self.modo_zoom:
            mx1, my1, mx2, my2 = self.mira.get_rect()
            # Margem de 20% ao redor da mira
            margem = int(self.mira.tamanho * 0.20)
            fh, fw = frame.shape[:2]
            cx1 = max(0, mx1 - margem)
            cy1 = max(0, my1 - margem)
            cx2 = min(fw, mx2 + margem)
            cy2 = min(fh, my2 + margem)

            crop = frame[cy1:cy2, cx1:cx2]
            if crop.size > 0:
                # Passagem 1: Inferência de alta resolução no crop nativo
                results_crop = self.modelo.predict(
                    crop,
                    conf=self.conf_threshold,
                    iou=IOU_THRESHOLD,
                    imgsz=IMGSZ_CROP,
                    verbose=False
                )
                tempo_ms = (time.time() - inicio) * 1000
                objetos = self._extrair_objetos_de_results(
                    results_crop, offset_x=cx1, offset_y=cy1, tempo_ms=tempo_ms
                )

                # Passagem 2 (Dual-Pass CLAHE): Se não achou de primeira ou confiança baixa, aplica realce
                if not objetos:
                    crop_clahe = self.aprimorar_contraste_clahe(crop)
                    results_clahe = self.modelo.predict(
                        crop_clahe,
                        conf=self.conf_threshold,
                        iou=IOU_THRESHOLD,
                        imgsz=IMGSZ_CROP,
                        verbose=False
                    )
                    tempo_ms = (time.time() - inicio) * 1000
                    objetos = self._extrair_objetos_de_results(
                        results_clahe, offset_x=cx1, offset_y=cy1, tempo_ms=tempo_ms
                    )

        # Se o modo zoom não achou nada ou estiver desligado, roda no frame inteiro
        if not objetos:
            results_frame = self.modelo.predict(
                frame,
                conf=self.conf_threshold,
                iou=IOU_THRESHOLD,
                verbose=False
            )
            tempo_ms = (time.time() - inicio) * 1000
            objetos = self._extrair_objetos_de_results(
                results_frame, offset_x=0, offset_y=0, tempo_ms=tempo_ms
            )

        return objetos

    def _desenhar_bbox_objeto(self, frame, obj):
        """Desenha o bounding box estilizado do objeto detectado."""
        x1, y1, x2, y2 = obj["bbox"]
        cor = COR_MIRA_DETECTANDO

        # Bounding box com cantos
        lado_x = x2 - x1
        lado_y = y2 - y1
        canto = min(20, min(lado_x, lado_y) // 4)

        # Cantos do bbox
        cv2.line(frame, (x1, y1), (x1 + canto, y1), cor, 2)
        cv2.line(frame, (x1, y1), (x1, y1 + canto), cor, 2)
        cv2.line(frame, (x2, y1), (x2 - canto, y1), cor, 2)
        cv2.line(frame, (x2, y1), (x2, y1 + canto), cor, 2)
        cv2.line(frame, (x1, y2), (x1 + canto, y2), cor, 2)
        cv2.line(frame, (x1, y2), (x1, y2 - canto), cor, 2)
        cv2.line(frame, (x2, y2), (x2 - canto, y2), cor, 2)
        cv2.line(frame, (x2, y2), (x2, y2 - canto), cor, 2)

        # Label acima do bbox
        label = f"{obj['nome_pt']} {obj['confianca']:.0f}%"
        font = cv2.FONT_HERSHEY_SIMPLEX
        (tw, th), _ = cv2.getTextSize(label, font, 0.5, 1)

        # Fundo do label
        cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw + 8, y1), cor, -1)
        cv2.putText(frame, label, (x1 + 4, y1 - 5),
                    font, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

        return frame

    def _processar_teclas(self, tecla):
        """Processa entrada do teclado."""
        if tecla == 27:  # ESC
            self.rodando = False

        elif tecla == 32:  # ESPAÇO - Disparo manual de foto
            if hasattr(self, '_frame_limpo') and self._frame_limpo is not None:
                melhor = self.deteccao_cache[0] if self.deteccao_cache else None
                self._capturar_foto_e_salvar(self._frame_limpo, melhor)

        elif tecla == ord('p') or tecla == ord('P'):
            self.auto_foto_ativa = not self.auto_foto_ativa
            status = "ATIVADA (A cada 5s)" if self.auto_foto_ativa else "PAUSADA"
            print(f"[CAPTURA AUTOMATICA] {status}")

        elif tecla == ord('+') or tecla == ord('='):
            self.mira.ajustar_tamanho(20)

        elif tecla == ord('-') or tecla == ord('_'):
            self.mira.ajustar_tamanho(-20)

        elif tecla == ord('['):
            self.conf_threshold = max(0.10, round(self.conf_threshold - 0.05, 2))
            print(f"[AJUSTE] Limiar de confianca reduzido para {self.conf_threshold*100:.0f}% (Mais sensivel)")

        elif tecla == ord(']'):
            self.conf_threshold = min(0.90, round(self.conf_threshold + 0.05, 2))
            print(f"[AJUSTE] Limiar de confianca aumentado para {self.conf_threshold*100:.0f}% (Mais rigoroso)")

        elif tecla == ord('1'):
            self._trocar_modelo("yolov8n.pt")

        elif tecla == ord('2'):
            self._trocar_modelo("yolov8s.pt")

        elif tecla == ord('3'):
            self._trocar_modelo("yolov8m.pt")

        elif tecla == ord('4'):
            self._trocar_modelo("yolov8s-worldv2.pt")

        elif tecla == ord('5'):
            self._trocar_modelo("yolov8m-worldv2.pt")

        elif tecla == ord('z') or tecla == ord('Z'):
            self.modo_zoom = not self.modo_zoom
            status = "ATIVADO (Foco total na mira)" if self.modo_zoom else "DESATIVADO (Frame completo)"
            print(f"[AJUSTE] Zoom ROI na Mira: {status}")

        elif tecla == ord('c') or tecla == ord('C'):
            self.mostrar_calibracao = not self.mostrar_calibracao

        elif tecla == ord('r') or tecla == ord('R'):
            self.mira.resetar()

        elif tecla == ord('s') or tecla == ord('S'):
            self._salvar_screenshot()

        elif tecla == ord('f') or tecla == ord('F'):
            self.fullscreen = not self.fullscreen
            if self.fullscreen:
                cv2.setWindowProperty("Espelho Interativo IA",
                                      cv2.WND_PROP_FULLSCREEN,
                                      cv2.WINDOW_FULLSCREEN)
            else:
                cv2.setWindowProperty("Espelho Interativo IA",
                                      cv2.WND_PROP_FULLSCREEN,
                                      cv2.WINDOW_NORMAL)

    def _salvar_screenshot(self):
        """Salva screenshot do frame atual."""
        pasta = "screenshots"
        os.makedirs(pasta, exist_ok=True)
        nome = os.path.join(
            pasta,
            f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        if hasattr(self, '_ultimo_frame') and self._ultimo_frame is not None:
            cv2.imwrite(nome, self._ultimo_frame)
            print(f"[OK] Screenshot salvo: {nome}")

    def _desenhar_calibracao(self, frame):
        """Desenha informações de calibração na tela."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        x, y = 10, 60
        cor = (0, 200, 200)

        zoom_txt = "LIGADO (HD)" if self.modo_zoom else "DESLIGADO"
        foto_txt = f"{AUTO_FOTO_INTERVALO:.0f}s ({'LIGADO' if self.auto_foto_ativa else 'PAUSADO'})"

        textos = [
            f"=== PAINEL DE CALIBRACAO ===",
            f"Modelo atual: {self.modelo_nome}",
            f"Confianca min: {self.conf_threshold*100:.0f}%",
            f"Zoom ROI Mira: {zoom_txt}",
            f"Auto Foto BD: {foto_txt}",
            f"Banco Dados: {BANCO_DADOS_PATH}",
            f"Tamanho mira: {self.mira.tamanho}px",
            f"",
            f"ESPACO     : Tirar foto imediata",
            f"P          : Pausar/Ativar auto foto 3s",
            f"1 a 5      : Modelos (1:Nano/2:S/3:M/4:W-S/5:W-M)",
            f"             (4 e 5: bone, fone, celular angular)",
            f"[ / ]      : Sensibilidade (+/-)",
            f"Z          : Alternar Zoom ROI",
            f"+ / -      : Tamanho da mira",
            f"C          : Fechar este painel",
        ]

        # Fundo
        overlay = frame.copy()
        cv2.rectangle(overlay, (5, 42), (330, 42 + len(textos) * 22 + 10),
                      (10, 10, 10), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

        for i, txt in enumerate(textos):
            cv2.putText(frame, txt, (x, y + i * 22),
                        font, 0.42, cor, 1, cv2.LINE_AA)

        return frame

    def executar(self):
        """Loop principal da aplicação."""
        self.rodando = True
        nome_janela = "Espelho Interativo IA"

        cv2.namedWindow(nome_janela, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(nome_janela, self.cam_w, self.cam_h)

        print("[EXECUTANDO] Loop principal iniciado...")
        print("[INFO] Segure um objeto dentro da mira para identificar!\n")

        while self.rodando:
            tempo_frame_inicio = time.time()

            # --- Capturar frame ---
            ret, frame = self.cap.read()
            if not ret:
                print("[ERRO] Falha ao capturar frame da camera!")
                break

            # ========================================
            # TAREFA 2.1: MODO ESPELHO (Horizontal Flip)
            # O espelhamento garante que o movimento na
            # tela é natural como um espelho de vidro.
            # Mão direita → reflete como mão direita.
            # ========================================
            frame = cv2.flip(frame, 1)

            # Cópia limpa do frame (sem HUD) para fotos e banco de dados
            self._frame_limpo = frame.copy()

            tempo_atual = time.time() - self.tempo_inicio
            self.frame_count += 1

            # --- Detecção YOLOv8 (a cada N frames para performance) ---
            if self.frame_count % DETECTION_INTERVAL == 0:
                self.deteccao_cache = self._detectar_objetos(frame)

            # --- Persistência Temporal Anti-Flicker (estabiliza micro-oscilações de 1-2 frames) ---
            if len(self.deteccao_cache) > 0:
                self.ultimo_objeto_valido = max(self.deteccao_cache, key=lambda o: o["confianca"])
                self.frames_sem_objeto = 0
                objetos = self.deteccao_cache
            else:
                self.frames_sem_objeto += 1
                if self.frames_sem_objeto <= 2 and self.ultimo_objeto_valido is not None:
                    objetos = [self.ultimo_objeto_valido]
                else:
                    self.ultimo_objeto_valido = None
                    objetos = []

            tem_objeto = len(objetos) > 0
            melhor = max(objetos, key=lambda o: o["confianca"]) if tem_objeto else None

            # --- Controle de Estabilização e Captura de Fotos (3 segundos estável) ---
            agora_foto = time.time()
            tempo_estavel = 0.0
            progresso_estabilizacao = 0.0

            if tem_objeto and melhor is not None and self.auto_foto_ativa:
                # Se começou a estabilizar agora
                if self.tempo_inicio_estabilizacao is None:
                    self.tempo_inicio_estabilizacao = agora_foto
                    self.objeto_estabilizando = melhor["nome_en"]

                # Se o objeto mudar enquanto estabiliza, reinicia para o novo item
                if self.objeto_estabilizando != melhor["nome_en"]:
                    self.tempo_inicio_estabilizacao = agora_foto
                    self.objeto_estabilizando = melhor["nome_en"]

                tempo_estavel = agora_foto - self.tempo_inicio_estabilizacao
                progresso_estabilizacao = min(1.0, tempo_estavel / AUTO_FOTO_INTERVALO)

                # Quando completar 3 segundos contínuos de estabilização:
                if tempo_estavel >= AUTO_FOTO_INTERVALO:
                    self._capturar_foto_e_salvar(self._frame_limpo, melhor)
                    self.tempo_inicio_estabilizacao = agora_foto
                    tempo_estavel = 0.0
                    progresso_estabilizacao = 0.0
            else:
                # Sem objeto na mira: reinicia e zera a contagem
                self.tempo_inicio_estabilizacao = None
                self.objeto_estabilizando = None

            # --- Desenhar HUD ---
            # Mira virtual com indicador de estabilização
            frame = self.mira.desenhar(frame, detectou_objeto=tem_objeto,
                                        tempo=tempo_atual,
                                        progresso_estabilizacao=progresso_estabilizacao)

            # Desenhar bounding boxes dos objetos
            for obj in objetos:
                frame = self._desenhar_bbox_objeto(frame, obj)

            # Painel de informações do objeto principal (lado esquerdo)
            if tem_objeto and melhor is not None:
                # Emitir beep se for um novo objeto
                if melhor["nome_en"] != self.objeto_anterior:
                    self.objeto_anterior = melhor["nome_en"]
                    self._emitir_beep()

                    # Registrar no log
                    self.log.registrar(
                        melhor["nome_en"],
                        melhor["nome_pt"],
                        melhor["categoria"],
                        melhor["confianca"],
                        melhor["tempo_ms"],
                    )

                # Posição do painel: lado esquerdo da tela para não cobrir a mira
                painel_x = 20
                painel_y = 52

                frame = self.painel.desenhar_painel_objeto(
                    frame,
                    melhor["nome_en"],
                    melhor["nome_pt"],
                    melhor["categoria"],
                    melhor["confianca"],
                    melhor["tempo_ms"],
                    painel_x, painel_y
                )
            else:
                self.objeto_anterior = None

            # Galeria lateral direita (Feed de fotos do Banco de Dados)
            frame = self.galeria.desenhar(frame, tempo_estavel=tempo_estavel,
                                          tem_objeto=tem_objeto,
                                          auto_ativa=self.auto_foto_ativa)

            # HUD superior (FPS, status, modelo)
            frame = self.painel.desenhar_hud_superior(
                frame, self.fps_atual, len(objetos), self.modelo_nome
            )

            # Instruções inferiores
            frame = self.painel.desenhar_instrucoes(frame)

            # Painel de calibração (se ativo)
            if self.mostrar_calibracao:
                frame = self._desenhar_calibracao(frame)

            # --- Calcular FPS ---
            tempo_frame = time.time() - tempo_frame_inicio
            self.fps_historico.append(1.0 / max(tempo_frame, 0.001))
            self.fps_atual = sum(self.fps_historico) / len(self.fps_historico)

            # Salvar referência do último frame (para screenshot)
            self._ultimo_frame = frame.copy()

            # --- Mostrar frame ---
            cv2.imshow(nome_janela, frame)

            # --- Processar teclas ---
            tecla = cv2.waitKey(1) & 0xFF
            self._processar_teclas(tecla)

        # --- Cleanup ---
        self._finalizar()

    def _finalizar(self):
        """Libera recursos e exibe relatório final."""
        print("\n" + "=" * 60)
        print("  ENCERRANDO ESPELHO INTERATIVO")
        print("=" * 60)

        self.cap.release()
        cv2.destroyAllWindows()

        # Relatório
        stats = self.log.get_estatisticas()
        if stats:
            print(f"\n--- RELATORIO DA SESSAO ---")
            print(f"Total de deteccoes registradas: {stats['total']}")
            print(f"Confianca media: {stats['confianca_media']}%")
            print(f"Tempo medio de resposta: {stats['tempo_medio']} ms")
            print(f"Log CSV: {self.log.arquivo}")
        else:
            print("\nNenhum objeto foi detectado nesta sessao.")

        print(f"Banco de Dados SQLite: {BANCO_DADOS_PATH}")
        print(f"Galeria de Fotos Salvas: {PASTA_FOTOS}/")
        print(f"\nPrograma encerrado com sucesso.")


# ============================================================================
#  PONTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    try:
        espelho = EspelhoInterativo()
        espelho.executar()
    except KeyboardInterrupt:
        print("\n\n[INFO] Programa interrompido pelo usuario (Ctrl+C).")
    except Exception as e:
        print(f"\n[ERRO FATAL] {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione ENTER para sair...")


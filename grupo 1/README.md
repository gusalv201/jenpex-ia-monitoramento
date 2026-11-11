# 🪞 Espelho Interativo com IA - Scanner de Objetos

## Projeto JENPEX - Visão Computacional com YOLOv8

Sistema de espelho interativo que usa câmera + Inteligência Artificial (YOLOv8) para identificar objetos em tempo real. O visitante se posiciona diante da tela como um espelho e segura objetos dentro de uma mira HUD cibernética para identificação automática.

---

## 📋 Requisitos

- **Python 3.8+**
- **Webcam** conectada ao computador
- **Windows 10/11** (para o beep sonoro via `winsound`)

### Instalação das dependências

```bash
pip install -r requirements.txt
```

Ou individualmente:

```bash
pip install opencv-python ultralytics numpy Pillow
```

> ⚠️ Na primeira execução, o YOLOv8 fará download automático do modelo `yolov8n.pt` (~6MB).

---

## 🚀 Como Executar

### 1. Espelho Interativo (programa principal)

```bash
python "projeto da câmera.py"
```

### 2. Gerar Tabela de Acurácia (após os testes)

```bash
python gerar_tabela_acuracia.py
```

---

## 🎮 Controles

| Tecla | Ação |
|-------|------|
| `ESC` | Sair do programa |
| `ESPAÇO` | Disparar foto manual imediatamente (salva no BD e na lateral) |
| `P` | Pausar / Retomar captura automática de fotos por estabilização (3s) |
| `+` / `-` | Aumentar / diminuir tamanho da mira |
| `[` / `]` | Diminuir / aumentar limiar de confiança (sensibilidade) |
| `1` a `5` | Alternar modelo: 1=Nano, 2=Small, 3=Medium, 4=YOLO-World Small, 5=YOLO-World Medium (Precisão Máxima) |
| `Z` | Alternar Zoom ROI na mira (alta resolução para objetos pequenos/difíceis) |
| `C` | Alternar painel de calibração |
| `S` | Salvar screenshot da tela com HUD |
| `R` | Resetar mira para posição padrão |
| `F` | Alternar tela cheia |

---

## 📸 Captura Automática por Estabilização (3s) & Banco de Dados SQLite

O sistema conta com um módulo inteligente de captura fotográfica por estabilização:
- **Critério de Estabilização (3 segundos contínuos)**: A contagem regressiva só inicia quando a pessoa posiciona um objeto dentro da mira cibernética. Se o objeto for movido para fora ou sumir antes de 3 segundos, a contagem zera automaticamente! Isso garante fotos focadas, nítidas e sem borrões de movimento.
- **Feedback Visual na Mira e Lateral**: Durante a contagem, uma barra neon e o texto `SEGURE FIRME: FOTO EM X.Xs` informam o visitante em tempo real.
- **Banco de Dados SQLite (`scanner_historico.db`)**: Registra ID, timestamp, caminho do arquivo, nome do objeto identificado (PT/EN), categoria, confiança e modelo usado.
- **Feed Visual Lateral Direito**: As últimas fotos tiradas são exibidas na lateral direita da tela. Conforme uma nova foto é tirada ao estabilizar por 3s, ela entra no topo da galeria com um efeito de flash e empurra as anteriores para baixo!

---

## 📐 Estrutura do Projeto

```
trabalho do gustavo/
├── projeto da câmera.py          # Código principal do espelho interativo
├── gerar_tabela_acuracia.py      # Gerador de tabela de acurácia JENPEX
├── requirements.txt              # Dependências Python
├── README.md                     # Documentação completa
├── scanner_historico.db          # Banco de dados SQLite de capturas
├── capturas/                     # Fotos tiradas a cada 5s
├── resultados/                   # Logs de detecção em CSV
└── screenshots/                  # Screenshots manuais salvos
```

---

## 🔧 Tarefas JENPEX - Frente 2

### ✅ Tarefa 2.1: Modo Espelho (Horizontal Flip)
- Implementado via `cv2.flip(frame, 1)` 
- Movimento 100% natural: mão direita → reflete como mão direita

### ✅ Tarefa 2.2: Calibração do Quadrado Imaginário
- Mira HUD cibernética com cantos tecnológicos
- Ajustável via teclas `+`/`-`
- Painel de calibração acessível via tecla `C`
- Posicionada na região central-superior para conforto ergonômico

### ✅ Tarefa 2.3: Filtro "Ignorar Corpo Humano"
- Classe `person` (índice 0 do COCO) é filtrada automaticamente
- Foco exclusivo nos objetos segurados pelo visitante

### ✅ Tarefa 2.4: Bateria Científica de Acurácia
- Log automático em CSV com: objeto, confiança, tempo de resposta
- Script `gerar_tabela_acuracia.py` para gerar a tabela JENPEX
- 15 objetos de teste predefinidos

---

## ⚙️ Configurações Ajustáveis

No início do arquivo `projeto da câmera.py`, você pode ajustar:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `CAMERA_INDEX` | `0` | Índice da câmera |
| `CAMERA_WIDTH` | `1280` | Largura da captura |
| `CAMERA_HEIGHT` | `720` | Altura da captura |
| `YOLO_MODEL` | `yolov8s.pt` | Modelo padrão: `yolov8s.pt` (Small - recomendado) |
| `CONFIDENCE_THRESHOLD` | `0.25` | Confiança mínima (25% - ideal para garrafa e mouse) |
| `MODO_ZOOM_MIRA` | `True` | Inspeciona a mira com alta resolução (Zoom ROI) |
| `MIRA_SIZE_PERCENT` | `0.30` | Tamanho da mira (% da tela) |
| `DETECTION_INTERVAL` | `2` | Detectar a cada N frames |
| `BEEP_COOLDOWN` | `2.0` | Segundos entre beeps |

### Modelos YOLO disponíveis:
- `yolov8n.pt` - **Nano** (ultra-leve)
- `yolov8s.pt` - **Small** (equilíbrio para objetos comuns do COCO)
- `yolov8m.pt` - **Medium** (alta precisão para COCO)
- `yolov8s-worldv2.pt` - **YOLO-World v2 Small** (Vocabulário Aberto: boné, fone, celular angular, etc.)
- `yolov8m-worldv2.pt` - **YOLO-World v2 Medium** (Precisão Máxima Absoluta em Vocabulário Aberto!)

---

## 🧪 Protocolo de Teste JENPEX

1. Execute o programa com 3 alunos diferentes
2. Cada aluno segura os 15 objetos da lista dentro da mira
3. O programa registra automaticamente cada detecção no CSV
4. Após os testes, execute `gerar_tabela_acuracia.py`
5. Use o relatório gerado no poster/artigo da JENPEX


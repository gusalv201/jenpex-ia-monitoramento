# 🌟 JENPEX: Projetos de Inteligência Artificial e Visão Computacional

Este repositório contém a documentação completa, metodologia e o código-fonte executável de **2 Trabalhos de Pesquisa e Inovação** para a **JENPEX** (Jornada de Ensino, Pesquisa e Extensão).

---

## 👥 Os 2 Grupos e Seus Trabalhos

```
                  ┌───────────────────────────────────────────────────┐
                  │            PROJETOS DE IA PARA A JENPEX           │
                  └─────────────────────────┬─────────────────────────┘
                                            │
               ┌────────────────────────────┴────────────────────────────┐
               │                                                         │
               ▼                                                         ▼
┌─────────────────────────────┐                           ┌─────────────────────────────┐
│          GRUPO 1            │                           │          GRUPO 2            │
│ Espelho Inteligente com IA  │                           │ Sistema de Dupla Câmera de  │
│ Scanner Frontal de Objetos  │                           │ Ocupação (Panorâmica+Porta) │
└──────────────┬──────────────┘                           └──────────────┬──────────────┘
               │                                                         │
     • Câmera frontal na altura dos olhos                      • Câmera 1: Panorâmica interna
     • A pessoa se vê na tela (espelho)                        • Câmera 2: Linha de fluxo
     • Quadrado imaginário no software                         • Auditoria cruzada em tempo real
     • [Ver Guia do Grupo 1](tarefas/GRUPO_1_SCANNER_OBJETOS.md)             • [Ver Guia do Grupo 2](tarefas/GRUPO_2_DUPLA_CAMERA_OCUPACAO.md)
```

---

## 🚀 Como Executar Cada Projeto

Ambos os projetos possuem iniciadores automáticos para Windows:

### 📦 Rodar Projeto 1 (Espelho Inteligente - Scanner de Objetos):
Dê um duplo clique em:
```
iniciar_projeto1_scanner.bat
```
- **Porta:** `http://localhost:5001`
- **O que faz:** Abre a interface de espelho inteligente. A pessoa se vê ao vivo na tela, segura qualquer objeto dentro do quadrado virtual holográfico, e a IA detecta, traduz o nome para Português, calcula a certeza e emite sinal sonoro de leitura.

---

### 🚪 Rodar Projeto 2 (Dupla Câmera de Ocupação da Sala):
Dê um duplo clique em:
```
iniciar_projeto2_cameras.bat
```
- **Porta:** `http://localhost:5002`
- **O que faz:** Abre o painel do monitor da porta da sala. Exibe simultaneamente a Câmera Panorâmica (contando quem está no salão) e a Câmera da Porta (linha virtual de fluxo IN/OUT), auditando a lotação e alertando os visitantes se a sala estiver cheia.

---

## 📋 Documentação e Roteiros de Tarefas

Consulte os guias passo a passo elaborados para os estudantes:
- 📄 [PLANO_GERAL_JENPEX.md](file:///c:/Users/Lenovo/Desktop/Imagem%20IA%20JENPEX%202M/tarefas/PLANO_GERAL_JENPEX.md) - Visão global, justificativa e critérios de avaliação
- 📄 [GRUPO_1_SCANNER_OBJETOS.md](file:///c:/Users/Lenovo/Desktop/Imagem%20IA%20JENPEX%202M/tarefas/GRUPO_1_SCANNER_OBJETOS.md) - Tarefas da bancada, tradução, testes e pitch
- 📄 [GRUPO_2_DUPLA_CAMERA_OCUPACAO.md](file:///c:/Users/Lenovo/Desktop/Imagem%20IA%20JENPEX%202M/tarefas/GRUPO_2_DUPLA_CAMERA_OCUPACAO.md) - Tarefas da dupla câmera, linha de fluxo e auditoria
- 📄 [CRONOGRAMA_INTEGRADO.md](file:///c:/Users/Lenovo/Desktop/Imagem%20IA%20JENPEX%202M/tarefas/CRONOGRAMA_INTEGRADO.md) - Linha do tempo de 4 semanas até o evento oficial

---

## 📁 Estrutura de Pastas

```
Imagem IA JENPEX 2M/
├── iniciar_projeto1_scanner.bat     # Executa o Scanner do Grupo 1
├── iniciar_projeto2_cameras.bat     # Executa a Dupla Câmera do Grupo 2
├── yolov8n.pt                       # Modelo de IA Local (Offline)
├── requirements.txt                 # Dependências (Flask, OpenCV, Ultralytics)
├── README.md                        # Documentação principal
├── src/
│   ├── projeto1_scanner/            # Código e templates do Trabalho 1
│   │   ├── scanner_detector.py
│   │   ├── scanner_app.py
│   │   └── templates/scanner.html
│   └── projeto2_dupla_camera/       # Código e templates do Trabalho 2
│       ├── dual_detector.py
│       ├── dual_camera_app.py
│       └── templates/dual_monitor.html
└── tarefas/                         # Fichas de tarefas para os alunos
    ├── PLANO_GERAL_JENPEX.md
    ├── GRUPO_1_SCANNER_OBJETOS.md
    ├── GRUPO_2_DUPLA_CAMERA_OCUPACAO.md
    └── CRONOGRAMA_INTEGRADO.md
```

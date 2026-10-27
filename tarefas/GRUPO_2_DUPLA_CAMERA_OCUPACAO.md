# 🚪 TRABALHO 2 - GRUPO 2: SISTEMA DE DUPLA CÂMERA DE OCUPAÇÃO DA SALA (PANORÂMICA + FLUXO)

---

### 🎯 Descrição do Trabalho
Desenvolver um **Sistema Inteligente de Gestão de Lotação e Auditoria com Dupla Visão Computacional**:
1. **Câmera 1 (Panorâmica no Teto):** Enxerga o salão inteiro e faz a **contagem instantânea de pessoas presentes** (detecção direta de quantos corpos/cabeças estão no ambiente).
2. **Câmera 2 (Portaria / Hall de Entrada):** Monitora uma **linha virtual de corte**, registrando quem entra (+1) e quem sai (-1).
3. **Painel na Entrada:** Faz a **validação cruzada em tempo real**: compara se a quantidade de pessoas que a câmera da porta contou bate com o número de pessoas que a câmera panorâmica está vendo no salão, alertando sobre superlotação!

---

## 👥 Divisão das Tarefas do Grupo 2 (2 Subgrupos)

Para garantir máxima eficiência e foco, o Grupo 2 foi estruturado em **2 Subgrupos Complementares**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            ORGANIZAÇÃO DO GRUPO 2                           │
├─────────────────────────────────────────────┬───────────────────────────────┤
│          SUBGRUPO 2A: ENGENHARIA DE         │   SUBGRUPO 2B: HARDWARE,      │
│          SOFTWARE (BACK-END + FRONT-END)    │   MONTAGEM FÍSICA E PITCH     │
└─────────────────────────────────────────────┴───────────────────────────────┘
```

---

## 💻 SUBGRUPO 2A: Engenharia de Software (Back-end & Front-end)
*Missão: Desenvolver, calibrar e integrar toda a lógica de inteligência artificial, processamento de imagem, servidor e painel web.*

### 📋 Tarefas Práticas:
- [ ] **Tarefa 2A.1: Back-end - Rastreamento e Linha de Corte (Câmera da Porta):**
  - No arquivo `src/projeto2_dupla_camera/dual_detector.py`, calibrar a posição da linha virtual (`self.line_pct`) e a zona de amortecimento/histerese (`self.buffer_px`).
  - Entender como o algoritmo calcula se a pessoa está descendo (Entrada: $+1$) ou subindo (Saída: $-1$) com base no histórico de coordenadas $(C_x, C_y)$ do centróide.
- [ ] **Tarefa 2A.2: Back-end - Contagem Panorâmica do Salão:**
  - Analisar o método `process_panoramic()`. Ele processa os quadros do salão com YOLOv8 filtrando a classe `person` (ID 0) e soma os corpos detectados.
- [ ] **Tarefa 2A.3: Back-end - Lógica de Auditoria e Convergência:**
  - Implementar o cálculo da divergência:
    $$\Delta = |N_{\text{panorâmica}} - N_{\text{catraca}}|$$
  - Definir regras de status: se $\Delta = 0 \rightarrow$ "Convergência Perfeita"; se $\Delta > 0 \rightarrow$ "Aviso de Divergência".
- [ ] **Tarefa 2A.4: Front-end - Customização do Monitor da Entrada:**
  - No arquivo `src/projeto2_dupla_camera/templates/dual_monitor.html`, ajustar:
    - O nome oficial da sala e da escola (IFMT).
    - O limite máximo de lotação (ex: 30 pessoas).
    - As cores dos alertas (**Verde**: Entrada Permitida, **Vermelho**: Sala Lotada).
    - Testar o modo tela cheia (F11) e a fluidez das duas transmissões de vídeo ao vivo.
- [ ] **Tarefa 2A.5: Entrega Obrigatória no GitHub:**
  - O Subgrupo 2A **deve enviar todo o código final testado para o repositório oficial no GitHub** (veja a seção de Git abaixo).

---

## 🛠️ SUBGRUPO 2B: Hardware, Montagem Física e Apresentação (Pitch & Banner)
*Missão: Instalar com segurança as duas câmeras e o monitor na sala física, elaborar a identidade visual acadêmica e encantar os jurados na apresentação.*

### 📋 Tarefas Práticas:
- [ ] **Tarefa 2B.1: Instalação da Câmera 1 (Panorâmica no Teto/Canto Alto):**
  - Fixar em um tripé alto ou suporte próximo ao teto, com ângulo aberto para cobrir o máximo do salão da sala sem pontos cegos.
- [ ] **Tarefa 2B.2: Instalação da Câmera 2 (Portaria / Hall de Entrada):**
  - Fixar sobre o batente da porta (altura entre 2,20m e 2,50m), inclinada a aproximadamente 50° apontando para o chão da passagem.
- [ ] **Tarefa 2B.3: Demarcação Física da Linha de Solo:**
  - Colar uma fita zebrada amarela e preta no chão da porta exatamente onde a linha virtual da Câmera 2 foi calibrada pelo Subgrupo 2A.
- [ ] **Tarefa 2B.4: Instalação do Totem / Monitor de Entrada:**
  - Posicionar o monitor do lado de fora da porta (altura dos olhos, ~1,50m).
  - Prender todos os cabos elétricos, USB e HDMI com fita silver tape ou canaletas para **evitar acidentes e tropeços**.
- [ ] **Tarefa 2B.5: Diagramação do Banner Científico Oficial da JENPEX:**
  - **Título:** *Sistema Integrado de Dupla Visão Computacional para Auditoria e Controle de Ocupação de Ambientes em Tempo Real*.
  - **Estrutura:** Introdução (problema da superlotação), Metodologia (fotos das 2 câmeras instaladas), Resultados (tabela de acurácia) e Conclusão.
- [ ] **Tarefa 2B.6: Ensaio do Pitch de 3 Minutos para os Avaliadores:**
  - Treinar a oratória seguindo o roteiro cronometrado:
    - **Minuto 1:** Apresentar o problema de segurança e combate a incêndio em salas cheias.
    - **Minuto 2 (Ao Vivo):** Convidar o jurado a atravessar a porta: a Câmera 2 apita e registra a entrada; a Câmera 1 mostra o jurado sendo detectado no salão!
    - **Minuto 3:** Explicar por que a validação cruzada entre duas câmeras é superior a qualquer sensor comum de porta.
- [ ] **Tarefa 2B.7: Entrega Obrigatória no GitHub:**
  - O Subgrupo 2B **deve enviar para o repositório oficial no GitHub**: o arquivo do banner (PDF/PNG), o roteiro do pitch escrito e as fotos da montagem física na sala.

---

## 🤖 Como Usar a IA Como Sua Tutora (Aprenda a Lógica, Não Apenas Copie!)

> ⚠️ **ATENÇÃO ESTUDANTES:** Na JENPEX, os jurados avaliam o **seu domínio do projeto**. Se você apenas copiar código ou comandos sem entender o que eles fazem, você perderá pontos na arguição. A Inteligência Artificial deve ser usada como uma **professora particular que te ensina a pensar**!

### 📝 Prompt Oficial para os Alunos Colarem na IA:
Copie e cole o texto abaixo no ChatGPT, Gemini ou Claude sempre que for trabalhar nas tarefas:

```text
"Olá! Sou aluno do Instituto Federal (IFMT) e estou desenvolvendo o projeto de Inteligência Artificial para a feira científica JENPEX (Sistema de Dupla Câmera de Ocupação com YOLOv8).

Você atuará como minha IA Tutora e Orientadora Pedagógica. Seu objetivo não é apenas me entregar códigos prontos, mas me ensinar as etapas para que eu entenda profundamente o projeto e consiga defender perfeitamente perante a banca de jurados.

Siga sempre esta metodologia de ensino:
1. Explique o 'PORQUÊ' de cada etapa ou comando antes de mostrar a sintaxe.
2. Use analogias simples do dia a dia para explicar conceitos como Bounding Box, Centróide, Rastreamento de Vetores (Tracking), Histerese e MJPEG Streaming.
3. Divida o aprendizado em pequenos passos lógicos.
4. No final de cada explicação, faça-me 1 ou 2 perguntas de verificação para testar se eu realmente compreendi a lógica.

Minha primeira dúvida/etapa é: [INSIRA SUA DÚVIDA OU ARQUIVO AQUI]"
```

### 🎯 Conceitos Chave que Vocês Precisam Saber Responder aos Jurados:
1. **O que é uma Bounding Box?** É o retângulo numérico $[x_{\text{min}}, y_{\text{min}}, x_{\text{max}}, y_{\text{max}}]$ que delimita a posição exata da pessoa na imagem.
2. **O que é Centróide?** É o ponto central $(C_x, C_y)$ do corpo da pessoa. É o centróide que o algoritmo rastreia para saber se a pessoa cruzou a linha.
3. **O que é Zona Morta / Buffer de Histerese?** É uma faixa de tolerância (ex: 25 pixels) acima e abaixo da linha. Se a pessoa parar ou hesitar em cima da linha, a histerese impede que o sistema fique contando repetidamente por oscilações mínimas.
4. **Por que usar duas câmeras em vez de uma?** Uma câmera na porta pode falhar se duas pessoas passarem muito coladas; já uma câmera no teto pode ter pequenas oclusões. A **fusão dos dados** das duas câmeras garante que os dados sejam auditados e confiáveis!

---

## 🌐 Envio Obrigatório do Produto do Código no Repositório GitHub

Todo o código desenvolvido pelo **Subgrupo 2A** e todo o material gráfico/roteiro do **Subgrupo 2B** deve ser versionado e entregue no repositório oficial do projeto:

🔗 **Link Oficial do Repositório:**  
[https://github.com/gusalv201/jenpex-ia-monitoramento](https://github.com/gusalv201/jenpex-ia-monitoramento)

### 🚀 Guia Passo a Passo de Git para os Estudantes:

#### 1. Clonar o repositório no seu computador:
```bash
git clone https://github.com/gusalv201/jenpex-ia-monitoramento.git
cd jenpex-ia-monitoramento
```

#### 2. Criar uma branch de trabalho do seu subgrupo:
- **Se você for do Subgrupo 2A (Software):**
  ```bash
  git checkout -b feature/subgrupo-2a-software
  ```
- **Se você for do Subgrupo 2B (Hardware e Pitch):**
  ```bash
  git checkout -b feature/subgrupo-2b-pitch-montagem
  ```

#### 3. Salvar suas alterações e fazer commits com mensagens claras:
```bash
git add .
git commit -m "feat(software): ajusta sensibilidade da linha de corte na porta"
```
*(ou no Subgrupo 2B: `git commit -m "docs: adiciona roteiro do pitch e fotos da camera"`)*

#### 4. Enviar o código e produtos para o GitHub:
```bash
git push origin feature/subgrupo-2a-software
```
*(ou `git push origin feature/subgrupo-2b-pitch-montagem`)*

#### 5. O que deve constar no repositório ao final do projeto:
- ✅ Todo o código-fonte atualizado e comentado.
- ✅ O arquivo digital do Banner da JENPEX (PDF ou imagem de alta resolução).
- ✅ As fotos da instalação física das duas câmeras na sala.
- ✅ O roteiro escrito do pitch de 3 minutos.

---

### 🚀 Como Rodar o Trabalho 2
Dê um duplo clique em:
```
iniciar_projeto2_cameras.bat
```
*(Ou execute no terminal: `python src/projeto2_dupla_camera/dual_camera_app.py`)*
Abre em `http://localhost:5002`. Pressione **F11** para colocar em tela cheia!

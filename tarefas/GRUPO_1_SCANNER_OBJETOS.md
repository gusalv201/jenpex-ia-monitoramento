# 🪞 TRABALHO 1 - GRUPO 1: ESPELHO INTELIGENTE COM IA (SCANNER DE OBJETOS)

---

### 🎯 Descrição do Trabalho
Desenvolver um **Espelho Interativo com IA para Identificação de Objetos em Tempo Real**.
- Uma câmera é instalada **na altura dos olhos de uma pessoa (1,50m a 1,65m)** apontada para a frente, de modo que o visitante se posicione e **se veja na tela** como se estivesse diante de um espelho interativo.
- Na tela do software, é desenhado um **"Quadrado Imaginário Virtual" (mira flutuante estilo HUD cibernético)**.
- O visitante segura e ergue qualquer objeto (celular, garrafa d'água, maçã, tesoura, mochila, livro, caneca, relógio, etc.) dentro do quadrado na tela.
- A Inteligência Artificial local (YOLOv8) detecta o objeto erguido dentro da mira virtual, **ignora o corpo da pessoa**, identifica o item com precisão, traduz para o Português, emite um sinal sonoro de escaneamento e exibe informações sobre o item em tempo real.

---

### 👥 Divisão das Tarefas Entre os Membros do Grupo 1

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            MEMBROS DO GRUPO 1                               │
├───────────────────────┬─────────────────────────────┬───────────────────────┤
│ Frente 1: Hardware,   │ Frente 2: Inteligência      │ Frente 3: Interface & │
│ Totem e Posição da Cam│ Artificial & Calibração     │ Apresentação (Pitch)  │
└───────────────────────┴─────────────────────────────┴───────────────────────┘
```

---

### 🛠️ FRENTE 1: Hardware, Totem Frontal e Ergonomia do Visitante
*Responsáveis: Alunos focados em física de lentes, montagem, posicionamento e experiência do visitante.*

- [ ] **Tarefa 1.1: Altura da Câmera Frontal (Efeito Espelho):**
  - Posicionar a webcam em um tripé ou fixá-la na borda superior do monitor a aproximadamente **1,50m a 1,65m do chão** (altura dos olhos do visitante médio).
  - A câmera deve apontar diretamente para a frente (ângulo reto de 90°), permitindo que a pessoa veja seu rosto, tronco e braços erguidos na tela.
- [ ] **Tarefa 1.2: Demarcação do Ponto do Visitante no Chão:**
  - Em vez de colar fita em uma mesa, colar uma fita amarela ou placa no chão a **1,20m de distância da tela** dizendo: `[ FIQUE AQUI PARA SE VER NO ESPELHO INTELIGENTE ]`.
  - Essa distância é ideal para que a pessoa enquadre o corpo e consiga esticar a mão com o objeto dentro da mira virtual.
- [ ] **Tarefa 1.3: Iluminação Frontal:**
  - Evitar lâmpadas atrás da pessoa (contra-luz). A iluminação do estande deve incidir sobre a pessoa e sobre o objeto para que a câmera capture detalhes nítidos.
- [ ] **Tarefa 1.4: Kit de Objetos Interativos para o Público:**
  - Separar em uma cesta ou bancada 10 a 15 objetos cotidianos suportados pelo modelo para os visitantes segurarem e testarem:
    - *Exemplos:* Celular, garrafa d'água, maçã/banana, tesoura escolar, caneca, livro, relógio de pulso, fone/mouse, mochila.

---

### 🧠 FRENTE 2: Inteligência Artificial, Quadrado Virtual e Calibração
*Responsáveis: Alunos focados em visão computacional, redes neurais e testes científicos.*

- [ ] **Tarefa 2.1: Modo Espelho (Horizontal Flip):**
  - O código já inclui o espelhamento (`cv2.flip(frame, 1)`). A equipe deve verificar se o movimento na tela é 100% natural (ao levantar a mão direita, o reflexo na tela levanta a mão correspondente, exatamente como um espelho de vidro).
- [ ] **Tarefa 2.2: Calibração do "Quadrado Imaginário no Software":**
  - No código `src/projeto1_scanner/scanner_detector.py`, ajustar a posição da mira flutuante:
    - O quadrado virtual fica renderizado com cantos tecnológicos de mira cibernética.
    - Testar se uma pessoa de estatura média e baixa consegue posicionar o objeto confortavelmente dentro da área.
- [ ] **Tarefa 2.3: Filtro "Ignorar Corpo Humano":**
  - Como a pessoa está em frente à tela, a IA detectaria `person` o tempo todo.
  - O algoritmo filtra a classe `person` dentro da mira, dando foco exclusivo aos **objetos que a pessoa está segurando** na mão!
- [ ] **Tarefa 2.4: Bateria Científica de Acurácia (Obrigatório para a JENPEX):**
  - Fazer 3 alunos diferentes segurarem 15 objetos dentro da mira virtual e preencher a tabela de validação experimental:

| Objeto Segurado | Categoria | Detectou Correto? (Sim/Não) | Certeza da IA (%) | Tempo de Resposta (ms) |
| :--- | :--- | :---: | :---: | :---: |
| 1. Celular / Smartphone | Eletrônico | | | |
| 2. Garrafa d'água | Utensílio | | | |
| 3. Caneca / Copo | Louça | | | |
| 4. Livro / Caderno | Papelaria | | | |
| 5. Tesoura escolar | Ferramenta | | | |
| 6. Maçã / Fruta | Alimento | | | |
| 7. Mochila nas costas/mão | Acessório | | | |
| 8. Relógio de pulso | Acessório | | | |
| ... | ... | ... | ... | ... |

$$\text{Taxa de Precisão Final} = \frac{\text{Detecções Corretas}}{\text{Total de Tentativas}} \times 100$$

---

### 🎨 FRENTE 3: Interface Gráfica, Banner Acadêmico e Apresentação
*Responsáveis: Alunos focados em design, experiência do usuário e oratória.*

- [ ] **Tarefa 3.1: Interface Interativa de Espelho:**
  - Garantir que o monitor em tela cheia exiba a imagem da pessoa com a mira holográfica e a ficha lateral com o nome gigante do objeto identificado, barra de certeza e efeitos sonoros.
- [ ] **Tarefa 3.2: Confecção do Banner da JENPEX:**
  - **Título:** *Espelho Inteligente com Inteligência Artificial: Reconhecimento em Tempo Real de Objetos por Visão Computacional*.
  - **Destaque:** Explicar a tecnologia de redes neurais convolucionais (YOLOv8) e a facilidade de uso onde a pessoa se enxerga e interage de forma intuitiva.
- [ ] **Tarefa 3.3: Roteiro do Pitch de 3 Minutos para os Avaliadores:**
  - **Minuto 1:** *"Vocês já imaginaram entrar em uma loja ou laboratório e um espelho inteligente identificar instantaneamente o que você está segurando? Apresentamos o Espelho Inteligente com IA da JENPEX..."*
  - **Minuto 2 (Demonstração prática):** Chamar o jurado: *"Por favor, fique aqui nesta marcação e segure seu celular dentro do quadrado na tela"*. O monitor faz o som de bipe e mostra: *"Celular / Smartphone (95% de certeza)"*.
  - **Minuto 3:** Apresentar a Tabela de Acurácia com os resultados científicos e falar sobre aplicações em caixas de supermercado sem código de barras, acessibilidade para deficientes visuais e automação.

---

### 🚀 Como Rodar o Trabalho 1
Dê um duplo clique em:
```
iniciar_projeto1_scanner.bat
```
*(Ou execute no terminal: `python src/projeto1_scanner/scanner_app.py`)*
Abre em `http://localhost:5001`. Pressione **F11** para colocar em tela cheia!

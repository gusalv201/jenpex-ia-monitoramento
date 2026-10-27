# 📅 CRONOGRAMA INTEGRADO: 2 PROJETOS DE IA PARA A JENPEX

---

### ⏱️ Organização das Fases (4 Semanas de Preparação)
Este cronograma alinha o **Grupo 1 (Scanner de Objetos)** e o **Grupo 2 (Dupla Câmera de Ocupação)** para que ambas as equipes avancem juntas e realizem ensaios conjuntos antes do evento oficial.

```mermaid
gantt
    title Cronograma dos 2 Projetos para a JENPEX
    dateFormat  YYYY-MM-DD
    section Grupo 1: Scanner de Objetos
    Montagem da bancada e suporte da câmera  :g1_1, 2026-11-01, 4d
    Calibração da ROI (Quadrado na tela/mesa):g1_2, after g1_1, 5d
    Bateria de testes com 15 objetos         :g1_3, after g1_2, 4d
    Banner acadêmico e ensaio do pitch       :g1_4, after g1_3, 4d
    section Grupo 2: Dupla Câmera
    Instalação da Câm. Panorâmica e Porta    :g2_1, 2026-11-01, 4d
    Calibração da linha e fusão de dados     :g2_2, after g2_1, 5d
    Testes de fluxo e auditoria de lotação   :g2_3, after g2_2, 4d
    Banner acadêmico e ensaio do pitch       :g2_4, after g2_3, 4d
    section Integração Geral
    Ensaio Geral Simulado com a Turma        :int_1, after g1_3, 2d
    Montagem Oficial nos Estandes da JENPEX  :int_2, after int_1, 1d
    Apresentação para Avaliadores            :milestone, after int_2, 0d
```

---

### 🗓️ Metas Semanais Compartilhadas

#### 📌 Semana 1: Estruturação dos Equipamentos e Primeiro Teste
- **Grupo 1:** Fixa a webcam apontada para a mesa e cola o quadrado de fita na bancada. Testa o executável `iniciar_projeto1_scanner.bat`.
- **Grupo 2:** Fixa a câmera panorâmica interna e a câmera da porta com a fita no chão. Testa o executável `iniciar_projeto2_cameras.bat`.

#### 📌 Semana 2: Calibração Fina dos Algoritmos de IA
- **Grupo 1:** Alinha as margens do quadrado virtual com o quadrado físico e testa a tradução e velocidade de identificação.
- **Grupo 2:** Ajusta a linha de corte virtual e verifica a estabilidade dos IDs rastreados ao cruzar a porta.

#### 📌 Semana 3: Bateria de Testes Científicos e Confecção dos Banners
- **Grupo 1:** Executa os testes formais com os 15 objetos escolares e preenche a Tabela de Acurácia.
- **Grupo 2:** Executa os testes de entrada, saída e pessoas sentadas no salão para a Tabela de Auditoria Cruzada.
- **Ambos:** Diagramam e enviam para impressão os seus respectivos Banners da JENPEX.

#### 📌 Semana 4: Ensaio de Oratória (Pitch) e Apresentação Oficial
- **Ensaio Cronometrado (3 minutos por grupo):** Apresentação simulada com colegas atuando como jurados exigentes.
- **Dia da JENPEX:**
  - Chegar com 1 hora de antecedência.
  - Ligar computadores e deixar as duas aplicações abertas em tela cheia (F11).
  - Demonstrar as tecnologias com clareza, entusiasmo e domínio científico!

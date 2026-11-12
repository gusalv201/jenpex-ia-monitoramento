# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════╗
║  GERADOR DE TABELA DE ACURÁCIA - BATERIA CIENTÍFICA JENPEX             ║
║  Gera a tabela de validação experimental a partir dos logs CSV         ║
╚══════════════════════════════════════════════════════════════════════════╝

Uso:
    python gerar_tabela_acuracia.py

Este script lê os CSVs gerados pelo Espelho Interativo e gera um
relatório formatado para incluir no artigo/poster da JENPEX.
"""

import os
import csv
import glob
from datetime import datetime


# Objetos da bateria de testes JENPEX
BATERIA_TESTES = [
    {"num": 1,  "objeto": "Celular / Smartphone",  "categoria": "Eletrônico",       "classe_en": "cell phone"},
    {"num": 2,  "objeto": "Garrafa d'água",         "categoria": "Utensílio",        "classe_en": "bottle"},
    {"num": 3,  "objeto": "Caneca / Copo",           "categoria": "Louça",            "classe_en": "cup"},
    {"num": 4,  "objeto": "Livro / Caderno",         "categoria": "Papelaria",        "classe_en": "book"},
    {"num": 5,  "objeto": "Tesoura escolar",         "categoria": "Ferramenta",       "classe_en": "scissors"},
    {"num": 6,  "objeto": "Maçã / Fruta",            "categoria": "Alimento",         "classe_en": "apple"},
    {"num": 7,  "objeto": "Mochila",                 "categoria": "Acessório",        "classe_en": "backpack"},
    {"num": 8,  "objeto": "Relógio de pulso",        "categoria": "Acessório",        "classe_en": "clock"},
    {"num": 9,  "objeto": "Controle Remoto",         "categoria": "Eletrônico",       "classe_en": "remote"},
    {"num": 10, "objeto": "Mouse",                   "categoria": "Eletrônico",       "classe_en": "mouse"},
    {"num": 11, "objeto": "Banana",                  "categoria": "Alimento",         "classe_en": "banana"},
    {"num": 12, "objeto": "Teclado",                 "categoria": "Eletrônico",       "classe_en": "keyboard"},
    {"num": 13, "objeto": "Guarda-chuva",            "categoria": "Acessório",        "classe_en": "umbrella"},
    {"num": 14, "objeto": "Garfo",                   "categoria": "Utensílio",        "classe_en": "fork"},
    {"num": 15, "objeto": "Laranja",                 "categoria": "Alimento",         "classe_en": "orange"},
]


def carregar_logs(pasta="resultados"):
    """Carrega todos os CSVs de log da pasta resultados."""
    registros = []
    arquivos = glob.glob(os.path.join(pasta, "log_deteccoes_*.csv"))

    if not arquivos:
        print(f"[AVISO] Nenhum arquivo de log encontrado em '{pasta}/'")
        print(f"        Execute o Espelho Interativo primeiro para gerar logs.")
        return registros

    for arq in sorted(arquivos):
        print(f"  Lendo: {arq}")
        with open(arq, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                registros.append(row)

    print(f"\n  Total de registros carregados: {len(registros)}")
    return registros


def gerar_tabela(registros):
    """Gera tabela formatada de acurácia."""
    print("\n" + "=" * 90)
    print("  TABELA DE VALIDAÇÃO EXPERIMENTAL - BATERIA CIENTÍFICA JENPEX")
    print("=" * 90)

    print(f"\n{'#':<4} {'Objeto Segurado':<25} {'Categoria':<15} "
          f"{'Detectou?':<12} {'Certeza IA':<12} {'Tempo (ms)':<12}")
    print("-" * 80)

    deteccoes_corretas = 0
    total_tentativas = len(BATERIA_TESTES)

    for teste in BATERIA_TESTES:
        # Procurar detecções correspondentes nos registros
        deteccoes_obj = [
            r for r in registros
            if r.get("Objeto (EN)", "").lower() == teste["classe_en"].lower()
        ]

        if deteccoes_obj:
            # Pegar a melhor detecção (maior confiança)
            melhor = max(deteccoes_obj, key=lambda r: float(r.get("Confianca (%)", 0)))
            detectou = "Sim"
            confianca = f"{float(melhor.get('Confianca (%)', 0)):.1f}%"
            tempo = f"{float(melhor.get('Tempo Resposta (ms)', 0)):.0f}"
            deteccoes_corretas += 1
        else:
            detectou = "Não"
            confianca = "-"
            tempo = "-"

        print(f"{teste['num']:<4} {teste['objeto']:<25} {teste['categoria']:<15} "
              f"{detectou:<12} {confianca:<12} {tempo:<12}")

    print("-" * 80)

    # Taxa de precisão
    taxa = (deteccoes_corretas / total_tentativas * 100) if total_tentativas > 0 else 0
    print(f"\n  Taxa de Precisão Final = {deteccoes_corretas}/{total_tentativas} "
          f"x 100 = {taxa:.1f}%")

    # Estatísticas adicionais
    if registros:
        confiancas = [float(r.get("Confianca (%)", 0)) for r in registros]
        tempos = [float(r.get("Tempo Resposta (ms)", 0)) for r in registros]

        print(f"\n  --- Estatísticas Gerais ---")
        print(f"  Confiança Média: {sum(confiancas)/len(confiancas):.1f}%")
        print(f"  Confiança Mínima: {min(confiancas):.1f}%")
        print(f"  Confiança Máxima: {max(confiancas):.1f}%")
        print(f"  Tempo Médio de Resposta: {sum(tempos)/len(tempos):.0f} ms")
        print(f"  Tempo Mínimo: {min(tempos):.0f} ms")
        print(f"  Tempo Máximo: {max(tempos):.0f} ms")

    print("\n" + "=" * 90)

    # Salvar relatório em arquivo texto
    salvar_relatorio(deteccoes_corretas, total_tentativas, taxa, registros)


def salvar_relatorio(corretas, total, taxa, registros):
    """Salva relatório em arquivo texto."""
    pasta = "resultados"
    os.makedirs(pasta, exist_ok=True)
    arquivo = os.path.join(pasta, f"relatorio_acuracia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write("RELATÓRIO DE ACURÁCIA - ESPELHO INTERATIVO COM IA\n")
        f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Detecções Corretas: {corretas}/{total}\n")
        f.write(f"Taxa de Precisão: {taxa:.1f}%\n\n")

        if registros:
            confiancas = [float(r.get("Confianca (%)", 0)) for r in registros]
            tempos = [float(r.get("Tempo Resposta (ms)", 0)) for r in registros]
            f.write(f"Confiança Média: {sum(confiancas)/len(confiancas):.1f}%\n")
            f.write(f"Tempo Médio: {sum(tempos)/len(tempos):.0f} ms\n")

        f.write(f"\nTotal de registros analisados: {len(registros)}\n")

    print(f"\n  Relatório salvo em: {arquivo}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  GERADOR DE TABELA DE ACURÁCIA - JENPEX")
    print("=" * 60)
    print("\n  Carregando logs de detecção...\n")

    registros = carregar_logs()
    gerar_tabela(registros)

    input("\n  Pressione ENTER para sair...")


"""Gera matrizes sintéticas em dados_sinteticos/, no mesmo formato de dados/.

Uso: python3 gerar_sinteticas.py

Servem para conferir se uma versão funciona em matrizes que ela nunca "viu",
e não só nas 10 públicas. O gerador aleatório só pode aparecer aqui, nunca no
solucao.py (o avaliador proíbe seed e default_rng).
"""
import os

import numpy as np

PASTA = "dados_sinteticos"
gerador = np.random.default_rng(2026)  # semente fixa: todos da equipe geram as mesmas matrizes


def tamanho():
    return gerador.integers(5, 41, size=2)  # o lote oficial vai até 40x40 (aviso do monitor, 03/11)


def rank_baixo(n, m, rank, ruido):
    base = gerador.normal(50, 10, size=(1, m))
    sinal = gerador.normal(size=(n, rank)) @ gerador.normal(size=(rank, m)) * 5
    return base + sinal + gerador.normal(size=(n, m)) * 5 * ruido


def ruido_puro(n, m):
    return gerador.normal(50, 2, size=(n, m))


def colunas_constantes(n, m):
    return np.linspace(5, 50, m)[None, :] + gerador.normal(size=(n, m)) * 0.7


casos = []
for rank in range(1, 9):
    for ruido in (0.05, 0.4):  # ruído baixo e alto
        for _ in range(2):
            n, m = tamanho()
            rank_ok = int(min(rank, min(n, m) - 1))
            casos.append((f"rank{rank}_ruido{ruido}", rank_baixo(n, m, rank_ok, ruido)))
for _ in range(10):
    n, m = tamanho()
    casos.append(("ruido_puro", ruido_puro(n, m)))
for _ in range(8):
    n, m = tamanho()
    casos.append(("colunas_constantes", colunas_constantes(n, m)))

os.makedirs(PASTA, exist_ok=True)
for antigo in os.listdir(PASTA):
    if antigo.endswith(".npy") or antigo == "tipos.txt":
        os.remove(os.path.join(PASTA, antigo))

with open(os.path.join(PASTA, "tipos.txt"), "w") as tipos:
    for i, (tipo, gabarito) in enumerate(casos, start=1):
        oculto = gerador.uniform(0.10, 0.45)
        mascara = gerador.random(gabarito.shape) > oculto
        observada = np.where(mascara, gabarito, 0.0)
        np.save(os.path.join(PASTA, f"observada_{i:02d}.npy"), observada)
        np.save(os.path.join(PASTA, f"mascara_{i:02d}.npy"), mascara)
        np.save(os.path.join(PASTA, f"gabarito_{i:02d}.npy"), gabarito)
        tipos.write(f"{i:02d} {tipo} {gabarito.shape[0]}x{gabarito.shape[1]} oculto={oculto:.0%}\n")

print(f"{len(casos)} matrizes geradas em {PASTA}/ (lista em {PASTA}/tipos.txt)")

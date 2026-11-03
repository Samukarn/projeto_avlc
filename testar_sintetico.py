"""Compara versões em matrizes sintéticas (evita decorar o banco público).

Uso: python3 testar_sintetico.py versoes/v3_partida_residuo.py versoes/v4_validacao_cruzada.py
Gera matrizes de rank baixo + ruído e de ruído puro, com 10% a 45% de buracos.
"""
import importlib.util
import sys
import time

import numpy as np

gerador = np.random.default_rng(2026)  # só no teste; proibido no solucao.py


def carregar(arquivo):
    spec = importlib.util.spec_from_file_location(arquivo, arquivo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.principal


casos = []
for _ in range(60):
    n, m = gerador.integers(6, 32, size=2)
    rank = int(gerador.integers(0, min(n, m) // 2 + 1))  # rank 0 = ruído puro
    ruido = gerador.choice([0.0, 0.05, 0.2, 0.5])
    base = gerador.normal(50, 10, size=(1, m))
    sinal = gerador.normal(size=(n, rank)) @ gerador.normal(size=(rank, m)) * 5 if rank else np.zeros((n, m))
    verdade = base + sinal + gerador.normal(size=(n, m)) * (5 * ruido if rank else 2)
    mascara = gerador.random((n, m)) > gerador.uniform(0.10, 0.45)
    casos.append((verdade, mascara, rank, ruido))

for arquivo in sys.argv[1:]:
    principal = carregar(arquivo)
    erros, pior_tempo = [], 0.0
    por_tipo = {"ruído puro": [], "rank baixo": []}
    for verdade, mascara, rank, ruido in casos:
        obs = np.where(mascara, verdade, 0.0)
        t0 = time.perf_counter()
        out = np.asarray(principal(obs, mascara), dtype=float)
        pior_tempo = max(pior_tempo, time.perf_counter() - t0)
        assert out.shape == obs.shape and np.isfinite(out).all()
        h = ~mascara
        e = np.sqrt(np.mean((out[h] - verdade[h]) ** 2)) / verdade[h].std()
        erros.append(e)
        por_tipo["ruído puro" if rank == 0 else "rank baixo"].append(e)
    print(f"{arquivo}: NRMSE médio {np.mean(erros):.4f} | "
          + " | ".join(f"{t} {np.mean(v):.4f} (n={len(v)})" for t, v in por_tipo.items())
          + f" | pior tempo {pior_tempo:.2f}s")

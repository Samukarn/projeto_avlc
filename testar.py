"""Testa uma solução contra o banco público, sem Docker.

Uso: python testar.py [arquivo.py]   (padrão: solucao.py)

O NRMSE aqui é RMSE nas posições ocultas / desvio padrão dos valores ocultos
do gabarito. O avaliador oficial pode normalizar de forma um pouco diferente;
use-o como referência final.
"""
import importlib.util
import sys
import time

import numpy as np

arquivo = sys.argv[1] if len(sys.argv) > 1 else "solucao.py"
spec = importlib.util.spec_from_file_location("solucao", arquivo)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

nrmses = []
tempo_total = 0.0
for i in range(1, 11):
    obs = np.load(f"dados/observada_{i:02d}.npy")
    msk = np.load(f"dados/mascara_{i:02d}.npy").astype(bool)
    gab = np.load(f"dados/gabarito_{i:02d}.npy")

    t0 = time.perf_counter()
    out = np.asarray(mod.principal(obs.copy(), msk.copy()), dtype=float)
    dt = time.perf_counter() - t0
    tempo_total += dt

    assert out.shape == obs.shape, f"matriz {i}: dimensão errada {out.shape}"
    assert np.isfinite(out).all(), f"matriz {i}: NaN/Inf na saída"

    oculto = ~msk
    rmse = np.sqrt(np.mean((out[oculto] - gab[oculto]) ** 2))
    nrmse = rmse / gab[oculto].std()
    nrmses.append(nrmse)
    alerta = "  <-- acima de 2s!" if dt > 2 else ""
    print(f"matriz {i:02d} {str(obs.shape):>9}  NRMSE={nrmse:.4f}  tempo={dt:.3f}s{alerta}")

print(f"\nNRMSE médio: {np.mean(nrmses):.4f}   tempo total: {tempo_total:.2f}s")

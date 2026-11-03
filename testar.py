"""Testa soluções localmente, sem Docker.

Uso:
  python3 testar.py [arquivo.py]                  banco público (padrão: solucao.py)
  python3 testar.py [arquivo.py] --sinteticas     matrizes de dados_sinteticos/
  python3 testar.py --comparar a.py b.py          duas versões lado a lado
  (--sinteticas também vale com --comparar)

Cada execução grava os resultados em resultados.csv (versão, conjunto, matriz,
NRMSE, tempo, data), substituindo as linhas antigas da mesma versão e conjunto.

O NRMSE aqui é RMSE nas posições ocultas / desvio padrão dos valores ocultos do
gabarito. O avaliador oficial pode normalizar de forma um pouco diferente; use-o
como referência final.
"""
import csv
import datetime
import importlib.util
import os
import sys
import time

import numpy as np

CSV = "resultados.csv"


def carregar(arquivo):
    spec = importlib.util.spec_from_file_location("solucao_teste", arquivo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.principal


def matrizes(pasta):
    ids = sorted(int(nome[10:-4]) for nome in os.listdir(pasta) if nome.startswith("observada_"))
    for i in ids:
        obs = np.load(f"{pasta}/observada_{i:02d}.npy")
        msk = np.load(f"{pasta}/mascara_{i:02d}.npy").astype(bool)
        gab = np.load(f"{pasta}/gabarito_{i:02d}.npy")
        yield i, obs, msk, gab


def rodar(arquivo, pasta):
    principal = carregar(arquivo)
    linhas = []
    for i, obs, msk, gab in matrizes(pasta):
        t0 = time.perf_counter()
        out = np.asarray(principal(obs.copy(), msk.copy()), dtype=float)
        dt = time.perf_counter() - t0
        assert out.shape == obs.shape, f"matriz {i}: dimensão errada {out.shape}"
        assert np.isfinite(out).all(), f"matriz {i}: NaN/Inf na saída"
        oculto = ~msk
        rmse = np.sqrt(np.mean((out[oculto] - gab[oculto]) ** 2))
        linhas.append((i, obs.shape, rmse / gab[oculto].std(), dt))
    return linhas


def gravar_csv(arquivo, conjunto, linhas):
    versao = os.path.splitext(os.path.basename(arquivo))[0]
    antigas = []
    if os.path.exists(CSV):
        with open(CSV, newline="") as f:
            antigas = [r for r in csv.DictReader(f) if not (r["versao"] == versao and r["conjunto"] == conjunto)]
    data = datetime.date.today().isoformat()
    with open(CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["versao", "conjunto", "matriz", "nrmse", "tempo", "data"])
        w.writeheader()
        w.writerows(antigas)
        for i, _, nrmse, dt in linhas:
            w.writerow({"versao": versao, "conjunto": conjunto, "matriz": i,
                        "nrmse": f"{nrmse:.4f}", "tempo": f"{dt:.3f}", "data": data})


args = sys.argv[1:]
sinteticas = "--sinteticas" in args
args = [a for a in args if a != "--sinteticas"]
pasta, conjunto = ("dados_sinteticos", "sinteticas") if sinteticas else ("dados", "publico")
if sinteticas and not os.path.isdir(pasta):
    sys.exit("dados_sinteticos/ não existe. Rode antes: python3 gerar_sinteticas.py")

if args and args[0] == "--comparar":
    a, b = args[1], args[2]
    la, lb = rodar(a, pasta), rodar(b, pasta)
    gravar_csv(a, conjunto, la)
    gravar_csv(b, conjunto, lb)
    print(f"{'matriz':>6} {'tamanho':>9}  {'A':>7}  {'B':>7}  {'B - A':>7}")
    for (i, forma, ea, _), (_, _, eb, _) in zip(la, lb):
        marca = "  melhor" if eb < ea - 0.005 else ("  pior" if eb > ea + 0.005 else "")
        print(f"{i:>6} {str(forma):>9}  {ea:7.4f}  {eb:7.4f}  {eb - ea:+7.4f}{marca}")
    ma, mb = np.mean([x[2] for x in la]), np.mean([x[2] for x in lb])
    print(f"\nA = {a}: média {ma:.4f}   tempo máx {max(x[3] for x in la):.2f}s")
    print(f"B = {b}: média {mb:.4f}   tempo máx {max(x[3] for x in lb):.2f}s")
    print(f"Diferença B - A: {mb - ma:+.4f}")
else:
    arquivo = args[0] if args else "solucao.py"
    linhas = rodar(arquivo, pasta)
    gravar_csv(arquivo, conjunto, linhas)
    for i, forma, nrmse, dt in linhas:
        alerta = "  <-- acima de 2s!" if dt > 2 else ""
        print(f"matriz {i:02d} {str(forma):>9}  NRMSE={nrmse:.4f}  tempo={dt:.3f}s{alerta}")
    print(f"\nNRMSE médio: {np.mean([x[2] for x in linhas]):.4f}   tempo total: {sum(x[3] for x in linhas):.2f}s")

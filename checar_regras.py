"""Confere se uma solução respeita as regras do torneio antes de entregar.

Uso: python3 checar_regras.py solucao.py

1. Análise estática: class, seed/default_rng/RandomState/Random, imports
   proibidos e funções definidas fora de principal.
   Também as regras do sandbox do avaliador: sem += em item de lista, sem nomes
   com "_" e só funções embutidas que existem lá (all, any, next etc. não existem).
2. Casos extremos: linha/coluna inteira oculta, 1xn, nx1, tudo visível,
   60x60, valores muito grandes.
3. Em cada caso: forma, NaN/Inf, valores visíveis preservados e tempo
   (alerta acima de 1 s, falha acima de 2 s).

Sai com código 1 se algum item falhar. Não substitui o avaliador Docker, que
usa RestrictedPython de verdade.
"""
import ast
import importlib.util
import sys
import time

import numpy as np

arquivo = sys.argv[1] if len(sys.argv) > 1 else "solucao.py"
falhas = 0


def resultado(nome, ok, detalhe=""):
    global falhas
    if not ok:
        falhas += 1
    print(f"{'OK     ' if ok else 'FALHOU '} {nome}{'  (' + detalhe + ')' if detalhe else ''}")


# ------------------------------------------------------------ 1. análise estática
codigo = open(arquivo, encoding="utf-8").read()
arvore = ast.parse(codigo)
PERMITIDOS = {"numpy", "scipy", "math", "random"}
PROIBIDOS = {"seed", "default_rng", "RandomState", "Random"}

classes = [n.lineno for n in ast.walk(arvore) if isinstance(n, ast.ClassDef)]
resultado("sem class", not classes, f"linhas {classes}" if classes else "")

imports_ruins = []
for n in ast.walk(arvore):
    if isinstance(n, ast.Import):
        imports_ruins += [(a.name, n.lineno) for a in n.names if a.name.split(".")[0] not in PERMITIDOS]
    elif isinstance(n, ast.ImportFrom):
        if (n.module or "").split(".")[0] not in PERMITIDOS:
            imports_ruins.append((n.module, n.lineno))
        imports_ruins += [(a.name, n.lineno) for a in n.names if a.name in PROIBIDOS]
resultado("só imports de numpy/scipy/math/random", not imports_ruins, str(imports_ruins) if imports_ruins else "")

nomes_ruins = sorted({(n.attr if isinstance(n, ast.Attribute) else n.id, n.lineno)
                      for n in ast.walk(arvore)
                      if (isinstance(n, ast.Attribute) and n.attr in PROIBIDOS)
                      or (isinstance(n, ast.Name) and n.id in PROIBIDOS)})
resultado("sem seed/default_rng/RandomState/Random", not nomes_ruins, str(nomes_ruins) if nomes_ruins else "")

funcoes_topo = [n.name for n in arvore.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
resultado("existe principal(observada, mascara)", "principal" in funcoes_topo)
fora = [f for f in funcoes_topo if f != "principal"]
resultado("nenhuma função fora de principal", not fora, str(fora) if fora else "")

# Regras do sandbox do avaliador (RestrictedPython 8.5, lidas de utils/sandbox_restrito.py).
# O código é recusado inteiro se usar += em item de lista/atributo ou nomes com "_".
aug = [n.lineno for n in ast.walk(arvore) if isinstance(n, ast.AugAssign) and not isinstance(n.target, ast.Name)]
resultado("sem += / -= em item de lista ou atributo (ex.: x[0] += 1)", not aug, f"linhas {aug}" if aug else "")
sublinhado = sorted({n.lineno for n in ast.walk(arvore)
                     if (isinstance(n, ast.Name) and n.id.startswith("_"))
                     or (isinstance(n, ast.Attribute) and n.attr.startswith("_"))
                     or (isinstance(n, ast.arg) and n.arg.startswith("_"))})
resultado("nenhum nome ou atributo começando com _", not sublinhado, f"linhas {sublinhado}" if sublinhado else "")
# Funções embutidas que existem no avaliador; qualquer outra vira NameError lá dentro
# (e o try/except trocaria a resposta pelo modelo de médias sem avisar).
EMBUTIDAS = {"None", "False", "True", "abs", "bool", "bytes", "callable", "chr", "complex", "divmod",
             "float", "hash", "hex", "id", "int", "isinstance", "issubclass", "len", "oct", "ord",
             "pow", "range", "repr", "round", "slice", "sorted", "str", "tuple", "zip", "enumerate",
             "map", "min", "max", "sum", "list", "dict", "set", "print", "Exception", "ValueError",
             "ArithmeticError", "ZeroDivisionError", "IndexError", "KeyError", "TypeError"}
import builtins
definidos = {n.id for n in ast.walk(arvore) if isinstance(n, ast.Name) and not isinstance(n.ctx, ast.Load)}
definidos |= {n.arg for n in ast.walk(arvore) if isinstance(n, ast.arg)}
definidos |= {n.name for n in ast.walk(arvore) if isinstance(n, ast.FunctionDef)}
definidos |= {(a.asname or a.name).split(".")[0] for n in ast.walk(arvore) if isinstance(n, (ast.Import, ast.ImportFrom)) for a in n.names}
faltando = sorted({(n.id, n.lineno) for n in ast.walk(arvore)
                   if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load) and n.id not in definidos
                   and hasattr(builtins, n.id) and n.id not in EMBUTIDAS})
resultado("só funções embutidas disponíveis no avaliador", not faltando, str(faltando) if faltando else "")

outros = [type(n).__name__ for n in arvore.body
          if not isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef))
          and not (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant))]
resultado("nada além de imports e principal no topo do arquivo", not outros, str(outros) if outros else "")

# ------------------------------------------------------------ 2. casos extremos
spec = importlib.util.spec_from_file_location("solucao_checar", arquivo)
mod = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(mod)
except Exception as e:
    resultado("arquivo carrega sem erro", False, repr(e))
    print(f"\nFALHOU: {falhas} item(ns). Corrija antes de entregar.")
    sys.exit(1)

g =np.random.default_rng(7)  # só aqui, nunca no solucao.py


def matriz(n, m, rank=3):
    return g.normal(size=(n, rank)) @ g.normal(size=(rank, m)) * 5 + 50


def caso(nome, verdade, mascara):
    obs = np.where(mascara, verdade, 0.0)
    try:
        t0 = time.perf_counter()
        out = np.asarray(mod.principal(obs.copy(), mascara.copy()), dtype=float)
        dt = time.perf_counter() - t0
    except Exception as e:
        resultado(nome, False, f"exceção: {e!r}")
        return
    if out.shape != obs.shape:
        resultado(nome, False, f"forma {out.shape}, esperada {obs.shape}")
    elif not np.isfinite(out).all():
        resultado(nome, False, "NaN/Inf na saída")
    elif not np.allclose(out[mascara], obs[mascara]):
        resultado(nome, False, "alterou valores visíveis")
    elif dt > 2:
        resultado(nome, False, f"{dt:.2f}s, acima do limite de 2 s")
    else:
        resultado(nome, True, f"{dt:.2f}s" + ("  ALERTA: acima de 1 s" if dt > 1 else ""))


m = g.random((12, 10)) > 0.3
m[:, 3] = False
caso("coluna inteira oculta", matriz(12, 10), m)
m = g.random((12, 10)) > 0.3
m[4, :] = False
caso("linha inteira oculta", matriz(12, 10), m)
caso("matriz 1xn", matriz(1, 15, 1), g.random((1, 15)) > 0.3)
caso("matriz nx1", matriz(15, 1, 1), g.random((15, 1)) > 0.3)
caso("máscara toda visível", matriz(10, 10), np.ones((10, 10), bool))
caso("quase tudo oculto", matriz(10, 10), g.random((10, 10)) > 0.95)
caso("matriz 40x40 (maior tamanho do lote oficial)", matriz(40, 40, 6) + g.normal(size=(40, 40)), g.random((40, 40)) > 0.35)
caso("matriz 60x60", matriz(60, 60, 5), g.random((60, 60)) > 0.3)
caso("valores muito grandes (1e12)", matriz(15, 12) * 1e10, g.random((15, 12)) > 0.3)
caso("ruído puro 30x30", g.normal(size=(30, 30)), g.random((30, 30)) > 0.4)

print()
if falhas:
    print(f"FALHOU: {falhas} item(ns). Corrija antes de entregar.")
    sys.exit(1)
print("Tudo OK. Confirme também no avaliador Docker.")

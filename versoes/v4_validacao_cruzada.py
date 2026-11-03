import numpy as np


def principal(observada, mascara):
    # Versão 4: Hard-Impute (SVD iterativo) com rank e modo de partida escolhidos por
    # validação cruzada.
    obs = np.array(observada, dtype=float)
    msk = np.array(mascara, dtype=bool)
    n_lin, n_col = obs.shape

    def preencher_media(m):
        # Ponto de partida: média da coluna + desvio médio da linha em relação a essas médias.
        geral = obs[m].mean() if m.any() else 0.0
        med_col = np.array([obs[m[:, j], j].mean() if m[:, j].any() else geral for j in range(n_col)])
        resid = obs - med_col[None, :]
        desvio_lin = np.array([resid[i, m[i]].mean() if m[i].any() else 0.0 for i in range(n_lin)])
        chute = med_col[None, :] + desvio_lin[:, None]
        return np.where(m, obs, chute)

    if msk.sum() < 10 or min(n_lin, n_col) < 2:
        return preencher_media(msk)

    # Faixa plausível: sem regularização, o Hard-Impute pode "explodir" numa coluna com
    # poucos valores conhecidos. Limitar as previsões evita que um erro desses domine tudo.
    faixa = obs[msk].max() - obs[msk].min()
    piso, teto = obs[msk].min() - 0.5 * faixa, obs[msk].max() + 0.5 * faixa

    # Custo aproximado de uma SVD em microssegundos (medido: 13 us em 10x10, 790 us em
    # 100x100). Serve para parar a busca antes de chegar perto do limite de 2 s.
    custo_svd = 15 + 0.001 * n_lin * n_col * min(n_lin, n_col)
    svds = [0]

    def hard_impute(m, k, inicio, iteracoes=100):
        # Repete: SVD truncada no rank k, depois recoloca os valores conhecidos.
        # Poucas iterações funcionam como regularização (parada antecipada).
        x = inicio
        for _ in range(iteracoes):
            svds[0] += 1
            u, s, vt = np.linalg.svd(x, full_matrices=False)
            aprox = np.clip((u[:, :k] * s[:k]) @ vt[:k], piso, teto)
            novo = np.where(m, obs, aprox)
            mudanca = np.linalg.norm(novo - x)
            x = novo
            if mudanca < 1e-5 * (np.linalg.norm(x) + 1e-12):
                break
        return x

    # Candidatos, em ordem do mais simples ao mais complexo:
    # (0, 'media'), (1, 'quente'), (1, 'frio'), (2, 'quente'), ...
    # 'quente' parte da solução de k-1 (warm start); 'frio' parte das médias.
    k_max = min(n_lin, n_col) - 1

    # Folds: permutação fixa dos conhecidos (sem seed), 10 grupos; avaliamos 5.
    # Cada fold esconde só 10%: escondendo mais, o que sobra pode não bastar para o
    # rank verdadeiro e a validação passa a preferir k pequeno demais.
    conhecidos = np.flatnonzero(msk)
    ordem = conhecidos[np.argsort((conhecidos * 2654435761) % 1000003)]
    # Em matrizes grandes há muitos valores por fold e a medição já é estável com 2 folds.
    n_folds, usar = 10, (5 if conhecidos.size <= 1500 else 2)
    folds = []
    for f in range(usar):
        validacao = ordem[f::n_folds]
        treino = msk.ravel().copy()
        treino[validacao] = False
        treino = treino.reshape(msk.shape)
        inicio = preencher_media(treino)
        folds.append([treino, validacao, obs.ravel()[validacao], inicio, inicio])

    def erro(sol, fold):
        return np.mean((sol.ravel()[fold[1]] - fold[2]) ** 2)

    # O modo "frio" recomeça do zero a cada k e é o mais caro. Em matrizes grandes
    # (mais de 1200 células) há dados de sobra e só o "quente" cabe no tempo.
    modos = ("quente", "frio") if n_lin * n_col <= 1200 else ("quente",)

    candidatos = [(0, "media")]
    erros = [[erro(fold[3], fold) for fold in folds]]
    melhor, sem_melhora = np.median(erros[0]), 0
    for k in range(1, k_max + 1):
        for modo in modos:
            linha = []
            for fold in folds:
                if modo == "quente":
                    fold[4] = hard_impute(fold[0], k, fold[4])
                    linha.append(erro(fold[4], fold))
                else:
                    linha.append(erro(hard_impute(fold[0], k, fold[3]), fold))
            candidatos.append((k, modo))
            erros.append(linha)
        # Parada antecipada no rank: se 6 ranks seguidos não melhoram, ranks maiores
        # dificilmente vão ajudar. (Com 3, perdíamos matrizes em que o erro só cai
        # quando k chega no rank verdadeiro.)
        atual = min(np.median(erros[-1]), np.median(erros[-2]))
        if atual < melhor:
            melhor, sem_melhora = atual, 0
        else:
            sem_melhora += 1
            if sem_melhora >= 6:
                break
        # Orçamento de tempo: estimativa do custo das SVDs já feitas (microssegundos).
        if svds[0] * custo_svd > 300000:
            break

    # Mediana dos folds: um fold que "explodiu" não decide sozinho.
    # Entre os candidatos a até 5% do melhor, fica o mais simples.
    mediana = np.median(np.array(erros), axis=1)
    escolhido = int(np.flatnonzero(mediana <= mediana.min() * 1.05)[0])
    k, modo = candidatos[escolhido]

    inicio = preencher_media(msk)
    if k == 0:
        saida = inicio
    elif modo == "frio":
        saida = hard_impute(msk, k, inicio)
    else:
        saida = inicio
        for r in range(1, k + 1):
            saida = hard_impute(msk, r, saida)

    if not np.isfinite(saida).all():
        saida = preencher_media(msk)
    return saida

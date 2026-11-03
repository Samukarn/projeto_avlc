import numpy as np


def principal(observada, mascara):
    # Versão 5: vários candidatos (médias com α, Soft-Impute, Hard-Impute) escolhidos
    # ou combinados por validação cruzada.
    # Etapas (ver ARQUITETURA.md):
    # preparar -> modelo_medias -> candidatos -> validacao_cruzada -> escolher_ou_combinar -> protecoes

    # ---------------------------------------------------------------- 1. preparar
    obs = np.array(observada, dtype=float)
    msk = np.array(mascara, dtype=bool)
    n_lin, n_col = obs.shape

    # ---------------------------------------------------------------- 2. modelo_medias
    def medias(m):
        # Média de cada coluna e desvio médio de cada linha em relação a essas médias.
        geral = obs[m].mean() if m.any() else 0.0
        med_col = np.array([obs[m[:, j], j].mean() if m[:, j].any() else geral for j in range(n_col)])
        resid = obs - med_col[None, :]
        desvio_lin = np.array([resid[i, m[i]].mean() if m[i].any() else 0.0 for i in range(n_lin)])
        return med_col, desvio_lin

    def modelo_medias(m, alfa=1.0):
        # x = média da coluna + α · desvio da linha. α < 1 confia menos na linha
        # (encolhimento): ajuda quando a linha tem poucos valores ou a matriz é ruído.
        med_col, desvio_lin = medias(m)
        return np.where(m, obs, med_col[None, :] + alfa * desvio_lin[:, None])

    def algoritmo():
        if msk.sum() < 10 or min(n_lin, n_col) < 2:
            return modelo_medias(msk)

        # ------------------------------------------------------------ 3. candidatos
        faixa = obs[msk].max() - obs[msk].min()
        piso, teto = obs[msk].min() - 0.5 * faixa, obs[msk].max() + 0.5 * faixa

        # Custo aproximado de uma SVD em microssegundos, para o orçamento de tempo.
        custo_svd = 15 + 0.001 * n_lin * n_col * min(n_lin, n_col)
        svds = [0]

        def hard_impute(m, k, inicio, iteracoes=100):
            # SVD truncada no rank k e recoloca os conhecidos, até estabilizar.
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

        def soft_impute(m, fracoes):
            # Soft-Impute (Mazumder, Hastie e Tibshirani, 2010): em vez de cortar os
            # valores singulares, subtrai λ de todos (σ -> max(σ - λ, 0)). O ruído some e a
            # estrutura encolhe um pouco. Trabalha com a matriz centrada pelas médias da
            # coluna e percorre λ do maior para o menor, cada um partindo do anterior.
            med_col, _ = medias(m)
            centro = np.where(m, obs - med_col[None, :], 0.0)
            sigma1 = np.linalg.svd(centro, compute_uv=False)[0]
            z = np.zeros_like(obs)
            saida = []
            for fr in fracoes:
                lam = fr * sigma1
                for _ in range(60):
                    svds[0] += 1
                    preenchida = np.where(m, obs - med_col[None, :], z)
                    u, s, vt = np.linalg.svd(preenchida, full_matrices=False)
                    novo = (u * np.maximum(s - lam, 0.0)) @ vt
                    mudanca = np.linalg.norm(novo - z)
                    z = novo
                    if mudanca < 1e-4 * (np.linalg.norm(z) + 1e-12):
                        break
                saida.append(np.where(m, obs, np.clip(z + med_col[None, :], piso, teto)))
            return saida

        modos = ("quente", "frio") if n_lin * n_col <= 1200 else ("quente",)
        fracoes_soft = (0.5, 0.3, 0.2, 0.12, 0.07, 0.04, 0.02)

        def candidatos_fixos(m, inicio):
            # Candidatos que não dependem do k do Hard-Impute, do mais simples ao mais
            # complexo: médias (α = 0; 0,5; 1) e Soft-Impute (λ do maior ao menor).
            saida = [(("media", 0.0), modelo_medias(m, 0.0)),
                     (("media", 0.5), modelo_medias(m, 0.5)),
                     (("media", 1.0), inicio)]
            for fr, sol in zip(fracoes_soft, soft_impute(m, fracoes_soft)):
                saida.append((("soft", fr), sol))
            return saida

        def passo_rank(m, k, inicio, estado):
            # Hard-Impute de rank k: 'quente' parte da solução de k-1; 'frio' das médias.
            saida = []
            for modo in modos:
                if modo == "quente":
                    estado[0] = hard_impute(m, k, estado[0])
                    saida.append((("quente", k), estado[0]))
                else:
                    saida.append((("frio", k), hard_impute(m, k, inicio)))
            return saida

        def reconstruir(nome, m):
            # Roda o candidato escolhido de novo, com todos os valores conhecidos.
            if nome[0] == "media":
                return modelo_medias(m, nome[1])
            if nome[0] == "soft":
                return soft_impute(m, fracoes_soft[:fracoes_soft.index(nome[1]) + 1])[-1]
            inicio = modelo_medias(m)
            if nome[0] == "frio":
                return hard_impute(m, nome[1], inicio)
            x = inicio
            for r in range(1, nome[1] + 1):
                x = hard_impute(m, r, x)
            return x

        # ------------------------------------------------------------ 4. validacao_cruzada
        # 10 folds de 10% dos conhecidos (permutação fixa, sem seed); avaliamos 5.
        conhecidos = np.flatnonzero(msk)
        ordem = conhecidos[np.argsort((conhecidos * 2654435761) % 1000003)]
        n_folds, usar = 10, (5 if conhecidos.size <= 1500 else 2)
        folds = []
        for f in range(usar):
            validacao = ordem[f::n_folds]
            treino = msk.ravel().copy()
            treino[validacao] = False
            treino = treino.reshape(msk.shape)
            inicio = modelo_medias(treino)
            folds.append({"treino": treino, "validacao": validacao,
                          "reais": obs.ravel()[validacao], "inicio": inicio, "estado": [inicio]})

        # Guardamos as previsões de cada candidato nos valores escondidos de cada fold.
        # Assim dá para medir o erro de qualquer combinação de candidatos sem rodar de novo.
        nomes, previsoes = [], []

        def avaliar(listas_por_fold):
            for c in range(len(listas_por_fold[0])):
                nomes.append(listas_por_fold[0][c][0])
                previsoes.append([listas_por_fold[f][c][1].ravel()[folds[f]["validacao"]]
                                  for f in range(usar)])

        def erros_de(prev):
            return [np.mean((prev[f] - folds[f]["reais"]) ** 2) for f in range(usar)]

        avaliar([candidatos_fixos(fd["treino"], fd["inicio"]) for fd in folds])
        melhor, sem_melhora = min(np.median(erros_de(p)) for p in previsoes), 0
        for k in range(1, min(n_lin, n_col)):
            avaliar([passo_rank(fd["treino"], k, fd["inicio"], fd["estado"]) for fd in folds])
            # Parada no rank (6 sem melhora) e orçamento de tempo.
            atual = min(np.median(erros_de(previsoes[-1])), np.median(erros_de(previsoes[-2])))
            if atual < melhor:
                melhor, sem_melhora = atual, 0
            else:
                sem_melhora += 1
                if sem_melhora >= 6:
                    break
            if svds[0] * custo_svd > 300000:
                break

        # ------------------------------------------------------------ 5. escolher_ou_combinar
        # Mediana dos folds; entre os candidatos a até 5% do melhor, o mais simples.
        mediana = np.array([np.median(erros_de(p)) for p in previsoes])
        escolhido = int(np.flatnonzero(mediana <= mediana.min() * 1.05)[0])

        # Combinação (blending): média dos 3 melhores candidatos de famílias diferentes
        # (médias, soft, hard; quente e frio contam como hard),
        # com peso 1/erro, só se todos estiverem até 10% do melhor e se a combinação
        # errar menos que o escolhido nos próprios folds.
        ordem_c = np.argsort(mediana)
        grupo, familias = [], []
        for c in ordem_c:
            if mediana[c] > mediana.min() * 1.10 or len(grupo) == 3:
                break
            fam = "hard" if nomes[c][0] in ("quente", "frio") else nomes[c][0]
            if fam not in familias:
                grupo.append(int(c))
                familias.append(fam)
        if len(grupo) >= 2:
            pesos = np.array([1.0 / (mediana[c] + 1e-12) for c in grupo])
            pesos = pesos / pesos.sum()
            mistura = [sum(pesos[i] * previsoes[c][f] for i, c in enumerate(grupo)) for f in range(usar)]
            if np.median(erros_de(mistura)) < mediana[escolhido]:
                return sum(pesos[i] * reconstruir(nomes[c], msk) for i, c in enumerate(grupo))
        return reconstruir(nomes[escolhido], msk)

    # ---------------------------------------------------------------- 6. protecoes
    try:
        saida = np.array(algoritmo(), dtype=float)
        if saida.shape != obs.shape or not np.isfinite(saida).all():
            saida = modelo_medias(msk)
    except Exception:
        saida = modelo_medias(msk)
    if not np.isfinite(saida).all():
        saida = np.where(np.isfinite(saida), saida, 0.0)
    return np.where(msk, obs, saida)

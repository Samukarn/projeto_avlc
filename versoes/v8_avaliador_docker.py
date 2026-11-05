import numpy as np


def principal(observada, mascara):
    # Versão 7: v6 com orçamento de tempo recalibrado para matrizes até 40x40.
    # Candidatos (médias com α, James-Stein, Soft-Impute, Hard-Impute, PCA
    # regularizada) escolhidos ou combinados por validação cruzada.
    # Etapas (ver md/ARQUITETURA.md):
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

    def james_stein(m):
        # James-Stein (1961): a média de cada coluna tem ruído porque usa poucos valores.
        # Puxar todas para a média geral reduz o erro total (com 3 ou mais colunas).
        # Encolhe pelo fator B = 1 - (c - 3)·v / Σ(média_j - média geral)², onde v é a
        # variância de cada média. O mesmo vale para o desvio de cada linha.
        med_col, desvio_lin = medias(m)
        resid = obs - med_col[None, :]
        s2 = np.mean(resid[m] ** 2)
        n_por_col = np.maximum(m.sum(axis=0), 1)
        centro = med_col.mean()
        dispersao = np.sum((med_col - centro) ** 2)
        b_col = 0.0
        if n_col > 3 and dispersao > 0:
            b_col = max(0.0, 1.0 - (n_col - 3) * np.mean(s2 / n_por_col) / dispersao)
        med_js = centro + b_col * (med_col - centro)
        resid = obs - med_js[None, :]
        desvio_lin = np.array([resid[i, m[i]].mean() if m[i].any() else 0.0 for i in range(n_lin)])
        n_por_lin = np.maximum(m.sum(axis=1), 1)
        disp_lin = np.sum(desvio_lin ** 2)
        b_lin = 0.0
        if n_lin > 2 and disp_lin > 0:
            b_lin = max(0.0, 1.0 - (n_lin - 2) * np.mean(s2 / n_por_lin) / disp_lin)
        return np.where(m, obs, med_js[None, :] + b_lin * desvio_lin[:, None])

    def algoritmo():
        if msk.sum() < 10 or min(n_lin, n_col) < 2:
            return modelo_medias(msk)

        # ------------------------------------------------------------ 3. candidatos
        faixa = obs[msk].max() - obs[msk].min()
        piso, teto = obs[msk].min() - 0.5 * faixa, obs[msk].max() + 0.5 * faixa

        # Custo aproximado de uma SVD em microssegundos, para o orçamento de tempo.
        # Acima de 900 células (maiores que as públicas; o lote oficial vai até 40x40)
        # a estimativa é mais conservadora: medimos ~3x mais que a fórmula simples.
        # O orçamento também sobe, para compensar a estimativa maior sem perder qualidade.
        if n_lin * n_col <= 900:
            custo_svd = 15 + 0.001 * n_lin * n_col * min(n_lin, n_col)
            orcamento = 300000
        else:
            custo_svd = 30 + 0.003 * n_lin * n_col * min(n_lin, n_col)
            orcamento = 600000
        svds = [0]

        def decompor(x):
            # Mesmos vetores e valores singulares da SVD, mas pela matriz de Gram
            # (autovalores de X·Xᵀ no lado menor). Sai ~2x mais rápido que np.linalg.svd
            # nas matrizes do torneio, o que importa quando o avaliador roda emulado.
            transposta = x.shape[0] > x.shape[1]
            a = x.T if transposta else x
            autoval, vetores = np.linalg.eigh(a @ a.T)
            s = np.sqrt(np.maximum(autoval[::-1], 0.0))
            return a, vetores[:, ::-1], s, transposta

        def recompor(a, vetores, s, novos, transposta):
            # Monta a matriz com os mesmos vetores singulares e os valores 'novos'.
            r = len(novos)
            fator = np.where(s[:r] > 1e-12 * (s[0] + 1e-300), novos / np.maximum(s[:r], 1e-300), 0.0)
            v = vetores[:, :r]
            saida = v @ (fator[:, None] * (v.T @ a))
            return saida.T if transposta else saida

        def hard_impute(m, k, inicio, iteracoes=100):
            # SVD truncada no rank k e recoloca os conhecidos, até estabilizar.
            x = inicio
            for repeticao in range(iteracoes):
                svds[0] = svds[0] + 1  # o avaliador não aceita += em item de lista
                a, vetores, s, tr = decompor(x)
                aprox = np.clip(recompor(a, vetores, s, s[:k], tr), piso, teto)
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
            med_col, desvio_lin = medias(m)
            centro = np.where(m, obs - med_col[None, :], 0.0)
            sigma1 = np.linalg.svd(centro, compute_uv=False)[0]
            z = np.zeros_like(obs)
            saida = []
            for fr in fracoes:
                lam = fr * sigma1
                for repeticao in range(iter_soft):
                    svds[0] = svds[0] + 1  # o avaliador não aceita += em item de lista
                    preenchida = np.where(m, obs - med_col[None, :], z)
                    a, vetores, s, tr = decompor(preenchida)
                    novo = recompor(a, vetores, s, np.maximum(s - lam, 0.0), tr)
                    mudanca = np.linalg.norm(novo - z)
                    z = novo
                    if mudanca < 1e-4 * (np.linalg.norm(z) + 1e-12):
                        break
                saida.append(np.where(m, obs, np.clip(z + med_col[None, :], piso, teto)))
            return saida

        def pca_regularizada(m, k, inicio, iteracoes=100):
            # PCA iterativa regularizada (Josse e Husson, missMDA): como o Hard-Impute,
            # mas cada valor singular encolhe em σ²/σₖ, com σ² = variância do ruído
            # estimada pelos valores singulares que sobram. Sinal forte quase não muda;
            # o que é parecido com ruído encolhe muito.
            faltando = (~m).sum()
            gl = n_lin * n_col - faltando - n_col - k * (n_lin + n_col - k)
            if gl <= 0:
                return None
            x = inicio
            for repeticao in range(iteracoes):
                svds[0] = svds[0] + 1  # o avaliador não aceita += em item de lista
                centro = x.mean(axis=0)
                a, vetores, s, tr = decompor(x - centro)
                sigma2 = np.sum(s[k:] ** 2) / gl
                encolhido = np.maximum(s[:k] - sigma2 / np.maximum(s[:k], 1e-12), 0.0)
                aprox = np.clip(centro + recompor(a, vetores, s, encolhido, tr), piso, teto)
                novo = np.where(m, obs, aprox)
                mudanca = np.linalg.norm(novo - x)
                x = novo
                if mudanca < 1e-5 * (np.linalg.norm(x) + 1e-12):
                    break
            return x

        modos = ("quente", "frio") if n_lin * n_col <= 1200 else ("quente",)
        fracoes_soft = (0.5, 0.3, 0.2, 0.12, 0.07, 0.04, 0.02)
        # Em matrizes grandes, cada SVD custa mais: menos iterações por λ (o warm start
        # entre λ compensa) para caber no limite de 2 s.
        iter_soft = 60 if n_lin * n_col <= 5000 else 25

        def candidatos_fixos(m, inicio):
            # Candidatos que não dependem do k do Hard-Impute, do mais simples ao mais
            # complexo: James-Stein, médias (α = 0; 0,5; 1) e Soft-Impute (λ do maior
            # ao menor).
            saida = [(("js", 0), james_stein(m)),
                     (("media", 0.0), modelo_medias(m, 0.0)),
                     (("media", 0.5), modelo_medias(m, 0.5)),
                     (("media", 1.0), inicio)]
            for fr, sol in zip(fracoes_soft, soft_impute(m, fracoes_soft)):
                saida.append((("soft", fr), sol))
            return saida

        def passo_rank(m, k, inicio, estado):
            # Candidatos de rank k: Hard-Impute ('quente' parte da solução de k-1; 'frio'
            # das médias) e PCA regularizada (parte das médias).
            saida = []
            for modo in modos:
                if modo == "quente":
                    estado[0] = hard_impute(m, k, estado[0])
                    saida.append((("quente", k), estado[0]))
                else:
                    saida.append((("frio", k), hard_impute(m, k, inicio)))
            # A PCA regularizada é a mais cara: só em matrizes até 1200 células, onde
            # a escolha entre sinal e ruído é mais difícil e ela mais ajuda.
            rpca = pca_regularizada(m, k, inicio) if n_lin * n_col <= 1200 else None
            if rpca is not None:
                saida.append((("rpca", k), rpca))
            return saida

        def reconstruir(nome, m):
            # Roda o candidato escolhido de novo, com todos os valores conhecidos.
            if nome[0] == "js":
                return james_stein(m)
            if nome[0] == "media":
                return modelo_medias(m, nome[1])
            if nome[0] == "soft":
                return soft_impute(m, fracoes_soft[:fracoes_soft.index(nome[1]) + 1])[-1]
            inicio = modelo_medias(m)
            if nome[0] == "rpca":
                return pca_regularizada(m, nome[1], inicio)
            if nome[0] == "frio":
                return hard_impute(m, nome[1], inicio)
            x = inicio
            for r in range(1, nome[1] + 1):
                x = hard_impute(m, r, x)
            return x

        # Matrizes enormes (acima de 90 mil células, ~300x300): a validação não cabe em
        # 2 s. Usamos direto o Soft-Impute, que foi o melhor método em matrizes grandes.
        if n_lin * n_col > 90000:
            return soft_impute(msk, (0.5, 0.3, 0.2, 0.12, 0.07))[-1]

        # ------------------------------------------------------------ 4. validacao_cruzada
        # 10 folds de 10% dos conhecidos (permutação fixa, sem seed); avaliamos 5.
        conhecidos = np.flatnonzero(msk)
        ordem = conhecidos[np.argsort((conhecidos * 2654435761) % 1000003)]
        # Matrizes grandes têm muitos valores por fold: 2 folds (ou 1, acima de 20 mil
        # conhecidos) já dão uma medição estável e mantêm o tempo abaixo de 2 s.
        n_folds = 10
        usar = 5 if conhecidos.size <= 1500 else (2 if conhecidos.size <= 20000 else 1)
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
            antes = len(previsoes)
            listas = [passo_rank(fd["treino"], k, fd["inicio"], fd["estado"]) for fd in folds]
            # Só entram candidatos que existem em todos os folds (a PCA regularizada pode
            # não caber nos graus de liberdade de algum fold).
            # (sem all(): essa função não existe no ambiente do avaliador)
            nomes_comuns = [nome for nome, cand in listas[0]
                            if min([len([1 for n, c in l if n == nome]) for l in listas]) > 0]
            avaliar([[par for par in l if par[0] in nomes_comuns] for l in listas])
            if len(previsoes) == antes:
                break
            # Parada no rank (6 sem melhora) e orçamento de tempo.
            atual = min(np.median(erros_de(p)) for p in previsoes[antes:])
            if atual < melhor:
                melhor, sem_melhora = atual, 0
            else:
                sem_melhora += 1
                if sem_melhora >= 6:
                    break
            if svds[0] * custo_svd > orcamento:
                break

        # ------------------------------------------------------------ 5. escolher_ou_combinar
        # Mediana dos folds; entre os candidatos a até 5% do melhor, o mais simples.
        mediana = np.array([np.median(erros_de(p)) for p in previsoes])
        escolhido = int(np.flatnonzero(mediana <= mediana.min() * 1.05)[0])

        # Combinação (blending): média dos 3 melhores candidatos de famílias diferentes
        # (médias e James-Stein; soft; hard quente/frio; PCA regularizada),
        # com peso 1/erro, só se todos estiverem até 10% do melhor e se a combinação
        # errar menos que o escolhido nos próprios folds.
        ordem_c = np.argsort(mediana)
        grupo, familias = [], []
        for c in ordem_c:
            if mediana[c] > mediana.min() * 1.10 or len(grupo) == 3:
                break
            fam = {"quente": "hard", "frio": "hard", "js": "media"}.get(nomes[c][0], nomes[c][0])
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

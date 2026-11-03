import numpy as np


def principal(observada, mascara):
    # Versão 4 (reorganizada em etapas; ver ARQUITETURA.md):
    # preparar -> modelo_medias -> candidatos -> validacao_cruzada -> escolher -> protecoes

    # ---------------------------------------------------------------- 1. preparar
    obs = np.array(observada, dtype=float)
    msk = np.array(mascara, dtype=bool)
    n_lin, n_col = obs.shape

    # ---------------------------------------------------------------- 2. modelo_medias
    def modelo_medias(m):
        # Média da coluna + desvio médio da linha em relação a essas médias.
        # É o ponto de partida dos outros candidatos e a rede de segurança final.
        geral = obs[m].mean() if m.any() else 0.0
        med_col = np.array([obs[m[:, j], j].mean() if m[:, j].any() else geral for j in range(n_col)])
        resid = obs - med_col[None, :]
        desvio_lin = np.array([resid[i, m[i]].mean() if m[i].any() else 0.0 for i in range(n_lin)])
        chute = med_col[None, :] + desvio_lin[:, None]
        return np.where(m, obs, chute)

    def algoritmo():
        if msk.sum() < 10 or min(n_lin, n_col) < 2:
            return modelo_medias(msk)

        # ------------------------------------------------------------ 3. candidatos
        # Faixa plausível: sem regularização, o Hard-Impute pode "explodir" numa coluna
        # com poucos valores conhecidos. Limitar as previsões evita que isso domine tudo.
        faixa = obs[msk].max() - obs[msk].min()
        piso, teto = obs[msk].min() - 0.5 * faixa, obs[msk].max() + 0.5 * faixa

        # Custo aproximado de uma SVD em microssegundos (medido: 13 us em 10x10, 790 us
        # em 100x100). Serve para parar a busca antes de chegar perto do limite de 2 s.
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

        # O modo "frio" recomeça das médias a cada k e é o mais caro. Em matrizes
        # grandes (mais de 1200 células) há dados de sobra e só o "quente" cabe no tempo.
        modos = ("quente", "frio") if n_lin * n_col <= 1200 else ("quente",)

        def candidatos_fixos(m, inicio):
            # Candidatos que não dependem do rank. Uma ideia nova entra aqui como mais
            # um par (nome, solução). Ordem: do mais simples ao mais complexo.
            return [(("media", 0), inicio)]

        def passo_rank(m, k, inicio, estado):
            # Candidatos de rank k. 'quente' parte da solução de k-1 (guardada em
            # estado); 'frio' parte das médias.
            saida = []
            for modo in modos:
                if modo == "quente":
                    estado[0] = hard_impute(m, k, estado[0])
                    saida.append((("quente", k), estado[0]))
                else:
                    saida.append((("frio", k), hard_impute(m, k, inicio)))
            return saida

        def reconstruir(nome, m):
            # Roda o candidato escolhido de novo, agora com todos os valores conhecidos.
            modo, k = nome
            inicio = modelo_medias(m)
            if modo == "frio":
                return hard_impute(m, k, inicio)
            x = inicio
            for r in range(1, k + 1):
                x = hard_impute(m, r, x)
            return x

        # ------------------------------------------------------------ 4. validacao_cruzada
        # Folds: permutação fixa dos conhecidos (sem seed), 10 grupos; avaliamos 5.
        # Cada fold esconde só 10%: escondendo mais, o que sobra pode não bastar para o
        # rank verdadeiro e a validação passa a preferir k pequeno demais.
        conhecidos = np.flatnonzero(msk)
        ordem = conhecidos[np.argsort((conhecidos * 2654435761) % 1000003)]
        # Em matrizes grandes há muitos valores por fold e 2 folds já bastam.
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

        def erro(sol, fold):
            return np.mean((sol.ravel()[fold["validacao"]] - fold["reais"]) ** 2)

        def avaliar(listas_por_fold):
            # Recebe, para cada fold, a lista [(nome, solução), ...] e devolve
            # os nomes e a matriz de erros (candidato x fold).
            nomes = [nome for nome, _ in listas_por_fold[0]]
            tabela = [[erro(listas_por_fold[f][c][1], folds[f]) for f in range(usar)]
                      for c in range(len(nomes))]
            return nomes, tabela

        nomes, erros = avaliar([candidatos_fixos(fd["treino"], fd["inicio"]) for fd in folds])
        melhor, sem_melhora = np.median(erros[0]), 0
        for k in range(1, min(n_lin, n_col)):
            novos, linhas = avaliar([passo_rank(fd["treino"], k, fd["inicio"], fd["estado"]) for fd in folds])
            nomes += novos
            erros += linhas
            # Parada no rank: se 6 ranks seguidos não melhoram, ranks maiores
            # dificilmente vão ajudar. (Com 3, perdíamos matrizes em que o erro só cai
            # quando k chega no rank verdadeiro.)
            atual = min(np.median(erros[-1]), np.median(erros[-2]))
            if atual < melhor:
                melhor, sem_melhora = atual, 0
            else:
                sem_melhora += 1
                if sem_melhora >= 6:
                    break
            # Orçamento de tempo: estimativa do custo das SVDs já feitas.
            if svds[0] * custo_svd > 300000:
                break

        # ------------------------------------------------------------ 5. escolher
        # Mediana dos folds: um fold que "explodiu" não decide sozinho.
        # Entre os candidatos a até 5% do melhor, fica o mais simples (o primeiro).
        mediana = np.median(np.array(erros), axis=1)
        escolhido = nomes[int(np.flatnonzero(mediana <= mediana.min() * 1.05)[0])]
        if escolhido[0] == "media":
            return modelo_medias(msk)
        return reconstruir(escolhido, msk)

    # ---------------------------------------------------------------- 6. protecoes
    # Qualquer erro ou valor inválido cai no modelo de médias. No fim, os valores
    # visíveis voltam exatamente como vieram.
    try:
        saida = np.array(algoritmo(), dtype=float)
        if saida.shape != obs.shape or not np.isfinite(saida).all():
            saida = modelo_medias(msk)
    except Exception:
        saida = modelo_medias(msk)
    if not np.isfinite(saida).all():
        saida = np.where(np.isfinite(saida), saida, 0.0)
    return np.where(msk, obs, saida)

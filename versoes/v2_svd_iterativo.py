import numpy as np


def principal(observada, mascara):
    # Versão 2: SVD iterativo de rank k, com k escolhido por validação interna.
    obs = np.array(observada, dtype=float)
    msk = np.array(mascara, dtype=bool)
    n_lin, n_col = obs.shape

    def preencher_media(m):
        # Ponto de partida: média da linha + média da coluna - média geral.
        geral = obs[m].mean() if m.any() else 0.0
        med_col = np.array([obs[m[:, j], j].mean() if m[:, j].any() else geral for j in range(n_col)])
        med_lin = np.array([obs[i, m[i]].mean() if m[i].any() else geral for i in range(n_lin)])
        chute = med_lin[:, None] + med_col[None, :] - geral
        return np.where(m, obs, chute)

    def svd_iterativo(m, k, iteracoes=100):
        x = preencher_media(m)
        for _ in range(iteracoes):
            u, s, vt = np.linalg.svd(x, full_matrices=False)
            aprox = (u[:, :k] * s[:k]) @ vt[:k]
            novo = np.where(m, obs, aprox)
            if np.linalg.norm(novo - x) < 1e-6 * (np.linalg.norm(x) + 1e-12):
                x = novo
                break
            x = novo
        return x

    # Validação: esconde ~10% dos valores conhecidos e testa cada k (k = 0 é só a média).
    conhecidos = np.flatnonzero(msk)
    validacao = conhecidos[::10]
    msk_treino = msk.copy().ravel()
    msk_treino[validacao] = False
    msk_treino = msk_treino.reshape(msk.shape)
    reais = obs.ravel()[validacao]

    melhor_k, melhor_erro = 0, np.mean((preencher_media(msk_treino).ravel()[validacao] - reais) ** 2)
    for k in range(1, min(n_lin, n_col)):
        erro = np.mean((svd_iterativo(msk_treino, k).ravel()[validacao] - reais) ** 2)
        if erro < melhor_erro:
            melhor_k, melhor_erro = k, erro

    saida = preencher_media(msk) if melhor_k == 0 else svd_iterativo(msk, melhor_k)
    if not np.isfinite(saida).all():
        saida = preencher_media(msk)
    return saida

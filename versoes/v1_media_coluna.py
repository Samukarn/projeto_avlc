import numpy as np


def principal(observada, mascara):
    # Versão 1 (baseline): preenche cada célula oculta com a média da sua coluna.
    obs = np.array(observada, dtype=float)
    msk = np.array(mascara, dtype=bool)
    saida = obs.copy()

    media_geral = obs[msk].mean() if msk.any() else 0.0
    for j in range(obs.shape[1]):
        conhecidos = msk[:, j]
        media = obs[conhecidos, j].mean() if conhecidos.any() else media_geral
        saida[~conhecidos, j] = media

    return saida

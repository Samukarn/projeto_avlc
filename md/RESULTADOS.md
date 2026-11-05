# Resultados por versão

NRMSE médio (menor é melhor). Gerado por `python3 testar.py --tudo`; não edite à mão.

| Versão | Dados (públicos) | Dados sintéticos | Os dois juntos |
|---|:---:|:---:|:---:|
| v1_media_coluna | 0.906 | 0.722 | 0.752 |
| v2_svd_iterativo | 0.297 | 0.570 | 0.524 |
| v3_partida_residuo | 0.275 | 0.563 | 0.515 |
| v4_validacao_cruzada | 0.275 | 0.545 | 0.500 |
| v5_candidatos | 0.272 | 0.497 | 0.460 |
| v6_pesquisa | 0.254 | 0.490 | 0.450 |
| v7_ajuste_40 | 0.254 | 0.490 | 0.450 |
| v8_avaliador_docker | 0.254 | 0.490 | 0.450 |

Dados: 10 matrizes do banco público. Sintéticos: 50 matrizes de `gerar_sinteticas.py`. Os dois juntos: média de todas as matrizes.

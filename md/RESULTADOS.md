# Resultados por versão

NRMSE médio (menor é melhor). Gerado por `python3 testar.py --tudo`; não edite à mão.

| Versão | Dados (públicos) | Dados sintéticos | Os dois juntos |
|---|:---:|:---:|:---:|
| v1_media_coluna | 0.906 | 0.674 | 0.712 |
| v2_svd_iterativo | 0.297 | 0.439 | 0.415 |
| v3_partida_residuo | 0.275 | 0.435 | 0.408 |
| v4_validacao_cruzada | 0.275 | 0.425 | 0.400 |
| v5_candidatos | 0.272 | 0.403 | 0.382 |
| v6_pesquisa | 0.254 | 0.393 | 0.370 |

Dados: 10 matrizes do banco público. Sintéticos: 50 matrizes de `gerar_sinteticas.py`. Os dois juntos: média de todas as matrizes.

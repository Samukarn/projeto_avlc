# Relatório — Equipe [N]

Torneio de Álgebra Linear, CIN0138. Integrantes: [nomes].

## Problema

Recebemos matrizes numéricas em que parte das células está oculta. A função `principal(observada, mascara)` deve estimar essas células. A nota é o NRMSE nas células ocultas: RMSE dividido pelo desvio padrão. 0 é perfeito e 1 equivale a chutar a média.

## Método

1. **Modelo de médias.** Cada célula começa como a média da sua coluna mais o desvio médio da sua linha em relação às médias das colunas. Comparar cada valor com a própria coluna evita a distorção que aparece quando uma linha só tem valores conhecidos em colunas "altas".
2. **Hard-Impute.** Repetimos: aproximar a matriz pela SVD truncada de rank k e recolocar os valores conhecidos. O rank k é o número de "direções" que explicam os dados.
3. **Validação cruzada.** Para escolher k sem olhar o gabarito, escondemos 10% dos valores conhecidos (5 vezes, grupos diferentes), testamos cada candidato e medimos o erro nesses valores. Usamos a mediana dos 5 erros, e entre candidatos quase empatados (até 5%) ficamos com o mais simples.
4. **Vários candidatos.** Além do Hard-Impute, a validação também testa o modelo de médias com encolhimento (α ∈ {0; 0,5; 1}) e o Soft-Impute, que subtrai λ de todos os valores singulares em vez de cortá-los. Quando os melhores candidatos de famílias diferentes estão empatados (até 10%), combinamos as previsões com peso 1/erro.
5. **Métodos da literatura (v6).** O estimador de James-Stein encolhe as médias das colunas e das linhas em direção à média geral, com o fator dado por fórmula. A PCA iterativa regularizada (Josse e Husson) encolhe cada valor singular em σ²/σₖ, separando sinal de ruído.
6. **Proteções.** Previsões limitadas a uma faixa plausível, orçamento de tempo, `try/except` que cai no modelo de médias, e os valores visíveis devolvidos como vieram.

## Álgebra linear usada

- **Decomposição em valores singulares:** A = U Σ Vᵀ, com σ₁ ≥ σ₂ ≥ … ≥ 0.
- **Teorema de Eckart–Young:** A_k = Σᵢ₌₁..ₖ σᵢ uᵢ vᵢᵀ é a matriz de rank k mais próxima de A. Por isso, se os dados verdadeiros têm rank baixo, a SVD truncada recupera a estrutura e preenche os buracos.
- **Soft-Impute (norma nuclear):** S_λ(X) = U · diag(max(σᵢ − λ, 0)) · Vᵀ. É a solução do problema de completar a matriz penalizando a soma dos valores singulares, que é a versão "suave" de penalizar o rank.
- **James-Stein:** θ̂ⱼ = m̄ + B·(x̄ⱼ − m̄), com B = max(0, 1 − (c − 3)·v / Σ(x̄ⱼ − m̄)²). Encolher várias médias juntas reduz o erro total.
- **PCA regularizada:** σₖ → σₖ − σ²/σₖ, com σ² = variância do ruído estimada pelos valores singulares descartados.
- **Rank e graus de liberdade:** uma matriz n×m de rank k tem k(n+m−k) parâmetros. Com poucos valores conhecidos, um rank alto não pode ser determinado. É por isso que a validação não pode esconder dados demais.

## Resultados (banco público)

| Versão | Ideia | NRMSE médio |
|---|---|:---:|
| v1 | Média da coluna | 0,906 |
| v2 | Hard-Impute, k escolhido com 1 grupo de validação | 0,297 |
| v3 | Ponto de partida pelo resíduo da linha | 0,275 |
| v4 | Validação cruzada com vários folds e mediana | 0,275 (estável entre 0,274 e 0,278) |
| v5 | Médias com α, Soft-Impute e combinação | 0,272 (0,382 juntando com as sintéticas) |
| v6 | James-Stein e PCA regularizada | 0,254 (0,370 juntando com as sintéticas) |

Na v3, o 0,275 dependia de qual grupo era escondido: com outros grupos, o resultado ia até 0,365. A v4 chega ao mesmo número com qualquer sorteio.

As matrizes de rank baixo (como 09 e 10) ficam perto de 0. As matrizes 01 e 08 ficam perto de 1, porque parecem ser só ruído: não há estrutura para descobrir.

## Limitações

- Matrizes que são só ruído: nenhum método vai muito abaixo de 1.
- Matrizes acima de ~200×200 se aproximam de 1 s por matriz; o Docker pode ser mais lento que o nosso computador.

# Pesquisa: métodos para completar matrizes

Pesquisa feita em 03/11 para encontrar técnicas além das que já usamos. Cada método foi testado sozinho, com parâmetros fixos e sem a validação cruzada da v5, nos três conjuntos. O objetivo do teste é ver onde cada método é forte: os melhores entram na v6 como candidatos, e a validação decide quando usar cada um.

## Os métodos encontrados

### 1. James-Stein: encolher as médias das colunas para a média geral

Origem: Stein (1956), James e Stein (1961); interpretação de Bayes empírico por Efron e Morris (1973).

Ideia: a média de cada coluna é calculada com poucos valores, então tem ruído. Puxar todas as médias um pouco para a média geral reduz o erro total quando há 3 ou mais colunas. Esse é um resultado provado, não uma heurística. Quanto mais as médias diferem entre si (em relação ao ruído), menos se encolhe.

```
θ̂ⱼ = m̄ + B · (x̄ⱼ − m̄),   B = max(0, 1 − (c − 3) · v / Σⱼ (x̄ⱼ − m̄)²)
x̄ⱼ = média da coluna j,   m̄ = média das médias,   v = variância de cada média,   c = número de colunas
```

O mesmo vale para o desvio de cada linha. É a versão "com fórmula" do nosso α: em vez de testar α ∈ {0; 0,5; 1}, a fórmula calcula o encolhimento certo para cada matriz.

### 2. Limiar ótimo de Gavish e Donoho (2014)

Ideia: em vez de testar todos os k, uma fórmula diz quais valores singulares são sinal e quais são ruído. Com ruído desconhecido, o limiar é ω(β) vezes a mediana dos valores singulares, com β = linhas/colunas (≈ 2,858 · mediana para matriz quadrada).

### 3. PCA iterativa regularizada (Josse e Husson, missMDA)

Ideia: como o Hard-Impute, mas cada valor singular é encolhido em σ²/σₖ, onde σ² é a variância do ruído estimada pelos resíduos. Valores singulares grandes (sinal) quase não mudam; os pequenos encolhem muito. O pacote missMDA recomenda a versão regularizada justamente para evitar o superajuste quando há muitos valores faltando.

```
σₖ → σₖ − σ² / σₖ,   σ² = Σ_{k>K} σₖ² / (graus de liberdade)
```

### 4. OptShrink (Nadakuditi, 2014)

Encolhimento ótimo de cada valor singular, calculado pela teoria de matrizes aleatórias e sem parâmetros. O autor diz que nunca é pior que a SVD truncada e que vai melhor com ruído baixo a moderado. Não testamos ainda, porque a fórmula exige estimar uma transformada da distribuição dos valores singulares do ruído. Fica como possibilidade se a PCA regularizada funcionar bem.

### 5. KNNimpute (Troyanskaya et al., 2001) e LLSimpute (Kim, Golub e Park, 2005)

Clássicos da imputação em dados de microarray, avaliados com o mesmo NRMSE do torneio. O KNN estima cada linha pela média das K linhas mais parecidas. O LLS faz uma regressão da linha nas K linhas mais correlacionadas. Nos comparativos da área, o BPCA e o LLS costumam liderar, e o SVD simples fica por último.

### 6. Centralização dupla (biScale, pacote softImpute de Hastie)

Modelo X = αᵢ + βⱼ + baixo rank: tira média de linha e de coluna antes do Soft-Impute. Nosso ponto de partida da v3 já faz algo parecido (média da coluna + desvio da linha).

## Resultados dos testes (NRMSE médio, menor é melhor)

Cada método rodando sozinho, sem a validação cruzada:

| Método | Público | Sintéticas | Rank baixo | Ruído puro | Colunas constantes | Juntos |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| v5 (atual, com validação) | 0,272 | 0,403 | 0,298 | 1,020 | 0,056 | 0,382 |
| Médias da v3 | 0,619 | 0,693 | 0,737 | 1,059 | 0,057 | 0,681 |
| James-Stein | 0,603 | 0,668 | 0,716 | **1,004** | **0,056** | 0,658 |
| Hard + rank de Gavish-Donoho | 0,441 | 0,523 | 0,471 | 1,061 | 0,057 | 0,509 |
| PCA regularizada (Josse) | 0,401 | 0,630 | 0,551 | 1,336 | 0,064 | 0,592 |
| KNN de linhas | 0,530 | 0,595 | 0,571 | 1,102 | 0,060 | 0,585 |
| LLS | 0,527 | 0,848 | 0,864 | 1,417 | 0,069 | 0,794 |

Destaques por matriz do público:

| Matriz | v5 | Melhor método da pesquisa |
|:---:|:---:|---|
| 01 (ruído) | 1,292 | James-Stein: 1,209. Melhor até que a "trapaça" com os métodos antigos (1,234) |
| 05 | 0,113 | PCA regularizada: 0,060 |
| 08 (ruído) | 1,028 | James-Stein: 0,994 |

## Conclusões

- Nenhum método sozinho ganha da v5. Isso confirma a estratégia: o ganho vem de ter vários candidatos e deixar a validação escolher.
- O James-Stein é o melhor método conhecido para ruído puro (1,004, contra 1,020 da v5) e também ganha nas matrizes 1 e 8. É barato e tem fórmula fechada. **Entra na v6.**
- A PCA regularizada é muito forte em matrizes com estrutura e ruído: na matriz 5 cai de 0,113 para 0,060. Sozinha erra feio no ruído puro (1,336), mas a validação não vai escolhê-la ali. **Entra na v6.**
- O rank de Gavish-Donoho erra mais que a validação cruzada para escolher k, mas é instantâneo. Pode servir para limitar a busca de k e economizar tempo, sem decidir sozinho.
- KNN e LLS não acrescentam: são piores que os candidatos que já temos em todos os tipos.
- OptShrink: deixar para depois. Mais complexo de implementar e de defender, e a PCA regularizada já captura parte da ideia.

## Fontes

- Gavish e Donoho. [The Optimal Hard Threshold for Singular Values is 4/√3](https://arxiv.org/pdf/1305.5870), IEEE Trans. Inf. Theory, 2014.
- Nadakuditi. [OptShrink](https://arxiv.org/pdf/1306.6042), 2014; [página do autor](https://web.eecs.umich.edu/~rajnrao/optshrink).
- Josse e Husson. [Regularised PCA to denoise and visualise data](https://arxiv.org/pdf/1301.4649); [missMDA imputePCA](https://search.r-project.org/CRAN/refmans/missMDA/html/imputePCA.html); [código do missMDA](https://rdrr.io/cran/missMDA/src/R/MIPCA.R).
- Hastie. [softImpute biScale](https://search.r-project.org/CRAN/refmans/softImpute/html/biScale.html).
- Kim, Golub e Park. [Local least squares imputation](https://faculty.cc.gatech.edu/~hpark/papers/bth499.pdf), Bioinformatics, 2005; [llsImpute](https://rdrr.io/bioc/pcaMethods/man/llsImpute.html).
- [Robust imputation method for missing values in microarray data](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1892075/) (comparativo KNN, SVD, BPCA, LLS).
- Efron. [The Future of Indirect Evidence](https://arxiv.org/pdf/1012.1161) (James-Stein e Bayes empírico).
- Koren, Bell e Volinsky. [BellKor, Netflix Prize](https://www.asc.ohio-state.edu/statistics/statgen/joul_aut2009/BellKor.pdf); [Winning the Netflix Prize: A Summary](https://www.r-bloggers.com/2011/10/winning-the-netflix-prize-a-summary/).

O código dos testes está em `experimentos/pesquisa_metodos.py`.

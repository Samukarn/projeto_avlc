# Experimentos

Aqui ficam as ideias que testamos e que não entraram no `solucao.py`, com os números. Registrar o que não deu certo evita repetir testes e é material para a apresentação ("o que tentamos e por que não funcionou").

Formato: ideia, resultado, por que não entrou.

## Antes da v3

| Ideia | NRMSE público | Por que não entrou |
|---|:---:|---|
| Ponto de partida `med_col + 0,5·(med_lin − geral)` (encolher o desvio da linha) | 0,271 | Empata com o ponto de partida pelo resíduo (0,275) dentro do ruído. Fica como candidato da v5 (α ∈ {0; 0,5; 1}) em vez de regra fixa |
| Ponto de partida só com a média da coluna | 0,294 | Consertou a matriz 3, mas a 9 foi de 0,000 para 0,224 |
| Validar com um único grupo de 20% | 0,324 | A matriz 6 saltou para 0,52: a escolha de k com um só grupo é instável |
| Misturar (blend) os 3 melhores candidatos | 0,301 | Estragou as matrizes de rank exato: 09 foi para 0,106 e 10 para 0,068 |

## Durante a v4

| Ideia | Resultado | Por que não entrou |
|---|:---:|---|
| 5 folds de 20% | Público 0,339 | Sem 20% dos dados, as matrizes 5 e 10 ficam quase sem informação para o rank verdadeiro, e a validação escolhe k pequeno demais |
| Média dos erros dos folds (em vez de mediana) | Sintético 0,476 | Um fold em que o Hard-Impute "explode" domina a média |
| Cada fold vota no seu melhor k | Público 0,310 | Pior que a mediana |
| Parar a busca após 3 ranks sem melhora | Sintético 0,454 | Em algumas matrizes o erro só cai exatamente no rank verdadeiro |
| Só o modo quente (warm start) | Sintético 0,423 | Bom no público, pior nas sintéticas |
| Só o modo frio, 300 iterações | Sintético 0,399, pior tempo 1,9 s | Lento demais |
| Limitar k pelos graus de liberdade, k(n+m−k) | Sintético 0,407 | Não ajudou: os ranks acima do limite quase não eram escolhidos |
| 30 iterações em vez de 100 | Público 0,301 | Rápido, mas pior no público |

## Durante a v5

| Ideia | Resultado (misturado) | Por que não entrou |
|---|:---:|---|
| ALS regularizado (rank 1, 2, 4, 8; λ ∈ {1; 10}) como candidato | 0,3815, igual sem ele | Não acrescentou nada e deixou o público pior (0,2746 contra 0,2731) e mais lento. O Soft-Impute já é uma fatoração regularizada |
| Combinação tratando Hard quente e frio como famílias diferentes | 0,3815 | Misturava duas versões do mesmo método. Contar como uma família só deu 0,2724 no público contra 0,2746 |

## Durante a v7 (matrizes até 40x40)

Teste com 40 matrizes de 30×30 a 40×40 (rank, rank com ruído e ruído puro), o novo tamanho máximo do lote oficial.

| Ideia | Média | Pior tempo | Por que não entrou |
|---|:---:|:---:|---|
| v6 sem mudança | 0,4898 | 1,25 s | Referência. A estimativa de custo da SVD ficava ~3x abaixo do real acima de 900 células, então a trava de tempo deixava rodar demais |
| Hard frio e PCA regularizada até 1600 células (em vez de 1200) | 0,4932 | 1,50 s | Pior e mais lento |
| Orçamento 200 mil / 150 mil / 100 mil para todas as matrizes | 0,4975 / 0,4980 / 0,4980 | 0,88 / 0,88 / 0,52 s | Mais rápido, mas a busca parava antes do melhor k nas matrizes com ruído |
| Menos folds (3) a partir de 600, 800 ou 1000 conhecidos | 0,4766 a 0,4939 | 1,23 a 1,29 s | Não reduziu o pior tempo: o gargalo não era o número de folds |
| Custo recalibrado para todas as matrizes | 0,4980 | 0,62 s | O público piorou de 0,2545 para 0,2683: superestimava o custo das matrizes pequenas |
| Custo recalibrado e orçamento dobrado para todas | 0,4912 | 1,01 s | Bom no tamanho 30-40, mas as pequenas passaram a rodar 2x mais sem ganho |

O que entrou na v7: custo recalibrado e orçamento de 600 mil só acima de 900 células; abaixo disso, igual à v6.

Os números "sintético" da v4 vieram de um gerador anterior (60 matrizes, até 31×31). O gerador atual é o `gerar_sinteticas.py`.

## v8 — tempo no Docker emulado

| Tentativa | Público | Sintéticas | Pior tempo (Mac nativo) | Decisão |
|---|:---:|:---:|:---:|---|
| v7 sem mudança | 0,2545 | 0,4896 | 0,61 s (Docker: 2,05 s) | reprovou por tempo no Docker |
| Orçamento × 0,5 | 0,2722 | 0,4962 | 0,36 s | descartada, perde nota |
| Orçamento × 0,33 | 0,2925 | 0,5037 | 0,34 s | descartada |
| Orçamento × 0,25 | 0,3070 | 0,5079 | 0,22 s | descartada |
| SVDs empilhadas (5 folds numa chamada) | — | — | só 8% mais rápida | descartada |
| Decomposição pela matriz de Gram | 0,2545 | 0,4896 | 0,47 s (Docker: 1,31 s) | adotada |

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

Os números "sintético" da v4 vieram de um gerador anterior (60 matrizes, até 31×31). O gerador atual é o `gerar_sinteticas.py`.

# Plano do Projeto

Torneio de Álgebra Linear — CIN0138. Este documento registra o objetivo, as regras de trabalho e as decisões da equipe.

## Objetivo e métrica

Objetivo: 1º lugar no torneio.

Métrica: NRMSE médio nas células ocultas, medido pelo `testar.py` no banco público. Também conferimos nas matrizes sintéticas (`testar.py --sinteticas`), porque a nota oficial sai de um lote privado.

## Regra de aceitação de uma versão

Uma versão nova só substitui o `solucao.py` se cumprir as três condições:

1. O NRMSE médio cai em relação à versão anterior.
2. Nenhuma matriz com estrutura (NRMSE da versão anterior < 0,5) piora mais de 0,05.
3. A versão passa no `checar_regras.py`.

Para comparar duas versões: `python3 testar.py --comparar versoes/a.py versoes/b.py`.

## Estratégia escolhida

Gerar vários candidatos e deixar a validação cruzada escolher, matriz por matriz. Os candidatos são o modelo de médias (com encolhimento α), o Hard-Impute com vários k e o Soft-Impute com vários λ.

Por quê: as matrizes do torneio são variadas. Algumas têm rank baixo exato, onde o Hard-Impute vence, e outras são só ruído, onde vence quem fica perto da média. Nenhum método único ganha em todas. Os vencedores do Netflix Prize chegaram lá combinando um baseline de médias, fatoração de matriz com regularização e a mistura de vários modelos. Mazumder, Hastie e Tibshirani (2010) mostraram que o Soft-Impute erra menos que o Hard-Impute quando há ruído ou quando o rank não é conhecido. A validação cruzada é o que permite escolher sem olhar o gabarito.

## O que decidimos NÃO fazer

- Otimizar para matrizes específicas do banco público (por exemplo, "se for 8×8, faça X"). O lote privado é outro.
- Usar redes neurais.
- Usar bibliotecas proibidas.

## Arquitetura

Ver [ARQUITETURA.md](ARQUITETURA.md). Resumo: uma ideia nova vira só "mais um candidato" dentro do `solucao.py`.

## Roteiro

| Versão | Ideia | Situação |
|---|---|---|
| v1 | Média da coluna | Feita: 0,906 |
| v2 | Hard-Impute com k escolhido por um grupo de validação | Feita: 0,297 |
| v3 | Ponto de partida pelo resíduo da linha | Feita: 0,275 (mas dependia de sorte no sorteio) |
| v4 | Validação cruzada com vários folds, mediana, regra do mais simples | Feita: 0,275, estável entre 0,274 e 0,278 |
| v5 | Candidatos Soft-Impute e médias com α ∈ {0; 0,5; 1}, combinação ponderada por 1/erro (o que era a v6). ALS testado e retirado | Feita: 0,272 público, 0,382 misturado |
| v6 | James-Stein e PCA regularizada (vindos da pesquisa em md/PESQUISA.md), travas de tempo para matrizes grandes | Feita: 0,254 público, 0,370 misturado |
| v7 | Trava de tempo recalibrada para matrizes até 40×40 (aviso do monitor) | Feita: 0,254 público, pior tempo 2,18 s → 1,36 s |
| v8 | Aceita pelo avaliador oficial no Docker (sandbox, tempo emulado, nova normalização) | Feita |
| v9 | Candidatos de simetria/vizinhança | Próxima |

Datas:
- 10/11 e 12/11: aulas de acompanhamento. Levar as perguntas em aberto.
- 18/11: congelamento. Depois disso, só correções.
- 20/11, 23:59: entrega do `Grupo[N].zip`, com 1 dia de folga.
- 29/11: classificados. 03/12: apresentação.

## Papéis

| Papel | Responsável | O que faz |
|---|---|---|
| Algoritmo | | Escreve as versões novas |
| Validação | | Matrizes sintéticas, Docker, `checar_regras.py` |
| Documentação | | Relatório, apresentação, diário |

Todos precisam entender o algoritmo inteiro. Na Etapa 2, os monitores fazem perguntas a cada membro sobre autoria e domínio do código.

## Perguntas em aberto

| Pergunta | Responsável | Resposta |
|---|---|---|
| O NRMSE final é a média dos NRMSE por matriz ou um RMSE agregado de todas? | | |
| O desvio padrão é o dos valores ocultos ou o da matriz inteira? | | |
| Existe tamanho máximo para as matrizes do lote privado? | | Sim: ordem até 40 (monitor no Discord, 03/11) |
| Como ficou a nova normalização do erro (monitor, 03/11)? | | Respondida na v8: desvio padrão dos ocultos, com piso de 5% da amplitude e teto de 10 |

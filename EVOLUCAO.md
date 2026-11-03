# Nossa Evolução

Torneio de Álgebra Linear — CIN0138.
Diário do que tentamos, do que funcionou e do que aprendemos.

---

## O desafio

Recebemos matrizes com buracos e precisamos adivinhar os valores que faltam usando álgebra linear.

A nota é o NRMSE (erro normalizado). Quanto menor, melhor:

| NRMSE | Significa |
|:---:|---|
| 0 | Acerto perfeito |
| 0,5 | Bom: o método captura a estrutura |
| 1 | Igual a chutar a média |
| > 1 | Pior que chutar a média |

---

## Linha do tempo

| Versão | Ideia | NRMSE médio | Arquivo |
|:---:|---|:---:|---|
| v1 | Média da coluna | 0,906 | `versoes/v1_media_coluna.py` |
| v2 | SVD iterativo com k automático | 0,297 | `versoes/v2_svd_iterativo.py` |

Resultado por matriz:

| Matriz | v1 | v2 |
|:---:|:---:|:---:|
| 01 | 1,368 | 1,258 |
| 02 | 1,163 | 0,049 |
| 03 | 0,074 | 0,307 |
| 04 | 0,873 | 0,038 |
| 05 | 0,900 | 0,139 |
| 06 | 1,054 | 0,042 |
| 07 | 1,027 | 0,089 |
| 08 | 1,015 | 1,036 |
| 09 | 0,859 | 0,000 |
| 10 | 0,730 | 0,011 |

---

## v1 — Média da coluna

Ideia: cada buraco recebe a média da sua coluna.

Resultado: 0,906, quase o mesmo que chutar.

O que aprendemos:
- A média ignora a relação entre linhas e colunas.
- A matriz 1 é só ruído em torno de 50 e não tem padrão para descobrir. Nenhum método vai bem nela.
- Na matriz 3 as colunas são quase constantes, então a média já acerta.

---

## v2 — SVD iterativo com k automático

Ideia:
1. Preencher os buracos com média da linha + média da coluna − média geral.
2. Calcular a SVD (A = U Σ Vᵀ) e manter só os k maiores valores singulares. Isso gera a melhor aproximação de rank k.
3. Devolver os valores conhecidos aos seus lugares.
4. Repetir até estabilizar.

Para escolher k, escondemos 10% dos valores conhecidos, testamos todos os k e ficamos com o que erra menos nesses valores. Assim o método se adapta a qualquer matriz, sem decorar o banco público.

Resultado: 0,297, três vezes melhor que a v1. As matrizes 9 e 10 ficaram quase perfeitas porque têm rank baixo de verdade. O tempo total foi de 0,37 s, bem abaixo do limite.

O que aprendemos:
- A estrutura de rank baixo é o que torna os buracos previsíveis.
- A matriz 3 piorou (de 0,07 para 0,31). Suspeita: o ponto de partida "linha + coluna" ou a validação com poucos valores (é a menor matriz) escolheu um k ruim.
- As matrizes 1 e 8 continuam perto de 1: parecem ser ruído sem estrutura.

Próximos passos possíveis:
- Testar se a média só da coluna como ponto de partida recupera a matriz 3.
- Soft-Impute (encolher os valores singulares em vez de cortar) para matrizes ruidosas.
- Validação mais robusta: repetir com vários grupos de valores escondidos.

---

<!-- Modelo para copiar:

## vN — Título

Ideia:
Resultado:
O que aprendemos:
Próximos passos:

-->

## Para estudar antes da apresentação

- O que é rank e por que ele ajuda a completar a matriz?
- O que significam U, Σ e Vᵀ na SVD?
- Por que devolvemos os valores conhecidos a cada iteração?
- Como escolhemos k sem decorar o banco público?

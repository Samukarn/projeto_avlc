# Evolução da Equipe — Torneio de Álgebra Linear (CIN0138)

Este diário registra cada versão do algoritmo: a ideia, a álgebra linear por trás dela, o resultado e o que aprendemos. Ele serve de roteiro para a apresentação da Etapa 2 (03/12): até 10 minutos de apresentação e cerca de 5 minutos de perguntas para cada membro.

## O problema

Recebemos uma matriz `observada` com células ocultas e uma `mascara` (`True` = conhecido). Precisamos estimar as células ocultas. A métrica é o **NRMSE**: o RMSE calculado só nas posições ocultas, dividido pelo desvio padrão. Quanto menor, melhor. Um NRMSE de cerca de 1,0 equivale a "chutar a média".

**Restrições:** só `numpy`, `scipy`, `math` e `random`. Limite de 2 s por matriz e 25 s por lote. Não pode usar `class` nem `seed`.

## Banco público (o que observamos)

| Matriz | Dimensão | % visível |
|---|---|---|
| 01 | 8×8 | 84% |
| 02 | 9×6 | 87% |
| 03 | 6×9 | 74% |
| 04 | 14×5 | 87% |
| 05 | 14×7 | 83% |
| 06 | 16×16 | 73% |
| 07 | 18×22 | 74% |
| 08 | 17×17 | 66% |
| 09 | 24×19 | 65% |
| 10 | 28×31 | 59% |

---

## Quadro de versões

| Versão | Data | Ideia | NRMSE médio (local) | NRMSE (avaliador Docker) |
|---|---|---|---|---|
| v1 | 03/11 | Média da coluna | 0,9060 | — |

---

## v1 — Baseline: média da coluna (03/11)

**Ideia:** cada célula oculta recebe a média dos valores conhecidos da sua coluna.

**Álgebra linear:** é a estimativa mais simples, que trata cada coluna como uma variável independente. Ela ignora qualquer relação entre linhas e colunas, ou seja, não usa a estrutura da matriz.

**Resultado:** NRMSE médio de **0,9060**. A matriz 03 foi muito bem (0,07). As matrizes 01 e 02 ficaram acima de 1, piores que a média global.

**O que aprendemos:** a média não basta. Na matriz 03 as colunas devem ser quase constantes. Nas outras, existe estrutura que a média não captura.

**Próximo passo:** explorar o **rank** das matrizes. Se a matriz tem rank baixo, as linhas são combinações de poucas "linhas-base", e dá para usar SVD truncada para reconstruir os valores ocultos.

---

<!-- Modelo para novas versões:

## vN — Título (dd/mm)

**Ideia:**
**Álgebra linear:**
**Resultado:**
**O que aprendemos:**
**Próximo passo:**
-->

## Possíveis perguntas da banca (para estudarmos)

- O que é o rank de uma matriz e por que ele importa para completar valores?
- O que a SVD decompõe (U, Σ, Vᵀ) e o que significa truncá-la?
- Por que reimpor os valores conhecidos a cada iteração?
- Como vocês escolheram o rank / parâmetros sem "decorar" o banco público?
- Por que o NRMSE divide pelo desvio padrão?

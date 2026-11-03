# Arquitetura do solucao.py

Tudo fica dentro de `principal(observada, mascara)`, como a regra exige. O código é dividido em 6 etapas fixas, marcadas com comentários numerados:

```
  observada, mascara
          |
  1. preparar            converte para numpy, guarda dimensões
          |
  2. modelo_medias       média da coluna + desvio da linha (ponto de partida e rede de segurança)
          |
  3. candidatos          candidatos_fixos (médias α=0/0,5/1, Soft-Impute com 7 λ)  +  passo_rank (Hard-Impute quente/frio de rank k)
          |
  4. validacao_cruzada   10 folds de 10% dos conhecidos (avalia 5); erro de cada candidato em cada fold
          |              parada no rank (6 sem melhora) e orçamento de tempo
  5. escolher_ou_combinar  mediana dos folds; entre os que ficam a 5% do melhor, o mais simples;
          |              combina até 3 famílias empatadas (10%) se a mistura errar menos;
          |              reconstruir: roda o(s) escolhido(s) de novo com todos os dados
  6. protecoes           try/except -> modelo de médias; NaN/Inf -> modelo de médias;
          |              visíveis devolvidos exatamente como vieram
      matriz completa
```

## Como adicionar uma ideia nova

Uma ideia nova vira só "mais um candidato":

- Se ela não depende do rank (por exemplo, Soft-Impute com um λ, ou médias com outro α), acrescente um par `(nome, solução)` em `candidatos_fixos`.
- Se ela depende do rank k, acrescente em `passo_rank`.
- Ensine `reconstruir` a rodar o candidato novo com todos os dados.

A validação cruzada e a escolha não precisam mudar. Os candidatos ficam em ordem do mais simples ao mais complexo, porque a regra dos 5% escolhe o primeiro da lista entre os empatados.

## Por que essas proteções

- Faixa plausível (`piso`, `teto`): sem regularização, o Hard-Impute pode explodir numa coluna com poucos valores conhecidos.
- Orçamento de tempo: o limite é 2 s por matriz, e o lote privado pode ter matrizes maiores que as públicas.
- `try/except`: qualquer exceção desclassifica a equipe. Com ele, o pior caso vira só "chutar a média".

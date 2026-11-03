# projeto_avlc

Torneio de Álgebra Linear (CIN0138): completar matrizes com valores ocultos usando álgebra linear.

## Comece aqui

Depois de clonar, rode estes 3 comandos:

```bash
python3 testar.py
python3 gerar_sinteticas.py
python3 checar_regras.py solucao.py
```

O primeiro mostra o NRMSE da solução atual no banco público (hoje 0,275). O segundo cria as matrizes sintéticas em `dados_sinteticos/`. O terceiro confere as regras do torneio.

## Mapa dos arquivos

| Arquivo | Para que serve |
|---|---|
| `solucao.py` | A função `principal(observada, mascara)`. É o arquivo que vai no zip de entrega |
| `versoes/` | Cada versão salva separadamente (v1, v2, ...) |
| `testar.py` | NRMSE e tempo por matriz. `--sinteticas` usa as sintéticas; `--comparar a.py b.py` compara duas versões; `--tudo a.py b.py` mostra público, sintéticas por tipo e misturado. Grava `resultados.csv` |
| `gerar_sinteticas.py` | Gera ~50 matrizes de teste (rank baixo, ruído, colunas constantes) |
| `checar_regras.py` | Confere imports, `class`, `seed`, funções fora de `principal`, casos extremos e tempo |
| `resultados.csv` | Histórico de resultados por versão e matriz |
| `dados/` | Banco público: observada, mascara e gabarito |
| `PLANO.md` | Objetivo, regra de aceitação, estratégia, roteiro, papéis |
| `ARQUITETURA.md` | Como o `solucao.py` está organizado e como acrescentar uma ideia |
| `EVOLUCAO.md` | Diário da equipe, base da apresentação |
| `RELATORIO.md` | Rascunho do relatório de entrega |
| `experimentos/` | Ideias testadas que não funcionaram, com os números |

O teste oficial é o avaliador Docker (`docker compose up` no pacote do Classroom, depois http://localhost:8501).

## Fluxo de trabalho com Git

- Um branch por versão, por exemplo `v5-soft-impute`.
- O `main` tem sempre uma versão que pode ser entregue.
- Antes de abrir um Pull Request:
  1. `python3 testar.py`
  2. `python3 testar.py --sinteticas`
  3. `python3 checar_regras.py solucao.py`
  4. Atualizar o `EVOLUCAO.md`.
- Todo Pull Request é revisado e aprovado por outro integrante antes do merge. Quem revisa precisa entender a mudança, o que já é treino para a defesa da Etapa 2.
- A regra para uma versão nova entrar está no [PLANO.md](PLANO.md).

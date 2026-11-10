# Projeto de AVLC

Torneio de Álgebra Linear (CIN0138): completar matrizes com valores ocultos usando álgebra linear.

## Equipe (Grupo 4)

- Davi Marcelo Maikel Pedrosa
- Luiz Miguel de Oliveira Siqueira
- Samuel Renan Mendes Umbelino do Monte

## Estado atual

Versão v8 (`v8_avaliador_docker`), NRMSE médio (fonte: `md/RESULTADOS.md`):
- Públicas: 0.254
- Sintéticas: 0.490
- Os dois juntos: 0.450

## Requisitos

- Python 3
- NumPy e SciPy (instalação: `pip install numpy scipy`)

## Comece aqui

Depois de clonar, rode estes 3 comandos (no Windows, use `python` ou `py` no lugar de `python3`):

```bash
python3 testar.py
python3 gerar_sinteticas.py
python3 checar_regras.py solucao.py
```

O primeiro mostra o NRMSE da solução atual no banco público. O segundo cria as matrizes sintéticas em `dados_sinteticos/`. O terceiro confere as regras do torneio.

## Avaliador oficial (Docker)

1. Baixar o `.zip` do Classroom e extrair.
2. Na pasta extraída, rodar `docker compose up`.
3. Abrir http://localhost:8501 no navegador.
4. Enviar o `solucao.py`.
5. Para parar: `Ctrl+C` e `docker compose down`.

## Entrega da Etapa 1

Prazo: **20/11 (sexta), 23:59**, pelo Classroom. Só um integrante envia e deixa os nomes de todos em comentário particular na postagem.

Conteúdo do zip (arquivos soltos na raiz, sem pasta dentro):

```text
Grupo4.zip
├── solucao.py      # função principal(observada, mascara), código final
└── relatorio.pdf   # relatório curto e explicativo do algoritmo
```

Não entram no zip: `versoes/`, `experimentos/`, `dados/`, `testar.py`, `gerar_sinteticas.py`, `checar_regras.py`, `resultados.csv`, o README e nada do avaliador.

## Mapa dos arquivos

| Arquivo | Para que serve |
|---|---|
| `solucao.py` | A função `principal(observada, mascara)`. É o arquivo que vai no zip de entrega |
| `versoes/` | Cada versão salva separadamente (v1, v2, ...) |
| `testar.py` | NRMSE e tempo por matriz. `--sinteticas` usa as sintéticas; `--comparar a.py b.py` compara duas versões; `--tudo a.py b.py` mostra público, sintéticas por tipo e misturado. Grava `resultados.csv` |
| `gerar_sinteticas.py` | Gera ~50 matrizes de teste (rank baixo, ruído, colunas constantes) |
| `checar_regras.py` | Confere imports, `class`, `seed`, funções fora de `principal`, casos extremos e tempo |
| `md/RESULTADOS.md` | Resumo: NRMSE médio por versão nos dados públicos, sintéticos e nos dois juntos |
| `resultados.csv` | Histórico de resultados por versão e matriz |
| `dados/` | Banco público: observada, mascara e gabarito |
| `md/PLANO.md` | Objetivo, regra de aceitação, estratégia, roteiro, papéis |
| `md/ARQUITETURA.md` | Como o `solucao.py` está organizado e como acrescentar uma ideia |
| `md/EVOLUCAO.md` | Diário da equipe, base da apresentação |
| `md/PESQUISA.md` | Pesquisa de métodos (James-Stein, Gavish-Donoho, PCA regularizada, KNN, LLS) com fontes e testes |
| `md/RELATORIO.md` | Rascunho do relatório de entrega |
| `experimentos/` | Ideias testadas que não funcionaram, com os números |

## Fluxo de trabalho com Git

- Uma branch por versão, por exemplo `v5-soft-impute`.
- O `main` tem sempre uma versão que pode ser entregue.
- Antes de abrir um Pull Request:
  1. `python3 testar.py`
  2. `python3 testar.py --sinteticas`
  3. `python3 checar_regras.py solucao.py`
  4. Atualizar o `md/EVOLUCAO.md`.
- Todo Pull Request é revisado e aprovado por outro integrante antes do merge. Quem revisa precisa entender a mudança, o que já é treino para a defesa da Etapa 2.
- A regra para uma versão nova entrar está no [md/PLANO.md](md/PLANO.md).

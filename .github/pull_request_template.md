## O que muda

<!-- Uma ou duas frases: qual ideia esta versão testa e por quê. -->

## Resultados

| | Antes | Depois |
|---|:---:|:---:|
| NRMSE médio, banco público | | |
| NRMSE médio, sintéticas | | |
| Tempo máximo por matriz | | |

Comparação por matriz: cole a saída de `python3 testar.py --comparar versoes/anterior.py versoes/nova.py`.

## Checklist

- [ ] `python3 testar.py` rodou e a média caiu
- [ ] `python3 testar.py --sinteticas` rodou e a média não piorou
- [ ] Nenhuma matriz com estrutura (NRMSE anterior < 0,5) piorou mais de 0,05
- [ ] `python3 checar_regras.py solucao.py` deu "Tudo OK"
- [ ] Versão salva em `versoes/vN_nome.py`
- [ ] `EVOLUCAO.md` atualizado (ideia, resultado, aprendizado)
- [ ] Ideias que não funcionaram registradas em `experimentos/`

## Revisão

Quem revisa precisa conseguir explicar a mudança com as próprias palavras. Isso também é treino para a apresentação.

# 📈 Nossa Evolução

> Torneio de Álgebra Linear — CIN0138
> Diário do que tentamos, do que funcionou e do que aprendemos.

---

## 🎯 O desafio em uma frase

Recebemos matrizes com **buracos** e precisamos **adivinhar os valores que faltam** usando álgebra linear.

**Como medimos:** NRMSE (erro normalizado). Quanto **menor**, melhor.

| NRMSE | Significa |
|:---:|---|
| **0** | 🏆 Acerto perfeito |
| **0,5** | 👍 Bom: o método captura a estrutura da matriz |
| **1** | 😐 Igual a chutar a média |
| **> 1** | 👎 Pior que chutar a média |

---

## 🗺️ Linha do tempo

| Versão | Ideia | NRMSE médio |
|:---:|---|:---:|
| v1 | Média da coluna | **0,906** |
| v2 | *(em breve)* SVD iterativo | — |

---

## v1 · Média da coluna

💡 **Ideia:** cada buraco recebe a média da sua coluna.

📊 **Resultado:** 0,906, praticamente o mesmo que chutar.

🧠 **O que aprendemos:**
- A média ignora a relação entre linhas e colunas. Ela não enxerga a estrutura da matriz.
- **Matriz 1 (NRMSE 1,37):** é só ruído em torno de 50 e não há padrão para descobrir. Nenhum método vai muito bem nela, e está tudo bem.
- **Matriz 3 (0,07):** as colunas são quase constantes, então a média já acerta.

➡️ **Próximo passo:** usar o **rank** das matrizes. Se elas têm poucas "direções" importantes, a SVD consegue reconstruir os buracos.

---

<!-- 📋 Modelo para copiar:

## vN · Título

💡 **Ideia:**
📊 **Resultado:**
🧠 **O que aprendemos:**
➡️ **Próximo passo:**

-->

## ❓ Para estudar antes da apresentação

- O que é **rank** e por que ele ajuda a completar a matriz?
- O que significam **U, Σ e Vᵀ** na SVD?
- Por que devolvemos os valores conhecidos a cada iteração?
- Como escolhemos os parâmetros sem "decorar" o banco público?

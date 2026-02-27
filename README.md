# 🔀 QuizRandomShuffle — Gerador de Versões de Prova $\LaTeX$

Código em Python para gerar múltiplas versões embaralhadas de uma prova em formato $\LaTeX$, a partir de um arquivo-base `.tex` com questões de múltipla escolha e/ou verdadeiro/falso.


## 📋 Descrição

O **QuizRandomShuffle** recebe um arquivo-base de questões (ex.: `P1A.tex`) e produz automaticamente N versões com a ordem das questões e/ou as alternativas de múltipla escolha embaralhadas. O gabarito é preservado: o marcador `\di` acompanha a alternativa correta independentemente da posição em que ela for sorteada. Questões Verdadeiro/Falso nunca têm suas alternativas reordenadas.

Para evitar provas com o gabarito concentrado em uma única posição, o sistema aplica uma restrição configurável de gabaritos consecutivos: se a restrição não puder ser satisfeita de imediato, novas permutações são tentadas automaticamente.

O sistema foi projetado para funcionar em conjunto com o _template_ LaTeX Para Provas Com Gabarito, disponível em [https://github.com/wyllianbs/carderno_prova](https://github.com/wyllianbs/carderno_prova).


## ✨ Características

- ✅ **Embaralhamento da ordem das questões** entre versões.
- ✅ **Embaralhamento das alternativas** de múltipla escolha com preservação do gabarito (`\di`).
- ✅ **Questões V/F intocadas** — alternativas V. e F. nunca são reordenadas.
- ✅ **Restrição de gabaritos consecutivos** — evita sequências longas da mesma posição de resposta.
- ✅ **Sufixo automático** — versões nomeadas sequencialmente a partir da letra informada (`P1B.tex`, `P1C.tex`, …).
- ✅ **Preservação de cabeçalho e rodapé** do arquivo-base.
- ✅ **Não modifica** o arquivo original (apenas o lê).
- ✅ **Arquitetura POO** (Orientação a Objetos).


## 📁 Estrutura do Projeto

```
.
├── QuizRandomShuffle.py   # Script principal
├── P1A.tex          # Arquivo-base (fornecido pelo usuário)
├── P1B.tex          # Versão 1 gerada (saída)
├── P1C.tex          # Versão 2 gerada (saída)
└── README.md        # Este arquivo
```

Os arquivos gerados são gravados no mesmo diretório do arquivo-base.


## 🚀 Instalação

### Requisitos

- **Python 3.8+**
- **Linux** (testado no SO Linux, distro Debian Trixie).
- Bibliotecas padrão Python (não requer instalação de pacotes externos).

### Clone o repositório

```bash
git clone https://github.com/wyllianbs/QuizRandomShuffle.git
cd QuizRandomShuffle
```


## 📖 Como Usar

### Execução Básica

```bash
python3 QuizRandomShuffle.py
```

### Fluxo de Uso

1. **Arquivo-base**: Informe o caminho do `.tex` de entrada (default: `P1A.tex`).
2. **Número de versões**: Quantas versões embaralhadas gerar (default: `2`).
3. **Letra inicial do sufixo**: Define a partir de qual letra os arquivos de saída serão nomeados — ex.: `B` gera `P1B.tex`, `P1C.tex`, … (default: letra seguinte à do arquivo-base).
4. **Embaralhar questões**: Se a ordem das questões deve ser aleatorizada (default: `S`).
5. **Embaralhar alternativas**: Se as alternativas de múltipla escolha devem ser reordenadas (default: `S`).
6. **Máximo de gabaritos consecutivos**: Limite de vezes que a mesma posição de resposta pode aparecer em sequência (default: `3`).

### Exemplo de Execução

```
python3 QuizRandomShuffle.py

=======================================================
  QuizRandomShuffle — Gerador de Versões de Prova LaTeX
=======================================================

Caminho do arquivo-base [padrão: P1A.tex]:
Número de versões a gerar [padrão: 2]:
Letra inicial do sufixo (ex.: B → gera P1B.tex, ...) [padrão: B]:
Embaralhar a ordem das questões (S/n) [padrão: s]:
Embaralhar alternativas de múltipla escolha (S/n) [padrão: s]:
Máximo de gabaritos consecutivos na mesma posição [padrão: 3]: 2

[INFO] Carregando: P1A.tex
[INFO] Questões encontradas: 6 (4 múltipla escolha, 2 V/F)

[VERSÃO 1/2] → P1B.tex
  [INFO] Embaralhando alternativas de múltipla escolha...
  [INFO] Embaralhando ordem das questões...
  [OK] Arquivo gravado: /home/user/QuizRandomShuffle/P1B.tex

[VERSÃO 2/2] → P1C.tex
  [INFO] Embaralhando alternativas de múltipla escolha...
  [INFO] Embaralhando ordem das questões...
  [INFO] Restrição satisfeita na tentativa 2.
  [OK] Arquivo gravado: /home/user/QuizRandomShuffle/P1C.tex

[CONCLUÍDO] Todas as versões foram geradas.
```

> **Nota sobre sufixo automático**: o default da letra inicial é inferido a partir do arquivo-base — se o arquivo-base é `P1A.tex`, o default sugerido é `B`.


## 📝 Formato das Questões `.tex`

O QuizRandomShuffle utiliza exatamente o mesmo formato de questões do ExamForge [https://github.com/wyllianbs/ExamForge](https://github.com/wyllianbs/ExamForge). Cada questão é delimitada por um bloco `{% ID ... }` contendo o marcador `\rtask`. O cabeçalho e o rodapé do arquivo (tudo antes da primeira questão e depois da última) são preservados integralmente nas versões geradas.

### Questão de Múltipla Escolha

As alternativas são embaralhadas. O marcador `\di` identifica a alternativa correta e acompanha o texto correto na nova posição:

```latex
{% Q1383489[49D]
\needspace{8\baselineskip}
\item \rtask \ponto{\pt}
Assinale a opção abaixo que contém SOMENTE informações CORRETAS.

\begin{answerlist}[label={\texttt{\Alph*}.},leftmargin=*]
    \ti Python 3 possui retrocompatibilidade total com Python 2.
    \ti Python 3 não é compatível com strings Unicode.
    \ti \lstinline[style=Python]|count(d)| retorna o número de elementos do dict.
    \di Dicionários em Python 3 preservam a ordem de inserção.
    \ti Utiliza-se \lstinline[style=Python]|array.add(x)| para adicionar x a array.
\end{answerlist}
}
```

- `\ti` — alternativa **incorreta**.
- `\di` — alternativa **correta** (gabarito). Segue o conteúdo correto após o embaralhamento.

### Questão Verdadeiro/Falso

As alternativas **não são embaralhadas**. O QuizRandomShuffle detecta automaticamente o padrão V/F pela presença de `\ti[V.]`, `\ti[F.]`, `\doneitem` ou `\ifnum\gabarito`:

```latex
{% Q3258082
\needspace{7\baselineskip}
\item \rtask \ponto{\pt}
Julgue o próximo item.

Em Python, listas podem ser preenchidas por qualquer tipo de objeto, porém
a quantidade de objetos só poderá ser alterada durante a criação delas.

% F
{\setlength{\columnsep}{0pt}\renewcommand{\columnseprule}{0pt}
\begin{multicols}{2}
\begin{answerlist}[label={\texttt{\Alph*}.},leftmargin=*]
    \ti[V.]
    \ifnum\gabarito=1\doneitem[F.]\else\ti[F.]\fi % gabarito
\end{answerlist}
\end{multicols}
}
}
```


## 🎯 Lógica de Embaralhamento

### Alternativas de múltipla escolha
Cada alternativa é representada internamente como um par `(marcador, conteúdo)`. O marcador `\ti` ou `\di` viaja junto com o texto da alternativa, de modo que o gabarito é preservado automaticamente após qualquer reordenação.

### Ordem das questões
A lista de questões é embaralhada aleatoriamente a cada versão. Questões V/F interrompem a contagem de gabaritos consecutivos ao serem intercaladas.

### Restrição de gabaritos consecutivos
Após embaralhar, o sistema verifica se alguma posição de gabarito (A, B, C…) aparece repetida mais vezes do que o limite configurado. Se a restrição for violada, uma nova permutação é gerada — até 2.000 tentativas. Caso não seja possível satisfazer a restrição dentro desse limite, o sistema emite um aviso e usa a última permutação disponível.

### Nomenclatura dos arquivos de saída
O prefixo é extraído do nome do arquivo-base removendo o último caractere do _stem_ (ex.: `P1A` → prefixo `P1`). As versões são nomeadas concatenando o prefixo com letras sequenciais a partir da letra inicial informada (`P1B.tex`, `P1C.tex`, `P1D.tex`, …).


## 🏗️ Arquitetura (POO)

O projeto utiliza Programação Orientada a Objetos com as seguintes classes e funções principais:

| Componente | Tipo | Responsabilidade |
|------------|------|------------------|
| `Config` | dataclass | Configurações de execução fornecidas pelo usuário |
| `AnswerItem` | dataclass | Representa uma alternativa individual (marcador + conteúdo) |
| `Question` | classe | Representa um bloco de questão; detecta tipo e embaralha alternativas |
| `QuizRandomShuffler` | classe | Carrega o arquivo-base, embaralha e gera as versões de saída |
| `_ask` / `_ask_bool` | funções | Leitura de entrada do usuário com valores padrão |
| `_next_char` | função | Infere o sufixo padrão a partir do nome do arquivo-base |


## 🔧 Integração com $\LaTeX$

Os arquivos gerados seguem o mesmo formato do arquivo-base e são compiláveis diretamente com o _template_ LaTeX Para Provas Com Gabarito:

```bash
# Para cada versão gerada:
pdflatex main.tex   # com \input{P1B.tex}
pdflatex main.tex   # com \input{P1C.tex}
```

O gabarito de cada versão é resolvido pelo próprio _template_ ao processar os marcadores `\di` e `\ifnum\gabarito`.


## 🔗 Integração com o ExamForge

O QuizRandomShuffle e o ExamForge [https://github.com/wyllianbs/ExamForge](https://github.com/wyllianbs/ExamForge) são ferramentas **complementares** dentro do mesmo fluxo de trabalho:

1. **ExamForge** — sorteia questões de um banco `.tex` configurado via planilha ODS e gera o arquivo `P1A.tex` com as questões selecionadas.
2. **QuizRandomShuffle** — recebe `P1A.tex` como entrada e gera as versões embaralhadas `P1B.tex`, `P1C.tex`, …

```
banco de questões (.tex) + db.ods
         ↓
      ExamForge
         ↓
       P1A.tex
         ↓
     QuizRandomShuffle
         ↓
  P1B.tex · P1C.tex · …
```


## 🐛 Tratamento de Erros

O programa valida:

- ✅ Existência do arquivo-base informado.
- ✅ Número de versões maior ou igual a 1.
- ✅ Questões não fechadas no `.tex` (aviso de bloco malformado).
- ✅ Restrição de gabaritos consecutivos — avisa se não puder ser satisfeita após 2.000 tentativas.
- ✅ Interrupção limpa com `Ctrl+C` ou `EOF`.


## 📜 Licença

Este projeto está licenciado sob a Licença [GNU General Public License v3.0](LICENSE).


## 👤 Autor

**Prof. Wyllian B. da Silva**  
Universidade Federal de Santa Catarina (UFSC)  
Departamento de Informática e Estatística (INE)


---

**Nota**: Este projeto foi desenvolvido especificamente para uso na UFSC, mas pode ser facilmente adaptado para outras instituições de ensino e outros formatos de prova.

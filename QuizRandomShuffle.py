'''
QuizShuffle.py
Gera versões embaralhadas de arquivos de prova em LaTeX (.tex).

Funcionalidades:
  - Embaralha a ordem das questões entre versões.
  - Embaralha as alternativas de múltipla escolha (mantém di na alternativa correta).
  - Questões Verdadeiro/Falso nao têm suas alternativas embaralhadas.
  - Controla o número máximo de gabaritos iguais consecutivos.
'''

import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Estruturas de dados
# ---------------------------------------------------------------------------

@dataclass
class Config:
    """Configurações de execução fornecidas pelo usuário."""
    filepath: Path
    num_versions: int
    suffix_char: str
    shuffle_questions: bool
    shuffle_alternatives: bool
    max_consecutive_same_answer: int


@dataclass
class AnswerItem:
    """Representa uma alternativa individual dentro de um answerlist."""
    marker: str      # '\\ti' ou '\\di'
    content: str     # Texto da alternativa (incluindo espaços/newlines iniciais)


# ---------------------------------------------------------------------------
# Classe Question
# ---------------------------------------------------------------------------

class Question:
    """
    Representa um bloco de questão LaTeX delimitado por {% Qxxxxx ... }.
    Suporta questões de múltipla escolha e V/F.
    """

    _VF_PATTERN = re.compile(
        r'\\ti\[V\.\]'
        r'|\\ti\[F\.\]'
        r'|\\doneitem\[V\.\]'
        r'|\\doneitem\[F\.\]'
        r'|\\ifnum\\gabarito'
    )
    _ANSWERLIST_BLOCK = re.compile(
        r'(\\begin\{answerlist\}[^\n]*\n)'   # grupo 1: linha do begin
        r'(.*?)'                              # grupo 2: conteúdo dos itens
        r'(\n?[ \t]*\\end\{answerlist\})',    # grupo 3: linha do end
        re.DOTALL,
    )
    _ITEM_SPLIT = re.compile(
        r'(?=[ \t]*\\(?:ti|di)(?:\[[^\]]*\])?(?:\s|$))',
        re.MULTILINE,
    )
    _ITEM_MARKER = re.compile(r'^[ \t]*(\\(?:ti|di))(?:\[[^\]]*\])?')

    def __init__(self, content: str) -> None:
        self.content: str = content
        self._is_vf: Optional[bool] = None

    # ------------------------------------------------------------------
    # Propriedades
    # ------------------------------------------------------------------

    @property
    def is_vf(self) -> bool:
        """Retorna True se for questão V/F (alternativas não devem ser embaralhadas)."""
        if self._is_vf is None:
            self._is_vf = bool(self._VF_PATTERN.search(self.content))
        return self._is_vf

    @property
    def is_multiple_choice(self) -> bool:
        return not self.is_vf

    def correct_answer_position(self) -> Optional[int]:
        """
        Retorna o índice (base 0) da alternativa correta (\\di) na questão.
        Retorna None para questões V/F ou sem answerlist detectável.
        """
        if self.is_vf:
            return None
        items = self._extract_items()
        for idx, item in enumerate(items):
            if item.marker == r'\di':
                return idx
        return None

    # ------------------------------------------------------------------
    # Parsing interno
    # ------------------------------------------------------------------

    def _extract_items(self) -> list[AnswerItem]:
        """
        Extrai as alternativas do primeiro bloco answerlist da questão.
        Retorna lista de AnswerItem com (marker, content).
        """
        match = self._ANSWERLIST_BLOCK.search(self.content)
        if not match:
            return []

        items_text: str = match.group(2)
        # Divide no início de cada \ti ou \di
        parts = self._ITEM_SPLIT.split(items_text)
        result: list[AnswerItem] = []

        for part in parts:
            if not part.strip():
                continue
            m = self._ITEM_MARKER.match(part)
            if not m:
                # Texto antes do primeiro item (possíveis espaços) — ignorar
                continue
            marker = m.group(1)          # '\ti' ou '\di'
            # O conteúdo começa após o marcador completo (incluindo [label] opcional)
            after_marker = part[m.end():]
            result.append(AnswerItem(marker=marker, content=after_marker))

        return result

    # ------------------------------------------------------------------
    # Transformações
    # ------------------------------------------------------------------

    def with_shuffled_alternatives(self) -> 'Question':
        """
        Retorna uma nova Question com as alternativas embaralhadas.
        Questões V/F são retornadas sem modificação.
        """
        if self.is_vf:
            return Question(self.content)

        block_match = self._ANSWERLIST_BLOCK.search(self.content)
        if not block_match:
            return Question(self.content)

        items = self._extract_items()
        if len(items) < 2:
            return Question(self.content)

        random.shuffle(items)

        # Reconstrói o bloco de itens preservando indentação original
        new_items_text = ''
        for item in items:
            new_items_text += f'    {item.marker}{item.content}'

        # Garante que não haja espaço duplo no final
        new_items_text = new_items_text.rstrip()

        new_content = (
            self.content[: block_match.start(2)]
            + new_items_text
            + self.content[block_match.end(2):]
        )
        return Question(new_content)

    def __repr__(self) -> str:
        first_line = self.content.split('\n')[0]
        return f'Question({first_line!r})'


# ---------------------------------------------------------------------------
# Classe QuizShuffler
# ---------------------------------------------------------------------------

class QuizShuffler:
    """
    Carrega um arquivo LaTeX de questões, embaralha e gera as versões.
    """

    # { seguido de % e um ID (com possíveis espaços entre { e %)
    # Cobre: {% ID  /  { % ID  /  {%ID  /  { %ID
    _RE_ID = re.compile(r'\{\s*%\s*(\S+)')

    def __init__(self, config: Config) -> None:
        self.config = config
        self.questions: list[Question] = []
        self._header: str = ''
        self._footer: str = ''

    # ------------------------------------------------------------------
    # Carregamento
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Lê e parseia o arquivo-base."""
        print(f'[INFO] Carregando: {self.config.filepath}')
        text = self.config.filepath.read_text(encoding='utf-8')
        self.questions, self._header, self._footer = self._parse(text)
        mc = sum(1 for q in self.questions if q.is_multiple_choice)
        vf = sum(1 for q in self.questions if q.is_vf)
        print(f'[INFO] Questões encontradas: {len(self.questions)} '
              f'({mc} múltipla escolha, {vf} V/F)')

    def _parse(self, text: str) -> tuple[list[Question], str, str]:
        r"""
        Extrai blocos de questão por pilha de chaves, seguindo a mesma
        lógica do ExamForge:
          - { seguido de % (com espaços opcionais) abre um bloco candidato.
          - \rtask no bloco mais externo o promove a questão válida.
          - O bloco é coletado do início da linha que contém a abertura
            até o } de fechamento correspondente.
        Retorna (lista_de_questões, header, footer).
        """
        questions: list[Question] = []
        lines = text.splitlines(keepends=True)

        # stack: lista de dicts por nível de chave aberta
        stack: list[dict] = []
        acc_lines: list[str] = []
        start_line: int = 0        # 1-based
        current_id: str = ''
        inside: bool = False
        first_start_char: Optional[int] = None
        last_end_char: int = 0

        for i, line in enumerate(lines):
            num = i + 1            # 1-based
            has_rtask = r'\rtask' in line
            id_match = self._RE_ID.search(line)
            opens = line.count('{')
            closes = line.count('}')

            # Bloco malformado: novo ID encontrado com pilha não vazia — reseta
            if opens > 0 and id_match and stack:
                stack.clear()
                inside = False
                acc_lines = []

            for _ in range(opens):
                block: dict = {'line_start': num, 'has_rtask': False, 'id': None}
                if id_match:
                    block['id'] = id_match.group(1)
                    id_match = None          # só o primeiro { desta linha recebe o ID
                stack.append(block)

            # Propaga \rtask para o bloco mais externo (índice 0)
            if stack and has_rtask and not stack[0]['has_rtask']:
                stack[0]['has_rtask'] = True

            # Coleta linhas quando o bloco raiz já tem \rtask
            if stack and stack[0]['has_rtask']:
                if not inside:
                    inside = True
                    start_line = int(stack[0]['line_start'])
                    current_id = str(stack[0].get('id') or '')
                    acc_lines = lines[start_line - 1: num]
                else:
                    acc_lines.append(line)

            for _ in range(closes):
                if stack:
                    closed = stack.pop()
                    if closed['has_rtask'] and not stack:
                        content = ''.join(acc_lines)

                        block_char_start = sum(len(lines[j]) for j in range(start_line - 1))
                        block_char_end = sum(len(lines[j]) for j in range(num))

                        if first_start_char is None:
                            first_start_char = block_char_start
                        last_end_char = block_char_end

                        questions.append(Question(content))
                        inside = False
                        acc_lines = []

        if inside and stack:
            print(f'[AVISO] Questão não fechada, linha {start_line}, ID: {current_id}')

        header = text[:first_start_char] if first_start_char is not None else ''
        footer = text[last_end_char:]
        return questions, header, footer

    # ------------------------------------------------------------------
    # Embaralhamento
    # ------------------------------------------------------------------

    def _shuffled_with_constraint(
        self, questions: list[Question]
    ) -> list[Question]:
        """
        Embaralha questões respeitando o limite de gabaritos consecutivos iguais.
        """
        limit = self.config.max_consecutive_same_answer
        shuffled = questions.copy()
        random.shuffle(shuffled)

        max_attempts = 2000
        for attempt in range(1, max_attempts + 1):
            if self._constraint_ok(shuffled, limit):
                if attempt > 1:
                    print(f'  [INFO] Restrição satisfeita na tentativa {attempt}.')
                return shuffled
            random.shuffle(shuffled)

        print('  [AVISO] Restrição de gabaritos consecutivos não pôde ser '
              'totalmente satisfeita após muitas tentativas.')
        return shuffled

    @staticmethod
    def _constraint_ok(questions: list[Question], limit: int) -> bool:
        """Verifica se nenhuma posição de gabarito se repete mais de `limit` vezes seguidas."""
        consecutive = 0
        last_pos: Optional[int] = None

        for q in questions:
            pos = q.correct_answer_position()
            if pos is None:
                # Questão V/F: reseta contador
                consecutive = 0
                last_pos = None
                continue
            if pos == last_pos:
                consecutive += 1
                if consecutive >= limit:
                    return False
            else:
                consecutive = 1
            last_pos = pos

        return True

    # ------------------------------------------------------------------
    # Geração de versões
    # ------------------------------------------------------------------

    def generate(self) -> None:
        """Gera todos os arquivos de versão configurados."""
        base_stem = self.config.filepath.stem          # ex.: "P1A"
        prefix = base_stem[:-1]                        # ex.: "P1"
        out_dir = self.config.filepath.parent

        for v in range(self.config.num_versions):
            version_char = chr(ord(self.config.suffix_char) + v)
            out_name = f'{prefix}{version_char}.tex'
            out_path = out_dir / out_name

            print(f'\n[VERSÃO {v + 1}/{self.config.num_versions}] → {out_name}')

            qs: list[Question] = list(self.questions)  # cópia

            if self.config.shuffle_alternatives:
                print('  [INFO] Embaralhando alternativas de múltipla escolha...')
                qs = [q.with_shuffled_alternatives() for q in qs]

            if self.config.shuffle_questions:
                print('  [INFO] Embaralhando ordem das questões...')
                qs = self._shuffled_with_constraint(qs)

            # Monta o conteúdo final
            separator = '\n' * 4  # 3 linhas em branco entre blocos
            joined = separator.join(q.content.rstrip() for q in qs)
            content = self._header + joined + self._footer
            out_path.write_text(content, encoding='utf-8')
            print(f'  [OK] Arquivo gravado: {out_path.resolve()}')

        print('\n[CONCLUÍDO] Todas as versões foram geradas.')


# ---------------------------------------------------------------------------
# Utilitários de entrada do usuário
# ---------------------------------------------------------------------------

def _ask(prompt: str, default: str) -> str:
    """Solicita entrada ao usuário com valor padrão."""
    try:
        value = input(f'{prompt} [padrão: {default}]: ').strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    return value if value else default


def _ask_bool(prompt: str, default: bool) -> bool:
    """Solicita resposta s/n ao usuário. A opção padrão é exibida em maiúsculo."""
    options = 'S/n' if default else 's/N'
    default_str = 's' if default else 'n'
    raw = _ask(f'{prompt} ({options})', default_str).lower()
    if raw in ('s', 'n'):
        return raw == 's'
    return default


def _next_char(filepath: Path) -> str:
    """Sugere o próximo caractere de sufixo baseado no arquivo-base."""
    stem = filepath.stem          # ex.: "P1A"
    last = stem[-1].upper()       # 'A'
    return chr(ord(last) + 1)     # 'B'


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------

def main() -> None:
    print('=' * 55)
    print('  QuizShuffle — Gerador de Versões de Prova LaTeX')
    print('=' * 55)
    print()

    # 1. Arquivo-base
    path_str = _ask('Caminho do arquivo-base', 'P1A.tex')
    filepath = Path(path_str)
    if not filepath.exists():
        print(f'[ERRO] Arquivo não encontrado: {filepath}')
        sys.exit(1)

    # 2. Número de versões
    num_versions = int(_ask('Número de versões a gerar', '2'))
    if num_versions < 1:
        print('[ERRO] O número de versões deve ser >= 1.')
        sys.exit(1)

    # 3. Sufixo inicial
    default_suffix = _next_char(filepath)
    suffix_input = _ask(
        f'Letra inicial do sufixo (ex.: {default_suffix} → gera '
        f'{filepath.stem[:-1]}{default_suffix}.tex, ...)',
        default_suffix,
    )
    suffix_char = suffix_input[0].upper()

    # 4. Embaralhar questões
    shuffle_q = _ask_bool('Embaralhar a ordem das questões', True)

    # 5. Embaralhar alternativas
    shuffle_a = _ask_bool('Embaralhar alternativas de múltipla escolha', True)

    # 6. Limite de gabaritos consecutivos iguais
    max_consec = int(_ask(
        'Máximo de gabaritos consecutivos na mesma posição', '3'
    ))

    print()
    config = Config(
        filepath=filepath,
        num_versions=num_versions,
        suffix_char=suffix_char,
        shuffle_questions=shuffle_q,
        shuffle_alternatives=shuffle_a,
        max_consecutive_same_answer=max_consec,
    )

    shuffler = QuizShuffler(config)
    shuffler.load()
    shuffler.generate()


if __name__ == '__main__':
    main()

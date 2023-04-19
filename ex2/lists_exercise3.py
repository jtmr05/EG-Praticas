#!/usr/bin/env python3

import lark
import typing
import functools
import sys


# utility function
def annotate(original: typing.Any, *ansi_escape_codes: int):

    length: int = len(ansi_escape_codes)

    if length == 0:
        return str(original)

    prefix: str = '\033[' + str(ansi_escape_codes[0])
    for i in range(1, length):
        prefix += ';' + str(ansi_escape_codes[i])

    return prefix + 'm' + str(original) + '\033[0m'


grammar: str = '''
start          : LIST_BEGIN elements LIST_END
elements       : element (COMMA element)*
element        : NUMBER
               | WORD
LIST_BEGIN     : /^lista/i
LIST_END       : /\.$/
COMMA          : /,/
NUMBER         : /\d+/
WORD           : /\w+/

%import common.WS
%ignore WS
'''


Element = typing.Union[str, int]


class ListTransformer(lark.Transformer):

    _number_of_nodes: int
    _mode: Element
    _is_sequence: bool
    _curr_sequence: list[int]
    _sequences_sums: list[int]
    _elem_to_occurrences: dict[Element, int]

    def __init__(self):
        self._number_of_nodes     = 0
        self._mode                = None
        self._is_sequence         = False
        self._curr_sequence       = None
        self._sequences_sums      = list()
        self._elem_to_occurrences = dict()

    def _add_element(self, elem: Element):
        if elem not in self._elem_to_occurrences:
            self._elem_to_occurrences[elem] = 1
        else:
            self._elem_to_occurrences[elem] += 1

    def start(self, tree):
        print(f"Number of elements: {annotate(self._number_of_nodes, 1)}")
        print(f"Mode: {annotate(self._mode, 1)}")
        print(f"Sums of each 'agora' ... 'fim' sequence: {annotate(self._sequences_sums, 1)}")

    def elements(self, tree):

        if self._is_sequence:
            raise lark.GrammarError()

        def dict_min(a: Element, b: Element) -> Element:
            if self._elem_to_occurrences[a] < self._elem_to_occurrences[b]:
                return b
            return a

        self._mode = functools.reduce(dict_min, self._elem_to_occurrences)

        return tree

    def element(self, tree):
        return tree[0]

    def NUMBER(self, tree):

        if self._is_sequence:
            self._curr_sequence.append(int(tree))

        number: int = int(tree)

        self._number_of_nodes += 1

        self._add_element(number)

        return number

    def WORD(self, tree):

        word: str = str(tree)

        if word == 'agora':

            if self._is_sequence:
                raise lark.GrammarError()

            else:
                self._curr_sequence = list()
                self._is_sequence = True

        elif word == 'fim':

            if not self._is_sequence:
                raise lark.GrammarError()

            else:
                self._sequences_sums.append(sum(self._curr_sequence))
                self._curr_sequence = None
                self._is_sequence = False

        elif self._is_sequence:
            raise lark.GrammarError()

        self._number_of_nodes += 1

        self._add_element(word)

        return word

    def LIST_BEGIN(self, tree):
        return lark.Discard

    def LIST_END(self, tree):
        return lark.Discard

    def COMMA(self, tree):
        return lark.Discard


# Exercício 3
def main():

    tests: list[str] = [
        "LISTA 1  .",
        "lIstA 1, 3, 4, 4, 4, 6, 4, 8, agora, 666, fim .",
        "lIstA agora, agora, 666, fim .",
        "Lista aaa .",
        "Lista 1, 2, agora, 3, 4, fim, 7, 8.",
        "Lista 1, 2, 2, 2, 2, agora, 3, 4, fim, agora, 7, 81, fim, 8.",
        "Lista 1, 2, 2, 2, agora, 3, coiso, 4, fim, agora, 7, 81, 8, fim.",
    ]

    parser: lark.Lark = lark.Lark(grammar)

    for t in tests:

        try:
            tree: lark.ParseTree = parser.parse(t)
            #print(tree.pretty())
            ListTransformer().transform(tree)
            print(f"==> Test '{annotate(t, 1)}' {annotate('passed', 32, 1)}!\n", file=sys.stderr)

        except lark.UnexpectedCharacters:
            print(f"==> Test '{annotate(t, 1)}' {annotate('failed', 31, 1)}!\n", file=sys.stderr)

        except lark.GrammarError:
            print(f"==> Test '{annotate(t, 1)}' {annotate('failed', 31, 1)}!\n", file=sys.stderr)


if __name__ == '__main__':
    main()

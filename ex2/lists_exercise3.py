#!/usr/bin/env python3

import lark
import typing
import functools
import sys

# utility function
def annotate(original : typing.Any, *ansi_escape_codes : int):

    length : int = len(ansi_escape_codes)

    if length == 0:
        return str(original)


    prefix : str = '\033[' + str(ansi_escape_codes[0])
    for i in range(1, length):
        prefix += ';' + str(ansi_escape_codes[i])

    return prefix + 'm' + str(original) + '\033[0m'


grammar : str = '''
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

    __number_of_nodes__     : int
    __mode__                : Element
    __is_sequence__         : bool
    __curr_sequence__       : list[int]
    __sequences_sums__      : list[int]
    __elem_to_occurrences__ : dict[Element, int]


    def __init__(self):
        self.__number_of_nodes__     = 0
        self.__mode__                = None
        self.__is_sequence__         = False
        self.__curr_sequence__       = None
        self.__sequences_sums__      = list()
        self.__elem_to_occurrences__ = dict()

    def __add_element__(self, elem : Element):
        if elem not in self.__elem_to_occurrences__:
            self.__elem_to_occurrences__[elem] = 1
        else:
            self.__elem_to_occurrences__[elem] += 1


    def start(self, tree):
        print(f"Number of elements: {annotate(self.__number_of_nodes__, 1)}")
        print(f"Mode: {annotate(self.__mode__, 1)}")
        print(f"Sums of each 'agora' ... 'fim' sequence: {annotate(self.__sequences_sums__, 1)}")

    def elements(self, tree):

        if self.__is_sequence__:
            raise lark.GrammarError()


        def dict_min(a : Element, b : Element) -> Element:
            if self.__elem_to_occurrences__[a] < self.__elem_to_occurrences__[b]:
                return b
            return a

        self.__mode__ = functools.reduce(dict_min, self.__elem_to_occurrences__)

        return tree


    def element(self, tree):
        return tree[0]

    def NUMBER(self, tree):

        if self.__is_sequence__:
            self.__curr_sequence__.append(int(tree))


        number : int = int(tree)

        self.__number_of_nodes__ += 1

        self.__add_element__(number)

        return number

    def WORD(self, tree):

        word : str = str(tree)

        if word == 'agora':

            if self.__is_sequence__:
                raise lark.GrammarError()

            else:
                self.__curr_sequence__ = list()
                self.__is_sequence__ = True

        elif word == 'fim':

            if not self.__is_sequence__:
                raise lark.GrammarError()

            else:
                self.__sequences_sums__.append(sum(self.__curr_sequence__))
                self.__curr_sequence__ = None
                self.__is_sequence__ = False

        elif self.__is_sequence__:
            raise lark.GrammarError()


        self.__number_of_nodes__ += 1

        self.__add_element__(word)

        return word


    def LIST_BEGIN(self, tree):
        return lark.Discard

    def LIST_END(self, tree):
        return lark.Discard

    def COMMA(self, tree):
        return lark.Discard


#### Exercício 3
def main():

    tests : list[str] = [
        "LISTA 1  .",
        "lIstA 1, 3, 4, 4, 4, 6, 4, 8, agora, 666, fim .",
        "lIstA agora, agora, 666, fim .",
        "Lista aaa .",
        "Lista 1, 2, agora, 3, 4, fim, 7, 8.",
        "Lista 1, 2, 2, 2, 2, agora, 3, 4, fim, agora, 7, 81, fim, 8.",
        "Lista 1, 2, 2, 2, agora, 3, coiso, 4, fim, agora, 7, 81, 8, fim.",
    ]


    parser : lark.Lark = lark.Lark(grammar)

    for t in tests:

        try:
            tree : lark.ParseTree = parser.parse(t)
            #print(tree.pretty())
            ListTransformer().transform(tree)
            print(f"==> Test '{annotate(t, 1)}' {annotate('passed', 32, 1)}!\n", file=sys.stderr)

        except lark.UnexpectedCharacters:
            print(f"==> Test '{annotate(t, 1)}' {annotate('failed', 31, 1)}!\n", file=sys.stderr)

        except lark.GrammarError:
            print(f"==> Test '{annotate(t, 1)}' {annotate('failed', 31, 1)}!\n", file=sys.stderr)


if __name__ == '__main__':
    main()

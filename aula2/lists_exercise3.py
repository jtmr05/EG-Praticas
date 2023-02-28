#!/usr/bin/env python3

#TODO
# Make 'agora' and 'fim' keywords (how?)
# Prioritize productions

import lark
import typing
import functools
import sys

# utility function

def annotate(original : typing.Any, *ascii_escape_codes : int):

    length : int = len(ascii_escape_codes)

    if length == 0:
        return str(original)

    prefix : str = '\033[' + str(ascii_escape_codes[0])

    for i in range(1, length):
        prefix += ';' + str(ascii_escape_codes[i])

    return prefix + 'm' + str(original) + '\033[0m'


grammar : str = '''
start          : LIST_BEGIN elements LIST_END
elements       : element (COMMA element)*
element        : sequence
               | NUMBER
               | WORD
sequence       : SEQUENCE_BEGIN COMMA NUMBER (COMMA NUMBER)* COMMA SEQUENCE_END
LIST_BEGIN     : /^lista/i
LIST_END       : /\.$/
SEQUENCE_BEGIN : "agora"
SEQUENCE_END   : "fim"
COMMA          : /,/
NUMBER         : /\d+/
WORD           : /\w+/

%import common.WS
%ignore WS
'''


Element = typing.Union[str, int]

class ListTransformer(lark.Transformer):

    __number_of_nodes__ : int
    __mode__            : Element
    __is_sequence__     : bool
    __curr_sequence__   : list[int]
    __sequences_sums__  : list[int]


    def __init__(self):
        self.__number_of_nodes__ = 0
        self.__mode__            = None
        self.__is_sequence__     = False
        self.__curr_sequence__   = None
        self.__sequences_sums__  = list()


    def start(self, start):
        print(start[0])
        print(f"Number of elements: {annotate(self.__number_of_nodes__, 1)}")
        print(f"Mode: {annotate(self.__mode__, 1)}")
        print("Sums of each 'agora' ... 'fim' sequence: " +
              f"{annotate(self.__sequences_sums__, 1)}")

    def elements(self, elements):

        flat_elements : list[Element] = []
        for e in elements:

            if isinstance(e, list):
                flat_elements += e
            else:
                flat_elements.append(e)

        self.__number_of_nodes__ = len(flat_elements)

        elem_to_occurences : dict[Element, int] = dict()

        for e in flat_elements:
            if e not in elem_to_occurences:
                elem_to_occurences[e] = 1
            else:
                elem_to_occurences[e] += 1

        def dict_min(a : Element, b : Element) -> Element:
            if elem_to_occurences[a] < elem_to_occurences[b]:
                return b
            return a

        self.__mode__ = functools.reduce(dict_min, elem_to_occurences)

        return flat_elements

    def element(self, element):
        return element[0]
        #return element

    def sequence(self, sequence):
        return sequence

    def LIST_BEGIN(self, LIST_BEGIN):
        return lark.Discard

    def LIST_END(self, LIST_END):
        return lark.Discard

    def SEQUENCE_BEGIN(self, SEQUENCE_BEGIN):

        self.__is_sequence__ = True
        self.__curr_sequence__ = list()

        return str(SEQUENCE_BEGIN)

    def SEQUENCE_END(self, SEQUENCE_END):

        self.__is_sequence__ = False
        self.__sequences_sums__.append(sum(self.__curr_sequence__))

        return str(SEQUENCE_END)

    def COMMA(self, COMMA):
        return lark.Discard

    def NUMBER(self, NUMBER):
        if self.__is_sequence__:
            self.__curr_sequence__.append(int(NUMBER))

        return int(NUMBER)

    def WORD(self, WORD):
        return str(WORD)


#### Exercício 3
def main():

    tests : list[str] = [
        "LISTA 1  .",
        "lIstA 1, 3, 4, 4, 4, 6, 4, 8, agora, 666, fim .",
        "lIstA agora, agora, 666, fim .",
        "Lista aaa .",
        "Lista 1, 2, agora, 3, 4, fim, 7, 8.",
        "Lista 1, 2, agora, 3, 4, fim, agora, 7, 81, fim, 8.",
    ]


    parser : lark.Lark = lark.Lark(grammar)

    for t in tests:

        try:
            tree : lark.ParseTree = parser.parse(t)
            #print(tree.pretty())
            ListTransformer().transform(tree)
            print()

        except lark.UnexpectedCharacters:
            print(f"test '{annotate(t, 1)}' {annotate('failed', 31, 1)}!\n", file=sys.stderr)



if __name__ == '__main__':
    main()

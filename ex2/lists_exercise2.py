#!/usr/bin/env python3

import lark

grammar1 = '''
//Regras Sintaticas
start: PE elementos PD
elementos :
          | elemento (VIR elemento)*
elemento : NUMERO
//Regras Lexicográficas
NUMERO:"0".."9"+ // [0-9]+
PE:"["
PD:"]"
VIR:","
//Tratamento dos espaços em branco
%import common.WS
%ignore WS
'''

grammar2 = '''
//Regras Sintaticas
start: PE elementos PD
elementos: elemento VIR elementos
        |
elemento : NUMERO
//Regras Lexicograficas
NUMERO:"0".."9"+
PE:"["
PD:"]"
VIR:","
//Tratamento dos espaços em branco
%import common.WS
%ignore WS
'''

grammar3 = '''
//Regras Sintaticas
start: PE elementos PD
elementos: elementos VIR elemento
        |
elemento : NUMERO
//Regras Lexicograficas
NUMERO:"0".."9"+
PE:"["
PD:"]"
VIR:","
//Tratamento dos espaços em branco
%import common.WS
%ignore WS
'''

grammar4 = '''
//Regras Sintaticas
start: PE ( |elementos) PD
elementos: elemento VIR elementos
//elementos: elemento VIR elementos
         | elemento
elemento : NUMERO
//Regras Lexicograficas
NUMERO:"0".."9"+
PE:"["
PD:"]"
VIR:","
//Tratamento dos espaços em branco
%import common.WS
%ignore WS
'''

grammar = '''
//Regras Sintaticas
start: PE elemento* PD
elemento : NUMERO (VIR NUMERO)*
//Regras Lexicográficas
NUMERO:"0".."9"+
PE:"["
PD:"]"
VIR:","
//Tratamento dos espaços em branco
%import common.WS
%ignore WS
'''


class ExampleTransformer(lark.Transformer):

    _elem_sum: int
    _max_sum: int

    def __init__(self):
        self._elem_sum = 0
        self._max_sum  = 0

    def start(self, tree):
        print(f"sum is {self._elem_sum} and max is {self._max_sum}")

    def elemento(self, tree):
        return tree

    def NUMERO(self, tree):
        self._elem_sum += int(tree)
        self._max_sum   = max(self._max_sum, int(tree))
        return int(tree)

    def PE(self, tree):
        return lark.Discard
        #return str(tree)

    def PD(self, tree):
        return lark.Discard
        #return str(tree)

    def VIR(self, tree):
        return lark.Discard
        #return str(tree)


def main():

    phrase = "[1,23,345]"

    #p = lark.Lark(grammar)   #não muito bem
    p = lark.Lark(grammar1)  # recomendada
    #p = lark.Lark(grammar2)  #incorreta
    #p = lark.Lark(grammar3)  #incorreta
    #p = lark.Lark(grammar4)   #aceitável

    tree = p.parse(phrase)
    #print(tree.pretty())
    #for element in tree.children:
    #print(element)

    ExampleTransformer().transform(tree)


if __name__ == '__main__':
    main()

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

    __elem_sum : int
    __max_num  : int

    def __init__(self):
        self.__elem_sum = 0
        self.__max_num = 0

    def start(self, _):
        print(f"sum is {self.__elem_sum} and max is {self.__max_num}")

    def elemento(self, _):
        return _

    def NUMERO(self, numero):
        self.__elem_sum += int(numero)
        self.__max_num   = max(self.__max_num, int(numero))
        return int(numero)

    def PE(self, _):
        return lark.Discard
        #return str(_)

    def PD(self, _):
        return lark.Discard
        #return str(_)

    def VIR(self, _):
        #return str(_)
        return lark.Discard


def main():

    frase = "[1,23,345]"

    #p = lark.Lark(grammar)   #não muito bem
    p = lark.Lark(grammar1)  #recomendada
    #p = lark.Lark(grammar2)  #incorreta
    #p = lark.Lark(grammar3)  #incorreta
    #p = lark.Lark(grammar4)   #aceitável

    tree = p.parse(frase)
    #print(tree.pretty())
    #for element in tree.children:
      #print(element)

    data = ExampleTransformer().transform(tree)


if __name__ == '__main__':
    main()

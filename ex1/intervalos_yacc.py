#!/usr/bin/env python3

import sys
import functools
import ply.yacc
from intervalos_lex import tokens


parser = None


def print_statistics(l: list[tuple[int, int]]):

    size: int = len(l)

    print()
    print(f"Number of intervals: {size}")

    ranges: list[tuple[int, int]] = list(
        map(
            lambda x: (x, abs(l[x][1] - l[x][0])),
            range(0, size)
        )
    )

    print("Ranges: ", end='')
    print(
        list(
            map(
                lambda x: x[1],
                ranges
            )
        )
    )

    def min_tuple(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
        if a[1] > b[1]:
            return b
        return a

    def max_tuple(a: tuple[int, int], b: tuple[int, int]) -> tuple[int, int]:
        if a[1] < b[1]:
            return b
        return a

    min_ind: int = functools.reduce(min_tuple, ranges, (-1, sys.maxsize))[0]
    max_ind: int = functools.reduce(max_tuple, ranges, (-1, 0))[0]

    print(f"Min range interval: {l[min_ind]}")
    print(f"Max range interval: {l[max_ind]}")

    print(f"Absolute range: {abs(l[0][0] - l[-1][1])}")
    print()


# The set of syntatic rules
def p_sequencia(p):
    "sequencia : sentido intervalos"

    p[0] = p[2]

    for i in range(0, len(p[0]) - 1):

        if parser.is_plus:

            if p[0][i][1] >= p[0][i + 1][0]:

                parser.success = False

                print(
                    f"Syntax error: intervals {p[0][i]} and {p[0][i+1]} "
                    + "aren't in the correct order or intercept",
                    file=sys.stderr
                )

                raise SyntaxError

        else:

            if p[0][i][1] <= p[0][i + 1][0]:

                parser.success = False

                print(
                    f"Syntax error: intervals {p[0][i]} and {p[0][i+1]} "
                    + "aren't in the correct order or intercept",
                    file=sys.stderr
                )

                raise SyntaxError

    print_statistics(p[0])


def p_sentidoA(p):
    "sentido : '+'"
    parser.is_plus = True


def p_sentidoD(p):
    "sentido : '-'"
    parser.is_plus = False


def p_intervalos_intervalo(p):
    "intervalos : intervalo"
    p[0] = [p[1]]


def p_intervalos_intervalos(p):
    "intervalos : intervalos intervalo"
    p[0] = p[1] + [p[2]]


def p_intervalo(p):
    "intervalo : '[' NUM ',' NUM ']'"

    cmp_str: str = ''

    if parser.is_plus:
        cmp_str = 'lesser'
        parser.success = p[2] < p[4]
    else:
        cmp_str = 'greater'
        parser.success = p[2] > p[4]

    if not parser.success:
        print(
            f"Syntax error: lhs ('{p[2]}') is not {cmp_str} than to rhs ('{p[4]}')",
            file=sys.stderr
        )
        raise SyntaxError

    p[0] = (p[2], p[4])


# Syntatic Error handling rule
def p_error(p):
    print('Syntax error:', p)
    parser.success = False


# Build the parser
def main():

    global parser
    parser = ply.yacc.yacc()

    # Start parsing the input text
    for line in sys.stdin:
        parser.success = True
        parser.flag = True
        parser.is_plus = True
        parser.last = 0
        parser.parse(line)


if __name__ == '__main__':
    main()

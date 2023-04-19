#!/usr/bin/env python3

import lark
import lark.visitors
import lark.tree
import typing
import sys
import io


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
album     : cover "[" page+ "]" backcover
cover     : title author DATE
title     : STRING
author    : STRING
backcover : closure DATE
closure   : STRING
page      : sep | sheet
sep       : title
sheet     : photo+
photo     : FILE caption
caption   : STRING
STRING    : /".+?"/
FILE      : /\w+/
DATE      : /\d\d-\d\d-\d\d\d\d/

%import common.WS
%ignore WS
'''


class AlbumInterpreter(lark.visitors.Interpreter):

    _fig_count:     int
    _output_buffer: io.StringIO

    def __init__(self):
        self._fig_count     = 0
        self._output_buffer = io.StringIO()

    def print_output(self, fn: str):
        with open(fn, 'w') as fh:
            fh.write(self._output_buffer.getvalue().strip())

    def album(self, tree: lark.tree.Tree):

        self.visit(tree.children[0])  # cover
        for page in range(1, len(tree.children) - 1):
            self.visit(page)

    def cover(self, tree: lark.tree.Tree):
        self.visit(tree.children[0])
        self.visit(tree.children[1])

    def title(self, tree: lark.tree.Tree):
        value: str = tree.children[0].value.strip('"')
        self._output_buffer.write(f"\\title{{{value}}}\n")

    def author(self, tree: lark.tree.Tree):
        value: str = tree.children[0].value.strip('"')
        self._output_buffer.write(f"\\author{{{value}}}\n")

    def page(self, tree: lark.tree.Tree):
        self.visit(tree.children[0])
        self._output_buffer.write("\n\\newpage\n\n")

    def sep(self, tree: lark.tree.Tree):
        self.visit(tree.children[0])

    def photo(self, tree: lark.tree.Tree):
        self._fig_count += 1

        self._output_buffer.write("\\begin{figure}[h!]\n")
        self._output_buffer.write("\\centering\n")
        self._output_buffer.write(
            f"\\includegraphics[width=0.3\\textwidth]{{{tree.children[0].value}}}\n"
        )
        self.visit(tree.children[1])
        self._output_buffer.write("\\end{figure}\n")

    def caption(self, tree: lark.tree.Tree):
        value: str = tree.children[0].value.strip('"')
        self._output_buffer.write(
            f"\\caption{{\\label{{fig:fig{self._fig_count}}}" +
            f"{value}}}\n"
        )


def main():

    tests: list[str] = [
        '''
"Um passeio pelo Geres"
"Joaozinho"
03-04-2000
[
    "Cascata do tahiti"
    img1
    "Vista da cascata."

    "A aldeia de Soajo"
    img2
    "casa da aldeia."
]
"Dedicado à família"
03-05-2000
'''
    ]

    parser: lark.Lark = lark.Lark(grammar, start='album')
    test_count: int   = 1

    for t in tests:

        try:
            tree: lark.ParseTree = parser.parse(t)
            at: AlbumInterpreter = AlbumInterpreter()
            at.transform(tree)
            at.print_output(f"test{test_count}.tex")
            test_count += 1

            print(f"==> test '{annotate(t, 1)}' {annotate('passed', 32, 1)}!", file=sys.stderr)

        except lark.UnexpectedCharacters:
            print(f"==> test '{annotate(t, 1)}' {annotate('failed', 31, 1)}!", file=sys.stderr)

        except lark.GrammarError:
            print(f"==> test '{annotate(t, 1)}' {annotate('failed', 31, 1)}!", file=sys.stderr)

        print("\n")


if __name__ == '__main__':
    main()

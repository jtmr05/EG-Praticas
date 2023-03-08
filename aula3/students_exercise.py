#!/usr/bin/env python3

import lark
import typing
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
start          : students_class+
students_class : CLASS CLASS_ID students* "."
students       : student (";" student)*
student        : NAME "(" grades ")"
grades         : GRADE ("," GRADE)*
CLASS          : "TURMA"
CLASS_ID       : /[A-Z]+/
NAME           : /[a-z]+/
GRADE          : /\d+/

%import common.WS
%ignore WS
'''


class ClassTransformer(lark.Transformer):

    __number_of_students__  : int
    __class_to_students__   : dict[str, dict[str, float]]
    __student_to_average__  : dict[str, float]
    __curr_grades__         : list[int]
    __curr_class__          : str
    __curr_name__           : str


    def __init__(self):
        self.__number_of_students__  = 0
        self.__class_to_students__ = dict()
        self.__student_to_average__  = dict()
        self.__curr_grades__ = list()
        self.__curr_class__ = None
        self.__curr_name__ = None


    def start(self, tree):

        #print(tree)

        print(f"Number of students: {annotate(self.__number_of_students__, 1)}")

        for (student_class, students_dict) in self.__class_to_students__.items():

            for (student, avg) in students_dict.items():

                print(
                    f"Average grade for student {annotate(student, 1)} " +
                    f"of class {annotate(student_class, 1)}: "
                    f"{annotate('%.2f' % avg, 1, (36 if avg >= 9.5 else 31))}"
                )


    def students_class(self, tree):
        self.__class_to_students__[self.__curr_class__] = self.__student_to_average__
        self.__student_to_average__ = dict()
        return tree

    def students(self, tree):
        return tree

    def student(self, tree):

        self.__number_of_students__ += 1

        if self.__curr_name__ in self.__student_to_average__:
            raise lark.GrammarError()

        self.__student_to_average__[self.__curr_name__] = (
            sum(self.__curr_grades__)
            / len(self.__curr_grades__)
        )

        self.__curr_grades__.clear()

        return tree


    def grades(self, tree):
        return tree

    def CLASS(self, tree):
        return lark.Discard

    def CLASS_ID(self, tree):
        self.__curr_class__ = str(tree)
        return lark.Discard


    def NAME(self, tree):

        name : str = str(tree)

        self.__curr_grades__ = list()
        self.__curr_name__ = str(tree)

        return name

    def GRADE(self, tree):

        grade : int = int(tree)

        self.__curr_grades__.append(grade)

        return grade


def main():

    tests : list[str] = [
        '''TURMA A
        ana (12, 13, 15, 12, 13, 15, 14);
        joao (9,7,3,6,9);
        xico (12,16).''',

        '''TURMA B
        ana (12, 13, 15, 12, 13, 15, 14);
        joao (9,7,3,6,9,12);
        xico (13,16).''',

        '''
        TURMA A.
        TURMA D
        ana (12, 13, 15, 12, 13, 15, 14);
        joao (9,7,3,6,9,12);
        xico (12,16).
        TURMA C.
        ''',

        '''
        TURMA A.
        TURMA B
        henrique (12, 15);
        afonso ().
        '''
    ]


    parser : lark.Lark = lark.Lark(grammar)

    for t in tests:

        try:
            tree : lark.ParseTree = parser.parse(t)
            #print(tree.pretty())
            ClassTransformer().transform(tree)
            print(f"==> Test '{annotate(t, 1)}' {annotate('passed', 32, 1)}!\n", file=sys.stderr)

        except lark.UnexpectedCharacters:
            print(f"==> Test '{annotate(t, 1)}' {annotate('failed', 31, 1)}!\n", file=sys.stderr)

        #except lark.GrammarError:
        #    print(f"==> Test '{annotate(t, 1)}' {annotate('failed', 31, 1)}!\n", file=sys.stderr)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3

import lark
import typing
import sys
import datetime

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
students_class : CLASS CLASS_ID students+ "."
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

    __class_to_grades__     : dict[str, dict[int, set[str]]]
    __grade_to_students__   : dict[int, set[str]]

    __curr_class__          : str
    __curr_name__           : str

    __sql_queries__         : list[str]

    def __init__(self):
        self.__number_of_students__  = 0

        self.__class_to_students__   = dict()
        self.__student_to_average__  = dict()
        self.__curr_grades__         = list()

        self.__class_to_grades__     = dict()
        self.__grade_to_students__   = dict()

        self.__curr_class__          = None
        self.__curr_name__           = None

        self.__sql_queries__         = list()


    def start(self, tree):

        print(f"Number of students: {annotate(self.__number_of_students__, 1)}")

        for (students_class, students_dict) in self.__class_to_students__.items():

            for (student, avg) in students_dict.items():

                print(
                    f"Average grade for student {annotate(student, 1)} " +
                    f"of class {annotate(students_class, 1)}: "
                    f"{annotate('%.2f' % avg, 1, (32 if avg >= 9.5 else 31))}"
                )


        for (students_class, grades_dict) in self.__class_to_grades__.items():

            for (grade, students_set) in (
                sorted(grades_dict.items(), key = lambda e: e[0], reverse = True)
            ):

                print(
                    f"Students of class {annotate(students_class, 1)} that scored " +
                    f"{annotate(grade, 1)}: {annotate(students_set, 1)}"
                )

        for q in self.__sql_queries__:
            print(q)


    def students_class(self, tree):

        self.__class_to_students__[self.__curr_class__] = self.__student_to_average__
        self.__student_to_average__ = dict()

        self.__class_to_grades__[self.__curr_class__] = self.__grade_to_students__
        self.__grade_to_students__ = dict()

        return tree

    def students(self, tree):
        return tree

    def student(self, tree):

        if self.__curr_name__ in self.__student_to_average__:
            raise lark.GrammarError()

        self.__number_of_students__ += 1

        avg : float = sum(self.__curr_grades__) / len(self.__curr_grades__)
        self.__student_to_average__[self.__curr_name__] = avg
        self.__curr_grades__.clear()


        query : str = (f"{annotate('INSERT INTO', 36, 1)} {annotate('Resultado', 33, 1)} " +
            f"(StudentName, Grade, Date, Class) {annotate('VALUES', 36, 1)} " +
            f"('{self.__curr_name__}', '{'%.2f' % avg}', '{datetime.date.today()}', " +
            f"'{self.__curr_class__}');"
       )
        self.__sql_queries__.append(query)

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

        self.__curr_name__ = name

        return name

    def GRADE(self, tree):

        grade : int = int(tree)

        if grade not in self.__grade_to_students__:
            self.__grade_to_students__[grade] = set()
        #self.__grade_to_students__[grade].append(self.__curr_name__)
        self.__grade_to_students__[grade].add(self.__curr_name__)

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
        TURMA A
        tiago (18, 19).
        TURMA D
        ana (12, 13, 15, 12, 13, 15, 14);
        joao (9,7,3,6,9,12);
        xico (12,16).
        TURMA C
        rita (14, 14, 18).
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
            print(f"==> Test '{annotate(t, 1)}' {annotate('passed', 32, 1)}!", file=sys.stderr)

        except lark.UnexpectedCharacters:
            print(f"==> Test '{annotate(t, 1)}' {annotate('failed', 31, 1)}!", file=sys.stderr)

        except lark.GrammarError:
            print(f"==> Test '{annotate(t, 1)}' {annotate('failed', 31, 1)}!", file=sys.stderr)

        print("\n")


if __name__ == '__main__':
    main()

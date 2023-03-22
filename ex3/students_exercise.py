#!/usr/bin/env python3

import lark
import typing
import sys
import datetime
import io

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
students_class : CLASS CLASS_ID students "."
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

class HtmlTableWriter:

    __string_buffer__ : io.StringIO
    __grades__        : dict[str, [list[int]]]


    def __init__(self):
        self.__string_buffer__ = io.StringIO()
        self.__grades__        = None

    def __enter__(self):
        self.begin()
        return self

    def __exit__(self, *options):
        self.end()
        self.__dump__()

    def begin(self):

        self.__string_buffer__.write(
            '<!DOCTYPE html>\n<html>\n\t<head>\n\t\t<meta charset="utf-8"/>\n' +
            '\t\t<title>Classes</title>\n\t</head>\n'
        )

        self.__string_buffer__.write('\t<body>\n')

    def new_class(self, nclass):
        self.__grades__ = dict()
        self.__string_buffer__.write(f'\t\t<h1>{nclass}</h1>\n')

    def new_student(self, student : str, grades : list[int]):
        self.__grades__[student] = list(grades)

    def end_class(self):

        max_num_of_grades : int = max(map(lambda e: len(e[1]), self.__grades__.items()))

        self.__string_buffer__.write('\t\t<table>\n\t\t\t<tr>\n')

        self.__string_buffer__.write('\t\t\t\t<th>Nome</th>\n')
        for i in range(1, max_num_of_grades + 1):
            self.__string_buffer__.write(f'\t\t\t\t<th>Nota{i}</th>\n')
        self.__string_buffer__.write('\t\t\t\t<th>Média</th>\n')
        self.__string_buffer__.write('\t\t\t</tr>\n')


        for (stu, grades) in self.__grades__.items():
            self.__string_buffer__.write('\t\t\t<tr>\n')

            self.__string_buffer__.write(f'\t\t\t\t<td>{stu}</td>\n')
            for g in grades:
                self.__string_buffer__.write(f'\t\t\t\t<td>{g}</td>\n')
            for i in range(len(grades), max_num_of_grades):
                self.__string_buffer__.write('\t\t\t\t<td>-</td>\n')

            avg : float = sum(grades) / max_num_of_grades
            self.__string_buffer__.write(f'\t\t\t\t<td>{"%.2f" % avg}</td>\n')


        self.__string_buffer__.write('\t\t\t</tr>\n')
        self.__string_buffer__.write('\t\t</table>\n')

    def end(self):
        self.__string_buffer__.write('\t</body>\n</html>\n')

    def __dump__(self):
        with open('classes.html', 'w') as ofh:
            ofh.write(self.__string_buffer__.getvalue())


class ClassTransformer(lark.Transformer):

    __number_of_students__ : int

    __class_to_students__  : dict[str, dict[str, float]]
    __student_to_average__ : dict[str, float]
    __curr_grades__        : list[int]

    __class_to_grades__    : dict[str, dict[int, set[str]]]
    __grade_to_students__  : dict[int, set[str]]

    __curr_class__         : str
    __curr_name__          : str

    __sql_queries__        : list[str]

    __html_writer__        : HtmlTableWriter


    def __init__(self, hw : HtmlTableWriter):
        self.__number_of_students__ = 0

        self.__class_to_students__  = dict()
        self.__student_to_average__ = dict()
        self.__curr_grades__        = list()

        self.__class_to_grades__    = dict()
        self.__grade_to_students__  = dict()

        self.__curr_class__         = None
        self.__curr_name__          = None

        self.__sql_queries__        = list()

        self.__html_writer__        = hw


    def output_data(self):

        print(f"Number of students: {annotate(self.__number_of_students__, 1)}")

        with open('classes.md', 'w') as md_file_handle:

            md_file_handle.write('# Visualizador de turmas\n')

            html_writer : HtmlTableWriter = HtmlTableWriter()

            for (students_class, students_dict) in self.__class_to_students__.items():

                md_file_handle.write(f"## Turma {students_class}\n")

                list_buffer  : io.StringIO = io.StringIO()
                list_buffer.write('### Lista de alunos\n')

                table_buffer : io.StringIO = io.StringIO()
                table_buffer.write('### Notas\n| Aluno | Media |\n|  --------  |  -------  |\n')

                for (student, avg) in students_dict.items():

                    print(
                        f"Average grade for student {annotate(student, 1)} " +
                        f"of class {annotate(students_class, 1)}: " +
                        f"{annotate('%.2f' % avg, 1, (32 if avg >= 9.5 else 31))}"
                    )

                    list_buffer.write(f"- {student}\n")
                    table_buffer.write(f"| {student} | {'%.2f' % avg} |\n")

                md_file_handle.write(list_buffer.getvalue())
                md_file_handle.write('\n')
                md_file_handle.write(table_buffer.getvalue())
                md_file_handle.write('\n')


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

    def start(self, tree : lark.Tree):
        return self

    def students_class(self, tree : lark.Tree):

        self.__class_to_students__[self.__curr_class__] = self.__student_to_average__
        self.__student_to_average__ = dict()

        self.__class_to_grades__[self.__curr_class__] = self.__grade_to_students__
        self.__grade_to_students__ = dict()

        self.__html_writer__.end_class()

        return tree : lark.Tree

    def students(self, tree : lark.Tree):
        return tree : lark.Tree

    def student(self, tree : lark.Tree):

        if self.__curr_name__ in self.__student_to_average__:
            raise lark.GrammarError()

        self.__number_of_students__ += 1

        self.__html_writer__.new_student(self.__curr_name__, self.__curr_grades__)

        avg : float = sum(self.__curr_grades__) / len(self.__curr_grades__)
        self.__student_to_average__[self.__curr_name__] = avg
        self.__curr_grades__.clear()


        query : str = (f"{annotate('INSERT INTO', 36, 1)} {annotate('Resultado', 33, 1)} " +
            f"(StudentName, Grade, Date, Class) {annotate('VALUES', 36, 1)} " +
            f"('{self.__curr_name__}', '{'%.2f' % avg}', '{datetime.date.today()}', " +
            f"'{self.__curr_class__}');"
        )
        self.__sql_queries__.append(query)

        return tree : lark.Tree


    def grades(self, tree : lark.Tree):
        return tree : lark.Tree

    def CLASS(self, tree : lark.Tree):
        return lark.Discard

    def CLASS_ID(self, tree : lark.Tree):

        class_id : str = str(tree : lark.Tree)
        if class_id in self.__class_to_students__:
            raise lark.GrammarError()

        self.__html_writer__.new_class(class_id)

        self.__curr_class__ = class_id
        return lark.Discard


    def NAME(self, tree : lark.Tree):
        name : str = str(tree : lark.Tree)
        self.__curr_name__ = name
        return name

    def GRADE(self, tree : lark.Tree):

        grade : int = int(tree : lark.Tree)

        if grade not in self.__grade_to_students__:
            self.__grade_to_students__[grade] = set()

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
        ''',

        '''
        TURMA A
        henrique (12, 15);
        afonso (11);
        afonso (14).
        ''',
        '''
        TURMA A
        joao (11).
        TURMA A
        joana (12).
        '''
    ]


    parser : lark.Lark = lark.Lark(grammar)

    with HtmlTableWriter() as htw:

        for t in tests:

            try:
                tree : lark.ParseTree = parser.parse(t)
                ct : ClassTransformer = ClassTransformer(htw)
                ct.transform(tree)
                ct.output_data()

                print(f"==> Test '{annotate(t, 1)}' {annotate('passed', 32, 1)}!", file=sys.stderr)

            except lark.UnexpectedCharacters:
                print(f"==> Test '{annotate(t, 1)}' {annotate('failed', 31, 1)}!", file=sys.stderr)

            except lark.GrammarError:
                print(f"==> Test '{annotate(t, 1)}' {annotate('failed', 31, 1)}!", file=sys.stderr)

            print("\n")


if __name__ == '__main__':
    main()

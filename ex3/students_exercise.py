#!/usr/bin/env python3

import lark
import typing
import sys
import datetime
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

    _string_buffer: io.StringIO
    _grades: dict[str, [list[int]]]

    def __init__(self):
        self._string_buffer = io.StringIO()
        self._grades        = None

    def __enter__(self):
        self.begin()
        return self

    def __exit__(self, *options):
        self.end()
        self._dump()

    def begin(self):

        self._string_buffer.write(
            '<!DOCTYPE html>\n<html>\n\t<head>\n\t\t<meta charset="utf-8"/>\n'
            + '\t\t<title>Classes</title>\n\t</head>\n'
        )

        self._string_buffer.write('\t<body>\n')

    def new_class(self, nclass):
        self._grades = dict()
        self._string_buffer.write(f'\t\t<h1>{nclass}</h1>\n')

    def new_student(self, student: str, grades: list[int]):
        self._grades[student] = list(grades)

    def end_class(self):

        max_num_of_grades: int = max(map(lambda e: len(e[1]), self._grades.items()))

        self._string_buffer.write('\t\t<table>\n\t\t\t<tr>\n')

        self._string_buffer.write('\t\t\t\t<th>Nome</th>\n')
        for i in range(1, max_num_of_grades + 1):
            self._string_buffer.write(f'\t\t\t\t<th>Nota{i}</th>\n')
        self._string_buffer.write('\t\t\t\t<th>Média</th>\n')
        self._string_buffer.write('\t\t\t</tr>\n')

        for (stu, grades) in self._grades.items():
            self._string_buffer.write('\t\t\t<tr>\n')

            self._string_buffer.write(f'\t\t\t\t<td>{stu}</td>\n')
            for g in grades:
                self._string_buffer.write(f'\t\t\t\t<td>{g}</td>\n')
            for i in range(len(grades), max_num_of_grades):
                self._string_buffer.write('\t\t\t\t<td>-</td>\n')

            avg: float = sum(grades) / max_num_of_grades
            self._string_buffer.write(f'\t\t\t\t<td>{"%.2f" % avg}</td>\n')

        self._string_buffer.write('\t\t\t</tr>\n')
        self._string_buffer.write('\t\t</table>\n')

    def end(self):
        self._string_buffer.write('\t</body>\n</html>\n')

    def _dump(self):
        with open('classes.html', 'w') as ofh:
            ofh.write(self._string_buffer.getvalue())


class ClassTransformer(lark.Transformer):

    _number_of_students: int

    _class_to_students: dict[str, dict[str, float]]
    _student_to_average: dict[str, float]
    _curr_grades: list[int]

    _class_to_grades: dict[str, dict[int, set[str]]]
    _grade_to_students: dict[int, set[str]]

    _curr_class: str
    _curr_name: str

    _sql_queries: list[str]

    _html_writer: HtmlTableWriter

    def __init__(self, hw: HtmlTableWriter):
        self._number_of_students = 0

        self._class_to_students  = dict()
        self._student_to_average = dict()
        self._curr_grades        = list()

        self._class_to_grades    = dict()
        self._grade_to_students  = dict()

        self._curr_class         = None
        self._curr_name          = None

        self._sql_queries        = list()

        self._html_writer        = hw

    def output_data(self):

        print(f"Number of students: {annotate(self._number_of_students, 1)}")

        with open('classes.md', 'w') as md_file_handle:

            md_file_handle.write('# Visualizador de turmas\n')

            for (students_class, students_dict) in self._class_to_students.items():

                md_file_handle.write(f"## Turma {students_class}\n")

                list_buffer: io.StringIO = io.StringIO()
                list_buffer.write('### Lista de alunos\n')

                table_buffer: io.StringIO = io.StringIO()
                table_buffer.write('### Notas\n| Aluno | Media |\n|  --------  |  -------  |\n')

                for (student, avg) in students_dict.items():

                    print(
                        f"Average grade for student {annotate(student, 1)} "
                        + f"of class {annotate(students_class, 1)}: "
                        + f"{annotate('%.2f' % avg, 1, (32 if avg >= 9.5 else 31))}"
                    )

                    list_buffer.write(f"- {student}\n")
                    table_buffer.write(f"| {student} | {'%.2f' % avg} |\n")

                md_file_handle.write(list_buffer.getvalue())
                md_file_handle.write('\n')
                md_file_handle.write(table_buffer.getvalue())
                md_file_handle.write('\n')

        for (students_class, grades_dict) in self._class_to_grades.items():

            for (grade, students_set) in (
                sorted(grades_dict.items(), key=lambda e: e[0], reverse=True)
            ):

                print(
                    f"Students of class {annotate(students_class, 1)} that scored "
                    + f"{annotate(grade, 1)}: {annotate(students_set, 1)}"
                )

        for q in self._sql_queries:
            print(q)

    def start(self, tree: lark.Tree):
        return self

    def students_class(self, tree: lark.Tree):

        self._class_to_students[self._curr_class] = self._student_to_average
        self._student_to_average = dict()

        self._class_to_grades[self._curr_class] = self._grade_to_students
        self._grade_to_students = dict()

        self._html_writer.end_class()

        return tree

    def students(self, tree: lark.Tree):
        return tree

    def student(self, tree: lark.Tree):

        if self._curr_name in self._student_to_average:
            raise lark.GrammarError()

        self._number_of_students += 1

        self._html_writer.new_student(self._curr_name, self._curr_grades)

        avg: float = sum(self._curr_grades) / len(self._curr_grades)
        self._student_to_average[self._curr_name] = avg
        self._curr_grades.clear()

        query: str = (f"{annotate('INSERT INTO', 36, 1)} {annotate('Resultado', 33, 1)} "
                      + f"(StudentName, Grade, Date, Class) {annotate('VALUES', 36, 1)} "
                      + f"('{self._curr_name}', '{'%.2f' % avg}', '{datetime.date.today()}', "
                      + f"'{self._curr_class}');"
                      )
        self._sql_queries.append(query)

        return tree

    def grades(self, tree: lark.Tree):
        return tree

    def CLASS(self, tree: lark.Tree):
        return lark.Discard

    def CLASS_ID(self, tree: lark.Tree):

        class_id: str = str(tree)
        if class_id in self._class_to_students:
            raise lark.GrammarError()

        self._html_writer.new_class(class_id)

        self._curr_class = class_id
        return lark.Discard

    def NAME(self, tree: lark.Tree):
        name: str = str(tree)
        self._curr_name = name
        return name

    def GRADE(self, tree: lark.Tree):

        grade: int = int(tree)

        if grade not in self._grade_to_students:
            self._grade_to_students[grade] = set()

        self._grade_to_students[grade].add(self._curr_name)

        self._curr_grades.append(grade)

        return grade


def main():

    tests: list[str] = [
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

    parser: lark.Lark = lark.Lark(grammar)

    with HtmlTableWriter() as htw:

        for t in tests:

            try:
                tree: lark.ParseTree = parser.parse(t)
                ct: ClassTransformer = ClassTransformer(htw)
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

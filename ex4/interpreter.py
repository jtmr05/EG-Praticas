#!/usr/bin/env python3

import lark
import lark.visitors
import lark.tree
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


class ClassInterpreter(lark.visitors.Interpreter):

    # 1.1
    _number_of_students: int

    # 1.2
    _class_to_students: dict[str, dict[str, float]]

    # 1.3
    _class_to_grades: dict[str, dict[int, set[str]]]

    # 1.4
    _sql_queries: list[str]

    def __init__(self):

        self._number_of_students = 0
        self._class_to_students = dict()
        self._class_to_grades = dict()
        self._sql_queries = list()

    def output_data(self):

        print(f"Number of students: {annotate(self._number_of_students, 1)}")

        with open('classes.md', 'w') as md_file_handle:

            md_file_handle.write('# Visualizador de turmas\n')

            for (class_id, students_dict) in self._class_to_students.items():

                md_file_handle.write(f"## Turma {class_id}\n")

                list_buffer: io.StringIO = io.StringIO()
                list_buffer.write('### Lista de alunos\n')

                table_buffer: io.StringIO = io.StringIO()
                table_buffer.write('### Notas\n| Aluno | Media |\n|  --------  |  -------  |\n')

                for (student, avg) in students_dict.items():

                    print(
                        f"Average grade for student {annotate(student, 1)} " + f"of class {annotate(class_id, 1)}: " +
                        f"{annotate('%.2f' % avg, 1, (32 if avg >= 9.5 else 31))}"
                    )

                    list_buffer.write(f"- {student}\n")
                    table_buffer.write(f"| {student} | {'%.2f' % avg} |\n")

                md_file_handle.write(list_buffer.getvalue())
                md_file_handle.write('\n')
                md_file_handle.write(table_buffer.getvalue())
                md_file_handle.write('\n')

        for (class_id, grades_dict) in self._class_to_grades.items():
            for (grade, students_set) in (
                sorted(grades_dict.items(), key=lambda e: e[0], reverse=True)
            ):
                print(
                    f"Students of class {annotate(class_id, 1)} that scored "
                    + f"{annotate(grade, 1)}: {annotate(students_set, 1)}"
                )

        for q in self._sql_queries:
            print(q)

    def start(self, tree: lark.Tree):

        for sclass in tree.children:

            (class_id, students_dict, grades_dict) = self.visit(sclass)
            if class_id in self._class_to_students or class_id in self._class_to_grades:
                raise lark.GrammarError()

            self._class_to_students[class_id] = students_dict
            self._class_to_grades[class_id] = grades_dict

    def students_class(self, tree: lark.Tree):

        (student_to_avg, grade_to_students) = self.visit(tree.children[2])

        for (name, avg) in student_to_avg.items():

            query: str = (f"{annotate('INSERT INTO', 36, 1)} {annotate('Resultado', 33, 1)} "
                + f"(StudentName, Grade, Date, Class) {annotate('VALUES', 36, 1)} "
                + f"('{name}', '{'%.2f' % avg}', '{datetime.date.today()}', "
                          + f"'{str(tree.children[1].value)}');"
                          )
            self._sql_queries.append(query)

        return (str(tree.children[1].value), student_to_avg, grade_to_students)

    def students(self, tree: lark.Tree):

        student_to_avg: dict[str, float] = dict()
        grade_to_students: dict[int, set[str]] = dict()

        for student in tree.children:

            (name, grades_list) = self.visit(student)
            if name in student_to_avg:
                raise lark.GrammarError()

            grades_sum: int = 0
            for g in grades_list:
                grades_sum += g

                if g not in grade_to_students:
                    grade_to_students[g] = set()

                grade_to_students[g].add(name)

            student_to_avg[name] = grades_sum / len(grades_list)

        return (student_to_avg, grade_to_students)

    def student(self, tree: lark.Tree):

        self._number_of_students += 1

        grades_list: list[int] = self.visit(tree.children[1])

        return (str(tree.children[0].value), grades_list)

    def grades(self, tree: lark.Tree):

        return [int(g.value) for g in tree.children]


def main():

    tests: list[str] = [
        '''TURMA A
        ana (1, 2, 3);
        ze (2, 4);
        rui(12).

        TURMA PL
        zeca (2);
        rita (2, 4, 6).

        TURMA EG
        rosa (10, 11, 12, 13).
        '''
    ]

    parser: lark.Lark = lark.Lark(grammar)

    for t in tests:

        try:
            tree: lark.ParseTree = parser.parse(t)
            ci: ClassInterpreter = ClassInterpreter()
            ci.visit(tree)
            ci.output_data()

            print(f"==> test '{annotate(t, 1)}' {annotate('passed', 32, 1)}!", file=sys.stderr)

        except lark.UnexpectedCharacters:
            print(f"==> test '{annotate(t, 1)}' {annotate('failed', 31, 1)}!", file=sys.stderr)

        except lark.GrammarError:
            print(f"==> test '{annotate(t, 1)}' {annotate('failed', 31, 1)}!", file=sys.stderr)

        print("\n")


if __name__ == '__main__':
    main()

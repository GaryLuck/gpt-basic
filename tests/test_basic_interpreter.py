import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from basic_interpreter import BasicError, TinyBasicInterpreter


class TinyBasicInterpreterTests(unittest.TestCase):
    def make_interpreter(self, program_lines):
        interp = TinyBasicInterpreter()
        interp.program = dict(program_lines)
        return interp

    def run_program_capture(self, interp: TinyBasicInterpreter) -> str:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            interp.run_program()
        return buffer.getvalue()

    def test_hello_world_program(self):
        interp = self.make_interpreter(
            {
                10: 'PRINT "Hello, World!"',
                20: "END",
            }
        )
        output = self.run_program_capture(interp)
        self.assertEqual(output, "Hello, World!\n")

    def test_countdown_flow(self):
        interp = self.make_interpreter(
            {
                10: 'PRINT "Countdown from 3"',
                20: "LET N = 3",
                30: "IF N < 0 THEN 70",
                40: "PRINT N",
                50: "LET N = N - 1",
                60: "GOTO 30",
                70: 'PRINT "Blast off!"',
                80: "END",
            }
        )
        output = self.run_program_capture(interp)
        self.assertEqual(output, "Countdown from 3\n3\n2\n1\n0\nBlast off!\n")

    def test_array_sum_program(self):
        interp = self.make_interpreter(
            {
                10: "DIM A(5)",
                20: "LET A(0) = 10",
                30: "LET A(1) = 20",
                40: "LET A(2) = 30",
                50: "LET A(3) = 40",
                60: "LET A(4) = 50",
                70: "LET S = 0",
                80: "LET I = 0",
                90: "IF I >= 5 THEN 130",
                100: "LET S = S + A(I)",
                110: "LET I = I + 1",
                120: "GOTO 90",
                130: 'PRINT "Sum:", S',
                140: "END",
            }
        )
        output = self.run_program_capture(interp)
        self.assertEqual(output, "Sum: 150\n")

    def test_prime_checker_program(self):
        interp = self.make_interpreter(
            {
                10: "LET N = 17",
                20: "LET I = 2",
                30: "IF I * I > N THEN 70",
                40: "LET R = N - (N / I) * I",
                50: "IF R == 0 THEN 90",
                60: "LET I = I + 1",
                65: "GOTO 30",
                70: 'PRINT N, "is prime"',
                80: "END",
                90: 'PRINT N, "is not prime"',
                100: "END",
            }
        )
        output = self.run_program_capture(interp)
        self.assertEqual(output, "17 is prime\n")

    def test_expression_precedence_and_integer_division(self):
        interp = TinyBasicInterpreter()
        self.assertEqual(interp.eval_expr("2 + 3 * 4"), 14)
        self.assertEqual(interp.eval_expr("(2 + 3) * 4"), 20)
        self.assertEqual(interp.eval_expr("2 ** 3 ** 2"), 512)
        self.assertEqual(interp.eval_expr("7 / 3"), 2)
        self.assertEqual(interp.eval_expr("7 // 3"), 2)
        self.assertEqual(interp.eval_expr("7 % 3"), 1)

    def test_undefined_line_number_error(self):
        interp = self.make_interpreter({10: "GOTO 999"})
        with self.assertRaisesRegex(BasicError, r"Line 10: Undefined line number: 999"):
            interp.run_program()

    def test_undeclared_array_error(self):
        interp = self.make_interpreter({10: "LET A(0) = 1"})
        with self.assertRaisesRegex(BasicError, r"Line 10: Undeclared array: A"):
            interp.run_program()

    def test_array_out_of_bounds_error(self):
        interp = self.make_interpreter(
            {
                10: "DIM A(2)",
                20: "LET A(2) = 5",
            }
        )
        with self.assertRaisesRegex(
            BasicError, r"Line 20: Array index out of bounds: A\(2\)"
        ):
            interp.run_program()

    def test_save_and_load_roundtrip(self):
        interp = self.make_interpreter(
            {
                20: "END",
                10: 'PRINT "Hello"',
            }
        )
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "hello.bas"
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                interp.save_program(str(path))
            self.assertIn("Program saved to", buffer.getvalue())

            restored = TinyBasicInterpreter()
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                restored.load_program(str(path))
            self.assertIn("Program loaded from", buffer.getvalue())
            self.assertEqual(restored.program, {10: 'PRINT "Hello"', 20: "END"})


if __name__ == "__main__":
    unittest.main()

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class BasicError(Exception):
    """Interpreter error with user-friendly messages."""


@dataclass
class ProgramContext:
    line_numbers: List[int]
    line_to_index: Dict[int, int]


class ExpressionParser:
    """Recursive-descent parser for integer expressions."""

    TOKEN_RE = re.compile(
        r'\s*(?:(\d+)|([A-Za-z])|(==|!=|<=|>=|\*\*|//|[()+\-*/%,<>]))'
    )

    def __init__(self, text: str, interpreter: "TinyBasicInterpreter"):
        self.text = text
        self.interpreter = interpreter
        self.tokens = self._tokenize(text)
        self.pos = 0

    def _tokenize(self, text: str) -> List[Tuple[str, str]]:
        tokens: List[Tuple[str, str]] = []
        idx = 0
        while idx < len(text):
            m = self.TOKEN_RE.match(text, idx)
            if not m:
                if text[idx].isspace():
                    idx += 1
                    continue
                raise BasicError(f"Invalid expression near: {text[idx:idx+20]!r}")
            number, ident, op = m.groups()
            if number is not None:
                tokens.append(("NUMBER", number))
            elif ident is not None:
                tokens.append(("IDENT", ident.upper()))
            else:
                tokens.append(("OP", op))
            idx = m.end()
        tokens.append(("EOF", ""))
        return tokens

    def _peek(self) -> Tuple[str, str]:
        return self.tokens[self.pos]

    def _advance(self) -> Tuple[str, str]:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _match_op(self, op: str) -> bool:
        kind, value = self._peek()
        if kind == "OP" and value == op:
            self._advance()
            return True
        return False

    def _expect_op(self, op: str) -> None:
        if not self._match_op(op):
            raise BasicError(f"Expected '{op}' in expression")

    def parse_expression(self) -> int:
        value = self._parse_additive()
        kind, token = self._peek()
        if kind != "EOF":
            raise BasicError(f"Unexpected token in expression: {token!r}")
        return value

    def parse_condition(self) -> bool:
        left = self._parse_additive()
        kind, token = self._peek()
        if kind != "OP" or token not in {"==", "!=", "<", ">", "<=", ">="}:
            raise BasicError("Expected comparison operator in IF condition")
        self._advance()
        right = self._parse_additive()
        kind, extra = self._peek()
        if kind != "EOF":
            raise BasicError(f"Unexpected token in condition: {extra!r}")

        if token == "==":
            return left == right
        if token == "!=":
            return left != right
        if token == "<":
            return left < right
        if token == ">":
            return left > right
        if token == "<=":
            return left <= right
        return left >= right

    def _parse_additive(self) -> int:
        value = self._parse_multiplicative()
        while True:
            if self._match_op("+"):
                value += self._parse_multiplicative()
            elif self._match_op("-"):
                value -= self._parse_multiplicative()
            else:
                break
        return value

    def _parse_multiplicative(self) -> int:
        value = self._parse_power()
        while True:
            if self._match_op("*"):
                value *= self._parse_power()
            elif self._match_op("/") or self._match_op("//"):
                divisor = self._parse_power()
                value = value // divisor
            elif self._match_op("%"):
                value %= self._parse_power()
            else:
                break
        return value

    def _parse_power(self) -> int:
        # Right-associative exponentiation
        base = self._parse_unary()
        if self._match_op("**"):
            exp = self._parse_power()
            return base ** exp
        return base

    def _parse_unary(self) -> int:
        if self._match_op("+"):
            return self._parse_unary()
        if self._match_op("-"):
            return -self._parse_unary()
        return self._parse_primary()

    def _parse_primary(self) -> int:
        kind, token = self._peek()
        if kind == "NUMBER":
            self._advance()
            return int(token)

        if kind == "IDENT":
            self._advance()
            name = token
            if self._match_op("("):
                index = self._parse_additive()
                self._expect_op(")")
                return self.interpreter.get_array_value(name, index)
            return self.interpreter.get_variable(name)

        if kind == "OP" and token == "(":
            self._advance()
            value = self._parse_additive()
            self._expect_op(")")
            return value

        raise BasicError(f"Unexpected token in expression: {token!r}")


class TinyBasicInterpreter:
    PROGRAM_LINE_RE = re.compile(r"^\s*(\d+)\s*(.*)$")

    def __init__(self) -> None:
        self.program: Dict[int, str] = {}
        self.vars: Dict[str, int] = {chr(c): 0 for c in range(ord("A"), ord("Z") + 1)}
        self.arrays: Dict[str, List[int]] = {}

    def repl(self) -> None:
        while True:
            try:
                line = input("> ")
            except EOFError:
                print("Goodbye!")
                break

            line = line.rstrip("\n")
            if not line.strip():
                continue

            try:
                if self._handle_program_entry(line):
                    continue
                if self._handle_command(line):
                    continue
                print("? Unknown command")
            except BasicError as exc:
                print(f"? {exc}")

    def _handle_program_entry(self, line: str) -> bool:
        m = self.PROGRAM_LINE_RE.match(line)
        if not m:
            return False

        line_no = int(m.group(1))
        if line_no <= 0:
            raise BasicError("Line number must be positive")
        statement = m.group(2).strip()
        if statement:
            self.program[line_no] = statement
        else:
            self.program.pop(line_no, None)
        return True

    def _handle_command(self, line: str) -> bool:
        text = line.strip()
        upper = text.upper()

        if upper == "RUN":
            self.run_program()
            return True
        if upper == "LIST":
            self.list_program()
            return True
        if upper == "NEW":
            self.program.clear()
            self.reset_runtime_state()
            print("Program cleared")
            return True
        if upper == "QUIT":
            print("Goodbye!")
            raise SystemExit(0)

        if upper.startswith("LOAD "):
            filename = text[5:].strip()
            if not filename:
                raise BasicError("LOAD requires a filename")
            self.load_program(filename)
            return True

        if upper.startswith("SAVE "):
            filename = text[5:].strip()
            if not filename:
                raise BasicError("SAVE requires a filename")
            self.save_program(filename)
            return True

        return False

    def list_program(self) -> None:
        for line_no in sorted(self.program):
            print(f"{line_no} {self.program[line_no]}")

    def reset_runtime_state(self) -> None:
        for k in self.vars:
            self.vars[k] = 0
        self.arrays.clear()

    def run_program(self) -> None:
        self.reset_runtime_state()
        if not self.program:
            return

        line_numbers = sorted(self.program)
        line_to_index = {line_no: i for i, line_no in enumerate(line_numbers)}
        context = ProgramContext(line_numbers=line_numbers, line_to_index=line_to_index)

        pc = 0
        while 0 <= pc < len(context.line_numbers):
            line_no = context.line_numbers[pc]
            stmt = self.program[line_no]
            try:
                next_pc = self.execute_statement(stmt, context, pc)
                if next_pc is None:
                    pc += 1
                elif next_pc == -1:
                    break
                else:
                    pc = next_pc
            except BasicError as exc:
                raise BasicError(f"Line {line_no}: {exc}") from exc
            except ZeroDivisionError:
                raise BasicError(f"Line {line_no}: Division by zero") from None

    def execute_statement(
        self,
        stmt: str,
        context: ProgramContext,
        current_pc: int,
    ) -> Optional[int]:
        text = stmt.strip()
        upper = text.upper()

        if upper.startswith("PRINT"):
            payload = text[5:].strip()
            self._exec_print(payload)
            return None

        if upper.startswith("LET"):
            payload = text[3:].strip()
            self._exec_let(payload)
            return None

        if upper.startswith("GOTO"):
            payload = text[4:].strip()
            target = self._parse_positive_int(payload, "GOTO")
            return self._resolve_jump(target, context)

        if upper.startswith("IF"):
            payload = text[2:].strip()
            return self._exec_if(payload, context)

        if upper.startswith("DIM"):
            payload = text[3:].strip()
            self._exec_dim(payload)
            return None

        if upper == "END":
            return -1

        raise BasicError(f"Unknown statement: {stmt}")

    def _exec_print(self, payload: str) -> None:
        if payload == "":
            print()
            return

        items = self._split_csv(payload)
        outputs: List[str] = []
        for item in items:
            piece = item.strip()
            if len(piece) >= 2 and piece[0] == '"' and piece[-1] == '"':
                outputs.append(piece[1:-1])
            else:
                outputs.append(str(self.eval_expr(piece)))
        print(" ".join(outputs))

    def _exec_let(self, payload: str) -> None:
        if "=" not in payload:
            raise BasicError("LET requires '='")
        lhs, rhs = payload.split("=", 1)
        lhs = lhs.strip()
        rhs = rhs.strip()
        if not lhs:
            raise BasicError("Invalid LET target")
        value = self.eval_expr(rhs)

        arr_match = re.fullmatch(r"([A-Za-z])\((.*)\)", lhs)
        if arr_match:
            name = arr_match.group(1).upper()
            index = self.eval_expr(arr_match.group(2).strip())
            self.set_array_value(name, index, value)
            return

        if re.fullmatch(r"[A-Za-z]", lhs):
            self.set_variable(lhs.upper(), value)
            return

        raise BasicError("Invalid LET target")

    def _exec_if(self, payload: str, context: ProgramContext) -> Optional[int]:
        parts = re.split(r"\bTHEN\b", payload, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) != 2:
            raise BasicError("IF requires THEN")

        cond_text = parts[0].strip()
        target_text = parts[1].strip()
        if not cond_text or not target_text:
            raise BasicError("Invalid IF-THEN syntax")

        condition = self.eval_condition(cond_text)
        if condition:
            target = self._parse_positive_int(target_text, "IF THEN")
            return self._resolve_jump(target, context)
        return None

    def _exec_dim(self, payload: str) -> None:
        m = re.fullmatch(r"([A-Za-z])\((.*)\)", payload)
        if not m:
            raise BasicError("Invalid DIM syntax")

        name = m.group(1).upper()
        size = self.eval_expr(m.group(2).strip())
        if size < 0:
            raise BasicError("Array size must be non-negative")
        self.arrays[name] = [0] * size

    def _resolve_jump(self, target_line: int, context: ProgramContext) -> int:
        if target_line not in context.line_to_index:
            raise BasicError(f"Undefined line number: {target_line}")
        return context.line_to_index[target_line]

    def _parse_positive_int(self, text: str, label: str) -> int:
        text = text.strip()
        if not re.fullmatch(r"\d+", text):
            raise BasicError(f"{label} requires a positive line number")
        val = int(text)
        if val <= 0:
            raise BasicError(f"{label} requires a positive line number")
        return val

    def eval_expr(self, text: str) -> int:
        parser = ExpressionParser(text, self)
        return parser.parse_expression()

    def eval_condition(self, text: str) -> bool:
        parser = ExpressionParser(text, self)
        return parser.parse_condition()

    def get_variable(self, name: str) -> int:
        name = name.upper()
        if not re.fullmatch(r"[A-Z]", name):
            raise BasicError(f"Invalid variable name: {name}")
        return self.vars[name]

    def set_variable(self, name: str, value: int) -> None:
        name = name.upper()
        if not re.fullmatch(r"[A-Z]", name):
            raise BasicError(f"Invalid variable name: {name}")
        self.vars[name] = int(value)

    def get_array_value(self, name: str, index: int) -> int:
        name = name.upper()
        if name not in self.arrays:
            raise BasicError(f"Undeclared array: {name}")
        arr = self.arrays[name]
        if index < 0 or index >= len(arr):
            raise BasicError(f"Array index out of bounds: {name}({index})")
        return arr[index]

    def set_array_value(self, name: str, index: int, value: int) -> None:
        name = name.upper()
        if name not in self.arrays:
            raise BasicError(f"Undeclared array: {name}")
        arr = self.arrays[name]
        if index < 0 or index >= len(arr):
            raise BasicError(f"Array index out of bounds: {name}({index})")
        arr[index] = int(value)

    def load_program(self, filename: str) -> None:
        path = Path(filename)
        if not path.exists():
            raise BasicError(f"File not found: {filename}")

        new_program: Dict[int, str] = {}
        try:
            with path.open("r", encoding="utf-8") as f:
                for raw in f:
                    line = raw.rstrip("\n")
                    if not line.strip():
                        continue
                    m = self.PROGRAM_LINE_RE.match(line)
                    if not m:
                        raise BasicError(f"Invalid program line in file: {line!r}")
                    line_no = int(m.group(1))
                    stmt = m.group(2).strip()
                    if stmt:
                        new_program[line_no] = stmt
        except OSError as exc:
            raise BasicError(f"Failed to load {filename}: {exc}") from exc

        self.program = new_program
        print(f"Program loaded from {filename}")

    def save_program(self, filename: str) -> None:
        path = Path(filename)
        try:
            with path.open("w", encoding="utf-8") as f:
                for line_no in sorted(self.program):
                    f.write(f"{line_no} {self.program[line_no]}\n")
        except OSError as exc:
            raise BasicError(f"Failed to save {filename}: {exc}") from exc

        print(f"Program saved to {filename}")

    def _split_csv(self, text: str) -> List[str]:
        parts: List[str] = []
        current: List[str] = []
        in_string = False
        i = 0
        while i < len(text):
            ch = text[i]
            if ch == '"':
                in_string = not in_string
                current.append(ch)
            elif ch == "," and not in_string:
                parts.append("".join(current).strip())
                current = []
            else:
                current.append(ch)
            i += 1

        if in_string:
            raise BasicError("Unterminated string literal")

        tail = "".join(current).strip()
        if tail:
            parts.append(tail)
        elif text.endswith(","):
            parts.append("")

        if any(p == "" for p in parts):
            raise BasicError("PRINT has empty argument")
        return parts


def main() -> None:
    interpreter = TinyBasicInterpreter()
    try:
        interpreter.repl()
    except SystemExit:
        raise
    except KeyboardInterrupt:
        print("\nGoodbye!")


if __name__ == "__main__":
    main()

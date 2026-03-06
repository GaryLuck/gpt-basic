# Tiny BASIC Interpreter
[![CI](https://github.com/GaryLuck/gpt-basic/actions/workflows/ci.yml/badge.svg)](https://github.com/GaryLuck/gpt-basic/actions/workflows/ci.yml)

A fully functional BASIC interpreter written in Python supporting classic BASIC features.

## Features

- **Variables**: Single letters A-Z (automatically initialized to 0)
- **Arrays**: Declare with DIM, access with subscripts
- **Integer Arithmetic**: +, -, *, /, //, %, ** (power)
- **Control Flow**: GOTO, IF-THEN
- **I/O**: PRINT with string literals and expressions
- **File Operations**: LOAD and SAVE programs

## Supported Commands

### Program Commands

- **PRINT** - Print comma-separated values and string literals
  ```basic
  10 PRINT "Hello, World!"
  20 PRINT "X =", X
  30 PRINT A, B, C
  ```

- **LET** - Assign values to variables or array elements
  ```basic
  10 LET A = 42
  20 LET B = A * 2 + 10
  30 LET C(5) = A + B
  ```

- **GOTO** - Jump to a line number
  ```basic
  10 GOTO 100
  ```

- **IF-THEN** - Conditional jump
  ```basic
  10 IF A > 10 THEN 100
  20 IF B == 0 THEN 200
  30 IF C != D THEN 50
  ```
  Supported operators: ==, !=, <, >, <=, >=

- **DIM** - Declare an array
  ```basic
  10 DIM A(10)
  20 DIM B(100)
  ```

- **END** - End program execution
  ```basic
  100 END
  ```

### Interactive Commands

- **RUN** - Execute the current program
- **LIST** - Display all program lines
- **NEW** - Clear the current program
- **LOAD filename** - Load a program from file
- **SAVE filename** - Save the current program to file
- **QUIT** - Exit the interpreter

## Usage

### Running the Interpreter

```bash
python3 basic_interpreter.py
```

### Running Tests

From the repository root:

```bash
python -m unittest -v
```

Alternative discovery command:

```bash
python -m unittest discover -s tests -v
```

Current test coverage includes:
- Core execution flow (RUN/LIST behavior via program execution tests)
- Control flow (`IF-THEN`, `GOTO`)
- Arrays (`DIM`, read/write, bounds checking)
- Expression parsing and integer arithmetic semantics
- Error handling (undefined line targets, undeclared arrays, invalid access)
- File roundtrip (`SAVE`/`LOAD`)

### Interactive Mode

```
> 10 PRINT "Hello, World!"
> 20 END
> LIST
10 PRINT "Hello, World!"
20 END
> RUN
Hello, World!
> SAVE hello.bas
Program saved to hello.bas
> NEW
Program cleared
> LOAD hello.bas
Program loaded from hello.bas
> RUN
Hello, World!
> QUIT
Goodbye!
```

### Example Programs

#### Fibonacci Sequence
```basic
10 PRINT "Fibonacci Sequence"
20 LET A = 0
30 LET B = 1
40 LET C = 1
50 PRINT A
60 PRINT B
70 IF C > 8 THEN 130
80 LET D = A + B
90 PRINT D
100 LET A = B
110 LET B = D
120 LET C = C + 1
130 GOTO 70
140 END
```

#### Countdown Timer
```basic
10 PRINT "Countdown from 10"
20 LET N = 10
30 IF N < 0 THEN 70
40 PRINT N
50 LET N = N - 1
60 GOTO 30
70 PRINT "Blast off!"
80 END
```

#### Array Sum
```basic
10 DIM A(5)
20 LET A(0) = 10
30 LET A(1) = 20
40 LET A(2) = 30
50 LET A(3) = 40
60 LET A(4) = 50
70 LET S = 0
80 LET I = 0
90 IF I >= 5 THEN 130
100 LET S = S + A(I)
110 LET I = I + 1
120 GOTO 90
130 PRINT "Sum:", S
140 END
```

#### Prime Number Checker
```basic
10 PRINT "Prime Number Checker"
20 LET N = 17
30 PRINT "Checking if", N, "is prime"
40 IF N <= 1 THEN 150
50 LET I = 2
60 IF I * I > N THEN 130
70 LET R = N - (N / I) * I
80 IF R == 0 THEN 150
90 LET I = I + 1
100 GOTO 60
130 PRINT N, "is prime"
140 END
150 PRINT N, "is not prime"
160 END
```

## Implementation Details

- Variables are case-sensitive (A-Z only)
- All arithmetic is integer-based
- Arrays are 0-indexed
- Line numbers can be any positive integer
- Lines are executed in numerical order unless redirected by GOTO or IF-THEN
- Division uses Python's integer division (//)
- Parentheses supported in arithmetic expressions

## Error Handling

The interpreter provides helpful error messages for:
- Undefined line numbers in GOTO/IF-THEN
- Array out of bounds access
- Undeclared arrays
- Invalid syntax
- Division by zero (from Python)
- Invalid expressions

## Limitations

- Only single-letter variables (A-Z)
- Only single-letter array names (A-Z)
- Integer arithmetic only (no floating-point)
- No INPUT statement (but can be added)
- No FOR-NEXT loops (but can be simulated with IF-GOTO)
- No subroutines (GOSUB/RETURN)
- No string variables

## Future Enhancements

Possible additions:
- INPUT statement for user input during execution
- FOR-NEXT loops
- GOSUB/RETURN for subroutines
- String variables
- More array operations
- REM for comments in code
- Multiple statements per line with colons

## License

Public domain - feel free to use and modify!

#!/usr/bin/env python
import argparse
import os
import struct
import sys


JUMPS = {
        'JGT': 1,
        'JEQ': 2,
        'JGE': 3,
        'JLT': 4,
        'JNE': 5,
        'JLE': 6,
        'JMP': 7,
        }
DESTS = {
        'A': 32,
        'D': 16,
        'M': 8,
        }
COMPS = {
        '0':   0x2A, # 1 0 1 0 1 0
        '1':   0x3F, # 1 1 1 1 1 1
        '-1':  0x3A, # 1 1 1 0 1 0
        'D':   0xC,  # 0 0 1 1 0 0
        'A':   0x30, # 1 1 0 0 0 0
        '!D':  0xD,  # 0 0 1 1 0 1
        '!A':  0x31, # 1 1 0 0 0 1
        '-D':  0xF,  # 0 0 1 1 1 1
        '-A':  0x33, # 1 1 0 0 1 1
        'D+1': 0x1F, # 0 1 1 1 1 1
        'A+1': 0x37, # 1 1 0 1 1 1
        'D-1': 0xE,  # 0 0 1 1 1 0
        'A-1': 0x32, # 1 1 0 0 1 0
        'D+A': 0x2,  # 0 0 0 0 1 0
        'D-A': 0x13, # 0 1 0 0 1 1
        'A-D': 0x7,  # 0 0 0 1 1 1
        'D&A': 0x0,  # 0 0 0 0 0 0
        'D|A': 0x15, # 0 1 0 1 0 1
        }
SYMBOLS = {
        'R0': 0,
        'R1': 1,
        'R2': 2,
        'R3': 3,
        'R4': 4,
        'R5': 5,
        'R6': 6,
        'R7': 7,
        'R8': 8,
        'R9': 9,
        'R10': 10,
        'R11': 11,
        'R12': 12,
        'R13': 13,
        'R14': 14,
        'R15': 15,
        'SCREEN': 16384,
        'KBD': 24576,
        }


def translate_c_instruction(source: str) -> int:
    """Translate a 'C' instruction from assembly to machine code.

    The assembly instruction has the format dest=comp;jump, where only 'comp'
    is mandatory. The machine code instrucion has the format 011accccccdddjjj,
    where:

    - `a` switches the lower input to the ALU between A or M
    - `c` selects the computation by setting ALU control bits
    - `d` selects the destination(s) of the computation (A, D and M)
    - `j` selects the jump behaviour

    Return the machine code instruction as an integer value.
    """
    jumpcode = 0
    destcode = 0
    a = 0
    instruction = source
    if ';' in instruction:
        instruction, jump = instruction.split(';')
        if jump not in JUMPS:
            raise ValueError(f"Invalid jump expression {jump}")
        jumpcode = JUMPS[jump]
    if '=' in instruction:
        dest, instruction = instruction.split('=')
        for ch in dest:
            if ch not in DESTS:
                raise ValueError(f"Invalid destination code {dest}")
            destcode |= DESTS[ch]
    if 'M' in instruction:
        # Set the 'a' bit, and then subsitute 'M' for 'A', for matching
        # the computation code.
        a = 0x1000
        instruction = instruction.replace('M', 'A')
    if instruction not in COMPS:
        raise ValueError(f"Invalid computation {instruction}")
    compcode = COMPS[instruction] << 6
    return 0xE000 | a | compcode | destcode | jumpcode


def assemble(source: str) -> list[int]:
    instructions = []
    symbols = dict(SYMBOLS)
    # First pass: remove comments and whitespace, assign line numbers and
    # identify line marker symbols
    n = 0
    for line in source.split('\n'):
        line = line.strip()

        if '//' in line:
            index = line.index('//')
            line = line[:index]
            line = line.strip()
        if line == '':
            continue

        if line[0] == '(':
            # A line marker -- assume that the line also ends with ')' and take
            # all the characters in between as the marker name. The marker line
            # itself does not translate into any machine code, and does not get
            # an instruction number.
            marker = line[1:-1]
            symbols[marker] = n
            continue

        instructions.append(line)
        n += 1

    # Second pass: translate each instruction into machine code.
    symbols = {}
    result = []
    register = 16
    for n, instruction in enumerate(instructions):
        if instruction[0] == '@':
            # An 'A' instruction. This will be either a literal integer
            # expression, or a text label. Text labels are either a reference
            # to a previously stored line marker, or a variable symbol. Each
            # time we encounter a variable symbol for the first time, we
            # allocate a new register for it, starting at address 16. Either
            # way, the high bit is set to 1 and combined with the low 15 bits
            # of the resolved integer address, to produce the final machine
            # code.
            label = instruction[1:]
            if label.isdigit():
                # Literal address
                address = int(label)
            elif label in symbols:
                # Existing variable symbol
                address = symbols[label]
            else:
                # New variable symbol
                address = register
                symbols[label] = address
                register += 1
            code = 0x7FFF & address
        else:
            code = translate_c_instruction(instruction)
        print(f'{instruction:12s}  {code:5d}   {code:016b}')
        result.append(code)
    return result


def hackify(codes: list[int]) -> str:
    """Translate a binary Hack program into a text representation.

    Takes an array of integer machine instructions, and produces the text
    representation as a single string.  The text representation has one
    instruction per line, each line containing sixteen '1' or '0' characters.
    """
    result = []
    for code in codes:
        text = f'{code:016b}'
        result.append(text)
    return '\n'.join(result)


def main(args):
    inpath = args.inputfile
    base, _ = os.path.splitext(inpath)
    outpath = f'{base}.bin'
    hackpath = f'{base}.hack'

    with open(inpath, 'r') as fp:
        source = fp.read()

    result = assemble(source)

    with open(outpath, 'wb') as fp:
        for code in result:
            fp.write(struct.pack('>H', code))

    hack = hackify(result)
    with open(hackpath, 'w') as fp:
        fp.write(hack)

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('inputfile')

    args = parser.parse_args()
    sys.exit(main(args))

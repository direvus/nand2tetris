#!/usr/bin/env python
"""HACK VM Translator: translate VM code into HACK assembly
"""
import argparse
import os
import sys


SEGMENT_NAMES = (
        'local', 'argument', 'this', 'that',
        'constant', 'static', 'temp', 'pointer')
SEGMENT_BASES = {
        'local': 'LCL',
        'argument': 'ARG',
        'this': 'THIS',
        'that': 'THAT',
        }
POINTER_BASES = {0: 'THIS', 1: 'THAT'}
TEMP_BASE = 5
STATIC_OPS = {
        'neg': (
            '@SP  // neg',
            'A=M-1',
            'M=-M',
            ),
        'add': (
            '@SP  // add',
            'AM=M-1',
            'D=M',
            'A=A-1',
            'M=D+M',
            ),
        'sub': (
            '@SP  // sub',
            'AM=M-1',
            'D=-M',
            'A=A-1',
            'M=D+M',
            ),
        'and': (
            '@SP  // and',
            'AM=M-1',
            'D=M',
            'A=A-1',
            'M=D&M',
            ),
        'or': (
            '@SP  // or',
            'AM=M-1',
            'D=M',
            'A=A-1',
            'M=D|M',
            ),
        'not': (
            '@SP  // not',
            'A=M-1',
            'M=!M',
            ),
        }
COMPARISON_OPS = {
        'eq': 'JEQ',
        'lt': 'JLT',
        'gt': 'JGT',
        }


def translate_push(context: str, segment: str, offset: int) -> tuple[str]:
    """Translate a `push` instruction into assembly.

    A push instruction takes a single value from some memory register and adds
    it to the top of the stack. More precisely, we find the base memory address
    of the memory segment, add the offset to it, take the value held in the
    register at that address, write it into the register currently pointed to
    by the stack pointer SP, and then advance SP to point at the next register.
    In assembly pseudo-code:

    1. addr = segment + offset
    2. *SP = *addr
    3. SP++

    Return the assembly code as an iterable of strings, one string per line.
    """
    if segment in SEGMENT_BASES:
        base = SEGMENT_BASES[segment]
        return (
                f'@{offset}  // push <- {segment} {offset}',
                'D=A',
                f'@{base}',
                'A=D+M',
                'D=M',
                '@SP',
                'M=M+1',
                'A=M-1',
                'M=D',
                )
    elif segment == 'constant':
        return (
                f'@{offset}  // push <- constant {offset}',
                'D=A',
                '@SP',
                'M=M+1',
                'A=M-1',
                'M=D',
                )
    elif segment == 'temp':
        addr = TEMP_BASE + offset
        return (
                f'@{addr}  // push <- temp {offset}',
                'D=M',
                '@SP',
                'M=M+1',
                'A=M-1',
                'M=D',
                )
    elif segment == 'static':
        return (
                f'@{context}.{offset}  // push <- static {offset}',
                'D=M',
                '@SP',
                'M=M+1',
                'A=M-1',
                'M=D',
                )
    elif segment == 'pointer':
        if offset not in POINTER_BASES:
            raise ValueError(
                    f"Invalid pointer offset {offset}, must be 0 or 1.")
        addr = POINTER_BASES[offset]
        return (
                f'@{addr}  // push <- pointer {offset}',
                'D=M',
                '@SP',
                'M=M+1',
                'A=M-1',
                'M=D',
                )
    else:
        raise ValueError(f"Invalid segment name '{segment}'.")


def translate_pop(context: str, segment: str, offset: int) -> tuple[str]:
    """Translate a `pop` instruction into assembly.

    A pop instruction removes the value from the top of the stack, and writes
    it to some memory location. More precisely, we find the base memory address
    of the memory segment, add the offset to it, and store that address. Then
    we decrement SP to point at the previous register, and write the value
    found there to the memory address we stored earlier.
    In assembly pseudo-code:

    1. addr = segment + offset
    2. SP--
    3. *addr = *SP

    Return the assembly code as a list of strings, one string per line.
    """
    if segment in SEGMENT_BASES:
        base = SEGMENT_BASES[segment]
        return (
                f'@{offset}  // pop -> {segment} {offset}',
                'D=A',
                f'@{base}',
                'D=D+M',
                '@addr',
                'M=D',
                '@SP',
                'AM=M-1',
                'D=M',
                '@addr',
                'A=M',
                'M=D',
                )
    elif segment == 'constant':
        raise ValueError("Pop to constant is not valid.")
    elif segment == 'temp':
        addr = TEMP_BASE + offset
        return (
                '@SP  // pop -> temp {offset}',
                'AM=M-1',
                'D=M',
                f'@{addr}',
                'M=D',
                )
    elif segment == 'static':
        return (
                f'@SP  // pop -> static {offset}',
                'AM=M-1',
                'D=M',
                f'@{context}.{offset}',
                'M=D',
                )
    elif segment == 'pointer':
        if offset not in POINTER_BASES:
            raise ValueError(
                    f"Invalid pointer offset {offset}, must be 0 or 1.")
        addr = POINTER_BASES[offset]
        return (
                '@SP  // pop -> pointer {offset}',
                'AM=M-1',
                'D=M',
                f'@{addr}',
                'M=D',
                )
    else:
        raise ValueError(f"Invalid segment name '{segment}'.")


def translate_comparison(context: str, linenum: int, op: str) -> tuple[str]:
    jump = COMPARISON_OPS[op]
    label = f'{context}.{linenum}'
    return (
            f'@SP  // {op}',
            'AM=M-1',
            'D=-M',
            'A=A-1',
            'D=D+M',
            f'@{label}.TRUE',
            f'D;{jump}',
            'D=0',
            f'@{label}.END',
            '0;JMP',
            f'({label}.TRUE)',
            'D=-1',
            f'({label}.END)',
            '@SP',
            'A=M-1',
            'M=D',
            )


def translate(basename: str, stream) -> list[str]:
    result = []
    linenum = 1
    for line in stream:
        if '//' in line:
            index = line.index('//')
            line = line[:index]
        line = line.strip()
        if line == '':
            linenum += 1
            continue

        words = line.split()
        command = words[0]

        try:
            if command in STATIC_OPS:
                result.extend(STATIC_OPS[command])
            elif command in COMPARISON_OPS:
                result.extend(translate_comparison(basename, linenum, command))
            elif command == 'push':
                segment = words[1]
                offset = int(words[2])
                result.extend(translate_push(basename, segment, offset))
            elif command == 'pop':
                segment = words[1]
                offset = int(words[2])
                result.extend(translate_pop(basename, segment, offset))
            else:
                raise ValueError(f"Invalid command name '{command}'.")
        except Exception as e:
            raise Exception(f"Error on {basename} line {linenum}: {e}")

        linenum += 1
    return result


def main(args):
    inpath = args.inputfile
    base, _ = os.path.splitext(inpath)
    outpath = f'{base}.asm'

    try:
        with open(inpath, 'r') as fp:
            result = translate(base, fp)

        with open(outpath, 'w') as fp:
            for line in result:
                fp.write(line + '\n')
        return 0
    except Exception as e:
        sys.stderr.write(str(e))
        return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('inputfile')

    args = parser.parse_args()
    sys.exit(main(args))

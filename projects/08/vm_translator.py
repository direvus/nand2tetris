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
ARG_COUNTS = {
        'push': 2,
        'pop': 2,
        'label': 1,
        'goto': 1,
        'if-goto': 1,
        'function': 2,
        'call': 2,
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


def make_label(label: str) -> str:
    return f'LABEL-{label}'


def translate_command(
        basename: str, linenum: int, command: str, args: list[str]
        ) -> tuple[str]:
    count = ARG_COUNTS.get(command, 0)
    if len(args) != count:
        raise ValueError(
                f"Wrong number of arguments for {command}, require {count} "
                f"but found {len(args)}.")

    if command in STATIC_OPS:
        return STATIC_OPS[command]
    elif command in COMPARISON_OPS:
        return translate_comparison(basename, linenum, command)
    elif command == 'push':
        segment = args[0]
        offset = int(args[1])
        return translate_push(basename, segment, offset)
    elif command == 'pop':
        segment = args[0]
        offset = int(args[1])
        return translate_pop(basename, segment, offset)
    elif command == 'label':
        label = make_label(args[0])
        return (f'({label})',)
    elif command == 'goto':
        label = make_label(args[0])
        return (
                f'@{label}',
                '0;JMP',
                )
    elif command == 'if-goto':
        label = make_label(args[0])
        return (
                f'@SP  // {command} {args[0]}',
                'AM=M-1',
                'D=M',
                f'@{label}',
                'D;JNE',
                )
    raise ValueError(f"Invalid command name '{command}'.")


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
        args = words[1:]

        try:
            assembly = translate_command(basename, linenum, command, args)
            result.extend(assembly)
        except Exception as e:
            raise Exception(f"Error on {basename} line {linenum}: {e}")

        linenum += 1
    return result


def main(args):
    inpath = args.inputfile
    basepath, _ = os.path.splitext(inpath)
    basename = os.path.basename(basepath)
    outpath = f'{basepath}.asm'

    try:
        with open(inpath, 'r') as fp:
            result = translate(basename, fp)

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

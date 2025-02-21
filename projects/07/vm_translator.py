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
TEMP_BASE = 5
NEG = (
        '@SP  // neg',
        'A=M-1',
        'M=-M',
        )
ADD = (
        '@SP  // add',
        'AM=M-1',
        'D=M',
        'A=A-1',
        'M=D+M',
        )
SUB = (
        '@SP  // sub',
        'AM=M-1',
        'D=-M',
        'A=A-1',
        'M=D+M',
        )


def translate_push(segment: str, offset: int) -> tuple[str]:
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
    else:
        # TODO
        return tuple()


def translate_pop(segment: str, offset: int) -> tuple[str]:
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
    else:
        # TODO
        return tuple()


def translate(stream) -> list[str]:
    result = []
    for line in stream:
        if '//' in line:
            index = line.index('//')
            line = line[:index]
        line = line.strip()
        if line == '':
            continue

        words = line.split()
        command = words[0]

        if command == 'push':
            segment = words[1]
            offset = int(words[2])
            result.extend(translate_push(segment, offset))
        elif command == 'pop':
            segment = words[1]
            offset = int(words[2])
            result.extend(translate_pop(segment, offset))
        elif command == 'neg':
            result.extend(NEG)
        elif command == 'add':
            result.extend(ADD)
        elif command == 'sub':
            result.extend(SUB)
        else:
            # TODO
            raise NotImplementedError()
    return result


def main(args):
    inpath = args.inputfile
    base, _ = os.path.splitext(inpath)
    outpath = f'{base}.asm'

    with open(inpath, 'r') as fp:
        result = translate(fp)

    with open(outpath, 'w') as fp:
        for line in result:
            fp.write(line + '\n')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('inputfile')

    args = parser.parse_args()
    sys.exit(main(args))

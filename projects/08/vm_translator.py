#!/usr/bin/env python
"""HACK VM Translator: translate VM code into HACK assembly
"""
import argparse
import os
import re
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


def make_label_text(text: str) -> str:
    return re.sub(r'\W+', '__', text)


def make_label(label: str) -> str:
    return f'LABEL_{make_label_text(label)}'


def make_function_label(function_name: str) -> str:
    return f'FUNC_{make_label_text(function_name)}'


def translate_function(
        basename: str, linenum: int, name: str, nlocals: int) -> tuple[str]:
    label = make_function_label(name)
    result = [
            f'({label})',
            '@LCL',
            'A=M',
            ]
    # Initialise local variables to zero
    for _ in range(nlocals):
        result.extend([
            'M=0',
            'A=A+1',
            ])
    # Advance the stack pointer past the locals
    if nlocals > 0:
        result.extend([
            'D=A',
            '@SP',
            'M=D',
            ])
    return tuple(result)


def translate_call(
        basename: str, linenum: int, name: str, nargs: int) -> tuple[str]:
    loc = f'{basename}__{linenum}'
    label = f'RETURN_{make_label_text(loc)}'
    result = [
            f'// call {name} {nargs}',
            # Save the return address to the stack
            f'@{label}',
            'D=A',
            '@SP',
            'A=M',
            'M=D',
            ]
    # Save the current memory segment pointers to the stack
    for segment in ('LCL', 'ARG', 'THIS', 'THAT'):
        result.extend((
            f'@{segment}',
            'D=M',
            '@SP',
            'AM=M+1',
            'M=D',
            ))
    # Set up the SP, ARG and LCL pointers for the target function
    offset = 5 + nargs
    target = make_function_label(name)
    result.extend((
            'D=A+1',
            '@SP',
            'M=D',
            '@LCL',
            'M=D',
            f'@{offset}',
            'D=D-A',
            '@ARG',
            'M=D',
            # Jump to the target function definition
            f'@{target}',
            '0;JMP',
            # Return here when the target function completes
            f'({label})',
            ))
    return tuple(result)


def translate_return(basename: str, linenum: int) -> tuple[str]:
    result = [
            # Copy the top value from the stack to ARG[0]
            f'@SP  // return {basename}.{linenum}',
            'A=M-1',
            'D=M',
            '@ARG',
            'A=M',
            'M=D',
            # Set the stack pointer to point after the new return value
            'D=A+1',
            '@SP',
            'M=D',
            # Restore the saved pointers for LCL, ARG, THIS and THAT from the
            # calling scope.
            '@LCL',
            'D=M-1',
            '@addr',
            'AM=D',
            ]
    for segment in ('THAT', 'THIS', 'ARG', 'LCL'):
        result.extend((
                'D=M',
                f'@{segment}',
                'M=D',
                '@addr',
                'AM=M-1',
                ))
    # Jump to the return address
    result.extend((
            'A=M',
            '0;JMP',
            ))
    return tuple(result)


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
    elif command == 'function':
        name = args[0]
        nlocals = int(args[1])
        return translate_function(basename, linenum, name, nlocals)

    elif command == 'call':
        name = args[0]
        nargs = int(args[1])
        return translate_call(basename, linenum, name, nargs)

    elif command == 'return':
        return translate_return(basename, linenum)

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
    inpath = args.inputpath

    if os.path.isdir(inpath):
        # For an input directory, scan the directory for *.vm files, translate
        # each file and write the complete resulting assembly code as a single
        # .asm file, inside the source directory and with the same name as the
        # directory.
        with os.scandir(inpath) as entries:
            infiles = [
                    os.path.join(inpath, x.name) for x in entries
                    if x.name.endswith('.vm') and x.is_file()]
        name = os.path.split(inpath)[-1]
        outpath = f'{inpath}/{name}.asm'

    else:
        # For a single input file, translate that file and write the assembly
        # code output to a file with the same base name but with a *.asm
        # suffix.
        infiles = [inpath]
        basepath, _ = os.path.splitext(inpath)
        outpath = f'{basepath}.asm'

    result = []
    try:
        for infile in infiles:
            print(f"Translating {infile} ...")
            basename = os.path.basename(os.path.splitext(infile)[0])
            with open(infile, 'r') as fp:
                result = translate(basename, fp)

        print(f"Writing translated assembly code to {outpath} ...")
        with open(outpath, 'w') as fp:
            for line in result:
                fp.write(line + '\n')

        print("Done")
        return 0
    except Exception as e:
        sys.stderr.write(str(e))
        return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('inputpath')

    args = parser.parse_args()
    sys.exit(main(args))

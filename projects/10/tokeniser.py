#!/usr/bin/env python
import argparse
import sys


SYMBOLS = set('{}()[].,;+-*/&|<>=~')
KEYWORDS = {
        'class', 'constructor', 'function', 'method',
        'field', 'static', 'var',
        'int', 'char', 'boolean', 'void',
        'true', 'false', 'null', 'this',
        'let', 'do', 'if', 'else', 'while', 'return'}


class Tokeniser:
    """Tokenise a Jack code file input stream.

    Once a Tokeniser has been initialised with an open file stream into a Jack
    source code file, it can be used to emit a stream of valid code tokens in
    the file. You can do this by checking the return of the has_next() method,
    and then calling advance() if has_next() was True. After calling advance(),
    the Tokeniser will have a token stored in its `token_type` and `value`
    attributes. Or, you can simply loop over the `generate()` method which will
    take care of all this for you.
    """
    def __init__(self, stream):
        self.stream = stream
        self.buf = self.stream.read()
        self.index = 0
        self.token_type = None
        self.value = None

    def has_next(self):
        """Return whether there are any more tokens in the input stream.

        Automatically advances the internal pointer past any whitespace and
        comments.
        """
        i = self.index
        ch = self.buf[i]
        ch2 = self.buf[i: i+2]
        try:
            while ch.isspace() or ch2 in {'//', '/*'}:
                while self.buf[i].isspace():
                    i += 1

                ch2 = self.buf[i: i+2]
                if ch2 == '//':
                    # Skip characters until end-of-line
                    while self.buf[i] != '\n':
                        i += 1
                    i + 1
                    ch = self.buf[i]

                elif ch2 == '/*':
                    # Skip characters until end-of-comment marker
                    while self.buf[i: i+2] != '*/':
                        i += 1
                    i += 2
                ch = self.buf[i]
                ch2 = self.buf[i: i+2]

            # After we're done ignoring comments and whitespace, if there
            # remains anything to be read from the buffer, then it must be a
            # token.
            self.index = i
            return i < (len(self.buf) - 1)
        except IndexError:
            return False

    def advance(self):
        """Consume one token from the input.

        Set the `token_type` and `value` attributes to the next token in the
        input stream, and move the internal pointer to the next character
        following the end of the token.
        """
        i = self.index
        ch = self.buf[i]
        if ch in SYMBOLS:
            self.token_type = 'symbol'
            self.value = ch
            self.index += 1
        elif ch.isdigit():
            i += 1
            while self.buf[i].isdigit():
                i += 1
            self.token_type = 'integerConstant'
            self.value = int(self.buf[self.index: i])
            self.index = i
        elif ch == '"':
            i += 1
            while self.buf[i] != '"':
                i += 1
            self.token_type = 'stringConstant'
            self.value = self.buf[self.index + 1: i]
            self.index = i + 1
        elif ch.isalpha() or ch == '_':
            i += 1
            while self.buf[i].isalnum() or self.buf[i] == '_':
                i += 1
            self.value = self.buf[self.index: i]
            if self.value in KEYWORDS:
                self.token_type = 'keyword'
            else:
                self.token_type = 'identifier'
            self.index = i
        else:
            raise ValueError(f"Invalid character {ch} at index {i}.")

    def generate(self):
        """A generator function that returns tokens from the stream.

        Each token is yielded as a (type, value) tuple, and the generator
        continues to yield tokens until no more are available.

        This function can be used as an iterator in a loop expression.
        """
        while self.has_next():
            self.advance()
            yield (self.token_type, self.value)


def main(args):
    inpath = args.inputpath

    try:
        with open(inpath, 'r') as fp:
            tok = Tokeniser(fp)
            for token_type, value in tok.generate():
                print(f'<{token_type}> {value} </{token_type}>')
        return 0
    except Exception as e:
        sys.stderr.write(str(e))
        return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('inputpath')

    args = parser.parse_args()
    sys.exit(main(args))

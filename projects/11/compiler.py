#!/usr/bin/env python
import argparse
import sys
from collections import defaultdict, deque

from tokeniser import Token, Tokeniser


PRIMITIVE_TYPES = {'int', 'char', 'boolean'}
CLASS_VAR_TYPES = {'field', 'static'}
SUBROUTINE_TYPES = {'constructor', 'function', 'method'}
STATEMENT_TYPES = {'let', 'if', 'while', 'do', 'return'}
KEYWORD_CONSTANTS = {'true', 'false', 'null', 'this'}
OPERATORS = {'+', '-', '*', '/', '&', '|', '<', '>', '='}
UNARY_OPERATORS = {'-': 'neg', '~': 'not'}


class SymbolTable:
    def __init__(self):
        self.symbols = {}
        self.counters = defaultdict(lambda: 0)

    def add_symbol(self, name, typ, kind):
        index = self.counters[kind]
        if name in self.symbols:
            raise ValueError(f"Symbol '{name}' already exists in this table.")
        record = (typ, kind, index)
        self.symbols[name] = record
        self.counters[kind] += 1
        return index

    def get(self, name):
        return self.symbols[name]

    def get_count(self, kind):
        return self.counters[kind]


class Compiler:
    """A Compiler instance compiles a single Jack source code file to VM code.

    The Compiler passes its input stream to the tokeniser, and analyses the
    stream of tokens produced by the Tokeniser in order to generate VM code.
    """
    def __init__(self, input_stream, output_stream):
        self.output_stream = output_stream
        self.tokeniser = Tokeniser(input_stream)
        self.tokens = deque()
        self.class_symbols = SymbolTable()
        self.subroutine_symbols = SymbolTable()
        self.class_name = None
        self.label_counter = 0

    def write(self, text):
        """Write text as-is to the output stream."""
        self.output_stream.write(text)

    def write_line(self, line):
        """Write one line of text (VM instruction) to the output stream.

        A newline character is appended to the stream automatically.
        """
        self.write(line)
        self.write('\n')

    def read_token(self):
        """Consume one token from the tokeniser.

        The token is appended to end of the internal tokens list and also
        returned from this method, as a Token object.

        Raise an exception if there are no more tokens available.
        """
        try:
            token = next(self.tokeniser.generate())
            self.tokens.append(token)
            return token
        except StopIteration:
            raise ValueError('No more tokens available')

    def get_token(self):
        """Get the next token, reading it from the tokeniser if necessary.

        If there are any tokens currently in the internal token list, simply
        return the first token. Otherwise, consume one token from the
        tokeniser, add it to the internal token list, and return it. If there
        are no tokens available, raise a ValueError.
        """
        if len(self.tokens) == 0:
            self.read_token()
        return self.tokens[0]

    def pop_token(self, type_required=None, value_required=None):
        """Remove the next token from the internal token list.

        If there are no tokens currently in the token list, attempt to consume
        one from the tokeniser, raising a ValueError if none are available.

        If `type_required` or `value_required` are not None, then raise a
        ValueError if the next token does not conform to the requirements.

        Return the token.
        """
        if len(self.tokens) == 0:
            self.read_token()

        if type_required is not None or value_required is not None:
            self.require_token(type_required, value_required)

        return self.tokens.popleft()

    def match_token(self, type_required=None, value_required=None):
        """Return whether the next token conforms to a given type and/or value.

        If there is a token available, and it conforms to the type and value
        requirements, return True. Otherwise, return False.

        `type_required` may be either None, or one of the token type strings.

        `value_required` may be None, or a single string, or a collection of
        strings, such as a list, tuple or set. If it is a single string, then
        the value of the token must match this string exactly. If it is a
        collection, then the value of the token must be a member of that
        collection.
        """
        try:
            token = self.get_token()
        except ValueError:
            return False

        if type_required is not None and type_required != token.token_type:
            return False
        if value_required is not None:
            if isinstance(value_required, str):
                if value_required != token.value:
                    return False
            elif token.value not in value_required:
                return False
        return True

    def require_token(self, type_required=None, value_required=None):
        """Check that the next token conforms to a given type and/or value.

        If there are no tokens available, or the next token does not match the
        required type and/or value, raise a ValueError.

        `type_required` may be either None, or one of the token type strings.

        `value_required` may be None, or a literal string, or a collection such
        as a list, tuple or set. If it is a string, then the value of the token
        must match this string exactly. If it is a collection, then the value
        of the token must be a member of that collection.
        """
        if value_required is None:
            label = type_required
        elif isinstance(value_required, str):
            label = f"{type_required} '{value_required}'"
        else:
            label = f"{type_required} '{'|'.join(value_required)}'"

        try:
            token = self.get_token()
        except ValueError:
            raise ValueError(f'Expected {label} but no more tokens available')

        if type_required is not None and type_required != token.token_type:
            raise ValueError(f'Expected {label}, but got {token}')
        if value_required is not None:
            if isinstance(value_required, str):
                if value_required != token.value:
                    raise ValueError(f"Expected {label}, but got '{token}'")
            elif token.value not in value_required:
                raise ValueError(f"Expected {label}, but got '{token}'")
        return token

    def lookup_symbol(self, name):
        """Look up a symbol in the symbol tables.

        If the symbol exists in the subroutine symbol table, it is returned
        from there first. Otherwise, we look for it in the class table. If it
        is not in either table, that is an error.

        If the symbol is found, return its memory segment name and index as a
        string. If not, raise an error.
        """
        try:
            symbol = self.subroutine_symbols.get(name)
        except KeyError:
            symbol = self.class_symbols.get(name)

        return f'{symbol[1]} {symbol[2]}'

    def compile(self):
        """Begin compiling a Jack source code stream.

        Every Jack source code file is expected to contain exactly one class,
        and nothing else besides. So in this method, we simply hand control off
        to compile_class().
        """
        self.compile_class()

    def compile_class(self):
        """Compile a class declaration.

        A class begins with the keyword 'class', then an identifier for the
        name of the class, followed by zero or more class variable
        declarations, followed by zero or more subroutine declarations, all
        enclosed within curly braces. Formally:

            class: 'class' identifier '{' classVarDec* subroutineDec* '}'
        """
        self.pop_token('keyword', 'class')
        self.class_name = self.compile_identifier()
        self.pop_token('symbol', '{')

        while self.match_token('keyword', CLASS_VAR_TYPES):
            self.compile_class_var_dec()

        while self.match_token('keyword', SUBROUTINE_TYPES):
            self.compile_subroutine_dec()

        self.pop_token('symbol', '}')

    def compile_class_var_dec(self):
        """Compile a class variable declaration.

        A class variable is one of the two keywords 'static' or 'field',
        followed by a type specifier, followed by a variable name. It can then
        optionally be followed by additional variable names separated with
        commas, and finally it is concluded with a semicolon.

            classVarDec: ('static' | 'field') type varName (',' varName)* ';'
        """
        kind = self.pop_token('keyword', CLASS_VAR_TYPES).value
        vartype = self.compile_type()
        name = self.pop_token('identifier')
        self.class_symbols.add_symbol(name, vartype, kind)

        # Zero or more commas followed by additional variable names
        while self.match_token('symbol', ','):
            self.pop_token()
            name = self.pop_token('identifier')
            self.class_symbols.add_symbol(name, vartype, kind)

        self.pop_token('symbol', ';')

    def compile_subroutine_dec(self):
        """Compile a subroutine declaration.

        A subroutine declaration begins with one of the three keywords
        'constructor', 'method' or 'function', followed by the return type,
        followed by an identifier naming the subroutine.

        It is then followed by a (possibly empty) list of parameters enclosed
        in parentheses, then the body of the subroutine enclosed in curly
        braces.

            subroutineDec: ('constructor' | 'method' | 'function')
                    ('void' | type) identifier '(' parameterList ')'
                    subroutineBody
        """
        subtype = self.pop_token('keyword', SUBROUTINE_TYPES).value
        if self.match_token('keyword', 'void'):
            return_type = self.pop_token().value
        else:
            return_type = self.compile_type()

        name = self.compile_identifier()
        self.local_count = 0
        self.subroutine_symbols = SymbolTable()
        self.pop_token('symbol', '(')
        self.compile_parameter_list()
        self.pop_token('symbol', ')')

        # Leave the line running so that subroutine_body can fill in the number
        # of locals.
        self.write(f'function {self.class_name}.{name} ')
        self.compile_subroutine_body()

    def compile_parameter_list(self):
        """Compile a list of parameters to a subroutine.

        A parameter list consists of zero or more sequences of a type followed
        by a parameter name identifier, separated by commas.

            parameterList: ( type varName (',' type varName)* )?
        """
        if not self.match_token('symbol', ')'):
            ptype = self.compile_type()
            name = self.compile_identifier()
            self.subroutine_symbols.add_symbol(name, ptype, 'argument')

        while self.match_token('symbol', ','):
            ptype = self.compile_type()
            name = self.compile_identifier()
            self.subroutine_symbols.add_symbol(name, ptype, 'argument')

    def compile_var_dec(self):
        """Compile a variable declaration.

        A variable declaration is the keyword 'var' followed by a type
        specifier, followed by a list of one or more variable name identifiers
        separated by commas, and finally concluded with a semicolon.

            classVarDec: 'var' type varName (',' varName)* ';'
        """
        self.pop_token('keyword', 'var')
        vartype = self.compile_type()
        name = self.compile_identifier()
        self.subroutine_symbols.add_symbol(name, vartype, 'local')

        # Zero or more commas followed by additional variable names
        while self.match_token('symbol', ','):
            self.pop_token()
            name = self.compile_identifier()
            self.subroutine_symbols.add_symbol(name, vartype, 'local')

        self.pop_token('symbol', ';')

    def compile_type(self):
        """Compile a type declaration.

        A type declaration can be either a keyword giving the name of a
        primitive type, or an identifier giving the name of a class.

        In either case, consume the token and return its value.

        Grammar:
            type: 'int' | 'char' | 'boolean' | className
            className: identifier
        """
        if not (
                self.match_token('keyword', PRIMITIVE_TYPES) or
                self.match_token('identifier')):
            raise ValueError(
                    "Expected a primitive type or class name")
        return self.pop_token().value

    def compile_identifier(self):
        """Compile an identifier.

        Consume one identifier token, and return its value.
        """
        return self.pop_token('identifier').value

    def compile_subroutine_body(self):
        """Compile a subroutine body.

        A subroutine body is enclosed in curly brace symbols, and consists of
        zero or more variable declarations, followed by zero or more
        statements.

            subroutineBody: '{' varDec* statements '}'
        """
        self.pop_token('symbol', '{')

        while self.match_token('keyword', 'var'):
            self.compile_var_dec()
        # Complete the 'function' code line that was previously left open by
        # compile_subroutine_dec().
        nlocals = self.subroutine_symbols.get_count('local')
        self.write_line(str(nlocals))

        self.compile_statements()
        self.pop_token('symbol', '}')

    def compile_statements(self):
        """Compile zero or more statements."""
        while self.match_token('keyword', STATEMENT_TYPES):
            key = self.get_token().value
            if key == 'let':
                self.compile_let_statement()
            elif key == 'if':
                self.compile_if_statement()
            elif key == 'while':
                self.compile_while_statement()
            elif key == 'do':
                self.compile_do_statement()
            elif key == 'return':
                self.compile_return_statement()
            else:
                # Should never arrive here
                raise RuntimeError(f"Unrecognised statement type {key}.")

    def compile_let_statement(self):
        """Compile a 'let' statement (variable assignment).

        A 'let' statement consists of the keyword 'let', followed by a variable
        name, followed optionally by an array index expression enclosed in
        square brackets, followed by the equals symbol, then an expression and
        finally a semicolon.

            letStatement: 'let' varName ( '[' expression ']' )?
                    '=' expression ';'
        """
        self.pop_token('keyword', 'let')
        name = self.compile_identifier()
        symbol = self.lookup_symbol(name)

        if self.match_token('symbol', '['):
            # Assignment to an array index
            self.pop_token()
            self.compile_expression()
            # TODO: align 'that' to the index
            self.pop_token('symbol', ']')

        self.pop_token('symbol', '=')
        self.compile_expression()
        self.write_line(f'pop {symbol}')
        self.pop_token('symbol', ';')

    def compile_if_statement(self):
        """Compile an 'if' statement (conditional execution).

        An 'if' statement consists of the keyword 'if', followed by an
        expression enclosed in parentheses, followed by zero or more statements
        enclosed in curly braces.

        It may then be optionally followed by the keyword 'else', and zero or
        more statements enclosed in curly braces.

            ifStatement: 'if' '(' expression ')' '{' statements '}'
                    ( 'else' '{' statements '}' )?
        """
        node = Node('ifStatement')
        node.add_child(*self.pop_token('keyword', 'if'))
        node.add_child(*self.pop_token('symbol', '('))
        node.add_child(self.compile_expression())
        node.add_child(*self.pop_token('symbol', ')'))
        node.add_child(*self.pop_token('symbol', '{'))
        node.add_child(self.compile_statements())
        node.add_child(*self.pop_token('symbol', '}'))

        if self.match_token('keyword', 'else'):
            node.add_child(*self.pop_token())
            node.add_child(*self.pop_token('symbol', '{'))
            node.add_child(self.compile_statements())
            node.add_child(*self.pop_token('symbol', '}'))

        return node

    def compile_while_statement(self):
        """Compile a 'while' statement (repeated execution).

        A 'while' statement consists of the keyword 'while', followed by an
        expression enclosed in parentheses, followed by zero or more statements
        enclosed in curly braces.

            whileStatement: 'while' '(' expression ')' '{' statements '}'
        """
        node = Node('whileStatement')
        node.add_child(*self.pop_token('keyword', 'while'))
        node.add_child(*self.pop_token('symbol', '('))
        node.add_child(self.compile_expression())
        node.add_child(*self.pop_token('symbol', ')'))
        node.add_child(*self.pop_token('symbol', '{'))
        node.add_child(self.compile_statements())
        node.add_child(*self.pop_token('symbol', '}'))
        return node

    def compile_do_statement(self):
        """Compile a 'do' statement (subroutine invocation).

        A 'do' statement consists of the keyword 'do', followed by a subroutine
        call, and ending with a semicolon.

            doStatement: 'do' subroutineCall ';'
        """
        self.pop_token('keyword', 'do')
        parts = []
        while not self.match_token('symbol', '('):
            parts.append(self.pop_token().value)
        name = ''.join(parts)

        self.pop_token('symbol', '(')
        nargs = self.compile_expression_list()
        self.pop_token('symbol', ')')
        self.pop_token('symbol', ';')
        self.write_line(f'call {name} {nargs}')

    def compile_return_statement(self):
        """Compile a 'return' statement.

        A 'return' statement consists of the keyword 'return', followed
        optionally by an expression, and ending with a semicolon.

            returnStatement: 'return' expression? ';'
        """
        self.pop_token('keyword', 'return')
        if self.match_token('symbol', ';'):
            self.write_line('push 0')
        else:
            self.compile_expression()
        self.pop_token('symbol', ';')
        self.write_line('return')

    def compile_expression(self):
        """Compile an expression.

        An expression consists of a term, followed by zero or more op and term
        pairs.

            expression: term (op term)*
        """
        self.compile_term()

        while self.match_token('symbol', OPERATORS):
            self.pop_token()
            self.compile_term()

    def compile_term(self):
        """Compile a term.

        A term can be a constant, a variable name, an array index into a
        variable name, a subroutine call, a nested expression enclosed in
        parentheses, or a unary operator followed by a term.

            term: integerConstant | stringConstant | keywordConstant |
                    varName | varName '[' expression ']' | subroutineCall |
                    '(' expression ')' | unaryOp term
        """
        if self.match_token('integerConstant'):
            value = self.pop_token().value
            self.write_line(f'push constant {value}')

        elif self.match_token('keyword', KEYWORD_CONSTANTS):
            value = self.pop_token().value
            if value == 'true':  # true is -1
                self.write_line('push constant 1')
                self.write_line('neg')
            elif value in {'null', 'false'}:  # null and false are both 0
                self.write_line('push constant 0')

        elif self.match_token('stringConstant'):
            self.pop_token()

        elif self.match_token('symbol', '('):
            self.pop_token()
            self.compile_expression()
            self.pop_token('symbol', ')')

        elif self.match_token('symbol', UNARY_OPERATORS.keys()):
            op = self.pop_token().value
            self.compile_term()
            self.write_line(UNARY_OPERATORS[op])

        else:
            # The only remaining cases are a variable reference, array index
            # into a variable, or subroutine call, so the next token must be an
            # identifier regardless.
            name = self.compile_identifier()
            if self.match_token('symbol', '['):
                # Array index
                self.pop_token()
                self.compile_expression()
                self.pop_token('symbol', ']')
            elif self.match_token('symbol', {'.', '('}):
                # Subroutine call
                if self.match_token('symbol', '.'):
                    # className.subroutineName syntax
                    self.pop_token()
                    name += '.' + self.compile_identifier()
                self.pop_token('symbol', '(')
                self.compile_expression_list()
                self.pop_token('symbol', ')')
            else:
                symbol = self.lookup_symbol(name)
                self.write_line(f'push {symbol}')

    def compile_expression_list(self):
        if self.match_token('symbol', ')'):
            return 0

        self.compile_expression()
        count = 1

        while self.match_token('symbol', ','):
            self.pop_token()
            self.compile_expression()
            count += 1
        return count


def main(args):
    inpath = args.inputpath

    try:
        with open(inpath, 'r') as fp:
            compiler = Compiler(fp, sys.stdout)
            compiler.compile()

        return 0
    except Exception as e:
        sys.stderr.write(str(e))
        raise e
        return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('inputpath')

    args = parser.parse_args()
    sys.exit(main(args))

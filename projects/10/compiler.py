#!/usr/bin/env python
import argparse
import sys
from collections import deque

from tokeniser import Tokeniser


PRIMITIVE_TYPES = {'int', 'char', 'boolean'}
CLASS_VAR_TYPES = {'field', 'static'}
SUBROUTINE_TYPES = {'constructor', 'function', 'method'}
STATEMENT_TYPES = {'let', 'if', 'while', 'do', 'return'}
KEYWORD_CONSTANTS = {'true', 'false', 'null', 'this'}


def escape(text):
    return text.replace(
            '&', '&amp;').replace(
            '<', '&lt;').replace(
            '>', '&gt;').replace(
            '"', '&quot;')


class Node:
    def __init__(self, node_type, content=None):
        self.node_type = node_type
        self.content = content
        self.children = []

    def add_child(self, node_type, content=None):
        if isinstance(node_type, Node):
            child = node_type
        else:
            child = Node(node_type, content)
        self.children.append(child)
        return child


class Compiler:
    """A Compiler instance compiles a single Jack code file.

    The Compiler calls the tokeniser and analyses the stream of tokens to
    produce an abstract syntax tree.

    This abstract syntax tree can then be rendered to its XML representation.
    """
    def __init__(self, stream):
        self.tokeniser = Tokeniser(stream)
        self.tokens = deque()
        self.root = None

    def read_token(self):
        """Consume one token from the tokeniser.

        The token is appended to end of the internal tokens list and also
        returned from this method, as a tuple of (type, value).

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
            token_type, value = self.get_token()
        except ValueError:
            return False

        if type_required is not None and type_required != token_type:
            return False
        if value_required is not None:
            if isinstance(value_required, str):
                if value_required != value:
                    return False
            elif value not in value_required:
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
            token_type, value = self.get_token()
        except ValueError:
            raise ValueError(f'Expected {label} but no more tokens available')

        if type_required is not None and type_required != token_type:
            raise ValueError(f'Expected {label}, but got {token_type} {value}')
        if value_required is not None:
            if isinstance(value_required, str):
                if value_required != value:
                    raise ValueError(f"Expected {label}, but got '{value}'")
            elif value not in value_required:
                raise ValueError(f"Expected {label}, but got '{value}'")
        self.token_type = token_type
        self.token_value = value
        return token_type, value

    def compile(self):
        self.root = self.compile_class()

    def compile_class(self):
        """Compile a class declaration.

        A class begins with the keyword 'class', then an identifier for the
        name of the class, followed by zero or more class variable
        declarations, followed by zero or more subroutine declarations, all
        enclosed within curly braces. Formally:

            class: 'class' identifier '{' classVarDec* subroutineDec* '}'
        """
        node = Node('class')
        node.add_child(*self.pop_token('keyword', 'class'))
        node.add_child(*self.pop_token('identifier'))
        node.add_child(*self.pop_token('symbol', '{'))

        while self.match_token('keyword', CLASS_VAR_TYPES):
            vardec = self.compile_class_var_dec()
            node.add_child(vardec)

        while self.match_token('keyword', SUBROUTINE_TYPES):
            sub = self.compile_subroutine_dec()
            node.add_child(sub)

        node.add_child(*self.pop_token('symbol', '}'))
        return node

    def compile_class_var_dec(self):
        """Compile a class variable declaration.

        A class variable is one of the two keywords 'static' or 'field',
        followed by a type specifier, followed by a variable name. It can then
        optionally be followed by additional variable names separated with
        commas, and finally it is concluded with a semicolon.

            classVarDec: ('static' | 'field') type varName (',' varName)* ';'
        """
        node = Node('classVarDec')
        node.add_child(*self.pop_token('keyword', CLASS_VAR_TYPES))
        node.add_child(self.compile_type())
        node.add_child(*self.pop_token('identifier'))

        # Zero or more commas followed by additional variable names
        while self.match_token('symbol', ','):
            node.add_child(*self.pop_token())
            node.add_child(*self.pop_token('identifier'))

        node.add_child(*self.pop_token('symbol', ';'))
        return node

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
        node = Node('subroutineDec')
        node.add_child(*self.pop_token('keyword', SUBROUTINE_TYPES))
        if self.match_token('keyword', 'void'):
            node.add_child(*self.pop_token())
        else:
            node.add_child(self.compile_type())

        node.add_child(*self.pop_token('identifier'))
        node.add_child(*self.pop_token('symbol', '('))
        node.add_child(self.compile_parameter_list())
        node.add_child(*self.pop_token('symbol', ')'))

        node.add_child(self.compile_subroutine_body())
        return node

    def compile_parameter_list(self):
        """Compile a list of parameters to a subroutine.

        A parameter list consists of zero or more sequences of a type followed
        by a parameter name identifier, separated by commas.

            parameterList: ( type varName (',' type varName)* )?
        """
        node = Node('parameterList')
        if not self.match_token('symbol', ')'):
            node.add_child(self.compile_type())
            node.add_child(*self.pop_token('identifier'))

        while self.match_token('symbol', ','):
            node.add_child(*self.pop_token())
            node.add_child(self.compile_type())
            node.add_child(*self.pop_token('identifier'))

        return node

    def compile_var_dec(self):
        """Compile a variable declaration.

        A variable declaration is the keyword 'var' followed by a type
        specifier, followed by a list of one or more variable name identifiers
        separated by commas, and finally concluded with a semicolon.

            classVarDec: 'var' type varName (',' varName)* ';'
        """
        node = Node('varDec')
        node.add_child(*self.pop_token('keyword', 'var'))
        node.add_child(self.compile_type())
        node.add_child(*self.pop_token('identifier'))

        # Zero or more commas followed by additional variable names
        while self.match_token('symbol', ','):
            node.add_child(*self.pop_token())
            node.add_child(*self.pop_token('identifier'))

        node.add_child(*self.pop_token('symbol', ';'))
        return node

    def compile_type(self):
        """Compile a type declaration.

        A type declaration can be either a keyword giving the name of a
        primitive type, or an identifier giving the name of a class.

        Grammar:
            type: 'int' | 'char' | 'boolean' | className
            className: identifier
        """
        if not (
                self.match_token('keyword', PRIMITIVE_TYPES) or
                self.match_token('identifier')):
            raise ValueError(
                    "Expected a primitive type or class name")
        return Node(*self.pop_token())

    def compile_subroutine_body(self):
        """Compile a subroutine body.

        A subroutine body is enclosed in curly brace symbols, and consists of
        zero or more variable declarations, followed by zero or more
        statements.

            subroutineBody: '{' varDec* statements '}'
        """
        node = Node('subroutineBody')
        node.add_child(*self.pop_token('symbol', '{'))

        while self.match_token('keyword', 'var'):
            node.add_child(self.compile_var_dec())

        node.add_child(self.compile_statements())
        node.add_child(*self.pop_token('symbol', '}'))
        return node

    def compile_statements(self):
        """Compile zero or more statements."""
        node = Node('statements')
        while self.match_token('keyword', STATEMENT_TYPES):
            _, key = self.get_token()
            if key == 'let':
                node.add_child(self.compile_let_statement())
            elif key == 'if':
                node.add_child(self.compile_if_statement())
            elif key == 'while':
                node.add_child(self.compile_while_statement())
            elif key == 'do':
                node.add_child(self.compile_do_statement())
            elif key == 'return':
                node.add_child(self.compile_return_statement())
            else:
                # Should never arrive here
                raise RuntimeError(f"Unrecognised statement type {key}.")
        return node

    def compile_let_statement(self):
        """Compile a 'let' statement (variable assignment).

        A 'let' statement consists of the keyword 'let', followed by a variable
        name, followed optionally by an array index expression enclosed in
        square brackets, followed by the equals symbol, then an expression and
        finally a semicolon.

            letStatement: 'let' varName ( '[' expression ']' )?
                    '=' expression ';'
        """
        node = Node('letStatement')
        node.add_child(*self.pop_token('keyword', 'let'))
        node.add_child(*self.pop_token('identifier'))

        if self.match_token('symbol', '['):
            node.add_child(*self.pop_token())
            node.add_child(self.compile_expression())
            node.add_child(*self.pop_token('symbol', ']'))

        node.add_child(*self.pop_token('symbol', '='))
        node.add_child(self.compile_expression())
        node.add_child(*self.pop_token('symbol', ';'))
        return node

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
        node = Node('doStatement')
        node.add_child(*self.pop_token('keyword', 'do'))
        # TODO: replace with less lazy code once we've tested the
        # expressionless version
        while not self.match_token('symbol', '('):
            node.add_child(*self.pop_token())
        node.add_child(*self.pop_token('symbol', '('))
        node.add_child(self.compile_expression_list())
        node.add_child(*self.pop_token('symbol', ')'))
        node.add_child(*self.pop_token('symbol', ';'))
        return node

    def compile_return_statement(self):
        """Compile a 'return' statement.

        A 'return' statement consists of the keyword 'return', followed
        optionally by an expression, and ending with a semicolon.

            returnStatement: 'return' expression? ';'
        """
        node = Node('returnStatement')
        node.add_child(*self.pop_token('keyword', 'return'))
        if not self.match_token('symbol', ';'):
            node.add_child(self.compile_expression())
        node.add_child(*self.pop_token('symbol', ';'))
        return node

    def compile_expression(self):
        node = Node('expression')
        node.add_child(self.compile_term())
        return node

    def compile_term(self):
        node = Node('term')
        node.add_child(*self.pop_token())
        return node

    def compile_expression_list(self):
        node = Node('expressionList')
        if self.match_token('symbol', ')'):
            return node

        node.add_child(self.compile_expression())

        while self.match_token('symbol', ','):
            node.add_child(*self.pop_token())
            node.add_child(self.compile_expression())
        return node

    def write_xml(self, stream, node=None, depth=0):
        if node is None:
            node = self.root

        padding = '  ' * depth
        stream.write(f'{padding}<{node.node_type}>')
        if node.content is not None:
            stream.write(escape(node.content))
            stream.write(f'</{node.node_type}>\n')
        else:
            stream.write('\n')
            for child in node.children:
                self.write_xml(stream, child, depth + 1)
            stream.write(f'{padding}</{node.node_type}>\n')


def main(args):
    inpath = args.inputpath

    try:
        with open(inpath, 'r') as fp:
            comp = Compiler(fp)
            comp.compile()

        comp.write_xml(sys.stdout)
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

#!/usr/bin/env python
import argparse
import sys

from tokeniser import Tokeniser


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
        child = Node(node_type, content)
        self.children.append(child)
        return child


class Compiler:
    """Compile a Jack code file."""
    def __init__(self, stream):
        self.tokeniser = Tokeniser(stream)
        self.root = None

    def consume(self, type_required=None, value_required=None):
        token_type, value = next(self.tokeniser.generate())
        if type_required is not None and type_required != token_type:
            raise ValueError(f'Expected {type_required}, but got {token_type}')
        if value_required is not None and value_required != value:
            raise ValueError(f'Expected {value_required}, but got {value}')
        return token_type, value

    def compile(self):
        self.root = self.compile_class()

    def compile_class(self):
        node = Node('class')
        node.add_child(*self.consume('keyword', 'class'))
        node.add_child(*self.consume('identifier'))
        node.add_child(*self.consume('symbol', '{'))
        return node

    def write_xml(self, stream, node=None, depth=0):
        if node is None:
            node = self.root

        padding = '  ' * depth
        stream.write(f'{padding}<{node.node_type}>')
        if node.children:
            stream.write('\n')
            for child in node.children:
                self.write_xml(stream, child, depth + 1)
            stream.write(f'{padding}</{node.node_type}>\n')
        else:
            stream.write(escape(node.content))
            stream.write(f'</{node.node_type}>\n')


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
        return 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('inputpath')

    args = parser.parse_args()
    sys.exit(main(args))

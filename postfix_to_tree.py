"""
Laboratorio 3 - Teoría de la Computación
Problema 1: De postfix (Shunting Yard) a Árbol Sintáctico
"""

import sys
from graphviz import Digraph

# ---------------------------------------------------------
# 1. Clases de nodos del árbol sintáctico
# ---------------------------------------------------------

class TreeNode:
    _id_counter = 0

    def __init__(self):
        self.id = TreeNode._id_counter
        TreeNode._id_counter += 1
        self.left = None
        self.right = None

    def label(self):
        raise NotImplementedError


class LeafNode(TreeNode):
    """Nodo hoja: un símbolo del alfabeto o épsilon."""

    def __init__(self, symbol):
        super().__init__()
        self.symbol = symbol

    def label(self):
        return self.symbol


class StarNode(TreeNode):
    """Nodo unario: cerradura de Kleene (*)."""

    def __init__(self, child):
        super().__init__()
        self.left = child

    def label(self):
        return '*'


class ConcatNode(TreeNode):
    """Nodo binario: concatenación."""

    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right

    def label(self):
        return '.'


class UnionNode(TreeNode):
    """Nodo binario: unión (|)."""

    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right

    def label(self):
        return '|'


def clone_tree(node):
    """Clona un subárbol (necesario para expandir r+ = r.r*)."""

    if node is None:
        return None

    if isinstance(node, LeafNode):
        return LeafNode(node.symbol)

    if isinstance(node, StarNode):
        return StarNode(clone_tree(node.left))

    if isinstance(node, ConcatNode):
        return ConcatNode(
            clone_tree(node.left),
            clone_tree(node.right)
        )

    if isinstance(node, UnionNode):
        return UnionNode(
            clone_tree(node.left),
            clone_tree(node.right)
        )


# ---------------------------------------------------------
# 2. Shunting Yard: infix -> postfix
# ---------------------------------------------------------

PRECEDENCE = {
    '|': 1,
    '.': 2,
    '*': 3,
    '+': 3,
    '?': 3
}

UNARY_OPS = {'*', '+', '?'}
BINARY_OPS = {'.', '|'}


def is_operand(c):
    return c not in '()|.*+?'


def insert_concat(regex):
    """Inserta el operador de concatenación explícito '.' donde haga falta."""

    result = []

    for i, c in enumerate(regex):
        result.append(c)

        if i + 1 >= len(regex):
            continue

        next_c = regex[i + 1]

        if c in '(|':
            continue

        if c in '*+?)' or is_operand(c):
            if next_c in '*+?|)':
                continue

            if next_c == '(' or is_operand(next_c):
                result.append('.')

    return ''.join(result)


def to_postfix(regex):
    output = []
    stack = []

    for token in regex:

        if token == '(':
            stack.append(token)

        elif token == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())

            stack.pop()  # descarta el '('

        elif token in PRECEDENCE:
            while (
                stack
                and stack[-1] != '('
                and PRECEDENCE.get(stack[-1], 0) >= PRECEDENCE[token]
            ):
                output.append(stack.pop())

            stack.append(token)

        else:
            output.append(token)  # operando (símbolo o ε)

    while stack:
        output.append(stack.pop())

    return output


# ---------------------------------------------------------
# 3. Postfix -> Árbol sintáctico
#    (con simplificación de + y ?)
# ---------------------------------------------------------

def build_tree(postfix_tokens):
    stack = []

    for token in postfix_tokens:

        if token == '*':
            child = stack.pop()
            stack.append(StarNode(child))

        elif token == '+':
            # r+ = r . r*
            child = stack.pop()
            star_part = StarNode(clone_tree(child))
            stack.append(ConcatNode(child, star_part))

        elif token == '?':
            # r? = r | ε
            child = stack.pop()
            stack.append(
                UnionNode(child, LeafNode('ε'))
            )

        elif token == '.':
            right = stack.pop()
            left = stack.pop()
            stack.append(
                ConcatNode(left, right)
            )

        elif token == '|':
            right = stack.pop()
            left = stack.pop()
            stack.append(
                UnionNode(left, right)
            )

        else:
            stack.append(LeafNode(token))

    return stack.pop()


# ---------------------------------------------------------
# 4. Dibujar el árbol con Graphviz
# ---------------------------------------------------------

def draw_tree(root, filename):
    dot = Digraph()
    dot.attr('node', shape='circle')

    def visit(node):
        if node is None:
            return

        dot.node(str(node.id), node.label())

        if node.left:
            visit(node.left)
            dot.edge(
                str(node.id),
                str(node.left.id)
            )

        if node.right:
            visit(node.right)
            dot.edge(
                str(node.id),
                str(node.right.id)
            )

    visit(root)

    dot.render(
        filename,
        format='png',
        cleanup=True
    )

    print(f"  -> Árbol guardado como {filename}.png")


# ---------------------------------------------------------
# 5. Main: lee el archivo, procesa cada línea
# ---------------------------------------------------------

def main():

    if len(sys.argv) < 2:
        print("Uso: python main.py expresiones.txt")
        return

    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        lines = [
            line.strip()
            for line in f
            if line.strip()
        ]

    for idx, raw_regex in enumerate(lines, start=1):

        print(f"\n=== Expresión {idx}: {raw_regex} ===")

        regex = raw_regex.replace(' ', '')

        with_concat = insert_concat(regex)

        print(
            f"Con concatenación explícita: {with_concat}"
        )

        postfix = to_postfix(with_concat)

        print(
            f"Postfix: {''.join(postfix)}"
        )

        TreeNode._id_counter = 0

        tree = build_tree(postfix)

        draw_tree(
            tree,
            filename=f"arbol_{idx}"
        )

main()
import itertools
import random

# TODO:
#   - more function calls
#   - improve for loop


def choose_from(options):
    return random.choices(*zip(*options.items()))[0]


def type():
    return ["int"]


def constant(*_):
    return [str(random.randint(*const_range))]


def variable(variables, depth):
    return [random.choice(variables)]


def variable_declaration(variables):
    name = f"x{len(variables)}"
    variables.append(name)
    return [*type(), name]


def variable_definition(variables, depth):
    expr = expression(variables, depth)
    return [*variable_declaration(variables), "=", *expr]


def unary_operation(variables, depth, operator, type="int", prefix=True):
    if prefix:
        return [operator, *expression(variables, depth, type)]
    else:
        return [*expression(variables, depth, type), operator]


def binary_operation(variables, depth, operator, type="int"):
    return [*expression(variables, depth, type), operator, *expression(variables, depth, type)]


# arithmetic operators
def addition(*args):
    return binary_operation(*args, "+")


def subtraction(*args):
    return binary_operation(*args, "-")


def multiplication(*args):
    return binary_operation(*args, "*")


def division(*args):
    return binary_operation(*args, "/")


def modulus(*args):
    return binary_operation(*args, "%")


def increment(*args):
    return [*variable(*args), "++"]
    # return unary_operation(*args, "++", prefix=False)


def decrement(*args):
    return [*variable(*args), "--"]
    # return unary_operation(*args, "--", prefix=False)


# relational operators
def equality(*args):
    return binary_operation(*args, "==")


def inequality_ne(*args):
    return binary_operation(*args, "!=")


def inequality_lt(*args):
    return binary_operation(*args, "<")


def inequality_le(*args):
    return binary_operation(*args, "<=")


def inequality_gt(*args):
    return binary_operation(*args, ">")


def inequality_ge(*args):
    return binary_operation(*args, ">=")


# logical operators
def logical_or(*args):
    return binary_operation(*args, "&&", type="bool")


def logical_and(*args):
    return binary_operation(*args, "||", type="bool")


def logical_not(*args):
    return unary_operation(*args, "!", type="bool")


# bitwise operators
def bitwise_and(*args):
    return binary_operation(*args, "&")


def bitwise_or(*args):
    return binary_operation(*args, "|")


def bitwise_xor(*args):
    return binary_operation(*args, "^")


def bitwise_shift_left(*args):
    return binary_operation(*args, "<<")


def bitwise_shift_right(*args):
    return binary_operation(*args, ">>")


def bitwise_complement(*args):
    return unary_operation(*args, "~")


# assignment operator(s)
def assignment(variables, depth):
    return [*variable(variables, depth), "=", *expression(variables, depth)]


def expression(variables, depth, type="int", overwrited_weights={}):
    if type == "int":
        weights = expression_weights
    elif type == "bool":
        weights = bool_expression_weights
    else:
        raise ValueError(f"Unexpected type: {type}")

    return ["(", *choose_from({**weights, **overwrited_weights})(variables, depth), ")"]


def if_statement(variables, depth):
    return ["if", "(", *expression(variables, depth, "bool", overwrited_weights={constant: 0}), ")", *block(variables, depth + 1)]


def if_else_statement(variables, depth):
    return [*if_statement(variables, depth), "else", *block(variables, depth + 1)]


def for_loop(variables, depth):
    return ["for", "(",
            *expression(variables, depth), ";",
            *expression(variables, depth, "bool", overwrited_weights={constant: 0}), ";",
            *expression(variables, depth), ")",
            *block(variables, depth + 1)
            ]


def while_loop(variables, depth):
    return ["while", "(", *expression(variables, depth, "bool", overwrited_weights={constant: 0}), ")", *block(variables, depth + 1)]


def return_statement(variables, depth):
    return ["return", *expression(variables, depth, overwrited_weights={constant: 0})]


def function_call(variables, depth):
    return [random.choice(functions), "(", *expression(variables, depth), ")"]


def statement(variables, depth, overwrited_weights={}):
    weights = statement_weights if depth < max_depth else simple_statement_weights
    st = choose_from({**weights, **overwrited_weights})(variables, depth)
    return st if st[-1] == "}" else [*st, ";"]


def block(variables, depth, needs_return=False):
    variables = variables.copy()
    statements = [statement(variables, depth) for _ in range(random.randint(*statement_count))]

    if needs_return:
        statements.append([*return_statement(variables, depth), ";"])

    return ["{", *itertools.chain.from_iterable(statements), "}"]


def function(functions):
    name = f"f{len(functions)}"
    functions.append(name)

    variables = []

    parameters = (variable_declaration(variables) for _ in range(random.randint(*parameter_count)))
    parameters_flattened = [token for param in parameters for token in (*param, ",")][:-1]

    return [*type(), name, "(", *parameters_flattened, ")", *block(variables, depth=0, needs_return=True)]


def program():
    incl = [f"#include <{file}>\n" for file in includes]
    functions = []

    return [*incl, *forward_declarations, *itertools.chain.from_iterable(function(functions) for _ in range(random.randint(*function_count)))]


from config import *

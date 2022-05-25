from generate import *

function_count = (1, 1)
statement_count = (2, 4)
parameter_count = (1, 3)
const_range = (-8, 8)
functions = ["ext_func"]
includes = []
forward_declarations = ["int ext_func(int) ;"]
max_depth = 2


simple_statement_weights = {
    variable_declaration: 0,  # Should not be allowed, cannot guarantee definition before use.
    variable_definition: 1,
    assignment: 1,
    return_statement: 0,
    function_call: 1,
    increment: 1,
    decrement: 1
}

compound_statement_weights = {
    if_statement: 2,
    if_else_statement: 1,
    for_loop: 0,
    while_loop: 0
}

statement_weights = {**simple_statement_weights,**compound_statement_weights}

expression_weights = {
    constant: 10,
    variable: 20,
    addition: 2,
    subtraction: 1,
    multiplication: 1,
    division: 0,
    modulus: 0,
    bitwise_shift_left: 0,
    bitwise_shift_right: 0,
    bitwise_and: 1,
    bitwise_or: 1,
    bitwise_xor: 1,
    bitwise_complement: 1
}

bool_expression_weights = {
    equality: 5,
    inequality_ne: 5,
    inequality_lt: 2,
    inequality_le: 2,
    inequality_gt: 2,
    inequality_ge: 2,
    logical_and: 1,
    logical_or: 1,
    logical_not: 1
}

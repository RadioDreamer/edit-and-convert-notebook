import re

SEP_UNWANTED = r"[\s,]"
SEP_WANTED = r"[\[\]+\-*:]"
separator = re.compile(f"{SEP_UNWANTED}+|(?<!{SEP_UNWANTED})(?={SEP_WANTED})|(?<={SEP_WANTED})(?!{SEP_UNWANTED}|$)")

substitutions_str = {
    "ext_func@PLT": "symbol",
    "ext_func": "symbol",
}

# TODO
substitutions_re = [
    (re.compile(r"\.L\d+"), "symbol")
]

def substitute(elem):
    try:
        return hex(int(elem))
    except ValueError:
        pass

    if elem in substitutions_str:
        return substitutions_str[elem]
    
    for pattern, new in substitutions_re:
        if re.fullmatch(pattern, elem):
            return new

    return elem

def tokenize(d):
    d = {k: [list(map(substitute, re.split(separator, x))) for x in v] for (k, v) in d.items()}
    return d
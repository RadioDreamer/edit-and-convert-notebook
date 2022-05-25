import difflib
import itertools
import os
import platform
import re
import subprocess
import sys
import tempfile
from typing import Dict
from operator import itemgetter
from pprint import pprint

import msgpack

import generate
from palmtree import eval_utils as utils
from tokenizer import tokenize

NEWLINE_CHAR = {"Windows": "\r\n", "Linux": "\n"}[platform.system()]

verbose = False

GENERATE_BATCH = int(sys.argv[1])
NUM_OF_BATCHES = int(sys.argv[2])
NEEDED_OUTPUT = sys.argv[3:]


def program_to_string(l):
    return " ".join(l).replace(" ; ", ";\n").replace("{ ", "{\n").replace("} ", "}\n")


def generate_assemblies(program_count,
                        opt_flags=["-O0", "-O2"],
                        other_flags=["-S", "-o-", "-fno-asynchronous-unwind-tables", "-fverbose-asm", "-masm=intel"]):
    data = {"assemblies": []}

    with tempfile.NamedTemporaryFile(suffix=".c", delete=platform.system() == "Linux") as f:
        data["filename"] = f.name

        for program in (program_to_string(generate.program()) for _ in range(program_count)):
            f.seek(0)
            f.write(program.encode("UTF-8"))
            f.truncate()
            f.flush()

            data["assemblies"].append({})

            if verbose:
                print(program)

            for opt_flag in opt_flags:
                assembly = subprocess.check_output(["gcc", opt_flag, *other_flags, f.name],
                                                   input=program.encode("UTF-8"))
                assembly = assembly.decode()

                compiler, temp = assembly.split(NEWLINE_CHAR * 2, 1)
                opt_algs, assembly = temp.split("\t.text" + NEWLINE_CHAR, 1)

                if "compiler" not in data:
                    data["compiler"] = compiler

                if "opt_algs" not in data:
                    data["opt_algs"] = {opt_flag: opt_algs}
                elif opt_flag not in data["opt_algs"]:
                    data["opt_algs"][opt_flag] = opt_algs

                if compiler != data["compiler"]:
                    print(f"Unusual compiler properties: {compiler}")
                if opt_algs != data["opt_algs"][opt_flag]:
                    print(f"Unusual heuristics or optimalization algorithms: {opt_algs}")

                # data["assemblies"][-1]["source"] = program
                data["assemblies"][-1][opt_flag] = assembly

                if verbose:
                    print(assembly)

    return data

def string_to_program(s):
    return s.replace('\t', ' ').replace('\r', '').split('\n')


def compare_insn_dicts(*, o0: Dict = None, o2: Dict = None):
    result: Dict = {}

    for key in o0.keys() & o2.keys():  # FIXME: combine lines together if necessary
        if keep_assembly(o0[key], o2[key]):
            result[key] = {'O0': o0[key], 'O2': o2[key]}

    return result


def keep_assembly(o0, o2):
    return o0 != o2 and len(o2) <= len(o0) + 1 and len(o2) <= 8


def make_insn_dict(l):
    # TODO: 1 utasításból álló C kód esetét lekezelni -> szedjük ki
    result: Dict = {}

    # (line_number_in_source , index in list)
    helper = []

    for i in range(len(l)):
        expr = re.search(r'.*# [a-zA-Z0-9\/\\_:~]+\.c:(\d+)', l[i])
        if expr is not None:
            line_num = int(expr.group(1))
            helper.append((line_num, i))

    # The last line always corresponds to quitting the main function
    for i in range(len(helper) - 1):
        if helper[i][0] in result:
            result[helper[i][0]].extend(l[helper[i][1] + 1:helper[i + 1][1]])
        else:
            result[helper[i][0]] = l[helper[i][1] + 1:helper[i + 1][1]]

    return result


def asm_token_diff(d: Dict):
    for k in d.keys():
        line_diff = difflib.SequenceMatcher(None, list(map(itemgetter(0), d[k]['O0'])), list(map(itemgetter(0), d[k]['O2'])))
        matching_blocks = iter(line_diff.get_matching_blocks())

        next_match = next(matching_blocks)
        i = j = 0
        total_edit_list = []
        while i < len(d[k]['O0']) or j < len(d[k]['O2']):

            if (i >= next_match.a and j >= next_match.b) or (i < next_match.a and j < next_match.b):
                fst_list = d[k]['O0'][i]
                snd_list = d[k]['O2'][j]
                # s = difflib.SequenceMatcher(lambda x: x == ' ', fst_list, snd_list)
                s = difflib.SequenceMatcher(None, fst_list, snd_list)
                edit_seq = []
                for tag, i1, i2, j1, j2 in s.get_opcodes():
                    if tag == 'delete':
                        edit_seq += list(itertools.repeat('-', i2 - i1))
                    elif tag == 'equal':
                        edit_seq += list(itertools.repeat('_', i2 - i1))
                    elif tag == 'replace':
                        edit_seq += list(itertools.repeat('!=', i2 - i1))
                    elif tag == 'insert':
                        edit_seq += list(itertools.repeat('+', j2 - j1))

                if i == next_match.a + max(0, next_match.size - 1):
                    next_match = next(matching_blocks)

                i += 1
                j += 1
            elif i < next_match.a:
                fst_list = d[k]['O0'][i]
                edit_seq = ['-'] * len(fst_list)
                i += 1
            else:
                snd_list = d[k]['O2'][j]
                edit_seq = ['+'] * len(snd_list)
                j += 1
                # 3.10 version
                # match tag:
                #     case 'delete':
                #         edit_seq += (list(itertools.repeat('-', i2 - i1)))
                #     case 'equal':
                #         edit_seq += (list(itertools.repeat('_', i2 - i1)))
                #     case 'replace':
                #         edit_seq += (list(itertools.repeat('!=', i2 - i1)))
                #     case 'insert':
                #         edit_seq += (list(itertools.repeat('+', j2 - j1)))

            total_edit_list.append(list(itertools.chain(edit_seq)))
        d[k]['diff'] = total_edit_list

    return d


def cleanse_insn_dict(d: Dict):
    for k in d.keys():
        for i in range(0, len(d[k])):
            last_htag = d[k][i].rfind('#')
            rplc = d[k][i][:last_htag].strip()
            d[k][i] = rplc

        d[k] = [line for line in d[k] if not line.startswith(".")]

    return {k: v for k, v in d.items() if v}


def calculate_diffs(gen_data):
    # with open(path, 'r', encoding='UTF-8') as f:
    #    gen_data = json.load(f)

    # var = make_insn_dict(string_to_program(gen_data['assemblies'][0]['-O0']))
    nof_examples = len(gen_data['assemblies'])
    print(f'{nof_examples}')

    dataset = []
    # print(tokenize(cleanse_insn_dict(make_insn_dict(string_to_program(gen_data['assemblies'][0]['-O0'])))))
    # print(asm_token_diff(compare_insn_dicts(
    #     o0=tokenize(cleanse_insn_dict(make_insn_dict(string_to_program(gen_data['assemblies'][0]['-O0'])))),
    #     o3=tokenize(cleanse_insn_dict(make_insn_dict(string_to_program(gen_data['assemblies'][0]['-O2'])))))))
    for i in range(0, nof_examples):
        asm_diff = compare_insn_dicts(
            o0=tokenize(cleanse_insn_dict(make_insn_dict(string_to_program(gen_data['assemblies'][i]['-O0'])))),
            o2=tokenize(cleanse_insn_dict(make_insn_dict(string_to_program(gen_data['assemblies'][i]['-O2'])))))
        dataset.append(asm_token_diff(asm_diff))
    return dataset


sys.path.append(os.path.abspath(os.path.join('', '/')))

palmtree = utils.UsableTransformer(
    model_path="palmtree/palmtree/transformer.ep19",
    vocab_path="palmtree/palmtree/vocab")


# tokens has to be seperated by spaces.


one_hot = {'-': [0, 0, 0, 1], '!=': [0, 0, 1, 0], '_': [0, 1, 0, 0], '+': [1, 0, 0, 0]}


def make_fixed_length(l):
    l = l[:40]
    if len(l) < 40:
        l.extend([0] * (40 - len(l)))
    return l


if __name__ == '__main__':

    data_format = {"O0": lambda di: palmtree.encode(list(map(" ".join, di['O0']))).tolist(),
                   "O2": lambda di: palmtree.encode(list(map(" ".join, di['O2']))).tolist(),
                   "O0_tokens": lambda di: di['O0'],
                   "O2_tokens": lambda di: di['O2'],
                   "diff": lambda di: [make_fixed_length([b for x in map(one_hot.get, line) for b in x]) for line in
                                       di["diff"]]}

    with open('data.bin', 'wb') as f:
        metadata = {"max_line_count_O0": 0, "max_line_count_O2": 0}
        metadata_estimated_size = len(msgpack.packb(metadata, use_bin_type=True)) # remains the same if numbers are in [0; 127]
        f.write(msgpack.packb(metadata, use_bin_type=True))

        kept_samples = 0
        counter = 0
        while kept_samples < NUM_OF_BATCHES * GENERATE_BATCH:
            dataset = calculate_diffs(generate_assemblies(GENERATE_BATCH))
            counter += 1
            # print(dataset)
            for d in dataset:
                if not d:
                    continue
                kept_samples += len(d)

                for line in d.values():
                    metadata["max_line_count_O0"] = max(metadata["max_line_count_O0"], len(line["O0"]))
                    metadata["max_line_count_O2"] = max(metadata["max_line_count_O2"], len(line["O2"]))

                f.write(msgpack.packb({i: {format: data_format[format](d[i]) for format in NEEDED_OUTPUT}
                                       for i in d}, use_bin_type=True))
        print(f"Number of batches for {kept_samples} data: {counter}")

        if metadata_estimated_size != len(msgpack.packb(metadata, use_bin_type=True)):
            print(f"Metadata size not estimated correctly, cannot write into file.\n{metadata}")
        else:
            f.seek(0)
            f.write(msgpack.packb(metadata, use_bin_type=True))


    # with open('data.bin',"rb") as f:
    #     unpacker = msgpack.Unpacker(f, raw=False, strict_map_key=False)
    #     counter = 0
    #     len_counter = 0
    #     for unpacked in unpacker:
    #         len_counter += len(unpacked)
    #         counter += 1
    #     print(f"NUM OF EXAMPLES: {counter}")
    #     print(f"LENGTH OF EXAMPLES: {len_counter}")

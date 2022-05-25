import sys

import msgpack

metadata = {}
with open(sys.argv[1], "rb") as f:
    unpacker_fst = msgpack.Unpacker(f, raw=False, strict_map_key=False)
    metadata_fst = next(unpacker_fst)
    with open(sys.argv[2], "rb") as g:
        unpacker_snd = msgpack.Unpacker(g, raw=False, strict_map_key=False)
        metadata_snd = next(unpacker_snd)
        metadata["max_line_count_O0"] = max(metadata_fst["max_line_count_O0"], metadata_snd["max_line_count_O0"])
        metadata["max_line_count_O2"] = max(metadata_fst["max_line_count_O2"], metadata_snd["max_line_count_O2"])

        with open(sys.argv[3], 'wb') as out_file:
            out_file.write(msgpack.packb(metadata, use_bin_type=True))
            f.seek(len(msgpack.packb(metadata, use_bin_type=True)))
            g.seek(len(msgpack.packb(metadata, use_bin_type=True)))
            out_file.write(f.read())
            out_file.write(g.read())

# with open(sys.argv[3], "rb") as h:
#     unpacker = msgpack.Unpacker(h, raw=False, strict_map_key=False)
#     counter = 0
#     len_counter = 0
#     for unpacked in unpacker:
#         print(unpacked)
#         len_counter += len(unpacked)
#         counter += 1
#     print(f"NUM OF EXAMPLES: {counter}")
#     print(f"LENGTH OF EXAMPLES: {len_counter}")

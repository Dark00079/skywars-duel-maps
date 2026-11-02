"""Minimal NBT writer (big-endian, gzip) - enough for WorldEdit/FAWE schematics.

Values are passed as (tag_type, payload) tuples. Helpers below build them.
"""
import gzip
import struct

END, BYTE, SHORT, INT, LONG, FLOAT, DOUBLE, BYTE_ARRAY, STRING, LIST, COMPOUND, INT_ARRAY, LONG_ARRAY = range(13)


def Byte(v): return (BYTE, v)
def Short(v): return (SHORT, v)
def Int(v): return (INT, v)
def String(v): return (STRING, v)
def ByteArray(b): return (BYTE_ARRAY, bytes(b))
def IntArray(v): return (INT_ARRAY, list(v))
def Compound(d): return (COMPOUND, d)
def List(elem_type, items): return (LIST, (elem_type, items))


def _w_string(out, s):
    b = s.encode("utf-8")
    out += struct.pack(">H", len(b))
    out += b


def _w_payload(out, t, v):
    if t == BYTE:
        out += struct.pack(">b", v)
    elif t == SHORT:
        out += struct.pack(">h", v)
    elif t == INT:
        out += struct.pack(">i", v)
    elif t == LONG:
        out += struct.pack(">q", v)
    elif t == FLOAT:
        out += struct.pack(">f", v)
    elif t == DOUBLE:
        out += struct.pack(">d", v)
    elif t == BYTE_ARRAY:
        out += struct.pack(">i", len(v))
        out += v
    elif t == STRING:
        _w_string(out, v)
    elif t == LIST:
        et, items = v
        out += struct.pack(">bi", et if items else (et or END), len(items))
        for it in items:
            # items are raw payloads for et (compounds: dict)
            _w_payload(out, et, it)
    elif t == COMPOUND:
        for name, (ct, cv) in v.items():
            out += struct.pack(">b", ct)
            _w_string(out, name)
            _w_payload(out, ct, cv)
        out += b"\x00"
    elif t == INT_ARRAY:
        out += struct.pack(">i", len(v))
        out += struct.pack(">%di" % len(v), *v)
    elif t == LONG_ARRAY:
        out += struct.pack(">i", len(v))
        out += struct.pack(">%dq" % len(v), *v)
    else:
        raise ValueError("bad tag type %r" % t)


def dumps(root_name, compound_dict):
    out = bytearray()
    out += struct.pack(">b", COMPOUND)
    _w_string(out, root_name)
    _w_payload(out, COMPOUND, compound_dict)
    return bytes(out)


def write_gz(path, root_name, compound_dict):
    data = dumps(root_name, compound_dict)
    with open(path, "wb") as f:
        # mtime=0 keeps output byte-identical between runs
        f.write(gzip.compress(data, compresslevel=9, mtime=0))

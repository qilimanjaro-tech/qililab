import hashlib

from qm import Program
from qm.serialization.generate_qua_script import generate_qua_script
from qpysequence import Sequence


def hash_qua_program(program: Program) -> str:
    """Hash a QUA program"""
    program_str = "\n".join(generate_qua_script(program).split("\n")[3:])
    return hashlib.md5(program_str.encode("utf-8"), usedforsecurity=False).hexdigest()


def hash_qpy_sequence(sequence: Sequence):
    sequence_str = repr(sequence)
    return hashlib.md5(sequence_str.encode("utf-8"), usedforsecurity=False).hexdigest()

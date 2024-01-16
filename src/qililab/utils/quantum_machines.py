import hashlib

from qm import Program
from qm.serialization.generate_qua_script import generate_qua_script


def hash_qua_program(program: Program) -> str:
    """Hash a QUA program"""
    program_str = "\n".join(generate_qua_script(program).split("\n")[3:])
    return hashlib.md5(program_str.encode("utf-8"), usedforsecurity=False).hexdigest()

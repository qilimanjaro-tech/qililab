"""Module containing utilities for the tests."""


def name_generator(base: str):
    """Unique name generator
    Args:
        base (str): common name for all the elements.
    Yields:
        str: Unique name in the format base_id.
    """
    next_id = 0
    while True:
        yield f"{base}_{str(next_id)}"
        next_id += 1


dummy_qrm_name_generator = name_generator("dummy_qrm")
dummy_qcm_name_generator = name_generator("dummy_qcm")

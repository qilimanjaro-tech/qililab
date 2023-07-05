""" Castings for Enums """
from dataclasses import fields
from enum import Enum


def cast_enum_fields(obj):
    for field in fields(obj):
        if isinstance(field.type, type) and issubclass(field.type, Enum):
            setattr(obj, field.name, field.type(getattr(obj, field.name)))

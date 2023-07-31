class ClassPropertyDescriptor(  # pylint: disable=too-few-public-methods # pylint: disable=missing-class-docstring
    object
):
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, obj, klass):
        return self.fget.__get__(obj, klass)()


def classproperty(func):  # pylint: disable=missing-function-docstring
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return ClassPropertyDescriptor(func)

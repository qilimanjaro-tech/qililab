# Copyright 2023 Qilimanjaro Quantum Tech
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Any, Callable


class FluqeParameter:
    """Basic implementation of a qcodes like parameter class, but much simpler.
    Working, but still work in progress


    Args:
        name(str): name of the parameter
        value(any|none): initial value of the parameter
        set_method(callable|None): the set method of the parameter. If not is given, defaults to `set_raw()`.
    Calling
    """

    def __init__(self, name: str, value: Any | None = None, set_method: Callable | None = None):
        """init method"""
        # TODO: add units and other useful info
        self.name = name
        self._value = value
        self.set = set_method

    def __call__(self, *args: Any, **kwargs: Any) -> Any | None:
        """Call method for the parameter class"""
        # TODO: implement get_raw like in qcodes
        if not args and not kwargs:
            return self.get(*args, **kwargs)
        self._value = self.set(*args, **kwargs) if self.set is not None else self.set_raw(args[0])
        return None

    def get(self) -> Any:
        """Get method. Returns the parameter current value.

        Returns:
            Any: parameter value
        """
        return self._value

    def set_raw(self, value: Any) -> Any:
        """set_raw method. This is the default if no set method is given. The parameter is assigned the value given as argument.

        Args:
            value (Any): parameter value to set

        Returns:
            Any: parameter value set.
        """
        self._value = value
        return value

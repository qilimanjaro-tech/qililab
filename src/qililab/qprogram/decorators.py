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

import functools

from .variable import Domain, Variable


def requires_domain(parameter: str, domain: Domain):
    """Decorator to denote that a parameter requires a variable of a specific domain.

    Args:
        parameter (str): The parameter name.
        domain (Domain): The variable's domain.
    """

    def decorator_function(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if the parameter is not inside kwargs, for optional parameters
            if parameter not in kwargs and len(args) == 1:
                kwargs[parameter] = None
            # Get the argument by name
            param_value = kwargs.get(parameter) if parameter in kwargs else None

            if isinstance(param_value, Variable) and param_value.domain != domain:
                raise ValueError(f"Expected domain {domain} for {parameter}, but got {param_value.domain}")
            return func(*args, **kwargs)

        return wrapper

    return decorator_function

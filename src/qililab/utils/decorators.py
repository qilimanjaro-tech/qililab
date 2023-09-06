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


class ClassPropertyDescriptor:  # pylint: disable=too-few-public-methods, disable=missing-class-docstring
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, obj, klass):
        return self.fget.__get__(obj, klass)()


def classproperty(func):  # pylint: disable=missing-function-docstring
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)

    return ClassPropertyDescriptor(func)

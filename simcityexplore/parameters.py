# SIM-CITY explore
#
# Copyright 2015 Joris Borgdorff <j.borgdorff@esciencecenter.nl>
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

from .util import make_hash
import sys


def parse_parameter_spec(idict):
    default = idict.get('default', None)
    if idict['type'] == 'interval':
        dtype = idict.get('dtype', 'float')
        return IntervalSpec(idict['name'], idict['min'], idict['max'],
                            default, dtype)
    if idict['type'] == 'choice':
        dtype = idict.get('dtype', 'str')
        return ChoiceSpec(idict['name'], idict['choices'], default, dtype)
    if idict['type'] == 'str':
        min_len = idict.get('min_length', None)
        max_len = idict.get('max_length', None)
        return StringSpec(idict['name'], default, min_len, max_len)

    raise ValueError('parameter type not recognized')


class ParameterSpec(object):
    TYPE_STR = {
        'int': int,
        'float': float,
        'str': str
    }

    def __init__(self, name, default, dtype):
        if type(dtype) == type:
            self._dtype = dtype
        else:
            try:
                self._dtype = ParameterSpec.TYPE_STR[dtype]
            except KeyError:
                opts = str(ParameterSpec.keys())
                raise ValueError(
                    "Type " + str(dtype) + " unknown; use one of " + opts)

        if default is None:
            self._default = None
        else:
            self._default = self.coerce(default)
        self._name = name

    @property
    def default(self):
        return self._default

    @property
    def dtype(self):
        return self._dtype

    @property
    def name(self):
        return self._name

    def coerce(self, value):
        if type(value) == self.dtype:
            return value
        elif value is None and self.dtype == str:
            return ''
        else:
            return self.dtype(value)

    def is_valid(self, value):
        raise NotImplementedError


class ChoiceSpec(ParameterSpec):

    """ Specify a limited amount of choices """

    def __init__(self, name, choices, default, dtype):
        if type(choices) != list:
            raise ValueError("Choices must be provided as a list")
        if len(choices) == 0:
            raise ValueError("At least one choice is required.")
        if default is None:
            default = choices[0]

        super(ChoiceSpec, self).__init__(name, default, dtype)
        self._choices = [self.coerce(choice) for choice in choices]
        self._choices.sort()

    @property
    def choices(self):
        return self._choices.copy()

    def is_valid(self, value):
        return type(value) == self.dtype and value in self._choices

    def __str__(self):
        return (self.name + ': choice ' + str(self._choices) + ' ' +
                str(self.dtype))

    def __eq__(self, other):
        return (type(self) == type(other) and
                self._choices == other._choices and
                self.default == other.default and
                self.dtype == other.dtype)

    def __hash__(self):
        return make_hash(self._default, self.dtype, *self._choices)


class IntervalSpec(ParameterSpec):

    """ Specify an interval for parameters to lie in """

    def __init__(self, name, min, max, default, dtype):
        if default is None:
            default = (self._min + self._max) / 2
        super(IntervalSpec, self).__init__(name, default, dtype)

        self._min = self.coerce(min)
        self._max = self.coerce(max)

        if self._min > self._max:
            raise ValueError(
                "Minimum to an interval must be smaller than maximum")

        if not self.is_valid(self.default):
            raise ValueError("default value for interval not valid")

    @property
    def max(self):
        return self._max

    @property
    def min(self):
        return self._min

    def is_valid(self, value):
        return (value >= self.min and
                value <= self.max and
                type(value) == self.dtype)

    def __str__(self):
        return (self.name + ': interval [' + str(self.min) + ',' +
                str(self.max) + '] ' + str(self.dtype))

    def __eq__(self, other):
        return (type(self) == type(other) and
                self._min == other._min and
                self._max == other._max and
                self._default == other._default and
                self.dtype == other.dtype)

    def __hash__(self):
        return make_hash(self._min, self._max, self._default, self.dtype)


class StringSpec(ParameterSpec):

    """ Specify string characteristics. """

    def __init__(self, name, default, min_len, max_len):
        super(StringSpec, self).__init__(name, default, str)
        if min_len is None:
            min_len = 0
        if max_len is None:
            max_len = sys.maxsize
        self._min_len = int(min_len)
        self._max_len = int(max_len)

    @property
    def min_len(self):
        return self._min_len

    @property
    def max_len(self):
        return self._max_len

    def is_valid(self, value):
        return (type(value) == self.dtype and
                len(value) >= self.min_len and
                len(value) <= self.max_len)

    def __str__(self):
        return (self.name + ': str [len ' + str(self.min_len) + '-' +
                str(self.max_len) + ']')

    def __eq__(self, other):
        return (type(self) == type(other) and
                self.min_len == other.min_len and
                self.max_len == other.max_len and
                self.default == other.default)

    def __hash__(self):
        return make_hash(self.min_len, self.max_len, self.default)
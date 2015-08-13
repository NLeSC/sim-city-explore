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

import sys
import math


def parse_parameters(parameters, parameter_specs):
    paramset = frozenset(parameters)
    param_specset = frozenset([param['name'] for param in parameter_specs])

    if not (paramset <= param_specset):
        raise ValueError("parameters {} not specified ({} vs {})"
                         .format(list(paramset - param_specset), parameters,
                                 parameter_specs))

    params = {}
    for spec_raw in parameter_specs:
        spec = parse_parameter_spec(spec_raw)
        try:
            value = parameters[spec.name]
            del parameters[spec.name]
            value = spec.coerce(value)
        except KeyError:
            raise ValueError("parameter for {} is not specified {} ... {}"
                             .format(spec.name, spec, parameters))
        except (TypeError, ValueError):
            raise ValueError("value of {} for parameter does not comply to {}"
                             .format(value, spec))
        else:
            if spec.is_valid(value):
                params[spec.name] = value
            else:
                raise ValueError(
                    "value of {} for parameter does not comply to {}"
                    .format(value, spec))
    return params


def parse_parameter_spec(idict):
    default = idict.get('default', None)
    if idict['type'] in ('number', 'interval'):
        dtype = idict.get('dtype', 'float')
        return IntervalSpec(idict['name'], dtype,
                            idict.get('min'), idict.get('max'), default)
    if idict['type'] == 'choice':
        dtype = idict.get('dtype', 'str')
        return ChoiceSpec(idict['name'], idict['choices'], dtype, default)
    if idict['type'] in ('str', 'string'):
        min_len = idict.get('min_length')
        max_len = idict.get('max_length')
        return StringSpec(idict['name'], default, min_len, max_len)
    if idict['type'] == 'point2d':
        x_dict = idict.get('x', {})
        x_dict.update({'name': 'x', 'type': 'interval'})
        y_dict = idict.get('y', {})
        y_dict.update({'name': 'y', 'type': 'interval'})
        x = parse_parameter_spec(x_dict)
        y = parse_parameter_spec(y_dict)
        try:
            properties = [parse_parameter_spec(prop)
                          for prop in idict.get('properties', [])]
        except KeyError:
            properties = None

        return Point2DSpec(idict['name'], x, y, properties)
    if idict['type'] == 'list':
        idict['contents'].update({'name': 'contents'})
        content_spec = parse_parameter_spec(idict['contents'])
        min_len = idict.get('min_length')
        max_len = idict.get('max_length')
        return ListSpec(idict['name'], content_spec, min_len, max_len)
    if idict['type'] == 'fixed':
        return FixedSpec(idict['name'], idict['value'])

    raise ValueError('parameter type not recognized')


class ParameterDatatype(object):
    TYPE_STR = {
        'int': int,
        'float': float,
        'str': str,
        'bool': bool,
    }

    def __init__(self, dtype):
        if type(dtype) == ParameterDatatype:
            self._dtype = dtype.dtype
        elif type(dtype) == type:
            self._dtype = dtype
        else:
            try:
                self._dtype = ParameterDatatype.TYPE_STR[dtype]
            except KeyError:
                opts = str(ParameterDatatype.TYPE_STR.keys())
                raise ValueError(
                    "Type " + str(dtype) + " unknown; use one of " + opts)

    @property
    def dtype(self):
        return self._dtype

    def coerce_if_set(self, value, default=None):
        if value is None:
            return default
        else:
            return self.coerce(value)

    def coerce(self, value):
        if type(value) == self.dtype:
            return value
        elif value is None and self.dtype == str:
            return ''
        else:
            return self.dtype(value)

    def __eq__(self, other):
        return type(self) == type(other) and self.dtype == other.dtype

    def __hash__(self):
        return hash(self.dtype)

    def __str__(self):
        return str(self.dtype)

    def is_valid(self, value):
        return type(value) == self.dtype


class ParameterSpec(object):

    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    def coerce(self, value):
        raise NotImplementedError

    def is_valid(self, value):
        raise NotImplementedError

    def choose(self, mapping):
        raise NotImplementedError

    def __eq__(self, other):
        return type(self) == type(other) and self.name == other.name

    def __hash__(self, other):
        return hash(self.name)

class FixedSpec(object):

    def __init__(self, name, value, dtype=None):
        super(FixedSpec, self).__init__(name)
        if dtype is None:
            self._value = ParameterDatatype(dtype).coerce(value)
        else:
            self._value = value

    def coerce(self, value):
        return type(self.value)(value)

    def is_valid(self, value):
        return self.value == value

    @property
    def value(self):
        return self._value

    def choose(self, mapping):
        return self.value
    
    def __str__(self):
        return "fixed: {}".format(self.value)

    def __eq__(self, other):
        return type(self) == type(other) and self.value == other.value

    def __hash__(self):
        return hash((super(SimpleParameterSpec, self).__hash__()), self.value)


class SimpleParameterSpec(ParameterSpec):

    def __init__(self, name, default, dtype):
        super(SimpleParameterSpec, self).__init__(name)
        self._dtype = ParameterDatatype(dtype)

        if default is None:
            self._default = None
        else:
            self._default = self.dtype.coerce(default)

    @property
    def default(self):
        return self._default

    @property
    def dtype(self):
        return self._dtype

    def coerce(self, value):
        return self.dtype.coerce(value)

    def __eq__(self, other):
        return (super(SimpleParameterSpec, self).__eq__(other) and
                self.default == other.default and
                self.dtype == other.dtype)

    def __hash__(self):
        return hash((super(SimpleParameterSpec, self).__hash__()),
                     self.default, self.dtype)


class ChoiceSpec(SimpleParameterSpec):

    """ Specify a limited amount of choices """

    def __init__(self, name, choices, dtype, default=None):
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
        return self.dtype.is_valid(value) and value in self._choices

    def choose(self, mapping):
        idx = int(mapping * len(self._choices))
        return self._choices[idx]

    def __str__(self):
        return ('{self.name}: choice {self._choices} {self.dtype}'
                .format(self=self))

    def __eq__(self, other):
        return (super(ChoiceSpec, self).__eq__(other) and
                self._choices == other._choices)

    def __hash__(self):
        return hash((super(ChoiceSpec, self).__hash__(), self._choices))


class IntervalSpec(SimpleParameterSpec):

    """ Specify an interval for parameters to lie in """

    def __init__(self, name, dtype, min_value=float('-inf'),
                 max_value=float('+inf'), default=None):
        dtype = ParameterDatatype(dtype)
        self._min = dtype.coerce_if_set(min_value, float('-inf'))
        self._max = dtype.coerce_if_set(max_value, float('+inf'))

        if self._min > self._max:
            raise ValueError(
                "Minimum to an interval must be smaller than maximum")

        if default is None:
            if self._min == float('-inf'):
                default = self._max
            elif self._max == float('+inf'):
                default = self._min
            else:
                default = (self._min + self._max) / 2
        super(IntervalSpec, self).__init__(name, default, dtype)

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
                self.dtype.is_valid(value))

    def choose(self, mapping):
        if self.min is not None and self.max is not None:
            return self.coerce(mapping * (self.max - self.min) + self.min)
        elif self.min is not None:
            # exponential tail: [0, 1) -> [min, +inf)
            return self.coerce(-100*math.log(1 - mapping) + self.min)
        elif self.max is not None:  # exponential tail towards +inf
            # exponential tail: [0, 1) -> [max, -inf)
            return self.coerce(100*math.log(1 - mapping) + self.max)
        elif mapping == 0.0:
            return float('-inf')
        else:
            # (0, 0.5, 1) -> (-inf, 0, inf)
            return math.sign(mapping - 0.5) * 100 *math.log(1 - 2 * math.abs(0.5 - mapping))

    def __str__(self):
        return ('{self.name}: interval [{self.min}, {self.max}] {self.dtype}'
                .format(self=self))

    def __eq__(self, other):
        return (super(IntervalSpec, self).__eq__(other) and
                self._min == other._min and
                self._max == other._max)

    def __hash__(self):
        return hash((super(IntervalSpec, self).__hash__(),
                     self._min, self._max))


class StringSpec(SimpleParameterSpec):

    """ Specify string characteristics. """

    def __init__(self, name, default='', min_len=0, max_len=sys.maxsize):
        super(StringSpec, self).__init__(name, default, str)
        len_dtype = ParameterDatatype(int)
        self._min_len = len_dtype.coerce_if_set(min_len, 0)
        self._max_len = len_dtype.coerce_if_set(max_len, sys.maxsize)
        if self._min_len > self._max_len:
            raise ValueError("Minimum string length of {self.name} "
                             "({self.min_len}) longer than maximum "
                             "({self.max_len}).".format(self=self))
        if self._min_len < 0:
            raise ValueError("Minimum string length of {self.name} "
                             "({self.min_len}) must be at least 0."
                             .format(self=self))

    @property
    def min_len(self):
        return self._min_len

    @property
    def max_len(self):
        return self._max_len

    def is_valid(self, value):
        return (self.dtype.is_valid(value) and
                len(value) >= self.min_len and
                len(value) <= self.max_len)

    def __str__(self):
        return ('{self.name}: str [len {self.min_len}-{self.max_len}]'
                .format(self=self))

    def __eq__(self, other):
        return (super(StringSpec, self).__eq__(other) and
                self.min_len == other.min_len and
                self.max_len == other.max_len)

    def __hash__(self):
        return hash((super(StringSpec, self).__hash__(), self.min_len,
                     self.max_len))


class ListSpec(ParameterSpec):

    """ Specify a list of data. """

    def __init__(self, name, content_spec, min_len=0, max_len=sys.maxsize):
        super(ListSpec, self).__init__(name)
        self._content_spec = content_spec
        len_dtype = ParameterDatatype(int)
        self._min_len = len_dtype.coerce_if_set(min_len, 0)
        self._max_len = len_dtype.coerce_if_set(max_len, sys.maxsize)
        if self._min_len > self._max_len:
            raise ValueError("Minimum list length of {self.name} "
                             "({self.min_len}) longer than maximum "
                             "({self.max_len}).".format(self=self))
        if self._min_len < 0:
            raise ValueError("Minimum list length of {self.name} "
                             "({self.min_len}) must be at least 0."
                             .format(self=self))

    @property
    def content_spec(self):
        return self._content_spec

    @property
    def min_len(self):
        return self._min_len

    @property
    def max_len(self):
        return self._max_len

    def is_valid(self, value):
        return (type(value) == list and
                all(self.content_spec.is_valid(v) for v in value) and
                len(value) >= self.min_len and
                len(value) <= self.max_len)

    def coerce(self, value):
        return [self.content_spec.coerce(v) for v in value]
    
    def __eq__(self, other):
        return (super(ListSpec, self).__eq__(other) and
                self.content_spec == other.content_spec and
                self.min_len == other.min_len and
                self.max_len == other.max_len)
    def __hash__(self):
        return hash((super(ListSpec, self).__hash__(), self.content_spec,
                     self.min_len, self.max_len))

    def __str__(self):
        return ("{self.name}: list [{self.min_len} - {self.max_len}] "
                "<{self.content_spec}>".format(self=self))


class Point2DSpec(ParameterSpec):

    """ Specify a 2D point, with given properties. """

    def __init__(self, name, x, y, valid_properties=[]):
        super(Point2DSpec, self).__init__(name)
        self._x = x
        self._y = y
        self._properties = valid_properties

    def is_valid(self, value):
        try:
            props = value.get('properties', {})
            return (
                type(value) == dict and
                self.x.is_valid(self.x.coerce(value['x'])) and
                self.y.is_valid(self.y.coerce(value['y'])) and
                frozenset(props.keys()).issubset(
                    prop.name for prop in self._properties) and
                all(
                    prop.is_valid(prop.coerce(
                        props[prop.name]
                    ))
                    for prop in self._properties)
            )
        except KeyError:
            return False

    def coerce(self, value):
        value['x'] = self.x.coerce(value['x'])
        value['y'] = self.y.coerce(value['y'])
        if 'properties' in value:
            value['properties'] = dict(
                (prop.name, prop.coerce(value['properties'][prop.name]))
                for prop in self._properties
                if prop.name in value['properties']
            )
        else:
            value['properties'] = {}

        return value

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def properties(self):
        return list(self._properties)

    def __str__(self):
        return ('{self.name}: point2d [{self.x}; {self.y}] {self.properties}'
                .format(self=self))

    def __eq__(self, other):
        return (super(Point2DSpec, self).__eq__(other) and
                self.x == other.x and
                self.y == other.y and
                self.properties == other.properties)

    def __hash__(self):
        return hash((super(Point2DSpec, self).__hash__(), self.x, self.y,
                     self.properties))

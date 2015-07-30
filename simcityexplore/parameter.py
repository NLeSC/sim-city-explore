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
                             .format(value, spec.dtype))
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
        return IntervalSpec(idict['name'], idict.get('min'), idict.get('max'),
                            default, dtype)
    if idict['type'] == 'choice':
        dtype = idict.get('dtype', 'str')
        return ChoiceSpec(idict['name'], idict['choices'], default, dtype)
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

    raise ValueError('parameter type not recognized')


class ParameterDatatype(object):
    TYPE_STR = {
        'int': int,
        'float': float,
        'str': str,
        'dict': dict
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

    def __init__(self, name, default, dtype):
        self._dtype = ParameterDatatype(dtype)

        if default is None:
            self._default = None
        else:
            self._default = self.dtype.coerce(default)
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
        return self.dtype.coerce(value)

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
        return self.dtype.is_valid(value) and value in self._choices

    def __str__(self):
        return ('{self.name}: choice {self._choices} {self.dtype}'
                .format(self=self))

    def __eq__(self, other):
        return (type(self) == type(other) and
                self._choices == other._choices and
                self.default == other.default and
                self.dtype == other.dtype)

    def __hash__(self):
        return hash((self._default, self.dtype, self._choices))


class IntervalSpec(ParameterSpec):

    """ Specify an interval for parameters to lie in """

    def __init__(self, name, min_value, max_value, default, dtype):
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

    def __str__(self):
        return ('{self.name}: interval [{self.min}, {self.max}] {self.dtype}'
                .format(self=self))

    def __eq__(self, other):
        return (type(self) == type(other) and
                self._min == other._min and
                self._max == other._max and
                self._default == other._default and
                self.dtype == other.dtype)

    def __hash__(self):
        return hash((self._min, self._max, self._default, self.dtype))


class StringSpec(ParameterSpec):

    """ Specify string characteristics. """

    def __init__(self, name, default, min_len, max_len):
        super(StringSpec, self).__init__(name, default, str)
        len_dtype = ParameterDatatype(int)
        self._min_len = len_dtype.coerce_if_set(min_len, 0)
        self._max_len = len_dtype.coerce_if_set(max_len, sys.maxsize)
        if self._min_len > self._max_len:
            raise ValueError("Minimum string length of {self.name} "
                             "({self.min_len}) longer than maximum "
                             "({self.max_len}).".format(self=self))

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
        return (type(self) == type(other) and
                self.min_len == other.min_len and
                self.max_len == other.max_len and
                self.default == other.default)

    def __hash__(self):
        return hash((self.min_len, self.max_len, self.default))


class Point2DSpec(ParameterSpec):

    """ Specify a 2D point, with given properties. """

    def __init__(self, name, x, y, valid_properties):
        super(Point2DSpec, self).__init__(name, None, dict)
        self._x = x
        self._y = y
        self._properties = valid_properties
        print(valid_properties)

    def is_valid(self, value):
        try:
            return (
                self.dtype.is_valid(value) and
                self.x.is_valid(self.x.coerce(value['x'])) and
                self.y.is_valid(self.y.coerce(value['y'])) and
                frozenset(value.get('properties', {}).keys()).issubset(
                    prop.name for prop in self._properties) and
                all(
                    prop.is_valid(prop.coerce(
                        value.get('properties', {})[prop.name]
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
        return self._properties.copy()

    def __str__(self):
        return ('{self.name}: point2d [{self.x}; {self.y}] {self.properties}'
                .format(self=self))

    def __eq__(self, other):
        return (type(self) == type(other) and
                self.name == other.name and
                self.x == other.x and
                self.y == other.y and
                self.properties == other.properties)

    def __hash__(self):
        return hash((self.name, self.x, self.y, self.properties))

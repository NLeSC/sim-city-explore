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
import jsonschema
import types


def parse_parameters(parameters, schema):
    try:
        jsonschema.validate(parameters, schema)
    except jsonschema.SchemaError as ex:
        raise EnvironmentError(ex.message)
    except jsonschema.ValidationError as ex:
        raise ValueError(ex.message)


def num_samples_object(chooser, schema):
    props = {}
    totalNum = 0
    for key in schema['properties']:
        num, v = chooser._number_of_samples(schema['properties'][key])
        totalNum += num
        props[key] = v
    return (totalNum, props)


def num_samples_array(chooser, schema):
    num, v = chooser._number_of_samples(schema['items'])
    return (num * schema.get('minItems', 0), [v])


def num_samples_ref(chooser, schema):
    return chooser._number_of_samples(chooser.resolver.resolve(schema['$ref'])[1])


def num_samples_allOf(chooser, schema):
    props = {}
    num = 0
    for s in schema['allOf']:
        n, v = chooser._number_of_samples(s, value)
        props.update(v)
        num += n

    return num, props


def choose_object(chooser, schema, value, idx):
    ordered = sorted(schema['properties'].keys())

    props = {}
    for key in ordered:
        props[key], idx = chooser._choose(schema['properties'][key], value, idx)

    return props, idx


def choose_array(chooser, schema, value, idx):
    arr = []
    for i in xrange(schema.get('minItems', 0)):
        v, idx = chooser._choose(schema['items'], value, idx)
        arr.append(v)
    return arr, idx


def choose_enum(chooser, schema, value, idx):
    return schema['enum'][int(value * len(schema))], idx + 1


def choose_ref(chooser, schema, value, idx):
    return chooser._choose(chooser.resolver.resolve(schema['$ref'])[1], value, idx)


def choose_allOf(chooser, schema, value, idx):
    props = {}
    for s in schema['allOf']:
        ret, idx = chooser._choose(s, value, idx)
        props.update(ret)
    return props, idx


def choose_number(chooser, schema, value, idx):
    x = value[idx]
    xmin = schema.get('minimum')
    xmax = schema.get('maximum')
    if xmin is not None and xmax is not None:
        return x * (xmax - xmin) + xmin, idx + 1
    elif xmin is not None:
        # exponential tail: [0, 1) -> [min, +inf)
        return -100 * math.log(1 - x) + xmin, idx + 1
    elif xmax is not None:  # exponential tail towards +inf
        # exponential tail: [0, 1) -> [max, -inf)
        return 100 * math.log(1 - x) + xmax, idx + 1
    elif x == 0.0:
        return float('-inf'), idx + 1
    else:
        # (0, 0.5, 1) -> (-inf, 0, inf)
        xcenter = x - 0.5
        return (
            100 * math.copysign(math.log(1 - 2 * abs(xcenter)), xcenter),
            idx + 1)


def choose_integer(chooser, schema, value, idx):
    return int(chooser.for_type('number')(chooser, schema, value, idx)[0]), idx + 1


def choose_string(chooser, schema, value, idx):
    if isinstance(value[idx], types.StringTypes):
        return value[idx], idx + 1

    length = min(
        schema.get('minLength', 10),
        schema.get('maxLength', float('inf'))
    )

    options = '0123456789abcdef'
    v = long(value[idx] * (math.pow(len(options), length) - 1))
    string = ''
    for i in range(length):
        string = options[v % len(options)] + string
        v /= len(options)
    return string, idx + 1


class Chooser(object):
    _choosers = {
        'properties': {
            'properties': choose_object,
            'items': choose_array,
            'enum': choose_enum,
            '$ref': choose_ref,
            'allOf': choose_allOf,
        },
        'types': {
            'number': choose_number,
            'integer': choose_integer,
            'string': choose_string,
        },
    }
    _num_samples = {
        'properties': num_samples_object,
        'items': num_samples_array,
        '$ref': num_samples_ref,
        'allOf': num_samples_allOf,
    }

    def __init__(self, schema, property_choosers={}, type_choosers={}, num_samples={}):
        self.resolver = jsonschema.RefResolver('', schema)
        self.choosers = {
            'properties': dict(Chooser._choosers['properties']),
            'types': dict(Chooser._choosers['types']),
        }
        self.choosers['properties'].update(property_choosers)
        self.choosers['types'].update(type_choosers)
        self.schema = schema
        self.num_samples = dict(Chooser._num_samples)
        self.num_samples.update(num_samples)

    def _choose(self, schema, value, idx):
        for prop in self.choosers['properties']:
            if prop in schema:
                chooser = self.for_property(prop)
                return chooser(self, schema, value, idx)

        if schema['type'] in self.choosers['types']:
            chooser = self.for_type(schema['type'])
            return chooser(self, schema, value, idx)

        raise ValueError('schema {0} cannot be chosen'.format(schema))

    def choose(self, value):
        return self._choose(self.schema, value, 0)[0]

    def num_parameters(self):
        return self._number_of_samples(self.schema)[0]

    def _number_of_samples(self, schema):
        for prop in self.num_samples:
            if prop in schema:
                return self.num_samples[prop](self, schema)
        else:
            return (1, None)

    def for_type(self, typename):
        return self.choosers['types'][typename]

    def for_property(self, prop):
        return self.choosers['properties'][prop]


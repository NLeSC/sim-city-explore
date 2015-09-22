# SIM-CITY webservice
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

from __future__ import print_function

import simcityexplore
from nose.tools import assert_equals, assert_true, assert_raises


def test_parse_parameters():
    parameters = {
        'a': 'bla',
        'b': 1,
        'c': {
            'x': 0.5,
            'y': 3,
            'name': 'lala'
        },
        'd': 'ja',
        'e': [
            'za',
            'na'
        ],
        'f': [
            {'x': 1, 'y': 2},
            {'x': -1, 'y': 1},
        ]
    }
    parameter_specs = {
        'properties': {
            'a': {'type': 'string'},
            'b': {'type': 'number'},
            'c': {
                'allOf': [
                   {'$ref': 'https://simcity.amsterdam-complexity.nl/schema/point2d'},
                   { 'properties': { 'name': {'type': 'string'} } }
                ]
            },
            'd': {'enum': ['ja', 'da']},
            'e': {'items': {'type': 'string'},
                'minItems': 1,  'maxItems': 2},
            'f': {'items': {'$ref': 'https://simcity.amsterdam-complexity.nl/schema/point2d'}},
        }
    }
    simcityexplore.parse_parameters(parameters, parameter_specs)
    assert_equals(1, parameters['b'])
    assert_equals(0.5, parameters['c']['x'])


def test_missing_parameter():
    parameters = {}
    parameter_specs = {'properties': {'a': {'type': 'string'}}, 'required': ['a']}
    assert_raises(ValueError, simcityexplore.parse_parameters, parameters,
                  parameter_specs)


def test_wrongtype_parameter():
    parameters = {'a': 'bla'}
    parameter_specs = {'properties': {'a': {'type': 'number'}}}
    assert_raises(ValueError, simcityexplore.parse_parameters, parameters,
                  parameter_specs)


def test_wrong_maxlen():
    parameters = {
        'a': 'bla'
    }
    parameter_specs = {'properties': {
        'a': {'type': 'string', 'maxLength': 2}
    }}
    assert_raises(ValueError, simcityexplore.parse_parameters, parameters,
                  parameter_specs)


def test_wrong_minlen():
    parameters = {
        'a': 'bla'
    }
    parameter_specs = {'properties': {
        'a': {'type': 'string', 'minLength': 4}
    }}
    assert_raises(ValueError, simcityexplore.parse_parameters, parameters,
                  parameter_specs)


def test_simple_point():
    parameters = {'a': {'x': 1, 'y': 2}}
    parameter_specs = {'properties': {
        'a': {'$ref': 'https://simcity.amsterdam-complexity.nl/schema/point2d'}
    }}
    simcityexplore.parse_parameters(parameters, parameter_specs)


def test_extended_point():
    parameters = {'a': {
        'x': 1,
        'y': 2,
        'name': 'mine',
        'id': 'la',
    }}
    parameter_specs = {'properties': {
        'a': {
            'allOf': [
                {'properties': {'name': {'type': 'string'}}},
                {'$ref': 'https://simcity.amsterdam-complexity.nl/schema/point2d'}
            ]
        }
    }}
    simcityexplore.parse_parameters(parameters, parameter_specs)

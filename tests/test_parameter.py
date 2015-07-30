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
        'b': '1',
        'c': {
            'x': '0.5',
            'y': '3',
            'properties': {
                'name': 'lala'
            }
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
    parameter_specs = [
        {'name': 'a', 'type': 'str'},
        {'name': 'b', 'type': 'interval'},
        {'name': 'c', 'type': 'point2d', 'properties': [
            {'name': 'name', 'type': 'string'},
        ]},
        {'name': 'd', 'type': 'choice', 'choices': ['ja', 'da']},
        {'name': 'e', 'type': 'list', 'contents': {'type': 'str'},
            'max_length': 2,  'max_length': 2},
        {'name': 'f', 'type': 'list', 'contents': {'type': 'point2d'}},
    ]
    params = simcityexplore.parse_parameters(parameters, parameter_specs)
    assert_equals(1, params['b'])
    assert_equals(0.5, params['c']['x'])


def test_missing_parameter():
    parameters = {}
    parameter_specs = [
        {'name': 'a', 'type': 'str'}
    ]
    assert_raises(ValueError, simcityexplore.parse_parameters, parameters,
                  parameter_specs)


def test_wrongtype_parameter():
    parameters = {'a': 'bla'}
    parameter_specs = [
        {'name': 'a', 'type': 'number'}
    ]
    assert_raises(ValueError, simcityexplore.parse_parameters, parameters,
                  parameter_specs)


def test_wrong_maxlen():
    parameters = {
        'a': 'bla'
    }
    parameter_specs = [
        {'name': 'a', 'type': 'str', 'max_length': 2},
    ]
    assert_raises(ValueError, simcityexplore.parse_parameters, parameters,
                  parameter_specs)


def test_wrong_minlen():
    parameters = {
        'a': 'bla'
    }
    parameter_specs = [
        {'name': 'a', 'type': 'str', 'min_length': 4},
    ]
    assert_raises(ValueError, simcityexplore.parse_parameters, parameters,
                  parameter_specs)


def test_wellformed_str():
    parameter_spec = {
        'name': 'a',
        'type': 'str',
        'min_length': 2,
        'max_length': 4,
    }
    spec = simcityexplore.parse_parameter_spec(parameter_spec)
    assert_equals(simcityexplore.StringSpec, type(spec))
    assert_equals(2, spec.min_len)
    assert_equals(4, spec.max_len)
    assert_equals(str, spec.dtype.dtype)


def test_malformed_str():
    parameter_spec = {
        'name': 'a',
        'type': 'str',
        'min_length': 5,
        'max_length': 4,
    }
    assert_raises(ValueError, simcityexplore.parse_parameter_spec,
                  parameter_spec)
    parameter_spec['min_length'] = -1
    assert_raises(ValueError, simcityexplore.parse_parameter_spec,
                  parameter_spec)


def test_wellformed_interval():
    parameter_spec = {'name': 'a', 'type': 'interval', 'min': 0, 'max': 4}
    spec = simcityexplore.parse_parameter_spec(parameter_spec)
    assert_equals(2, spec.default)


def test_halfformed_interval():
    parameter_spec = {'name': 'a', 'type': 'interval', 'max': 4}
    spec = simcityexplore.parse_parameter_spec(parameter_spec)
    assert_equals(4, spec.default)


def test_malformed_interval():
    assert_raises(ValueError, simcityexplore.parse_parameter_spec,
                  {'name': 'a', 'type': 'interval', 'min': 5, 'max': 4})


def test_unformed_interval():
    parameter_spec = {'name': 'a', 'type': 'interval'}
    spec = simcityexplore.parse_parameter_spec(parameter_spec)
    assert_equals(float('-inf'), spec.min)
    assert_equals(float('+inf'), spec.max)


def test_unformed_str():
    parameter_spec = {'name': 'a', 'type': 'str'}
    spec = simcityexplore.parse_parameter_spec(parameter_spec)
    assert_equals(0, spec.min_len)
    assert_true(spec.max_len > 10000000)


def test_simple_point():
    parameters = {'a': {'x': 1, 'y': 2}}
    parameter_specs = [{'name': 'a', 'type': 'point2d'}]
    simcityexplore.parse_parameters(parameters, parameter_specs)


def test_unknown_param_type():
    assert_raises(ValueError, simcityexplore.parse_parameter_spec,
                  {'name': 'a', 'type': 'not known'})


def test_unknown_param_dtype():
    assert_raises(ValueError, simcityexplore.parse_parameter_spec,
                  {'name': 'a', 'type': 'number', 'dtype': 'not known'})


def test_malformed_choice():
    assert_raises(ValueError, simcityexplore.parse_parameter_spec,
                  {'name': 'a', 'type': 'choice', 'choices': 'not a list'})
    assert_raises(ValueError, simcityexplore.parse_parameter_spec,
                  {'name': 'a', 'type': 'choice', 'choices': []})


def test_malformed_list():
    assert_raises(KeyError, simcityexplore.parse_parameter_spec,
                  {'name': 'a', 'type': 'list', 'contents': {}})
    assert_raises(ValueError, simcityexplore.parse_parameter_spec,
                  {'name': 'a', 'type': 'list', 'contents': {'type': 'str'},
                   'min_length': -1})
    assert_raises(ValueError, simcityexplore.parse_parameter_spec,
                  {'name': 'a', 'type': 'list', 'contents': {'type': 'str'},
                   'min_length': 5, 'max_length': '4'})

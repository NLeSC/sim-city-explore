#!/usr/bin/env python

from abc import ABCMeta, abstractmethod
import json
from __future__ import print_function

""" Parameter ranges are given as 'parameter.name: [list]' or 'parameter.name: interval'"""

class Point2D(object):
	def __init__(self, x, y):
		self._x = x
		self._y = y
	@property
	def x(self):
		return self._x
	@property
	def y(self):
		return self._y

class Interval(object):
	def __init__(self, min, max):
		if min > max:
			raise ValueError("Minimum to an interval must be smaller than maximum")
		self._min = min
		self._max = max
	@property
	def max(self):
		return self._max
	@property
	def min(self):
		return self._min

class AbstractSimpareAlgorithm(object):
	__metaclass__ = ABCMeta
	
	@abstractmethod
	def run(self):
		pass
	
	@property
	def parameters(self, params):
		self._parameters = params


class Parameters(object):
	def __getitem__(self, key):
		return self._params[key]
	
class ParameterSet(object):
	pass

class Simpare(object):
	def __init__(self):
		pass
		
	@property
	def set_algorithm(self, algo):
		self._algo = algo
	
	def run_function(self, parameters):
		self._algo.parameters = parameters
	
	def 

def default_class_serialization(obj):
	x = obj.__dict__.copy()
	x['__class__'] = obj.__class__.__name__
	return x

if __name__ == '__main__':
	params = {
		'testpoint': [Point2D(1,2), Point2D(0.5, 0.6)],
		'testinterval': Interval(1,2),
		'testlist': [1, 2, 4, 5],
		'testfixed': 'value'
	}
	
	print("JSON dump: ", json.dumps(params, default=default_class_serialization))

#!/usr/bin/env python

from __future__ import print_function
import json
import importlib
import os
import requests

modelSpec = None
exploreModule = None
preprocessModule = None

def run_osmium(parameters):
	url = "http://localhost:9998/job"

	if preprocessModule not is None:
		args = preprocessModule.preprocess(parameters)	
	
	if args is not None:
		modelSpec['simulation']['arguments'] = args

	data = json.dumps(modelSpec['simulation'])
	
	r = requests.put(url, data, header={'content-type': 'application/json'})
	jobId = r.headers['location']
	return jobId

def module_from_spec(moduleType, modelSpec):
	if moduleType not in modelSpec or 'name' not in modelSpec[moduleType]:
		return None
	
	moduleName = '{0}.{1}'.format(moduleType, modelSpec[moduleType]['name'])
	return importlib.import_module(moduleName)

if __name__ == '__main__':
	fname = 'input.json'
	
	with open(fname, 'r') as f:
		modelSpec = json.load(f)
	
	print(modelSpec)
	exploreModule = module_from_spec('parameter_exploration', modelSpec)
	preprocessModule = module_from_spec('preprocess', modelSpec)
	
	exploreModule.explore(modelSpec['parameters'], run_local)
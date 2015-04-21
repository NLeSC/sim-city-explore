#!/usr/bin/env python

import pypet
import subprocess

env = pypet.Environment(
	trajectory='SimTest',filename='./HDF/example01.hdf5',
	file_title='Example_01',log_folder='./logs/',comment='firstsim',
	multiproc=True,ncores=4,
	continuable=True)

def algo(traj):
	z = traj.x * traj.y
	traj.f_add_result('z', z, comment='product')

def algo_subprocess(traj):
	fname = 'out/traj.{0}.{1}.dat'.format(traj.x, traj.y)
 	retcode = subprocess.call(['./multiply.py', fname, str(traj.x), str(traj.y)])
	
	for key, val in traj._parameters.iteritems():
		if val is None or isinstance(val, int) or isinstance(val, str) or isinstance(val, dict) or isinstance(val, list) or isinstance(val, float):
			print("{0}: {1}".format(key, val))
		else:
			print("{0}: <{1}> {2}".format(key, type(val), val.__dict__))
	
	if retcode != 0:
		raise EnvironmentError("Subprocess failed")
	
	with open(fname, 'r') as f:
		z = float(f.read())
	
	traj.f_add_result('z', z, comment='product')

traj = env.v_trajectory

traj.f_add_parameter('x', 1.0, comment='first dimension')
traj.f_add_parameter('y', 1.0, comment='second dimension')

traj.f_explore(pypet.cartesian_product({'x': [1.0, 2.0, 3.0, 4.0], 'y': [6.0, 7.0, 8.0, 9.0]}))

res = env.f_run(algo_subprocess)
print(res)

if not traj.f_is_completed():
	env.f_continue(trajectory_name =traj._trajectory_name)
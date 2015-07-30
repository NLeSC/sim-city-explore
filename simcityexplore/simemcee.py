#!/usr/bin/env python
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

from __future__ import print_function
import numpy as np
import emcee
import simcity
import math
import matplotlib.pyplot as pl
from simulator import Simulator

ensemble = "myfirstbaselineensemble"
host = "lisa"
command = "~/baseline-model/optimallocations.py"
version = "0.1"

# Use a uniform random sample in [0, 1]^2


def flat_prior(x):
    if x[0] >= 0 and x[0] <= 1 and x[1] >= 0 and x[1] <= 1:
        return 0.0
    else:
        return float('-inf')

# def scoring(task):
#     geojson_str = task.get_attachment('GeoFirePaths.json',
#        retrieve_from_database=simcity.get_task_database())['data']
#     geojson = json.loads(geojson_str)
#
#     response_times = [feature['properties']['responsetime']
#                           for f in geojson['features']]
#
#     return math.log(response_times)


def scoring(task):
    response_time = task.get_attachment(
        'response_time.csv',
        retrieve_from_database=simcity.get_task_database()
    )['data']

    return math.log(float(response_time))


simulator = Simulator(ensemble, version, command, scoring, host, max_jobs=1,
                      argnames=['x', 'y'], argprecisions=[0.01, 0.01],
                      polling_time=3)
#
# ndim = 1
# means = np.random.rand(ndim)
#
# print("constructing covariance matrix")
# cov = 0.5 - np.random.rand(ndim ** 2).reshape((ndim, ndim))
# cov = np.triu(cov)
# cov += cov.T - np.diag(cov.diagonal())
# cov = np.dot(cov, cov)
#
# icov = np.linalg.inv(cov)

ntemps = 10
nwalkers = 4
ndim = 2
p0 = np.random.rand(ntemps, nwalkers, ndim)

# sampler
print("constructing walkers")
# nwalkers = 250
# p0 = np.random.rand(ndim * nwalkers).reshape((nwalkers, ndim))

# sampler = emcee.EnsembleSampler(
#     nwalkers, ndim, run_task, args=[means, icov], threads=15)

sampler = emcee.PTSampler(ntemps, nwalkers, ndim, simulator, flat_prior,
                          threads=8)

print("burning in mcmc")
for p, lnprob, lnlike in sampler.sample(p0, iterations=10):
    pass
sampler.reset()

print("running mcmc")
for p, lnprob, lnlike in sampler.sample(p, lnprob0=lnprob,
                                        lnlike0=lnlike,
                                        iterations=100, thin=10):
    pass

print(sampler.flatchain)

for walker in sampler.flatchain:
    for i in range(ndim):
        pl.figure()
        pl.hist(walker[:, i], 100, color="k", histtype="step")
        pl.title("Dimension {0:d}".format(i))

pl.show()

print("Mean acceptance fraction: {0:.3f}"
      .format(np.mean(sampler.acceptance_fraction)))

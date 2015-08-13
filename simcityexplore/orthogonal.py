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
import pyDOE
from simulator import Simulator
from parameter import IntervalSpec
import traceback
import simcity
import math
import numpy as np


def sample(parameter_specs, samples, seed=None):
    '''
    Sample from the parameter space using latin hypercube sampling.

    Does not ensure unique parameter settings.

    Returns:
        an enumerator with `samples` parameter settings, as a list of parameter
        values
    '''
    if seed is not None:
        np.random.seed(seed)

    lhd = pyDOE.lhs(len(parameter_specs), samples=samples)

    return (
        [
            spec.choose(sample[i])
            for i, spec in enumerate(parameter_specs)
        ] for sample in lhd)


if __name__ == '__main__':
    ensemble = "myfirstorthogonalbaselineensemble"
    host = "lisa"
    command = "~/baseline-model/optimallocations.py"
    version = "0.1"

    def scoring(task):
        response_time = task.get_attachment(
            'response_time.csv',
            retrieve_from_database=simcity.get_task_database()
        )['data']

        return math.log(float(response_time))

    simulator = Simulator(ensemble, version, command, scoring, host,
                          max_jobs=2, argnames=['x', 'y'],
                          argprecisions=[0.01, 0.01], polling_time=3)

    specs = [IntervalSpec('x', float, 0, 1), IntervalSpec('y', float, 0, 1)]
    samples = list(sample(specs, 10))
    results = {}
    print("Adding simulations", end="")
    for p in samples:
        simulator.start(p)
        print(".", end="")

    print("")

    while simulator.is_running():
        print("Waiting for process...", end="")
        i, value = simulator.join()
        print(" got result for process {}".format(i))
        if isinstance(value, Exception):
            traceback.print_exception(type(value), value, None)
        results[str(samples[i - 1])] = value

    print(results)

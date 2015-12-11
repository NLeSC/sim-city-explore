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
from .simulator import Simulator
from .parameter import Chooser
from .util import ProgressBar
import traceback
import simcity
import math
import numpy as np


def sample(parameter_specs, samples, seed=None):
    '''
    Sample from the parameter space using latin hypercube sampling.

    Does not ensure unique parameter settings.

    Parameters
    ----------
    parameter_specs: dict
        a JSON-Schema dict with the parameter specifications
    samples: int
        number of samples to take within the specification

    Returns: iterator
        an iterator with parameter values
    '''
    if seed is not None:
        np.random.seed(seed)

    chooser = Chooser(parameter_specs)
    sample_dimensions = chooser.num_parameters()

    lhd = pyDOE.lhs(sample_dimensions, samples=samples)

    return (chooser.choose(sample) for sample in lhd)


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

    unit = {'type': 'number', 'minimum': 0, 'maximum': 1}
    specs = {'properties':  {'x': unit, 'y': unit}}
    samples = list(sample(specs, 10))
    results = {}

    print("Adding simulations")
    for p in ProgressBar.iterate(samples):
        simulator.start(p)

    print("Waiting for processes")
    bar = ProgressBar(len(samples))
    bar.start()
    while simulator.is_running():
        i, value = simulator.join()
        if isinstance(value, Exception):
            traceback.print_exception(type(value), value, None)
        results[str(samples[i - 1])] = value
        bar.increment()
    bar.finish()

    print(results)

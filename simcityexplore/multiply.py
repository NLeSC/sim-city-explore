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
import sys
import time
import random

assert(len(sys.argv) == 4)

with open(sys.argv[1], 'w') as f:
    print(float(sys.argv[2]) * float(sys.argv[3]), file=f)

time.sleep(random.randint(0, 5))

if random.random() < 0.2:
    print("failed")
    sys.exit(1)

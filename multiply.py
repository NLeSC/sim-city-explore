#!/usr/bin/env python

from __future__ import print_function
import sys
import time
import random

assert(len(sys.argv) == 4)

with open(sys.argv[1], 'w') as f:
	print(float(sys.argv[2])*float(sys.argv[3]), file=f)

time.sleep(random.randint(0, 5))

if random.random() < 0.2:
	print("failed")
	sys.exit(1)
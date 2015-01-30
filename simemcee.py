#!/usr/bin/env python

from __future__ import print_function
import numpy as np
import emcee
import matplotlib.pyplot as pl

def lnprob(x, mu, icov):
    diff = x-mu
    return -np.dot(diff,np.dot(icov,diff))/2.0
	
ndim = 50

means = np.random.rand(ndim)

print("constructing covariance matrix")
cov = 0.5 - np.random.rand(ndim ** 2).reshape((ndim, ndim))
cov = np.triu(cov)
cov += cov.T - np.diag(cov.diagonal())
cov = np.dot(cov,cov)

icov = np.linalg.inv(cov)

print("constructing walkers")
nwalkers = 250
p0 = np.random.rand(ndim * nwalkers).reshape((nwalkers, ndim))

sampler = emcee.EnsembleSampler(nwalkers, ndim, lnprob, args=[means, icov], threads=15)

print("burning in mcmc")
pos, prob, state = sampler.run_mcmc(p0, 100)
sampler.reset()

print("running mcmc")
sampler.run_mcmc(pos, 1000)

for i in range(ndim):
    pl.figure()
    pl.hist(sampler.flatchain[:,i], 100, color="k", histtype="step")
    pl.title("Dimension {0:d}".format(i))

pl.show()

print("Mean acceptance fraction: {0:.3f}"
                .format(np.mean(sampler.acceptance_fraction)))
				
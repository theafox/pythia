# Translated code start.
import pyro
import pyro.distributions as dist
import torch
def autoregressive_moving_average_model(y):
    nu = torch.full((len(y),), 0, dtype=float)
    err = torch.full((len(y),), 0, dtype=float)
    mu = pyro.sample('mu', dist.Normal(0, 10))
    phi = pyro.sample('phi', dist.Normal(0, 10))
    theta = pyro.sample('theta', dist.Normal(0, 10))
    sigma = pyro.sample('sigma', dist.HalfCauchy(2.5))
    nu[0] = (mu) + ((phi) * (mu))
    err[0] = (y[0]) - (nu[0])
    for t in range(1, len(y), 1):
        nu[t] = ((mu) + ((phi) * (y[(t) - (1)]))) + ((theta) * (err[(t) - (1)]))
        err[t] = (y[t]) - (nu[t])
    pyro.sample('err', dist.Normal(0, sigma).expand((len(y),)), obs=err)
# Translated code end.
# Test data.
y = [ 1.1882e+02, 4.2169e+02, 1.3230e+03, 4.0375e+03, 1.2189e+04, 3.6625e+04,
      1.0992e+05, 3.2982e+05, 9.8951e+05, 2.9686e+06, 8.9058e+06, 2.6717e+07,
      8.0152e+07, 2.4046e+08, 7.2137e+08, 2.1641e+09, 6.4924e+09, 1.9477e+10,
      5.8431e+10, 1.7529e+11 ]
model = autoregressive_moving_average_model
arguments = (y,)
addresses = ["mu", "phi", "theta", "sigma"]
# Inference.
pyro.set_rng_seed(0)
importance = pyro.infer.Importance(model, num_samples=10_000)
posterior = importance.run(*arguments)
inferred = pyro.infer.EmpiricalMarginal(posterior, sites=addresses)
print("Inferred:")
for i, address in enumerate(addresses):
    print(f" - {address}={inferred.mean[i]}")

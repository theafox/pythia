# Translated code start.
import pyro
import pyro.distributions as dist
def rate_5_model(n1, n2, k1, k2):
    theta = pyro.sample('theta', dist.Beta(1, 1))
    pyro.sample('obs1', dist.Binomial(n1, theta), obs=k1)
    pyro.sample('obs2', dist.Binomial(n2, theta), obs=k2)
    postpredk1 = pyro.sample('postpredk1', dist.Binomial(n1, theta))
    postpredk2 = pyro.sample('postpredk2', dist.Binomial(n2, theta))
    return (postpredk1, postpredk2)
# Translated code end.
import torch
# Test data.
n1 = torch.tensor(10)
n2 = torch.tensor(15)
k1 = torch.tensor(7)
k2 = torch.tensor(8)
model = rate_5_model
arguments = (n1, n2, k1, k2)
addresses = ["theta"]
# Inference.
pyro.set_rng_seed(0)
importance = pyro.infer.Importance(model, num_samples=10_000)
posterior = importance.run(*arguments)
inferred = pyro.infer.EmpiricalMarginal(posterior, sites=addresses)
print("Inferred:")
for i, address in enumerate(addresses):
    print(f" - {address}={inferred.mean[i]}")

from math import log
# Translated code start.
import pyro
import pyro.distributions as dist
def cointoss_with_factor_model(data):
    p = pyro.sample('p', dist.Uniform(0, 1))
    for i in range(0, len(data), 1):
        new = p
        if (data[i]) != (1):
            new = (1) - (p)
        pyro.factor(f"{'data'}[{i}]", log(new))
    return p
# Translated code end.
import torch
# Test data.
data = torch.tensor([ 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0,
                      0 ], dtype=float)
model = cointoss_with_factor_model
arguments = (data,)
addresses = ["p"]
# Inference.
pyro.set_rng_seed(0)
importance = pyro.infer.Importance(model, num_samples=5_000)
posterior = importance.run(*arguments)
inferred = pyro.infer.EmpiricalMarginal(posterior, sites=addresses)
print("Inferred:")
for i, address in enumerate(addresses):
    print(f" - {address}={inferred.mean[i]}")

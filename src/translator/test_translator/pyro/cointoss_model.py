# Translated code start.
import pyro
import pyro.distributions as dist
def cointoss_model(data):
    probability = pyro.sample('probability', dist.Uniform(0, 1))
    for i in range(0, len(data), 1):
        if ((data[i]) != (0)) and ((data[i]) != (1)):
            continue
        pyro.sample(f"{'data'}[{i}]", dist.Bernoulli(probability), obs=data[i])
# Translated code end.
import torch
# Test data.
data = torch.tensor([ 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0,
                      0 ], dtype=float)
model = cointoss_model
arguments = (data,)
addresses = ["probability"]
# Inference.
pyro.set_rng_seed(0)
importance = pyro.infer.Importance(model, num_samples=10_000)
posterior = importance.run(*arguments)
inferred = pyro.infer.EmpiricalMarginal(posterior, sites=addresses)
print("Inferred:")
for i, address in enumerate(addresses):
    print(f" - {address}={inferred.mean[i]}")

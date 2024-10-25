# Translated code start.
import pyro
import pyro.distributions as dist
import torch
def number_of_heads_model(data):
    p = pyro.sample('p', dist.Uniform(0, 1))
    count = 0
    while True:
        cointoss = pyro.sample(f"{'cointoss'}[{count}]", dist.Bernoulli(p))
        if (cointoss) == (1):
            break
        count = (count) + (1)
    pyro.sample('count', dist.Delta(torch.tensor(count)), obs=data)
# Translated code end.
# Test data.
data = torch.tensor(149)
model = number_of_heads_model
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

# Translated code start.
import pyro
import pyro.distributions as dist
import torch
def number_of_heads_model(data):
    probability = pyro.sample('probability', dist.Uniform(0, 1))
    count = 0
    while True:
        cointoss = pyro.sample(f"{'cointoss'}[{count}]", dist.Bernoulli(probability))
        if (cointoss) == (1):
            break
        count = (count) + (1)
    # pyro.sample('count', dist.Delta(torch.tensor(data)), obs=count)
    pyro.sample('count', dist.Delta(torch.tensor(data)), obs=torch.tensor(count))
# Translated code end.
# Test data.
data = 149
model = number_of_heads_model
arguments = (data,)
addresses = ["probability"]
# Inference.
pyro.set_rng_seed(0)
importance = pyro.infer.Importance(model, num_samples=1_000)
posterior = importance.run(*arguments)
inferred = pyro.infer.EmpiricalMarginal(posterior, sites=addresses)
print("Inferred:")
for i, address in enumerate(addresses):
    print(f" - {address}={inferred.mean[i]}")

# Translated code start.
import pyro
import pyro.distributions as dist
import torch
def burglary_model(data):
    earthquake = pyro.sample('earthquake', dist.Bernoulli(0.02))
    burglary = pyro.sample('burglary', dist.Bernoulli(0.01))
    if (earthquake) == (1):
        phone_working = pyro.sample('phone_working', dist.Bernoulli(0.8))
    else:
        phone_working = pyro.sample('phone_working', dist.Bernoulli(0.9))
    if (earthquake) == (1):
        mary_wakes = pyro.sample('mary_wakes', dist.Bernoulli(0.8))
    else:
        if (burglary) == (1):
            mary_wakes = pyro.sample('mary_wakes', dist.Bernoulli(0.7))
        else:
            mary_wakes = pyro.sample('mary_wakes', dist.Bernoulli(0.1))
    called = ((mary_wakes) == (1)) and ((phone_working) == (1))
    pyro.sample('observed', dist.Delta(torch.tensor(called)), obs=data)
# Translated code end.
# Test data.
data = torch.tensor(False)
model = burglary_model
arguments = (data,)
addresses = ["earthquake", "burglary", "phone_working", "mary_wakes"]
# Inference.
pyro.set_rng_seed(0)
importance = pyro.infer.Importance(model, num_samples=10_000)
posterior = importance.run(*arguments)
inferred = pyro.infer.EmpiricalMarginal(posterior, sites=addresses)
print("Inferred:")
for i, address in enumerate(addresses):
    print(f" - {address}={inferred.mean[i]}")

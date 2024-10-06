from math import log
# Translated code start.
import pyro
import pyro.distributions as dist
def cointoss_with_factor_model(data):
    probability = pyro.sample('probability', dist.Uniform(0, 1))
    for i in range(0, len(data), 1):
        new = probability
        if (data[i]) != (1):
            new = (1) - (probability)
        pyro.factor(f"{'data'}[{i}]", log(new))
    return probability
# Translated code end.
# Test data generated with:
#   p~0.7
import torch
data = torch.tensor([1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1], dtype=float)
kernel = pyro.infer.NUTS(cointoss_with_factor_model)
mcmc = pyro.infer.MCMC(kernel, num_samples=100, warmup_steps=10)
mcmc.run(data)
print("Inferred:")
print(f"\tprobability={mcmc.get_samples()["probability"].mean(0)}")

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
# Test data generated with:
#   p~0.7
import torch
data = torch.tensor([1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1], dtype=float)
kernel = pyro.infer.NUTS(cointoss_model)
mcmc = pyro.infer.MCMC(kernel, num_samples=1000, warmup_steps=100)
mcmc.run(data)
print("Inferred:")
print(f"\tprobability={mcmc.get_samples()["probability"].mean(0)}")

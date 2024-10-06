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
    pyro.sample('count', dist.Delta(torch.tensor(count)), obs=data)
# Translated code end.
# Test data generated with:
#   probability~0.01
data = 100
kernel = pyro.infer.NUTS(number_of_heads_model)
mcmc = pyro.infer.MCMC(kernel, num_samples=1000, warmup_steps=100)
mcmc.run(data)
print("Inferred:")
samples = mcmc.get_samples()
print(f"\tprobability={samples["probability"].mean(0)}")

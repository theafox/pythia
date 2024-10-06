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
# Test data generated with:
#   theta~0.6
import torch
n1 = torch.tensor(10)
n2 = torch.tensor(15)
k1 = torch.tensor(7)
k2 = torch.tensor(8)
kernel = pyro.infer.NUTS(rate_5_model)
mcmc = pyro.infer.MCMC(kernel, num_samples=1000, warmup_steps=100)
mcmc.run(n1, n2, k1, k2)
print("Inferred:")
print(f"\ttheta={mcmc.get_samples()["theta"].mean(0)}")

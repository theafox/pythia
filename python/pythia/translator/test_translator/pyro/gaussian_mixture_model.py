# Translated code start.
import pyro
import pyro.distributions as dist
import torch
def gaussian_mixture_model(data):
    number_of_clusters = 2
    probability = pyro.sample('probability', dist.Uniform(0, 1))
    mu = torch.full((number_of_clusters,), 0, dtype=float)
    for i in range(0, number_of_clusters, 1):
        mu[i] = pyro.sample(f"{'mu'}[{i}]", dist.Normal(0, 1))
    z = torch.full((len(data),), 0, dtype=float)
    for i in range(0, len(data), 1):
        z[i] = pyro.sample(f"{'z'}[{i}]", dist.Bernoulli(probability))
        # pyro.sample(f"{'data'}[{i}]", dist.Normal(mu[z[i]], 1), obs=data[i])  # indexing with a tensor is not allowed.
        pyro.sample(f"{'data'}[{i}]", dist.Normal(mu[int(z[i])], 1), obs=data[i])
# Translated code end.
# Test data generated with:
#   probability~0.6
#   mu~[-2.4,1.2]
#   z~[0,1,0,1,1,1,0,0,1,1,0,0,1,1,1,1,1,1,0,0]
data = torch.tensor([
    -1.64, 1.01, 0.01, 2.26, 0.40, -0.54, -2.15, -2.08, 1.31, 0.64,
    -3.30, -2.19, 2.90, 0.36, 1.16, 1.28, 1.67, 0.18, -2.25, -2.36
])
kernel = pyro.infer.NUTS(gaussian_mixture_model)
mcmc = pyro.infer.MCMC(kernel, num_samples=50, warmup_steps=5)
mcmc.run(data)
print("Inferred:")
samples = mcmc.get_samples()
print(f"\tprobability={samples["probability"].mean(0)}")
print(f"\tmu={samples["mu"].mean(0)}")
print(f"\tz={samples["z"].mean(0)}")

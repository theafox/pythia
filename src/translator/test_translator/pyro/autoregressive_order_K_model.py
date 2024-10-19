# Translated code start.
import pyro
import pyro.distributions as dist
def autoregressive_order_K_model(y, K):
    alpha = pyro.sample('alpha', dist.Normal(0, 10))
    beta = pyro.sample('beta', dist.Normal(0, 10).expand((K,)))
    sigma = pyro.sample('sigma', dist.HalfCauchy(2.5))
    for t in range(K, len(y), 1):
        mu = alpha
        for k in range(0, K, 1):
            mu = (mu) + ((beta[k]) * (y[(t) - (k)]))
        pyro.sample(f"{'y'}[{t}]", dist.Normal(mu, sigma), obs=y[t])
# Translated code end.
import torch
# Test data.
y = torch.tensor([            0.00,             0.00,            0.00,
                              0.00,             0.00,           14.88,
                            117.33,           790.70,         5174.00,
                          33858.00,        221680.00,      1451600.00,
                        9505500.00,      62245000.00,    407600000.00,
                     2669100000.00,   17478000000.00, 114450000000.00,
                   749440000000.00, 4907600000000.00 ])
K = 5
model = autoregressive_order_K_model
arguments = (y, K)
addresses = ["alpha", "sigma"]
# Inference.
pyro.set_rng_seed(0)
importance = pyro.infer.Importance(model, num_samples=10_000)
posterior = importance.run(*arguments)
inferred = pyro.infer.EmpiricalMarginal(posterior, sites=addresses)
print("Inferred:")
for i, address in enumerate(addresses):
    print(f" - {address}={inferred.mean[i]}")

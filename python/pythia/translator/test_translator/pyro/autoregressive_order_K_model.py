# Translated code start.
import pyro
import pyro.distributions as dist
def autoregressive_order_K_model(y, K):
    alpha = pyro.sample('alpha', dist.Normal(0, 10))
    beta = pyro.sample('beta', dist.Normal(0, 10).expand((K,)))
    sigma = pyro.sample('sigma', dist.Cauchy(0, 2.5))
    for t in range(K, len(y), 1):
        mu = alpha
        for k in range(0, K, 1):
            mu = (mu) + ((beta[k]) * (y[(t) - (k)]))
        pyro.sample(f"{'y'}[{t}]", dist.Normal(mu, sigma), obs=y[t])
# Translated code end.
# Test data generated with:
#   alpha~14
#   sigma~0.5
#   beta~[-6.45,6.93,-2.48,-1.99,12.19]
import torch
y = torch.tensor([0, 0, 0, 0, 0, 14.33, 113.59, 765.56, 5009.41, 32779.81, 214616.96, 1405379.32, 9202875.14, 60263095.70, 394619612.99, 2584079307.87, 16921272464.00, 110805215612.65, 725583483758.52, 4751323202301.19])
K = 5
kernel = pyro.infer.NUTS(autoregressive_order_K_model)
mcmc = pyro.infer.MCMC(kernel, num_samples=1000, warmup_steps=100)
mcmc.run(y, K)
print("Inferred:")
samples = mcmc.get_samples()
print(f"\talpha={samples["alpha"].mean(0)}")
print(f"\tsigma={samples["sigma"].mean(0)}")
print(f"\tbeta={samples["beta"].mean(0)}")

# Translated code start.
import pyro
import pyro.distributions as dist
def linear_regression_model(xs, ys):
    gradient = pyro.sample('gradient', dist.Normal(0, 10))
    intercept = pyro.sample('intercept', dist.Normal(0, 10))
    for i in range(0, min(len(xs), len(ys)), 1):
        pyro.sample(f"{'ys'}[{i}]", dist.Normal(((gradient) * (xs[i])) + (intercept), 1), obs=ys[i])
# Translated code end.
# Test data generated with:
#   intercept~1
#   slope~0.5
import torch
xs = torch.tensor([0.93, 1.71, 2.61, 3.62, 4.12])
ys = torch.tensor([1.32, 2.00, 2.55, 2.39, 3.14])
kernel = pyro.infer.NUTS(linear_regression_model)
mcmc = pyro.infer.MCMC(kernel, num_samples=1000, warmup_steps=100)
mcmc.run(xs, ys)
print("Inferred:")
samples = mcmc.get_samples()
print(f"\tgradient={samples["gradient"].mean(0)}")
print(f"\tintercept={samples["intercept"].mean(0)}")

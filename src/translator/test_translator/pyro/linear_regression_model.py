# Translated code start.
import pyro
import pyro.distributions as dist
def linear_regression_model(xs, ys):
    slope = pyro.sample('slope', dist.Normal(0, 10))
    intercept = pyro.sample('intercept', dist.Normal(0, 10))
    for i in range(0, min(len(xs), len(ys)), 1):
        pyro.sample(f"{'ys'}[{i}]", dist.Normal(((slope) * (xs[i])) + (intercept), 1), obs=ys[i])
# Translated code end.
import torch
# Test data.
xs = torch.tensor([ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10 ])
ys = torch.tensor([ 1.8528, 2.0800, 2.6957, 3.4482, 3.8735, 3.8045, 4.6900,
                    4.9697, 5.4794, 6.0821 ])
model = linear_regression_model
arguments = (xs, ys)
addresses = ["slope", "intercept"]
# Inference.
pyro.set_rng_seed(0)
importance = pyro.infer.Importance(model, num_samples=10_000)
posterior = importance.run(*arguments)
inferred = pyro.infer.EmpiricalMarginal(posterior, sites=addresses)
print("Inferred:")
for i, address in enumerate(addresses):
    print(f" - {address}={inferred.mean[i]}")

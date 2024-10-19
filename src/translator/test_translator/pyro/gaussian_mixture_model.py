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
# Test data.
data = torch.tensor([ -0.6359476540323359,  1.6001572083672233,
                      -1.4212620158942606,  3.440893199201458,
                       3.067557990149967,   0.22272212012358894,
                      -1.4499115824744107, -2.5513572082976976,
                       1.096781148206442,   1.6105985019383722,
                      -2.255956428839122,  -0.9457264930370248,
                       1.9610377251469933,  1.3216750164928284,
                       1.6438632327454257,  1.5336743273742668,
                       2.694079073157606,   0.994841736234199,
                      -2.0869322983490983, -3.2540957393017247 ])
model = gaussian_mixture_model
arguments = (data,)
addresses = ["probability", "mu[0]", "mu[1]"]
# Inference.
pyro.set_rng_seed(0)
importance = pyro.infer.Importance(model, num_samples=5_000)
posterior = importance.run(*arguments)
inferred = pyro.infer.EmpiricalMarginal(posterior, sites=addresses)
print("Inferred:")
for i, address in enumerate(addresses):
    print(f" - {address}={inferred.mean[i]}")

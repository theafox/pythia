# Translated code start.
import pyro
import pyro.distributions as dist
import torch
def gaussian_mixture_model(data):
    number_of_clusters = 2
    theta = pyro.sample('theta', dist.Uniform(0, 1))
    mu = torch.full((number_of_clusters,), 0, dtype=float)
    for i in range(0, number_of_clusters, 1):
        mu[i] = pyro.sample(f"{'mu'}[{i}]", dist.Normal(0, 10))
    z = torch.full((len(data),), 0, dtype=int)
    for i in range(0, len(data), 1):
        z[i] = pyro.sample(f"{'z'}[{i}]", dist.Bernoulli(theta))
        pyro.sample(f"{'data'}[{i}]", dist.Normal(mu[z[i]], 1), obs=data[i])
# Translated code end.
# Test data.
data = torch.tensor([ 15.24052345967664,     5.201572083672233,
                       7.387379841057392,   23.60893199201458,
                      19.875579901499673,   -8.57277879876411,
                       7.100884175255894,   -3.913572082976979,
                       0.16781148206442142,  5.305985019383724,
                      -0.9595642883912201,  12.142735069629751,
                       8.810377251469934,    2.416750164928284,
                       5.638632327454257,    4.536743273742668,
                      16.14079073157606,    -0.8515826376580089,
                       0.7306770165090137, -10.940957393017248 ])
model = gaussian_mixture_model
arguments = (data,)
addresses = ["theta", "mu[0]", "mu[1]"]
# Inference.
pyro.set_rng_seed(0)
importance = pyro.infer.Importance(model, num_samples=5_000)
posterior = importance.run(*arguments)
inferred = pyro.infer.EmpiricalMarginal(posterior, sites=addresses)
print("Inferred:")
for i, address in enumerate(addresses):
    print(f" - {address}={inferred.mean[i]}")

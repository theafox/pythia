# See: https://github.com/stan-dev/posteriordb/blob/master/posterior_database/models/stan/normal_mixture.stan
@probabilistic_program
def gaussian_mixture_model(data):
    number_of_clusters = 2
    theta = sample("theta", Uniform(0, 1))
    mu = Vector(number_of_clusters, t=float)
    for i in range(0, number_of_clusters):
        mu[i] = sample(IndexedAddress("mu", i), Normal(0, 10))
    z = Vector(len(data), t=int)
    for i in range(0, len(data)):
        z[i] = sample(IndexedAddress("z", i), Bernoulli(theta))
        observe(data[i], IndexedAddress("data", i), Normal(mu[z[i]], 1))

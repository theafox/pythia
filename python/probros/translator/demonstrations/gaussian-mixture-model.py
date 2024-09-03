@probabilistic_program
def gaussian_mixture_model(numer_of_clusters, data):
    probability = sample("probability", Uniform(0, 1))
    mu = Vector(numer_of_clusters)
    for i in range(0, numer_of_clusters):
        mu[i] = sample(IndexedAddress("mu", i), Normal(0, 1))
    z = Vector(len(data))
    for i in range(0, len(data)):
        z[i] = sample(IndexedAddress("z", i), Bernoulli(probability))
        observe(data[i], IndexedAddress("data", i), Normal(mu[z[i]], 1))

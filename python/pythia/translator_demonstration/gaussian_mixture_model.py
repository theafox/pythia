@probabilistic_program
def gaussian_mixture_model(data):
    number_of_clusters = 2
    probability = sample("probability", Uniform(0, 1))
    mu = Vector(number_of_clusters, t=float)
    for i in range(0, number_of_clusters):
        mu[i] = sample(IndexedAddress("mu", i), Normal(0, 1))
    z = Vector(len(data), t=float)
    for i in range(0, len(data)):
        z[i] = sample(IndexedAddress("z", i), Bernoulli(probability))
        observe(data[i], IndexedAddress("data", i), Normal(mu[z[i]], 1))

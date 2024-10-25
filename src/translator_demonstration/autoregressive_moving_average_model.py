# See: https://github.com/stan-dev/posteriordb/blob/master/posterior_database/models/stan/arma11.stan
@probabilistic_program
def autoregressive_moving_average_model(y):
    nu = Vector(len(y), fill=0, t=float)
    err = Vector(len(y), fill=0, t=float)
    mu = sample("mu", Normal(0, 10))
    phi = sample("phi", Normal(0, 2))
    theta = sample("theta", Normal(0, 2))
    sigma = sample("sigma", HalfCauchy(2.5))
    nu[0] = mu + phi * mu
    err[0] = y[0] - nu[0]
    for t in range(1, len(y)):
        nu[t] = mu + phi * y[t - 1] + theta * err[t - 1]
        err[t] = y[t] - nu[t]
    observe(err, "err", IID(Normal(0, sigma), len(y)))

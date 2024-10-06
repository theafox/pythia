@probabilistic_program
def linear_regression_model(xs, ys):
    gradient = sample("gradient", Normal(0, 10))
    intercept = sample("intercept", Normal(0, 10))
    for i in range(0, min(len(xs), len(ys))):
        observe(
            ys[i],
            IndexedAddress("ys", i),
            Normal(gradient * xs[i] + intercept, 1),
        )

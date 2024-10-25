# Own model.
@probabilistic_program
def linear_regression_model(xs, ys):
    slope = sample("slope", Normal(0, 10))
    intercept = sample("intercept", Normal(0, 10))
    for i in range(0, min(len(xs), len(ys))):
        observe(
            ys[i],
            IndexedAddress("ys", i),
            Normal(slope * xs[i] + intercept, 1),
        )

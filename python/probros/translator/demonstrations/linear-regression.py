@probabilistic_program
def linear_regression(data):
    gradient = sample("gradient", Normal(0, 10))
    intercept = sample("intercept", Normal(0, 10))
    for i in range(0, len(data)):
        observe(
            data[i].y,
            IndexedAddress("data", i),
            Normal(gradient * data[i].x + intercept, 1),
        )

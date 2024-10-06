# Translated code start.
using Turing
@model function linear_regression_model(xs, ys)
    gradient ~ Normal(0, 10)
    intercept ~ Normal(0, 10)
    for i = 0:1:(min(length(xs), length(ys)))-1
        ys[(i) + 1] ~ Normal(((gradient) * (xs[(i) + 1])) + (intercept), 1)
    end
end
# Translated code end.
# Test data generated with:
#   intercept~1
#   slope~0.5
xs = [0.93, 1.71, 2.61, 3.62, 4.12]
ys = [1.32, 2.00, 2.55, 2.39, 3.14]
display(sample(linear_regression_model(xs, ys), NUTS(), 1000))

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
# Test data.
xs = [ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10 ]
ys = [ 1.8528, 2.0800, 2.6957, 3.4482, 3.8735, 3.8045, 4.6900, 4.9697, 5.4794,
       6.0821 ]
model = linear_regression_model
arguments = (xs, ys)
addresses = ("gradient", "intercept")
# Inference.
Turing.Random.seed!(0)
inferred = sample(model(arguments...), IS(), 10_000, progress=false)
println("Inferred:")
weights = exp.(inferred[:lp])
weights = weights / sum(weights)
for address in addresses
    mean = sum(inferred[address] .* weights)
    println(" - $address=$mean")
end

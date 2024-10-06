# Translated code start.
using Turing
@model function autoregressive_moving_average_model(y)
    nu = fill!(Array{Float64}(undef, length(y)), 0)
    err = fill!(Array{Float64}(undef, length(y)), 0)
    mu ~ Normal(0, 10)
    phi ~ Normal(0, 10)
    theta ~ Normal(0, 10)
    sigma ~ Truncated(Cauchy(), 2.5, +Inf)
    nu[(0) + 1] = (mu) + ((phi) * (mu))
    err[(0) + 1] = (y[(0) + 1]) - (nu[(0) + 1])
    for t = 1:1:(length(y))-1
        nu[(t) + 1] = ((mu) + ((phi) * (y[((t) - (1)) + 1]))) + ((theta) * (err[((t) - (1)) + 1]))
        err[(t) + 1] = (y[(t) + 1]) - (nu[(t) + 1])
    end
    err ~ filldist(Normal(0, sigma), length(y))
end
# Translated code end.
# Test data generated with:
#   y was generated with Normal(0, 3)
y = [-1.35, -3.5, -3.84, 0.71, -0.75, -0.12, 0.48, -0.7, 2.62, 6.95]
display(sample(autoregressive_moving_average_model(y), NUTS(), 1000))

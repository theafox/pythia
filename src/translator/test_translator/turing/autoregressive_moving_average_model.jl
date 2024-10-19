# Translated code start.
using Turing
@model function autoregressive_moving_average_model(y)
    nu = fill!(Array{Float64}(undef, length(y)), 0)
    err = fill!(Array{Float64}(undef, length(y)), 0)
    mu ~ Normal(0, 10)
    phi ~ Normal(0, 10)
    theta ~ Normal(0, 10)
    sigma ~ Truncated(Cauchy(2.5), 0, +Inf)
    nu[(0) + 1] = (mu) + ((phi) * (mu))
    err[(0) + 1] = (y[(0) + 1]) - (nu[(0) + 1])
    for t = 1:1:(length(y))-1
        nu[(t) + 1] = ((mu) + ((phi) * (y[((t) - (1)) + 1]))) + ((theta) * (err[((t) - (1)) + 1]))
        err[(t) + 1] = (y[(t) + 1]) - (nu[(t) + 1])
    end
    err ~ filldist(Normal(0, sigma), length(y))
end
# Translated code end.
# Test data.
y = [ 1.1882e+02, 4.2169e+02, 1.3230e+03, 4.0375e+03, 1.2189e+04, 3.6625e+04,
      1.0992e+05, 3.2982e+05, 9.8951e+05, 2.9686e+06, 8.9058e+06, 2.6717e+07,
      8.0152e+07, 2.4046e+08, 7.2137e+08, 2.1641e+09, 6.4924e+09, 1.9477e+10,
      5.8431e+10, 1.7529e+11 ]
model = autoregressive_moving_average_model
arguments = (y,)
addresses = ("mu", "phi", "theta", "sigma")
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

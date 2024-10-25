# Translated code start.
using Turing
@model function autoregressive_order_K_model(y, K)
    alpha ~ Normal(0, 10)
    beta ~ filldist(Normal(0, 10), K)
    sigma ~ Truncated(Cauchy(2.5), 0, +Inf)
    for t = K:1:(length(y))-1
        mu = alpha
        for k = 0:1:(K)-1
            mu = (mu) + ((beta[(k)+1]) * (y[((t) - (k))+1]))
        end
        y[(t)+1] ~ Normal(mu, sigma)
    end
end
# Translated code end.
# Test data.
y = [            0.00,             0.00,            0.00,
                 0.00,             0.00,           14.88,
               117.33,           790.70,         5174.00,
             33858.00,        221680.00,      1451600.00,
           9505500.00,      62245000.00,    407600000.00,
        2669100000.00,   17478000000.00, 114450000000.00,
      749440000000.00, 4907600000000.00 ]
K = 5
model = autoregressive_order_K_model
arguments = (y, K)
addresses = ("alpha", "sigma")
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

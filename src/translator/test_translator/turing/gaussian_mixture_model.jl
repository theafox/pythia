# Translated code start.
using Turing
@model function gaussian_mixture_model(data)
    number_of_clusters = 2
    probability ~ Uniform(0, 1)
    mu = fill!(Array{Float64}(undef, number_of_clusters), 0)
    for i = 0:1:(number_of_clusters)-1
        mu[(i) + 1] ~ Normal(0, 1)
    end
    z = fill!(Array{Float64}(undef, length(data)), 0)
    for i = 0:1:(length(data))-1
        z[(i) + 1] ~ Bernoulli(probability)
        # data[(i) + 1] ~ Normal(mu[(z[(i) + 1]) + 1], 1)  # float indexing is not allowed.
        data[(i) + 1] ~ Normal(mu[(trunc(Int, z[(i) + 1])) + 1], 1)
    end
end
# Translated code end.
# Test data.
data = [ -0.6359476540323359,  1.6001572083672233, -1.4212620158942606,
          3.440893199201458,   3.067557990149967,   0.22272212012358894,
         -1.4499115824744107, -2.5513572082976976,  1.096781148206442,
          1.6105985019383722, -2.255956428839122,  -0.9457264930370248,
          1.9610377251469933,  1.3216750164928284,  1.6438632327454257,
          1.5336743273742668,  2.694079073157606,   0.994841736234199,
         -2.0869322983490983, -3.2540957393017247 ]
model = gaussian_mixture_model
arguments = (data,)
addresses = ("probability", "mu[1]", "mu[2]")
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

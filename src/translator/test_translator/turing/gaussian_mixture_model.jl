# Translated code start.
using Turing
@model function gaussian_mixture_model(data)
    number_of_clusters = 2
    theta ~ Uniform(0, 1)
    mu = fill!(Array{Float64}(undef, number_of_clusters), 0)
    for i = 0:1:(number_of_clusters)-1
        mu[(i)+1] ~ Normal(0, 10)
    end
    z = fill!(Array{Int}(undef, length(data)), 0)
    for i = 0:1:(length(data))-1
        z[(i)+1] ~ Bernoulli(theta)
        data[(i)+1] ~ Normal(mu[(z[(i)+1])+1], 1)
    end
end
# Translated code end.
# Test data.
data = [ 15.24052345967664,     5.201572083672233,   7.387379841057392,
         23.60893199201458,    19.875579901499673,  -8.57277879876411,
          7.100884175255894,   -3.913572082976979,   0.16781148206442142,
          5.305985019383724,   -0.9595642883912201, 12.142735069629751,
          8.810377251469934,    2.416750164928284,   5.638632327454257,
          4.536743273742668,   16.14079073157606,   -0.8515826376580089,
          0.7306770165090137, -10.940957393017248 ]
model = gaussian_mixture_model
arguments = (data,)
addresses = ("theta", "mu[1]", "mu[2]")
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

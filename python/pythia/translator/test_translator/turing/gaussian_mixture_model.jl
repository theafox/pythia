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
# Test data generated with:
#   probability~0.6
#   mu~[-2.4,1.2]
#   z~[0,1,0,1,1,1,0,0,1,1,0,0,1,1,1,1,1,1,0,0]
data = [
    -1.64, 1.01, 0.01, 2.26, 0.40, -0.54, -2.15, -2.08, 1.31, 0.64,
    -3.30, -2.19, 2.90, 0.36, 1.16, 1.28, 1.67, 0.18, -2.25, -2.36
]
display(sample(gaussian_mixture_model(data), NUTS(), 1000))

# Translated code start.
using Gen
using Distributions
@gen function gaussian_mixture_model(data)
    number_of_clusters = 2
    theta = {"theta"} ~ uniform(0, 1)
    mu = fill!(Array{Float64}(undef, number_of_clusters), 0)
    for i = 0:1:(number_of_clusters)-1
        mu[(i)+1] = {"$("mu")[$(i)]"} ~ normal(0, 10)
    end
    z = fill!(Array{Int}(undef, length(data)), 0)
    for i = 0:1:(length(data))-1
        z[(i)+1] = {"$("z")[$(i)]"} ~ bernoulli(theta)
        {"$("data")[$(i)]"} ~ normal(mu[(z[(i)+1])+1], 1)
    end
end
__observe_constraints = Gen.choicemap()
function __choicemap_aggregation(data)
    number_of_clusters = 2
    mu = fill!(Array{Float64}(undef, number_of_clusters), 0)
    for i = 0:1:(number_of_clusters)-1
    end
    z = fill!(Array{Int}(undef, length(data)), 0)
    for i = 0:1:(length(data))-1
        __observe_constraints["$("data")[$(i)]"] = data[(i)+1]
    end
end
# Translated code end.
using Random
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
addresses = ("theta", "mu[0]", "mu[1]")
# Inference.
Random.seed!(0)
__choicemap_aggregation(arguments...)
(traces, log_weights) = importance_sampling(model, arguments,
                                            __observe_constraints, 10_000)
println("Inferred:")
weights = exp.(log_weights)
weights = weights / sum(weights)
for address in addresses
    mean = sum([trace[address] for trace in traces] .* weights)
    println(" - $address=$mean")
end

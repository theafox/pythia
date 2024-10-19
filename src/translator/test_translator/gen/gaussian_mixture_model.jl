# Translated code start.
using Gen
using Distributions
@gen function gaussian_mixture_model(data)
    number_of_clusters = 2
    probability = {"probability"} ~ uniform(0, 1)
    mu = fill!(Array{Float64}(undef, number_of_clusters), 0)
    for i = 0:1:(number_of_clusters)-1
        mu[(i) + 1] = {"$("mu")[$(i)]"} ~ normal(0, 1)
    end
    z = fill!(Array{Float64}(undef, length(data)), 0)
    for i = 0:1:(length(data))-1
        z[(i) + 1] = {"$("z")[$(i)]"} ~ bernoulli(probability)
        # {"$("data")[$(i)]"} ~ normal(mu[(z[(i) + 1]) + 1], 1)  # float indexing is not allowed.
        {"$("data")[$(i)]"} ~ normal(mu[(trunc(Int, z[(i) + 1])) + 1], 1)
    end
end
__observe_constraints = Gen.choicemap()
function __choicemap_aggregation(data)
    number_of_clusters = 2
    mu = fill!(Array{Float64}(undef, number_of_clusters), 0)
    for i = 0:1:(number_of_clusters)-1
    end
    z = fill!(Array{Float64}(undef, length(data)), 0)
    for i = 0:1:(length(data))-1
        __observe_constraints["$("data")[$(i)]"] = data[(i) + 1]
    end
end
# Translated code end.
using Random
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
addresses = ("probability", "mu[0]", "mu[1]")
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

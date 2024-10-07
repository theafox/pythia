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
# Test data generated with:
#   probability~0.6
#   mu~[-2.4,1.2]
#   z~[0,1,0,1,1,1,0,0,1,1,0,0,1,1,1,1,1,1,0,0]
data = [
    -1.64, 1.01, 0.01, 2.26, 0.40, -0.54, -2.15, -2.08, 1.31, 0.64,
    -3.30, -2.19, 2.90, 0.36, 1.16, 1.28, 1.67, 0.18, -2.25, -2.36
]
__choicemap_aggregation(data)
(trace,) = importance_resampling(gaussian_mixture_model, (data,), __observe_constraints, 1000)
println("Inferred:")
println("\tprobability=$(trace["probability"])")
println("\tmu=[$(trace["mu[0]"]), $(trace["mu[1]"])]")
println("\tz=[$(trace["z[0]"]), $(trace["z[1]"]), $(trace["z[2]"]), $(trace["z[3]"]), $(trace["z[4]"]), $(trace["z[5]"]), $(trace["z[6]"]), $(trace["z[7]"]), $(trace["z[8]"]), $(trace["z[9]"]), $(trace["z[10]"]), $(trace["z[11]"]), $(trace["z[12]"]), $(trace["z[13]"]), $(trace["z[14]"]), $(trace["z[15]"]), $(trace["z[16]"]), $(trace["z[17]"]), $(trace["z[18]"]), $(trace["z[19]"])]")

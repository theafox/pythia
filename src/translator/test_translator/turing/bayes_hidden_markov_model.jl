# Translated code start.
using Turing
@model function bayes_hidden_markov_model(y, K)
    s = fill!(Array{Int}(undef, length(y)), 0)
    m = fill!(Array{Float64}(undef, K), 0)
    T = fill!(Array{Float64}(undef, (K, K)), 0)
    for i = 0:1:(K)-1
        T[(i)+1, begin:1:end] ~ Dirichlet(K, (1) / (K))
        m[(i)+1] ~ Normal((i) + (1), 0.5)
    end
    s[(0)+1] ~ DiscreteUniform(0, (K) - (1))
    y[(0)+1] ~ Normal(m[(s[(0)+1])+1], 0.1)
    for i = 1:1:(length(y))-1
        __categorical__context__unique_address_1 = T[(s[((i) - (1))+1])+1, begin:1:end]
        s[(i)+1] ~ DiscreteNonParametric(0:length(__categorical__context__unique_address_1)-1, __categorical__context__unique_address_1)
        y[(i)+1] ~ Normal(m[(s[(i)+1])+1], 0.1)
    end
end
# Translated code end.
# Test data.
y = [ 6.500169164315597, 7.936579509333255, 9.317801661471384,
      8.077189678856062, 6.647212557828355, 1.8866898228924214,
      6.6439487634103465, 2.0341088048097773, 6.441242417801613,
      5.201439088726868 ]
K = 10
model = bayes_hidden_markov_model
arguments = (y, K)
addresses = ( "s[1]", "s[2]", "s[3]", "s[4]", "s[5]", "s[6]", "s[7]", "s[8]",
              "s[9]", "s[10]" )
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

# Translated code start.
using Turing
@model function cointoss_model(data)
    p ~ Uniform(0, 1)
    for i = 0:1:(length(data))-1
        if ((data[(i)+1]) != (0)) && ((data[(i)+1]) != (1))
            continue
        end
        data[(i)+1] ~ Bernoulli(p)
    end
end
# Translated code end.
# Test data.
data = [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
model = cointoss_model
arguments = (data,)
addresses = ("p",)
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

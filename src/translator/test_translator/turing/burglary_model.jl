# Translated code start.
using Turing
@model function burglary_model(data)
    earthquake ~ Bernoulli(0.02)
    burglary ~ Bernoulli(0.01)
    if (earthquake) == (1)
        phone_working ~ Bernoulli(0.8)
    else
        phone_working ~ Bernoulli(0.9)
    end
    if (earthquake) == (1)
        mary_wakes ~ Bernoulli(0.8)
    else
        if (burglary) == (1)
            mary_wakes ~ Bernoulli(0.7)
        else
            mary_wakes ~ Bernoulli(0.1)
        end
    end
    called = ((mary_wakes) == (1)) && ((phone_working) == (1))
    data ~ Dirac(called)
end
# Translated code end.
# Test data.
data = false
model = burglary_model
arguments = (data,)
addresses = ("earthquake", "burglary", "phone_working", "mary_wakes")
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

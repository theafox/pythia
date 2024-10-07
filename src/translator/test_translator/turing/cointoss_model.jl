# Translated code start.
using Turing
@model function cointoss_model(data)
    probability ~ Uniform(0, 1)
    for i = 0:1:(length(data))-1
        if ((data[(i) + 1]) != (0)) && ((data[(i) + 1]) != (1))
            continue
        end
        data[(i) + 1] ~ Bernoulli(probability)
    end
end
# Translated code end.
# Test data generated with:
#   p~0.7
data = [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 1, 1]
display(sample(cointoss_model(data), NUTS(), 1000))

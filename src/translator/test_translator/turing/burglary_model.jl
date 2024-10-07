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
observed = true
display(sample(burglary_model(observed), NUTS(), 1000))

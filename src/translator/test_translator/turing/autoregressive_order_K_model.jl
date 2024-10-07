# Translated code start.
using Turing
@model function autoregressive_order_K_model(y, K)
    alpha ~ Normal(0, 10)
    beta ~ filldist(Normal(0, 10), K)
    sigma ~ Cauchy(0, 2.5)
    for t = K:1:(length(y))-1
        mu = alpha
        for k = 0:1:(K)-1
            mu = (mu) + ((beta[(k) + 1]) * (y[((t) - (k)) + 1]))
        end
        y[(t) + 1] ~ Normal(mu, sigma)
    end
end
# Translated code end.
# Test data generated with:
#   alpha~14
#   sigma~0.5
#   beta~[-6.45,6.93,-2.48,-1.99,12.19]
y = [0, 0, 0, 0, 0, 14.33, 113.59, 765.56, 5009.41, 32779.81, 214616.96, 1405379.32, 9202875.14, 60263095.70, 394619612.99, 2584079307.87, 16921272464.00, 110805215612.65, 725583483758.52, 4751323202301.19]
K = 5
display(sample(autoregressive_order_K_model(y, K), NUTS(), 1000))

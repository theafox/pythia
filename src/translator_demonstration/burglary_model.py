# Own model.
@probabilistic_program
def burglary_model(data):
    earthquake = sample("earthquake", Bernoulli(0.02))
    burglary = sample("burglary", Bernoulli(0.01))
    if earthquake == 1:
        phone_working = sample("phone_working", Bernoulli(0.8))
    else:
        phone_working = sample("phone_working", Bernoulli(0.9))
    if earthquake == 1:
        mary_wakes = sample("mary_wakes", Bernoulli(0.8))
    elif burglary == 1:
        mary_wakes = sample("mary_wakes", Bernoulli(0.7))
    else:
        mary_wakes = sample("mary_wakes", Bernoulli(0.1))
    called = mary_wakes == 1 and phone_working == 1
    observe(data, "observed", Dirac(called))

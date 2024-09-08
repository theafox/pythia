"""A simple demonstration of the translator.

This showcases the translator using the examples of the thesis defining
_PyThia_.

Usage: This should be executed as a module, i.e.
    `python -m translator_demonstration [OPTIONS]`. In case any command-line
    arguments are provided, they are interpreted as the selection of target
    languages/frameworks to translate.

Author: T. Kaufmann <e12002221@student.tuwien.ac.at>
"""

from translator import (
    Translator,
    default_gen_translator,
    default_julia_translator,
    default_pyro_translator,
    default_python_translator,
    default_turing_translator,
)

AVAILABLE_TRANSLATORS = [
    ("python", default_python_translator()),
    ("pyro", default_pyro_translator()),
    ("julia", default_julia_translator()),
    ("gen", default_gen_translator()),
    ("turing", default_turing_translator()),
]
CODE_PIECES = [
    # Cointoss.
    """\
@probabilistic_program
def coinflip(data):
    probability = sample("probability", Uniform(0, 1))
    for i in range(0, len(data)):
        if data[i] != 0 and data[i] != 1:
            continue
        observe(data[i], IndexedAddress("data", i), Bernoulli(probability))""",
    # Number of Heads.
    """\
@probabilistic_program
def number_of_heads(probability):
    HEADS = 0
    TAILS = 1
    count = 0
    while True:
        cointoss = sample(
            IndexedAddress("cointoss", count),
            Bernoulli(probability),
        )
        if cointoss == TAILS:
            break
        count = count + 1
    return count""",
    # Linear regression.
    """\
@probabilistic_program
def linear_regression(data):
    gradient = sample("gradient", Normal(0, 10))
    intercept = sample("intercept", Normal(0, 10))
    for i in range(0, len(data)):
        observe(
            data[i].y,
            IndexedAddress("data", i),
            Normal(gradient * data[i].x + intercept, 1),
        )""",
    # Burglary
    """\
@probabilistic_program
def burglary(probabilities):
    earthquake = sample("earthquake", Bernoulli(probabilities.earthquake))
    earthquake = earthquake == 1
    burglary = sample("burglary", Bernoulli(probabilities.burglary))
    burglary = burglary == 1

    # Does the phone work?
    if earthquake:
        phoneWorking = sample(
            "phoneWorking",
            Bernoulli(probabilities.phoneWorkingDuringEarthquake),
        )
    else:
        phoneWorking = sample(
            "phoneWorking",
            Bernoulli(probabilities.phoneWorking),
        )
    phoneWorking = phoneWorking == 1

    # Does Mary wake?
    alarm = earthquake or burglary
    if alarm and earthquake:
        maryWakes = sample(
            "maryWakes",
            Bernoulli(probabilities.maryWakesDuringAlarmAndEarthquake),
        )
    elif alarm:
        maryWakes = sample(
            "maryWakes",
            Bernoulli(probabilities.maryWakesDuringAlarm),
        )
    else:
        maryWakes = sample("maryWakes", Bernoulli(probabilities.maryWakes))
    maryWakes = maryWakes == 1

    called = maryWakes and phoneWorking
    observe(called, "called", Dirac(True))""",
    # Rate 5 Model
    """\
@probabilistic_program
def model(n1, n2, k1, k2):
    # Prior on Single Rate Theta
    theta = sample("theta", Beta(1, 1))

    # Observed Counts
    observe(k1, "obs1", Binomial(n1, theta))
    observe(k2, "obs2", Binomial(n2, theta))

    # Posterior Predictive / generated quantities (correct?)
    postpredk1 = sample("postpredk1", Binomial(n1, theta))
    postpredk2 = sample("postpredk2", Binomial(n2, theta))

    return (postpredk1, postpredk2)""",
    # Bayes Hidden Markov
    """\
@probabilistic_program
def bayes_hidden_markov_model(y, K):
    s = Vector(len(y), fill=0)  # State sequence.
    m = Vector(K)  # Emission matrix.
    T = Array((K, K))  # Transition matrix.

    # Assign distributions to each element of the transition matrix and the
    # emission matrix.
    for i in range(0, K):
        T[i] = sample(IndexedAddress("T", i), IID(Dirichlet(1 / K), K))
        m[i] = sample(IndexedAddress("m", i), Normal(i + 1, 0.5))

    # Observe each point of the input.
    s[0] = DiscreteUniform(0, K)
    observe(y[0], IndexedAddress("y", 0), Normal(m[s[0]], 0.1))

    for i in range(1, len(y)):
        s[i] = DiscreteUniform(0, K)
        observe(y[i], IndexedAddress("y", i), Normal(m[s[i]], 0.1))""",
    # Autoregressive moving average
    """\
@probabilistic_program
def autoregressive_moving_average_model(y):
    nu = Vector(len(y), fill=0)
    err = Vector(len(y), fill=0)

    mu = sample("mu", Normal(0, 10))
    phi = sample("phi", Normal(0, 10))
    theta = sample("theta", Normal(0, 10))
    sigma = sample("sigma", HalfCauchy(2.5))

    nu[0] = mu + phi * mu
    err[0] = y[0] - nu[0]
    for t in range(1, len(y)):
        nu[t] = mu + phi * y[t - 1] + theta * err[t - 1]
        err[t] = y[t] - nu[t]

    observe(err, "err", IID(Normal(0, sigma), len(y)))""",
    # Autoregressive order K
    """\
@probabilistic_program
def autoregressive_order_K(y, K):
    alpha = sample("alpha", Normal(0, 10))
    beta = sample("beta", IID(Normal(0, 10), K))  # correct usage?
    sigma = sample("sigma", Cauchy(0, 2.5))

    for t in range(K, len(y)):
        mu = alpha
        for k in range(0, K):
            mu = mu + beta[k] * y[t - k]
        observe(y[t], IndexedAddress("y", t), Normal(mu, sigma))""",
    # Cointoss factor
    """\
@probabilistic_program
def coinflip_with_factor(data):
    probability = sample("probability", Uniform(0, 1))
    for i in range(0, len(data)):
        new = probability
        if data[i] != 1:
            new = 1 - probability
        factor(math.log(new))
    return probability""",
    # Gaussian Mixture Model
    """\
@probabilistic_program
def gaussian_mixture_model(numer_of_clusters, data):
    probability = sample("probability", Uniform(0, 1))
    mu = Vector(numer_of_clusters)
    for i in range(0, numer_of_clusters):
        mu[i] = sample(IndexedAddress("mu", i), Normal(0, 1))
    z = Vector(len(data))
    for i in range(0, len(data)):
        z[i] = sample(IndexedAddress("z", i), Bernoulli(probability))
        observe(data[i], IndexedAddress("data", i), Normal(mu[z[i]], 1))""",
]


def _display_translation(
    code: str,
    *translators: tuple[str, Translator],
    width: int = 60,
    header_character: str = "=",
    subheader_character: str = "-",
) -> None:
    print(f"\n{" Original Code ":{header_character}^{width}}")
    print(code, end="")
    for name, translator in translators:
        print(f"\n{f" Translated: {name} ":{subheader_character}^{width}}")
        if translation := translator.translate_code(code):
            print(translation, end="")
    print("\n" + header_character * width)


if __name__ == "__main__":
    import sys

    from translator.__main__ import Verbosity, configure_logger

    configure_logger(Verbosity.NORMAL)
    translators = [
        (name, translator)
        for name, translator in AVAILABLE_TRANSLATORS
        if not (arguments := sys.argv[1:]) or name in arguments
    ]
    for code in CODE_PIECES:
        _display_translation(code, *translators)

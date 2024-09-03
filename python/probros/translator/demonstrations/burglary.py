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
    observe(called, "called", Dirac(True))

import matplotlib.style
matplotlib.use("Qt5Agg")
matplotlib.style.use('classic')
from matplotlib import pyplot as plt
import numpy as np
import pickle
from cuts import Cuts
from montecarlo import MontecarloCharacterization, MonteCarloRunner

series = pickle.load( open( "salarios.p", "rb" ) )
parameters = MontecarloCharacterization(series=series, cuts=Cuts.argentinaCuts, period=12.0 / 252).getYieldsMeanAndSigma()


initialCut = 'macri'
remainingMonthsForActualCut = 6+12.0
monthsPerCut = 4*12.0
loanLength = 15*12.0


numberOfAdditionalPeriods = int( np.ceil( (loanLength-remainingMonthsForActualCut)/monthsPerCut) )
cuts = Cuts()

def currentSumOfPeriods(periods):
    return np.sum([months for cutName,months in [cut for cut in periods]])


for k in range(100):
    periods = [(initialCut, remainingMonthsForActualCut)]
    for i in range( numberOfAdditionalPeriods ):
        periods.append( ( cuts.cutTransition( periods[-1][0] ),np.min( [ monthsPerCut,loanLength-currentSumOfPeriods( periods ) ] ) ) )
    sample = [100]
    for period in periods:
        sample.extend( MonteCarloRunner(parameters[period[0]]).run(initialValue=sample[-1],size=int(period[1]),iterations=1) )

    plt.plot(sample)
plt.show()


import matplotlib.style
from simulations import salarySimulationRun, calculateSettlementToSalaryRatios

matplotlib.use("Qt5Agg")
matplotlib.style.use('classic')
from matplotlib import pyplot as plt
import pickle

series = pickle.load( open( "salarios.p", "rb" ) )

salaries = salarySimulationRun(totalIterations=1000,
                              loanLength=15*12.0,
                              remainingMonthsForActualCut=6+12.0,
                              monthsPerCut=4*12.0,
                              initialCut='macri',
                              historicSeries=series,
                              possibleExtensionInMonths=12)

indexWhereRefinanced,settlementToSalaryRatios = calculateSettlementToSalaryRatios(salaries=salaries,
                                                             initialSettlementToSalaryRatio=30,
                                                             explosionRate=60)


plt.plot(settlementToSalaryRatios.T, alpha=0.5)
plt.show()


import matplotlib.style
from simulations import salarySimulationRun, calculateSettlementToSalaryRatios, printLoanReport, killDefaulted
from cuts import mockContext

matplotlib.use("Qt5Agg")
matplotlib.style.use('classic')
from matplotlib import pyplot as plt
import pickle
from loan_calculator import LoanCalculator

loanLength= int(30*12)
monthsPerCut=int(4*12)
interestRate = 0.05/12
remainingMonthsForActualCut=6+12.0
initialSettlementToSalaryRatio=30
consecutiveAboveExplosionRateForRefinance=1
consecutiveAboveExplosionRateForDefault=1
explosionRate=60
initialCut='macri'


series = pickle.load( open( "salarios.p", "rb" ) )

salaries = salarySimulationRun(totalIterations=10000,
                              loanLength=loanLength,
                              remainingMonthsForActualCut=remainingMonthsForActualCut,
                              monthsPerCut=monthsPerCut,
                              initialCut=initialCut,
                              historicSeries=series,
                              possibleExtensionInMonths=12,
                              distrib='t')

loanCalculator = LoanCalculator(10000,loanLength,interestRate,payment='monthly',loanTimeIn='monthly')
indexWhereRefinanced,settlementToSalaryRatios = calculateSettlementToSalaryRatios(salaries=salaries,
                                                            loanCalculator=loanCalculator,
                                                            originalLoanLength=loanLength,
                                                            initialSettlementToSalaryRatio=initialSettlementToSalaryRatio,
                                                            explosionRate=explosionRate,
                                                            consecutiveAboveExplosionRateForRefinance=consecutiveAboveExplosionRateForRefinance
                                                            )
settlementToSalaryRatios, defaulted = killDefaulted(settlementToSalaryRatios, explosionRate=explosionRate,
                                         indexWhereRefinanced=indexWhereRefinanced,
                                         consecutiveAboveExplosionRateForDefault=consecutiveAboveExplosionRateForDefault)
printLoanReport(indexWhereRefinanced, settlementToSalaryRatios, loanLength, defaulted)

plt.plot(settlementToSalaryRatios.T, alpha=0.5)
plt.show()





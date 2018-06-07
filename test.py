import matplotlib.style
from simulations import salarySimulationRun, calculateSettlementToSalaryRatios, printLoanReport, killDefaulted
from loan_calculator import LoanCalculator

matplotlib.use("Qt5Agg")
matplotlib.style.use('classic')
from matplotlib import pyplot as plt
import pickle

loanLength= int(15*12)
monthsPerCut=int(4*12)
interestRate = 0.05/12
remainingMonthsForActualCut=6+12.0
initialSettlementToSalaryRatio=30
explosionRate=60
initialCut='macri'

series = pickle.load( open( "salarios.p", "rb" ) )
salaries = salarySimulationRun(totalIterations=10000,
                              loanLength=loanLength,
                              remainingMonthsForActualCut=remainingMonthsForActualCut,
                              monthsPerCut=monthsPerCut,
                              initialCut=initialCut,
                              historicSeries=series,
                              possibleExtensionInMonths=12)

loanCalculator = LoanCalculator(10000,loanLength,interestRate,payment='monthly',loanTimeIn='monthly')

indexWhereRefinanced,settlementToSalaryRatios = calculateSettlementToSalaryRatios(salaries=salaries,
                                                            loanCalculator=loanCalculator,
                                                            originalLoanLength=loanLength,
                                                            initialSettlementToSalaryRatio=initialSettlementToSalaryRatio,
                                                            explosionRate=explosionRate,
                                                            )
settlementToSalaryRatios = killDefaulted(settlementToSalaryRatios, explosionRate=explosionRate)
printLoanReport(indexWhereRefinanced, originalLoanLength, settlementToSalaryRatios)


plt.plot(settlementToSalaryRatios.T, alpha=0.5)
plt.show()


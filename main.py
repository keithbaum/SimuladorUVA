import matplotlib.style
from simulations import salarySimulationRun, calculateSettlementToSalaryRatios, printLoanReport, killDefaulted
from loan_calculator import LoanCalculator
from unittest import mock

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

def mockTransition(*args):
    if hasattr(mockTransition,'index'):
        mockTransition.index+=1
    else:
        mockTransition.index=0
    return list(['macri','hiperinflacion','kirchner','kirchner','macri'])[mockTransition.index % 5]

series = pickle.load( open( "salarios.p", "rb" ) )
with mock.patch('cuts.Cuts.cutTransition',side_effect=mockTransition):
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
printLoanReport(indexWhereRefinanced, settlementToSalaryRatios,loanLength)

plt.plot(settlementToSalaryRatios.T, alpha=0.5)
plt.show()


import numpy as np
from cuts import Cuts
from montecarlo import MonteCarloRunner, MontecarloCharacterization

def salarySimulationRun(totalIterations, loanLength, remainingMonthsForActualCut, monthsPerCut, initialCut, historicSeries, possibleExtensionInMonths):
    cuts = Cuts()
    extendedLoanLength = loanLength + possibleExtensionInMonths
    numberOfPeriods = int( np.ceil( (extendedLoanLength-remainingMonthsForActualCut)/monthsPerCut) )
    parameters = MontecarloCharacterization(series=historicSeries, cuts=Cuts.argentinaCuts,
                                            period=12.0 / 252).getYieldsMeanAndSigma()

    results = np.empty((totalIterations, int(extendedLoanLength + 1)))
    initialPeriod = (initialCut, remainingMonthsForActualCut)
    initialValue = 100

    for k in range(totalIterations):
        runValues = [initialValue]
        iterationPeriods=generatePeriodVector(cuts, initialPeriod, extendedLoanLength, monthsPerCut, numberOfPeriods)
        for period in iterationPeriods:
            runValues.extend( MonteCarloRunner(parameters[period[0]]).run(initialValue=runValues[-1], size=int(period[1]),
                                                                      iterations=1) )
        results[k, :] = runValues

    return results


def generatePeriodVector(cuts, initialPeriod, loanLength, monthsPerCut, numberOfAdditionalPeriods):
    periodVector = [initialPeriod]
    for i in range(numberOfAdditionalPeriods):
        periodVector.append(
            (cuts.cutTransition(periodVector[-1][0]), np.min([monthsPerCut, loanLength - currentSumOfPeriods(
                periodVector)])))

    return periodVector


def currentSumOfPeriods(periods):
    return np.sum([months for cutName,months in [cut for cut in periods]])

def refinance(settlementNumber):
    return 20


def calculateSettlementToSalaryRatios( salaries, initialSettlementToSalaryRatio=30, explosionRate=60):
    results = np.empty(salaries.shape)
    indexes = getIndexWhereLoanExplodes(explosionRate, initialSettlementToSalaryRatio, salaries)
    settlements = np.ones(salaries.shape)*initialSettlementToSalaryRatio
    if len(salaries.shape)==2:
        iterations = salaries.shape[0]
        for iterationNumber in range(iterations):
            if indexes[iterationNumber]:
                settlements[iterationNumber,indexes[iterationNumber]:]=refinance(indexes[iterationNumber])

    else:
        if indexes:
            settlements[indexes:]=refinance(indexes)

    return (indexes, settlements/salaries)



def getIndexWhereLoanExplodes(explosionRate, initialSettlementToSalaryRatio, salaries):
    if len(salaries.shape) == 2:  # If simulation had iterations
        iterations = salaries.shape[0]
        indexWhereRefinanced = np.empty(iterations)
        for iterationNumber in range(iterations):
            indexWhereRefinanced[iterationNumber] = getIndexWhereSingleLoanExplodes(salaries[iterationNumber, :],
                                                                                    initialSettlementToSalaryRatio, explosionRate)
    else:
        indexWhereRefinanced = getIndexWhereSingleLoanExplodes(salaries, initialSettlementToSalaryRatio, explosionRate)

    return indexWhereRefinanced.astype(int)


def getIndexWhereSingleLoanExplodes(salary, initialSettlementToSalaryRatio, explosionRate):
    initialRate = initialSettlementToSalaryRatio / salary
    indexes = np.where(initialRate > explosionRate / 100.0)[0]
    return 0 if len(indexes) == 0 else indexes[0]





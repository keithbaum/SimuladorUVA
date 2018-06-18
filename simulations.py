import numpy as np
import pandas as pd
from cuts import Cuts
from montecarlo import MonteCarloRunner, MontecarloCharacterization
from non_normal import NonGaussianCharacterization, NonGaussianParameters

def salarySimulationRun(totalIterations, loanLength, remainingMonthsForActualCut, monthsPerCut, initialCut, historicSeries, possibleExtensionInMonths, assumeGaussian=True):
    cuts = Cuts()
    extendedLoanLength = loanLength + possibleExtensionInMonths
    numberOfPeriods = int( np.ceil( (extendedLoanLength-remainingMonthsForActualCut)/monthsPerCut) )

    parameters = MontecarloCharacterization(series=historicSeries, cuts=Cuts.argentinaCuts,
                                                period=12.0 / 252).getYieldsMeanAndSigma()

    if not assumeGaussian:
        nonGaussianCalculators = NonGaussianCharacterization(series=historicSeries, cuts=Cuts.argentinaCuts,
                                                period=12.0 / 252).getInverseECDFs()
        for cutName, parameter in parameters.items():
            parameters[cutName] = NonGaussianParameters(*parameter,nonGaussianCalculators[cutName])

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


def calculateSettlementToSalaryRatios( salaries, loanCalculator, originalLoanLength, initialSettlementToSalaryRatio=30, explosionRate=60):
    originalSettlement = loanCalculator.compute().due
    indexes = getIndexWhereLoanExplodes(explosionRate, initialSettlementToSalaryRatio, salaries, originalLoanLength)
    settlements = np.ones(salaries.shape)*initialSettlementToSalaryRatio
    if len(salaries.shape)==2:
        iterations = salaries.shape[0]
        for iterationNumber in range(iterations):
            if indexes[iterationNumber]:
                settlements[iterationNumber,indexes[iterationNumber]:]=loanCalculator.reFinance(indexes[iterationNumber],
                                                                                                salaries.shape[1]-indexes[iterationNumber],
                                                                                                refinanceInTime='monthly').due/originalSettlement*initialSettlementToSalaryRatio
            else:
                settlements[iterationNumber,originalLoanLength:]=np.nan
    else:
        if indexes:
            settlements[indexes:]=loanCalculator.reFinance(indexes,salaries.shape[0]-indexes,refinanceInTime='monthly').due/originalSettlement*initialSettlementToSalaryRatio
        else:
            settlements[originalLoanLength:]=np.nan

    return (indexes, settlements/salaries)



def getIndexWhereLoanExplodes(explosionRate, initialSettlementToSalaryRatio, salaries, originalLoanLength):
    if len(salaries.shape) == 2:  # If simulation had iterations
        iterations = salaries.shape[0]
        indexWhereRefinanced = np.empty(iterations)
        for iterationNumber in range(iterations):
            indexWhereRefinanced[iterationNumber] = getIndexWhereSingleLoanExplodes(salaries[iterationNumber,:originalLoanLength],
                                                                                    initialSettlementToSalaryRatio, explosionRate)
    else:
        indexWhereRefinanced = getIndexWhereSingleLoanExplodes(salaries[:originalLoanLength], initialSettlementToSalaryRatio, explosionRate)

    return indexWhereRefinanced.astype(int)


def getIndexWhereSingleLoanExplodes(salary, initialSettlementToSalaryRatio, explosionRate):
    initialRate = initialSettlementToSalaryRatio / salary
    indexes = np.where(initialRate > explosionRate / 100.0)[0]
    return 0 if len(indexes) == 0 else indexes[0]

def printLoanReport(indexWhereRefinanced, settlementToSalaryRatios,originalLoanLength):
    data = []
    if len(settlementToSalaryRatios.shape)==2:
        for iterationNumber in range(settlementToSalaryRatios.shape[0]):
            refinancedMonth=indexWhereRefinanced[iterationNumber]
            hasDefaulted=np.count_nonzero(np.isnan(settlementToSalaryRatios[iterationNumber]))>settlementToSalaryRatios.shape[1]-originalLoanLength
            data.append((refinancedMonth,hasDefaulted))
    else:
        refinancedMonth = indexWhereRefinanced
        hasDefaulted = np.count_nonzero(np.isnan(settlementToSalaryRatios)) > len(settlementToSalaryRatios) - originalLoanLength
        data=(refinancedMonth, hasDefaulted)

    results = pd.DataFrame(columns=['Month where refinanced', 'Defaulted?'],data=data)

    print( results.to_string() )
    defaulted = len(results.loc[results['Defaulted?']==True])
    nonRefinanced = len(results.loc[results['Month where refinanced']==0])
    succesfullyRefinanced = len(results.loc[(results['Month where refinanced'] != 0) & (results['Defaulted?'] == False)])
    print( "%s defaulted, %s payed without refinancing, %s payed with refinancing"% (defaulted, nonRefinanced, succesfullyRefinanced) )
    print( "Default rate= %s%%" % str(defaulted/len(results.index)*100.0) )

def killDefaulted(settlementToSalaryRatios, explosionRate):
    defaulted=np.unique(np.argwhere(settlementToSalaryRatios>explosionRate/100.0)[:,0])
    indexWhereDefaultOccured=[ np.where( settlementToSalaryRatios[i]>explosionRate/100 )[0][0] for i in defaulted ]
    for iterationNumber,iteration in enumerate(defaulted):
        settlementToSalaryRatios[iteration,indexWhereDefaultOccured[iterationNumber]:]=np.nan
    return settlementToSalaryRatios
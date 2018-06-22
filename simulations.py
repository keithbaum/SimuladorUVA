import numpy as np
import pandas as pd
from cuts import Cuts
from montecarlo import MonteCarloRunner, MontecarloCharacterization
from non_normal import NonGaussianCharacterization, NonGaussianParameters

def salarySimulationRun(totalIterations, loanLength, remainingMonthsForActualCut, monthsPerCut, initialCut, historicSeries, possibleExtensionInMonths, distrib='norm'):
    cuts = Cuts()
    extendedLoanLength = loanLength + possibleExtensionInMonths
    numberOfPeriods = int( np.ceil( (extendedLoanLength-remainingMonthsForActualCut)/monthsPerCut) )

    parameters = MontecarloCharacterization(series=historicSeries, cuts=Cuts.argentinaCuts,
                                                period=12.0 / 252).getYieldsMeanAndSigma()

    if distrib != 'norm':
        calculators = NonGaussianCharacterization(series=historicSeries, cuts=Cuts.argentinaCuts, gaussianParameters=parameters).getCalculators(distrib)
        for cutName, parameter in parameters.items():
            parameters[cutName] = NonGaussianParameters(*parameter,calculators[cutName])

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


def calculateSettlementToSalaryRatios( salaries, loanCalculator, originalLoanLength, initialSettlementToSalaryRatio=30, explosionRate=60, consecutiveAboveExplosionRateForRefinance=3):
    originalSettlement = loanCalculator.compute().due
    indexes = getIndexWhereLoanExplodes(explosionRate, initialSettlementToSalaryRatio, salaries, originalLoanLength, consecutiveAboveExplosionRateForRefinance)
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



def getIndexWhereLoanExplodes(explosionRate, initialSettlementToSalaryRatio, salaries, originalLoanLength, consecutiveAboveExplosionRateForRefinance):
    if len(salaries.shape) == 2:  # If simulation had iterations
        iterations = salaries.shape[0]
        indexWhereRefinanced = np.empty(iterations)
        for iterationNumber in range(iterations):
            indexWhereRefinanced[iterationNumber] = getIndexWhereSingleLoanExplodes(salaries[iterationNumber,:originalLoanLength],
                                                                                    initialSettlementToSalaryRatio, explosionRate,
                                                                                    consecutiveAboveExplosionRateForRefinance)
    else:
        indexWhereRefinanced = getIndexWhereSingleLoanExplodes(salaries[:originalLoanLength], initialSettlementToSalaryRatio, explosionRate, consecutiveAboveExplosionRateForRefinance)

    return indexWhereRefinanced.astype(int)


def getIndexWhereSingleLoanExplodes(salary, initialSettlementToSalaryRatio, explosionRate, consecutiveAboveExplosionRateForRefinance):
    initialRate = initialSettlementToSalaryRatio / salary
    indexesWhereAboveExplosion = initialRate > explosionRate / 100.0
    indexes= find_subsequence( indexesWhereAboveExplosion, [True]*consecutiveAboveExplosionRateForRefinance )
    return 0 if len(indexes) == 0 else indexes[0]+consecutiveAboveExplosionRateForRefinance-1

def find_subsequence(seq, subseq):
    target = np.dot(subseq, subseq)
    candidates = np.where(np.correlate(seq,
                                       subseq, mode='valid') == target)[0]
    # some of the candidates entries may be false positives, double check
    check = candidates[:, np.newaxis] + np.arange(len(subseq))
    mask = np.all((np.take(seq, check) == subseq), axis=-1)
    return candidates[mask]

def printLoanReport(indexWhereRefinanced, settlementToSalaryRatios,originalLoanLength, defaulted):
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

    #print( results.to_string() )
    defaulted = len(results.loc[results['Defaulted?']==True])
    nonRefinanced = len(results.loc[results['Month where refinanced']==0])
    succesfullyRefinanced = len(results.loc[(results['Month where refinanced'] != 0) & (results['Defaulted?'] == False)])
    print( "%s defaulted, %s payed without refinancing, %s payed with refinancing"% (defaulted, nonRefinanced, succesfullyRefinanced) )
    #print( "Default rate= %s%%" % str(defaulted/len(results.index)*100.0) )

def killDefaulted(settlementToSalaryRatios, explosionRate, indexWhereRefinanced, consecutiveAboveExplosionRateForDefault):
    refinanced=np.argwhere( indexWhereRefinanced !=0 )[:,0]
    defaulted = {}
    for refinancedIndex in refinanced:
            remainingAfterRefinanced = settlementToSalaryRatios[refinancedIndex, indexWhereRefinanced[refinancedIndex]+1:]
            indexesWhereAboveExplosion = remainingAfterRefinanced > explosionRate / 100.0
            indexes = find_subsequence(indexesWhereAboveExplosion, [True] * consecutiveAboveExplosionRateForDefault)
            defaultIndex = None if len(indexes) == 0 else indexWhereRefinanced[refinancedIndex] + 1 + indexes[0] + consecutiveAboveExplosionRateForDefault - 1
            if not defaultIndex is None:
                defaulted[refinancedIndex]=defaultIndex

    for iteration,indexWhereDefaultOccured in defaulted.items():
        settlementToSalaryRatios[iteration,indexWhereDefaultOccured:]=np.nan
    return (settlementToSalaryRatios, defaulted)
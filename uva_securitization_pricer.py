import datetime
import numpy as np
import matplotlib.style
matplotlib.use("Qt5Agg")
matplotlib.style.use('classic')
from matplotlib import pyplot as plt
from scipy.optimize import curve_fit
import curve
from scipy.optimize import fsolve

bond_data_arg_usd = {
             'A2E2' :{'yield':6.78, 'maturity':datetime.date(2022,1,26),  'duration':3.11},
             'A2E3' :{'yield':7.62, 'maturity':datetime.date(2023,1,11),  'duration':3.88},
             #'A2E7' :{'yield':8.00, 'maturity':datetime.date(2027,1,26),  'duration':6.12},
             'A2E8' :{'yield':8.34, 'maturity':datetime.date(2028,1,11),  'duration':6.73},
             'AA19' :{'yield':1.55, 'maturity':datetime.date(2019,4,22),  'duration':0.79},
             'AA21' :{'yield':6.47, 'maturity':datetime.date(2021,4,22),  'duration':2.5},
             'AA25' :{'yield':7.81, 'maturity':datetime.date(2025,4,18),  'duration':4.72},
             'AA26' :{'yield':9.05, 'maturity':datetime.date(2026,4,22),  'duration':5.64},
             'AA37' :{'yield':8.96, 'maturity':datetime.date(2037,4,18),  'duration':9.04},
             'AA46' :{'yield':9.51, 'maturity':datetime.date(2046,4,22),  'duration':9.51},
             'AE48' :{'yield':8.80, 'maturity':datetime.date(2048,1,11),  'duration':10.60},
             'AL36' :{'yield':11.05, 'maturity':datetime.date(2036,7,6),  'duration':8.19},
             #'AN18' :{'yield':-1.81, 'maturity':datetime.date(2018,11,29),  'duration':0.43},
             'AO20' :{'yield':4.72, 'maturity':datetime.date(2020,10,8),  'duration':2.06},
             'AY24' :{'yield':6.32, 'maturity':datetime.date(2024,5,7),  'duration':2.84},
            'LTDD8' :{'yield':2.76, 'maturity':datetime.date(2018,12,14),  'duration':0.46},
            'L2DN8' :{'yield':4.47, 'maturity':datetime.date(2018,11,16),  'duration':0.38},
             #'LTDL8' :{'yield':-9.47, 'maturity':datetime.date(2018,7,13),  'duration':0.05},
             }

bond_data_cer = {
             #'FAKE' :{'yield':0.01, 'maturity':datetime.date(2045,12,31), 'duration':0},
             'CUAP' :{'yield':7.61, 'maturity':datetime.date(2045,12,31), 'duration':12.51},
             'DICP' :{'yield':7.55, 'maturity':datetime.date(2033,12,31), 'duration':7.26},
             #'DIP0' :{'yield':7.0, 'maturity':datetime.date(2033,12,31), 'duration':7.37},
             #'PAR0' :{'yield':6.62, 'maturity':datetime.date(2038,12,31), 'duration':12.41},
             'PARP' :{'yield':7.88, 'maturity':datetime.date(2038,12,31), 'duration':12.02},
             'PR13' :{'yield':7.69, 'maturity':datetime.date(2024,3,15),  'duration':2.65},
             'TC21' :{'yield':8.39, 'maturity':datetime.date(2021,7,21),  'duration':2.82},
             #'NO20' :{'yield':8.16, 'maturity':datetime.date(2020,10,4),  'duration':1.12},
             'TC25P':{'yield':5.01, 'maturity':datetime.date(2025,4,27),  'duration':5.85},
             }

bono_banco_hipotecario = {'ticker': 'BHCVO',
                          'schedule':[(datetime.date(2018, 11, 30), 4.85), (datetime.date(2019, 5, 30), 4.85),
                                        (datetime.date(2019, 11, 30), 4.85),(datetime.date(2020, 5, 30), 4.85), (datetime.date(2020, 11, 30), 104.85)],
                          'market_price':105.75,
                          'payment_frequency':180}

securitization = {'all_in_cost':0.01, 'liquidity_spread':0.01}


def interpolated_yield_duration(bondData=None,maxTenor=13):
    bondData = bondData or bond_data_arg_usd
    yields = []
    tenors = []
    allTenors = np.linspace(1,13,144)
    for bond in bondData:
        yields.append( bondData[bond]['yield'] )
        tenors.append(bondData[bond]['duration'])

    regressors = curve_fit(fNelsonSiegelInterp, tenors, yields, maxfev=10000000)[0]

    def _interpolate( tenorToInterpolate):
        return fNelsonSiegelInterp(tenorToInterpolate, *regressors)

    interpolatedYields = [_interpolate(aTenor) for aTenor in allTenors]
    return allTenors, interpolatedYields

def interpolated_yield(bondData=None,numberOfMonths=340, startMonths=1):
    bondData = bondData or bond_data_arg_usd
    yields = []
    tenors = []
    allTenors = [i for i in range(startMonths, numberOfMonths+1)]
    for bond in bondData:
        yields.append( bondData[bond]['yield'] )
        tenors.append(toMonthTenor(bondData[bond]['maturity']))

    regressors = curve_fit(fNelsonSiegelInterp, tenors, yields, maxfev=100000 )[0]

    def _interpolate( tenorToInterpolate):
        return fNelsonSiegelInterp(tenorToInterpolate, *regressors)

    interpolatedYields = [_interpolate(aTenor) for aTenor in allTenors]
    return allTenors, interpolatedYields

def fNelsonSiegelInterp(x,p1,p2,p3,p4):
    return p1 + (p2 + p3) * (p4 / x) * (1 - np.exp((-x / p4))) - p3 * np.exp((-x / p4))

def fPolynomialInterp(x,p1,p2,p3,p4):
    return p1 + p2 * x ** 1 + p3 * x ** 2 + p4 * x ** 3


def toMonthTenor( date ):
    days = (date - datetime.date.today()).days
    return int(days/30)

def zspread(bondData, curveData, referenceDate=None ):
    referenceDate       = referenceDate or datetime.date.today()
    marketPrice         = bondData['market_price']
    paymentFreq         = bondData['payment_frequency']
    paymentsPerYear     = 360/paymentFreq
    schedule            = bondData['schedule']
    tenors              = [toMonthTenor(data[0]) for data in schedule]
    cashFlows           = [data[1] for data in schedule]
    w                   = (schedule[0][0] - referenceDate).days/paymentFreq
    spotsToUse          = [curveData['spots'][curveData['tenors'].index(bondTenor)] for bondTenor in tenors]
    result              = [None]

    def solver_fuc(values):
        zspreadValue = values[0]
        result[0]     = zspreadValue
        pvs     = []
        for i in range(0,len(cashFlows)):
            discountTerm = 1+((zspreadValue+spotsToUse[i])/paymentsPerYear)
            pvs.append(cashFlows[i] / np.power( discountTerm, (i+1)-1+w ))

        pvsValue = sum(pvs)

        return marketPrice-pvsValue

    fsolve(solver_fuc, 0, xtol=1.5e-10, maxfev=1000000)

    return result[0]

def zspreadHipotecario():
    tenors, yields = interpolated_yield(bond_data_arg_usd, numberOfMonths=400, startMonths=3)
    spotCurve = curve.zeroCurve(np.array(yields) / 100, 1 / 12)
    curveData = {'tenors':tenors, 'spots':spotCurve.values }
    spread = zspread(bono_banco_hipotecario,curveData)
    print('Z-SPREAD {} '.format( spread ))
    return tenors, yields, spotCurve.values, spread

def creditSpreadHipotecario(liquiditySpread):
    tenors, yields, spots, zspread = zspreadHipotecario()
    creditSpread = zspread-liquiditySpread
    print('Credit-SPREAD {} '.format(creditSpread))
    return tenors, yields, spots, creditSpread

def valueBond( spotCurve, zspread, periods=180):
    spotsToUse = np.array(spotCurve[0:periods])+zspread
    denominator = sum([1.0/np.power(1+(aSpot/12.0),i+1) for i,aSpot in enumerate(spotsToUse)])
    numerator = 100 - 100/((1+(spotsToUse[-1]/12.0))**periods)

    return (numerator/denominator)*12.0


def ej3():
    tenors,yields = interpolated_yield(bond_data_cer, numberOfMonths=400, startMonths=1)
    spotCurve = curve.zeroCurve(np.array(yields) / 100, 1 / 12)
    tenorsSov, yieldsSov, spotsSov, creditSpread = creditSpreadHipotecario(securitization['liquidity_spread'])
    zspread = securitization['liquidity_spread'] + securitization['all_in_cost'] + creditSpread
    print("Coupon value {}".format(valueBond(spotCurve.values, zspread)))
    _plotCurves([(tenors, np.array(yields)/100, 'Yield Curve'),(tenors, spotCurve.values, 'Spot Curve'),
                 (tenors, (np.array(spotCurve.values) + zspread), 'Discount Curve')], 'CER Curve')
    _plotCurves([(tenorsSov[5:], np.array(yieldsSov[5:])/100, 'Yield Curve'),(tenorsSov[5:], spotsSov[5:], 'Spot Curve'),], 'Sovereign USD Curve')
    #_plotCurves( tenors, yields, spotCurve.values, 'Yield and Spot curve(CER)' )
    #_plotCurves(tenorsSov[5:], yieldsSov[5:], spotsSov[5:], 'Yield and Spot curve(USD)')
    plt.show()

def _plotCurves( data, name ):
    curvePlot = plt.figure(name)
    thePlot = curvePlot.add_subplot(111)
    thePlot.set_ylim(0, 0.4)
    for d in data:
        thePlot.plot(d[0], d[1] , label=d[2])
    thePlot.legend(loc='upper left')
    plt.xlabel('Tenors')
    plt.ylabel('Tasa')



if __name__ == '__main__':
    ej3()
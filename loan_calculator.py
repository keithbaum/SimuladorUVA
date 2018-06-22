import numpy as np
import datetime
from abc import ABC, abstractmethod
from matplotlib import pyplot as plt

class Inflation(ABC):
    def __init__(self, expectedValue):
        self._expectedValue = expectedValue

    @abstractmethod
    def canHandle(self, year):
        pass

    def monthlyAvgInflation(self):
        return np.power(float(self._expectedValue+1), 1/12.0)-1

class AnualInflation(Inflation):
    def __init__(self, expectedValue, forYear):
        super().__init__(expectedValue)
        self._forYear   = forYear

    def canHandle(self, year):
        return self._forYear == year

class DefaultInflation(Inflation):

    def __init__(self, expectedValue=0.0):
        super().__init__(expectedValue)

    def canHandle(self, year):
        return True

class InflationSchedule:
    def __init__(self, defaultInflation=None):
        defaultInflation = defaultInflation or DefaultInflation()
        self._inflationExpectations = [defaultInflation]

    def addAnualInflation(self, expectedInflation, year):
        self._inflationExpectations.append(AnualInflation(expectedInflation, year))

    def monthlyInflationForYear(self, year):
        theInflation = next(inflation for inflation in reversed(self._inflationExpectations) if inflation.canHandle(year))
        return theInflation.monthlyAvgInflation()


class LoanResult:

    def __init__(self, due, dueNumbers, paymentDetails, totalLoan, remainingLoan, description):
        self.due            = due
        self.dueNumbers     = dueNumbers
        self.paymentDetails = paymentDetails
        self.totalLoan = totalLoan
        self.remainingLoan = remainingLoan
        self.description   = description

    def output(self):
        print("Loan: {}".format(self.totalLoan))
        columns     = ['Due #', 'Loan', 'Amortization', 'IR', 'Due', 'Due Pesos']
        data        = [self._getPaymentDetailsRow(currentDue) for currentDue in range(1,self.dueNumbers+1)]
        row_format  = "{:>15}" * len(columns)
        print(row_format.format(*columns))
        for row in data:
            print(row_format.format(*row))

    def plot(self, otherLoans=None):
        otherLoans = otherLoans or []
        dueNumbers = self.dueNumbersList()
        dueInPesos = self.dueInPesosList()
        curvePlot = plt.figure('Loan')
        thePlot = curvePlot.add_subplot(111)
        thePlot.plot(dueNumbers, dueInPesos, label=self.description)
        for otherLoan in otherLoans:
            dueNumbers = otherLoan.dueNumbersList()
            dueInPesos = otherLoan.dueInPesosList()
            thePlot.plot(dueNumbers, dueInPesos, label=otherLoan.description)
        thePlot.legend(loc='upper left')
        plt.xlabel('N Cuota')
        plt.ylabel('Valor Cuota($)')
        plt.show()

    def dueNumbersList(self):
        return list(range(1, self.dueNumbers + 1))

    def dueInPesosList(self):
        data =  [self._getPaymentDetailsRow(currentDue) for currentDue in self.dueNumbersList()]
        return [float(d[-1]) for d in data]



    def _getPaymentDetailsRow(self, dueNumber):
        roundFunc       = lambda number: '%.2f' % number
        key             = str(dueNumber)
        irPayment       = self.paymentDetails['payment_details'][key]['ir_payment']
        amortPayment    = self.paymentDetails['payment_details'][key]['amort_payment']
        remainingLoan   = self.paymentDetails['payment_details'][key]['remaining_loan']
        duePesos        = self.paymentDetails['payment_details'][key]['due_pesos']
        return [str(dueNumber), roundFunc(remainingLoan), roundFunc(irPayment), roundFunc(amortPayment), roundFunc(self.due), roundFunc(duePesos)]

class LoanCalculator:
    def __init__(self, loan, loanTime, ir, payment='monthly', loanTimeIn='years', startDate=None, inflationSchedule=None,
                 adjustFactor=1, tag='Loan'):
        self.loan           = loan
        self.loanTime       = loanTime
        self.ir             = ir #Should be expressed in loanTime
        self.payment        = payment
        self.loanTimeIn     = loanTimeIn
        self.startDate      = startDate or datetime.datetime.today()
        self.inflationSchedule = inflationSchedule or InflationSchedule()
        self.adjustFactor = adjustFactor
        self.tag            = tag
        self._duesConverter = {'years':{'monthly':12},
                               'monthly':{'monthly':1},
                               'due_numbers':{'due_numbers':1},}

    def _duesCount(self):
        return self.loanTime * self._duesConverter[self.loanTimeIn][self.payment]

    def _dueInPesos(self, dueNumber, previousDueInPesos=None):
        if not previousDueInPesos:
            return self.due()*self.adjustFactor
        monthsInDays = dueNumber*30
        year         = (self.startDate + datetime.timedelta(monthsInDays)).year
        inflation    = self.inflationSchedule.monthlyInflationForYear(year)
        return previousDueInPesos*(1+inflation)

    def _adjustFactor(self, dueNumber, previousCer=None):
        if not previousCer:
            return self.adjustFactor
        monthsInDays = dueNumber*30
        year         = (self.startDate + datetime.timedelta(monthsInDays)).year
        inflation    = self.inflationSchedule.monthlyInflationForYear(year)
        return previousCer*(1+inflation)

    def due(self):
        duesCount = self._duesCount()
        return self.loan * np.divide( np.power(1.0+self.periodIR(),duesCount)*self.periodIR(), np.power(1.0+self.periodIR(),duesCount) - 1 )

    def periodIR(self):
        return self.ir/self._duesConverter[self.loanTimeIn][self.payment]

    def compute(self, dueFinal=None, dueInPesos=None, cer=None):
        maxDue = self._duesCount()
        dueCount = dueFinal or maxDue
        if dueCount > maxDue:
            raise Exception('dueFinal should be < {}'.format(maxDue))
        paymentDetails = {}
        due = self.due()
        periodIR = self.periodIR()
        remainingLoan = self.loan
        paymentDetails.update({'due':due, 'payment_details':{}})
        dueNumber = 1
        while(remainingLoan>0 and dueNumber<=dueCount):
            irPayment           =  remainingLoan*periodIR
            amortizationPayment = due - irPayment
            remainingLoan       = remainingLoan - amortizationPayment
            dueInPesos = self._dueInPesos(dueNumber, dueInPesos)
            cer        = self._adjustFactor(dueNumber, cer)
            if dueNumber == maxDue: #In case of rounding diff
                amortizationPayment+=remainingLoan
                remainingLoan=0.0
            self._addPaymentDetail(paymentDetails, irPayment, amortizationPayment, remainingLoan, dueNumber, dueInPesos, cer )
            dueNumber+=1

        return LoanResult( due, dueCount, paymentDetails, self.loan, remainingLoan, self.tag)

    def reFinance(self, fromDue, refinanceTime, ir=None, payment='monthly', refinanceInTime='years'):
        ir = ir or self.ir
        currentLoan   = self.compute(fromDue)
        remainingLoan = currentLoan.remainingLoan
        lastCer        = currentLoan.paymentDetails['payment_details'][str(fromDue)]['cer']
        newStartTime   = self.startDate + datetime.timedelta(30)*(fromDue+1)
        helper          = LoanCalculator(remainingLoan, refinanceTime, ir, payment, refinanceInTime, startDate=newStartTime, initialCer=lastCer
                                         ,inflationSchedule=self.inflationSchedule)
        return helper.compute()


    def _addPaymentDetail(self, paymentDetails, irPayment, amortizationPayment, remainingLoan, dueNumber, dueInPesos, cer):
        paymentDetails['payment_details']\
            .update({str(dueNumber):{'ir_payment':irPayment, 'amort_payment':amortizationPayment,'remaining_loan':remainingLoan,
                                     'due_pesos':dueInPesos, 'cer':cer}})


def argentinaOptimisticInflationSchedule():
    inflationSchedule= InflationSchedule(DefaultInflation(0.05))
    inflationSchedule.addAnualInflation(0.20, 2016)
    inflationSchedule.addAnualInflation(0.15,2017)
    inflationSchedule.addAnualInflation(0.12,2018)
    inflationSchedule.addAnualInflation(0.10,2019)
    inflationSchedule.addAnualInflation(0.07,2020)

    return inflationSchedule

def argentinaRealisticInflationSchedule():
    inflationSchedule= InflationSchedule(DefaultInflation(0.10))
    inflationSchedule.addAnualInflation(0.403, 2016)
    inflationSchedule.addAnualInflation(0.261,2017)
    inflationSchedule.addAnualInflation(0.30,2018)
    inflationSchedule.addAnualInflation(0.17,2019)
    inflationSchedule.addAnualInflation(0.14,2020)

    return inflationSchedule

def ej1a():
    print("Cer Loan 1.000.000, 5% , 15 year")
    uvaLoanOptimistic = LoanCalculator(1000000/14.053, 15, 0.05, startDate=datetime.date(2016,1,1), inflationSchedule=argentinaOptimisticInflationSchedule(), adjustFactor=14.053, tag='Préstamo UVA 5%, Inflación  Optimista')
    uvaLoanPesimistic = LoanCalculator(1000000/14.053, 15, 0.05, startDate=datetime.date(2016,1,1), inflationSchedule=argentinaRealisticInflationSchedule(), adjustFactor=14.053, tag='Préstamo UVA 5%, Inflación  Realista')
    fixLoan = LoanCalculator(1000000, 15, 0.24, startDate=datetime.date(2016,1,1), tag='Préstamo tasa fija 24%')
    resultLoanCEROptimistic = uvaLoanOptimistic.compute()
    resultLoanCERPesimistic= uvaLoanPesimistic.compute()
    resultFixed = fixLoan.compute()
    resultLoanCEROptimistic.output()
    print("Fix Loan 1.000.000, 24% , 15 year")
    resultFixed.output()
    resultLoanCEROptimistic.plot([resultFixed, resultLoanCERPesimistic])



if __name__ == '__main__':
    ej1a()

import numpy as np

class LoanResult:

    def __init__(self, due, dueNumbers, paymentDetails, totalLoan, remainingLoan):
        self.due            = due
        self.dueNumbers     = dueNumbers
        self.paymentDetails = paymentDetails
        self.totalLoan = totalLoan
        self.remainingLoan = remainingLoan

    def output(self):
        print("Loan: {}".format(self.totalLoan))
        columns     = ['Due #', 'Loan', 'Amortization', 'IR', 'Due']
        data        = [self._getPaymentDetailsRow(currentDue) for currentDue in range(1,self.dueNumbers+1)]
        row_format  = "{:>15}" * len(columns)
        print(row_format.format(*columns))
        for row in data:
            print(row_format.format(*row))

    def _getPaymentDetailsRow(self, dueNumber):
        roundFunc       = lambda number: '%.2f' % number
        key             = str(dueNumber)
        irPayment       = self.paymentDetails['payment_details'][key]['ir_payment']
        amortPayment    = self.paymentDetails['payment_details'][key]['amort_payment']
        remainingLoan   = self.paymentDetails['payment_details'][key]['remaining_loan']
        return [str(dueNumber), roundFunc(remainingLoan), roundFunc(irPayment), roundFunc(amortPayment), roundFunc(self.due)]

class LoanCalculator:
    def __init__(self, loan, loanTime, ir, payment='monthly', loanTimeIn='years'):
        self.loan           = loan
        self.loanTime       = loanTime
        self.ir             = ir #Should be expressed in loanTime
        self.payment        = payment
        self.loanTimeIn     = loanTimeIn
        self._duesConverter = {'years':{'monthly':12},
                               'monthly':{'monthly':1},
                               'due_numbers':{'due_numbers':1},}

    def _duesCount(self):
        return self.loanTime * self._duesConverter[self.loanTimeIn][self.payment]


    def due(self):
        duesCount = self._duesCount()
        return self.loan * np.divide( np.power(1.0+self.periodIR(),duesCount)*self.periodIR(), np.power(1.0+self.periodIR(),duesCount) - 1 )

    def periodIR(self):
        return self.ir/self._duesConverter[self.loanTimeIn][self.payment]

    def compute(self, dueFinal=None):
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
            if dueNumber == maxDue: #In case of rounding diff
                amortizationPayment+=remainingLoan
                remainingLoan=0.0
            self._addPaymentDetail(paymentDetails, irPayment, amortizationPayment, remainingLoan, dueNumber )
            dueNumber+=1

        return LoanResult( due, dueCount, paymentDetails, self.loan, remainingLoan)

    def reFinance(self, fromDue, refinanceTime, ir=None, payment='monthly', refinanceInTime='years'):
        ir = ir or self.ir
        remainingLoan = self.compute(fromDue).remainingLoan
        helper          = LoanCalculator(remainingLoan, refinanceTime, ir, payment, refinanceInTime)
        return helper.compute()


    def _addPaymentDetail(self, paymentDetails, irPayment, amortizationPayment, remainingLoan, dueNumber):
        paymentDetails['payment_details']\
            .update({str(dueNumber):{'ir_payment':irPayment, 'amort_payment':amortizationPayment,'remaining_loan':remainingLoan}})


def main():
    calculator = LoanCalculator(100000, 5, 0.05 )
    result = calculator.compute()
    result.output()
    print("Refinance original loan 2 years from due # 50")
    resultRefinance = calculator.reFinance(50, 2)
    resultRefinance.output()
    print("Refinance original loan 20 dues(monthly) from due #50")
    resultRefinance = calculator.reFinance(50, 20, payment='monthly', refinanceInTime='monthly', ir=0.05/12)
    resultRefinance.output()

if __name__ == '__main__':
    main()

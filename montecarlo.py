from collections import namedtuple
import numpy as np
import datetime

MonteCarloParameters = namedtuple('MonteCarloParameters',['mu','sigma','period'])

class MontecarloCharacterization(object):

    def __init__(self, series, cuts, period):
        self.series = series
        self.cuts = cuts
        self.period = period

    def getYieldsMeanAndSigma(self):
        results = {}
        for cutName, cut in self.cuts.items():
            subSeries = self.getSeriesByCuts(self.series, cut).values
            subSeriesYields = self.getSeriesYields(subSeries)
            results[cutName] = MonteCarloParameters( np.mean(subSeriesYields),
                                                     self.getSigmaEWMA(subSeriesYields,period=self.period),
                                                     self.period)

        return results

    @staticmethod
    def getSeriesByCuts( seriesDF, cut ):
        return seriesDF.loc[ (seriesDF.index<=cut.end) & (seriesDF.index>=cut.start) ]

    @staticmethod
    def getSeriesYields( series ):
        series = np.squeeze( series )
        return np.log( series[1:]/series[:-1] )

    @staticmethod
    def getSigmaEWMA( yields, k=0.97, period=12.0/252):
        initialVariance = np.var(yields, ddof=1)
        iterationFn = lambda k, prevVariance, prevSample: prevVariance * k + (prevSample ** 2) * (1 - k)
        Variance = np.empty(len(yields)+1)
        Variance[0]=initialVariance
        for i, dy in enumerate(yields):
            Variance[i+1]=iterationFn(k, Variance[i], dy)
        condVol = np.sqrt(Variance/period)
        return condVol[-1]



class MonteCarloRunner( object ):

    def __init__(self, monteCarloParameters):
        self.mu = monteCarloParameters.mu
        self.sigma = monteCarloParameters.sigma
        self.period = monteCarloParameters.period

        self.seed = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).microseconds)
        np.random.seed(self.seed)


    def run(self, initialValue, size, iterations=1):
        results =np.empty((iterations,size))
        for iterationNumber in range(iterations):
            iteration=np.empty(size+1)
            iteration[0] = initialValue
            phiVector = np.random.normal(loc=0, scale=1, size=size)
            yieldVector = np.exp(
                (self.mu - (self.sigma ** 2) / 2) * self.period + self.sigma * np.sqrt(self.period) * phiVector)
            for i in range(size):
                iteration[i+1]=iteration[i]*yieldVector[i]

            results[iterationNumber,:]=iteration[1:]

        return np.squeeze( results )

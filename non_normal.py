import numpy as np
from datetime import datetime
from collections import namedtuple
from statsmodels.distributions.empirical_distribution import ECDF
from scipy.interpolate import interp1d

NonGaussianParameters = namedtuple('NonGaussianParameters',['mu','sigma','period','calculator'])

class NonGaussianCharacterization( object ):

    def __init__(self, series, cuts, period):
        self.series = series
        self.cuts = cuts
        self.period = period
        self.seed = (datetime.utcnow() - datetime(1970, 1, 1)).microseconds
        np.random.seed(self.seed)

    def _runCharacterization(self, series):
        #ToDo: NonGaussian characterization
        ecdf = ECDF(series)
        return interp1d(ecdf.y[1:],ecdf.x[1:],fill_value='extrapolate')


    @staticmethod
    def getSeriesByCuts( seriesDF, cut ):
        return seriesDF.loc[ (seriesDF.index<=cut.end) & (seriesDF.index>=cut.start) ]

    @staticmethod
    def getSeriesYields( series ):
        series = np.squeeze( series )
        return np.log( series[1:]/series[:-1] )

    def getInverseECDFs(self):
        results = {}
        for cutName, cut in self.cuts.items():
            subSeries = self.getSeriesByCuts(self.series, cut).values
            subSeriesYields = self.getSeriesYields(subSeries)
            results[cutName] = self._runCharacterization(subSeriesYields)

        return results


def generateRandomVector(calculator,size):
    u = np.random.uniform(0,1,size)
    return calculator(u)
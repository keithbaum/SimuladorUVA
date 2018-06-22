import numpy as np
from collections import namedtuple
import scipy.stats
from functools import partial

NonGaussianParameters = namedtuple('NonGaussianParameters',['mu','sigma','period','calculator'])
distributions = ('norm','t','crystalball','gumbel_l','gumbel_r')

class NonGaussianCharacterization( object ):

    def __init__(self, series, cuts, gaussianParameters):
        self.series = series
        self.cuts = cuts
        self.gaussianParameters = gaussianParameters

    def _runCharacterization(self, series, distribution='t'):
        distrib = getattr(scipy.stats,distribution)
        args = list( distrib.fit(data=series) )
        args[-2:]=(0,1)     #mu and sigma locked to 0,1 because montecarlo will scale it
        return partial( distrib.rvs, *args )


    @staticmethod
    def getSeriesByCuts( seriesDF, cut ):
        return seriesDF.loc[ (seriesDF.index<=cut.end) & (seriesDF.index>=cut.start) ]

    @staticmethod
    def getSeriesYields( series ):
        series = np.squeeze( series )
        return np.log( series[1:]/series[:-1] )

    def getCalculators(self, distrib):
        results = {}
        for cutName, cut in self.cuts.items():
            subSeries = self.getSeriesByCuts(self.series, cut).values
            subSeriesYields = self.getSeriesYields(subSeries)
            results[cutName] = self._runCharacterization(subSeriesYields,distrib)

        return results


def generateRandomVector(calculator,size):
    return calculator(size=size)
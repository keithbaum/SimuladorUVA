from collections.__init__ import namedtuple
from datetime import datetime
import pandas as pd
import numpy as np

Cut = namedtuple('corte',['start','end'])

class Cuts( object ):
    argentinaCuts = {
        'hiperinflacion': Cut(datetime(year=1980, month=1, day=1), datetime(year=1991, month=3, day=1)),
        'convertibilidad': Cut(datetime(year=1991, month=4, day=1), datetime(year=1999, month=12, day=1)),
        'crisisYrecuperacion': Cut(datetime(year=2000, month=1, day=1), datetime(year=2003, month=4, day=1)),
        'kirchner': Cut(datetime(year=2003, month=5, day=1), datetime(year=2015, month=12, day=1)),
        'macri': Cut(datetime(year=2016, month=1, day=1), datetime(year=2018, month=3, day=1)),
    }

    CUT_NAMES_IN_ORDER = ['hiperinflacion', 'convertibilidad', 'crisisYrecuperacion', 'kirchner', 'macri']

    def __init__(self):
        self.transitionProbabilityMatrix = pd.DataFrame(columns=self.CUT_NAMES_IN_ORDER,
                                                   index=self.CUT_NAMES_IN_ORDER)
        self.populateTransitionMatrix()
        self.seed = int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds())
        np.random.seed(self.seed)

    def cutTransition(self, originalCut):
        posibleTransitions = self.transitionProbabilityMatrix.loc[originalCut,:].values
        sample = np.random.uniform(0,1)
        for i in range(len(posibleTransitions)):
            if sample <= np.sum(posibleTransitions[:i+1]):
                return self.CUT_NAMES_IN_ORDER[i]

    def populateTransitionMatrix(self):
        self.transitionProbabilityMatrix.loc['hiperinflacion', 'hiperinflacion']= 0.10
        self.transitionProbabilityMatrix.loc['hiperinflacion','convertibilidad']= 0.20
        self.transitionProbabilityMatrix.loc['hiperinflacion', 'crisisYrecuperacion'] = 0.40
        self.transitionProbabilityMatrix.loc['hiperinflacion', 'kirchner'] = 0.10
        self.transitionProbabilityMatrix.loc['hiperinflacion', 'macri'] = 0.20

        self.transitionProbabilityMatrix.loc['convertibilidad', 'hiperinflacion'] = 0.05
        self.transitionProbabilityMatrix.loc['convertibilidad', 'convertibilidad'] = 0.30
        self.transitionProbabilityMatrix.loc['convertibilidad', 'crisisYrecuperacion'] = 0.30
        self.transitionProbabilityMatrix.loc['convertibilidad', 'kirchner'] = 0.05
        self.transitionProbabilityMatrix.loc['convertibilidad', 'macri'] = 0.30

        self.transitionProbabilityMatrix.loc['crisisYrecuperacion', 'hiperinflacion'] = 0.05
        self.transitionProbabilityMatrix.loc['crisisYrecuperacion', 'convertibilidad'] = 0.10
        self.transitionProbabilityMatrix.loc['crisisYrecuperacion', 'crisisYrecuperacion'] = 0.10
        self.transitionProbabilityMatrix.loc['crisisYrecuperacion', 'kirchner'] = 0.70
        self.transitionProbabilityMatrix.loc['crisisYrecuperacion', 'macri'] = 0.05

        self.transitionProbabilityMatrix.loc['kirchner', 'hiperinflacion'] = 0.20
        self.transitionProbabilityMatrix.loc['kirchner', 'convertibilidad'] = 0.10
        self.transitionProbabilityMatrix.loc['kirchner', 'crisisYrecuperacion'] = 0.15
        self.transitionProbabilityMatrix.loc['kirchner', 'kirchner'] = 0.40
        self.transitionProbabilityMatrix.loc['kirchner', 'macri'] = 0.25

        self.transitionProbabilityMatrix.loc['macri', 'hiperinflacion'] = 0.20
        self.transitionProbabilityMatrix.loc['macri', 'convertibilidad'] = 0.10
        self.transitionProbabilityMatrix.loc['macri', 'crisisYrecuperacion'] = 0.15
        self.transitionProbabilityMatrix.loc['macri', 'kirchner'] = 0.20
        self.transitionProbabilityMatrix.loc['macri', 'macri'] = 0.35





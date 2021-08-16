from .flowheadrelationsfactory import FlowHeadRelationsFactory

from XPSS.pss.db.units import LengthUnits, FlowUnits

from XPSS.logger import Logger

logger = Logger(debug=True)

@FlowHeadRelationsFactory.register('HazenWilliams')
def HazenWilliams(d=None, L=None, C=None, **ignored):
    """
    Hazen-Williams equation for friction losses in pipe.

    ref:  https://www.engineeringtoolbox.com/hazen-williams-water-d_797.html

    h = 0.2083*(L/C)^1.852*Q^13852/(d^4.8655)

    Parameters
    ----------

    Q : array_like
        Flowrate [gpm]

    d : array_like
        Pipe inner diameter [in]

    L : array_like
        Pipe length [ft]

    C : array_like
        Hazen-Wiliams friction loss coefficient

    Returns
    -------

    h_fn : method
        Function that returns the head loss [ft] corresponding to a specified
        flowrate.

    """

    d = d.to("inch").magnitude
    L = L.to("feet").magnitude
    # C = self.C(pssvars)

    logger.debugger("diameter shape: "+str(d.shape))
    logger.debugger("length shape: "+str(L.shape))
    logger.debugger("C-factor shape: "+str(C.shape))

    def h_fn(Q):
        Q = Q.to(FlowUnits["gpm"])
        fl_ = (0.2083*(L/C)**1.852*Q**1.852/(d**4.8655)).magnitude
        return (fl_*LengthUnits['ft']).to_base_units()

    return h_fn

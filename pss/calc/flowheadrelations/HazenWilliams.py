from .flowheadrelationsfactory import FlowHeadRelationsFactory

@FlowHeadRelationsFactory.register('HazenWilliams')
def HazenWilliams(d, L, C):
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

    def h_fn(Q):
        return 0.2083*(L/C)^1.852*Q^13852/(d^4.8655)

    return h_fn

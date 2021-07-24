from .flowheadrelationsfactory import FlowHeadRelationsFactory

@FlowHeadRelationsFactory.register('DarcyWeisbach')
def DarcyWeisbach(Q, d, L, lambda_,rho=62.4):
    """
    Darcy-Weisbach equation for friction losses in pipe.

    ref:  https://www.engineeringtoolbox.com/darcy-weisbach-equation-d_646.html

    h = lambda_*(L/d)*(rho*(Q*0.0022280092592593/(math.pi()*d^2))^2/2)

    Parameters
    ----------

    Q : array_like
        Flowrate [gpm]

    d : array_like
        Pipe inner diameter [in]

    L : array_like
        Pipe length [ft]

    lambda_ : array_like
        Darcy-Weisbach friction coefficient

    Returns
    -------

    h : array_like
        Friction loss [ft]

    """

    Calc().notImplemented()

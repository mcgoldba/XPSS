from XPSS.logger import Logger

logger = Logger(debug=False)

def _Q(nOpEDU, flowrate):
    """
    Calculates the flowrate in a pipe based on the number of operating EDUs

    Parameters
    ----------

    nOpEDU : np.array_like
        THe number of operating edus

    flowrate : float
        The pump flowrate

    Returns
    -------

    Q : np.array_like
        The flowrate within each pipe

    """
    #TODO: Implement as Factory Method

    logger.debugger("nOpEDU shape: "+str(nOpEDU.shape))
    logger.debugger("flowrate: "+str(flowrate.magnitude))

    return (nOpEDU*flowrate.magnitude)*flowrate.units

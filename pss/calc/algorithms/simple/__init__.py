from .F import F
from userInpouts import lossformula

def simple(PipeMesh, NodeMesh, A, lossformula):
    """
    Solve the pipe network using the simple algorithm.

    Parameters
    ----------

    PipeMesh : (N,) array
        Matrix of pipe properties

    NodeMesh : (M,) array
        Matrix of node properties

    A : (N,N) array
        (Square) Indicidence matrix defining the geometry of the system.
        Contains a row for each junction and a column for each pipe.  (i.e. The
        incidence matrix without the first row designating the location of the
        reservior).  Assumes a directed tree graph geometry
    """
    #1. Initial pressures and flowrates are evaluated based on EPA equation and
    #   static head.  Values are stored in 'NodeMesh'

    #2. Momentum predictor (i.e. calculate the approximate / guessed flow)

    #- Build the F matrix:
    #   - If end node:  F is functional form of pump curve
    #   - else:  F is the specified friction loss formula (e.g. Hazen-Wiliams,
    #       Darcy-Wiesbach)

    Q = PipeMesh['Flowrate [gpm]']

    dp = dp(Q, A, lossformula)

    #3. Pressure correction

from scipy.sparse import linalg

def linearsolver(A, b, method="direct", **kwargs):
    """
    Solve the linear system, Ax=b, using the scipy library

    Parameters
    ----------

    A: {sparse matrix}
        The real or complex N-by-N mtarix of the linear system.

    b: {array, matrix}
        The right hand side of the linear system.  has shape (N,) or (N,1)

    Returns
    -------
    x: {array, matrix}
        The converged solution.

    info: {int}
        Convergence information.  0: Sucessful exit; >0 convergence to tolerance
        not acheived, number of iterations; <0 illegal input or breakdown.

    """


    callDict = {
        'direct': linalg.spsolve, # Direct solver
        'bicg': linalg.bicg, # Biconjugate gradient iterator
        'bicgstab': linalg.bicgstab, # Biconjugate gradient stabalized iterator
        'cg': linalg.cg, #Conjugae gradient iterator (Symmetric matrices)
        'cgs': linalg.cgs, # Conjugate gradient squared iterator (Symmetric matrices)
        'gmres': linalg.gmres, # Generalized minimal residual iterator
        'lgmres': linalg.lgmres,
        'minres': linalg.minres, # Minimum residual iterator
        'qmr': linalg.qmr, # quasi-minimal residual iterator
        'gcrotmk': linalg # flexible GCROT algorithm
    }

    return callDict[method](A, b, **kwargs)

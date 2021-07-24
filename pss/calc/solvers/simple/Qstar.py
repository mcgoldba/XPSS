def Qstar(Q, A, P, lossformula):
    """
    Build the vector of flow-head relations
    """
    end_pipes = get_end_pipes(A)

    pcurve = PumpCurve(pump_database, pump_model)

    return [PumpCurve(P[i]) if end_pipes[i] else LossFormula[lossformula](P[i])
           for i in range(end_pipes)]

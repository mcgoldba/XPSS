def PumpCurve(self, pump_database, pump_model):
    """
    Reads pump curve info stored as excel file, and return a functional
    description of the pump curve as H = f(Q).

    Parameters
    ----------
        pump_database : str
            The file name of the excel file containing pump curve
            information.  Database should store data for each pump as a
            separate sheet, with the sheet name specified as the pump
            model number.  Tabular data header information is located on
            line 6 with.  The first 5 lines of the sheet are ignored.

        pump_model : str
            The specific pump model for which to get data.  This
            should match the sheet name exactly.
    Returns
    -------
        curve_fn: method
            function that provides the pump curve flow for a given head
    """

    #interpolate pump table data to get a continuous curve

    pcurve = pd.read_excel(pump_database, sheet_name=pump_model)

    pflow = pcurve['Flow [gpm]'].to_numpy(float)
    phead = pcurve['Head [ft]'].to_numpy(float)

    curve_fn = interp1d(phead, pflow)

    return curve_fn

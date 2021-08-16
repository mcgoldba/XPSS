import pandas as pd

def get_pump_curve(self, pump_database, pump_model):
    """ {Function}
            Reads pump curve info stored as excel file, and stores ad pandas dataframe.
        {Variables}
            pump_database:
                (str) The file name of the excel file containing pump curve
                information.  Database should store data for each pump as a
                separate sheet, with the sheet name specified as the pump
                model number.  Tabular data header information is located on
                line 6 with.  The first 5 lines of the sheet are ignored.

            pump_model:
                (str) The specific pump model for which to get data.  This
                should match the sheet name exactly.
        {Outputs}
            pcurve:
                (pandas.DataFrame)  The pump curve info as a pandas
                dataframe.
    """

    pcurve = pd.read_excel(pump_database, sheet_name=pump_model, header=5)

    self.log_debug("Pump curve dataframe:\n"+str(pcurve))

    return pcurve

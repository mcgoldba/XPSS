class HeadLossCalc:
    def __init__(self, flow, dia_i, lossFactor):
        self.flow = flow
        self.dia_i = dia_i
        self.lossFactor = lossFactor
    
    def hazenWilliams(self):
        #  flow = flowrate [gpm]
        #  dia_i = inner diameter [inches]
        #  lossFactor = Hazen-Willams C factor [-] 
        
        loss = 0.2083*(100/lossFactor)^1.852*flow^1.852/(dia_i^4.8655)
        
        return loss
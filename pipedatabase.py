from enum import Enum, auto

class PipeMaterial(Enum):
    PVC = auto()
    HDPE = auto()
#PipeMaterialName = {}
#PipeMaterialName[PipeMaterial.PVC] = 'PVC'
#PipeMaterialName[PipeMaterial.HDPE] = 'HDPE'

class PipeClass(Enum):
    PVC_Sch40 = auto()
    HDPE_DR11 = auto()
#PipeClassName = {}
#PipeClassName[PipeClass.PVC_Sch40] = 'PVC Sch. 40'
#PipeClassName[PipeClass.HDPE_DR11] = 'HDPE DR11'

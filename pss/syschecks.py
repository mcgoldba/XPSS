class SysChecks(object):
# Singleton class: https://python-patterns.guide/gang-of-four/singleton/
    _instance = None
    # sysGeomErr = None
    # numEntityErr = None
    # nPipes = None
    # nNodes = None

    def __new__(cls, sysGeomErr=None, numEntityErr=None,
                 nPipes=None, nNodes=None):
        if cls._instance is None:
            cls._instance = super(SysChecks, cls).__new__(cls)
            cls._instance.sysGeom

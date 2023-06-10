from qgis.PyQt.QtCore import QSettings


class Config:
    """
    LocationFinder configuration:
    - url (str): the service base URL (required)
    - filter (str): value for filter parameter (optional)
    - sref (int|str): response spatial reference (optional)
    - limit (int): value for limit parameter (optional)
    - autoQuery (bool): lookup while typing query (off: only on Enter)
    - debugMode (bool): be more verbose on the QGIS protocol
    """


    def __init__(self):
        """Initialise a new config instance with default values"""
        self.url = None
        self.filter = None
        self.sref = None
        self.limit = -1
        self.autoQuery = False
        self.debugMode = False


    def __repr__(self):
        return f"Config url={self.url}, autoQuery={self.autoQuery}, debugMode={self.debugMode}"


    def load(self):
        settings = QSettings()
        self.url = getStr(settings, "locationfinder/serviceUrl")
        self.filter = getStr(settings, "locationfinder/filter")
        self.sref = getStr(settings, "locationfinder/sref")
        self.limit = getInt(settings, "locationfinder/limit") or -1
        self.autoQuery = getFlag(settings, "locationfinder/autoQuery")
        self.debugMode = getFlag(settings, "locationfinder/debugMode")


    def save(self):
        settings = QSettings()
        settings.setValue("locationfinder/serviceUrl", self.url)
        settings.setValue("locationfinder/filter", self.filter)
        settings.setValue("locationfinder/sref", self.sref)
        settings.setValue("locationfinder/limit", self.limit)
        settings.setValue("locationfinder/autoQuery", self.autoQuery)
        settings.setValue("locationfinder/debugMode", self.debugMode)


def getFlag(settings: QSettings, key: str):
    value = settings.value(key, False)
    if value is None: return None
    if type(value) is bool: return value
    value = str(value).lower()
    return value in ["true", "on", "1", "enable", "enabled"]


def getInt(settings: QSettings, key: str):
    value = settings.value(key)
    if value is None: return None
    if type(value) is int: return value
    return int(value)


def getStr(settings: QSettings, key: str):
    value = settings.value(key)
    if value is None: return None
    text = value if type(value) else str(value)
    return None if len(text) < 1 else text

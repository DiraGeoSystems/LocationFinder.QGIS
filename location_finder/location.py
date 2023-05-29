
class Location:
    """
    Represents a single location returned by a LocationFinder query:
    each Location has a name and a type (both strings), coordinates
    cx,cy (both float) and/or a bounding box xmin,ymin,xmax,ymax (all
    float), and an optional spatial reference ID sref (int)
    """

    def __init__(self, id, kind, name):
        """Initialise a new location instance; must pass
        id (int), type (str), and name (str) arguments"""
        assert type(id) is int
        assert type(kind) is str
        assert type(name) is str
        self.id = id
        self.type = kind
        self.name = name
        self.sref = None  # set via setCenter and/or setExtent
        self.cx = self.cy = 0.0
        self.xmin = self.ymin = self.xmax = self.ymax = None

    def setCenter(self, cx, cy, sref=None):
        self.cx = cx
        self.cy = cy
        if sref is not None:
            assert self.sref is None or self.sref == sref
            self.sref = sref
        return self

    def hasCenter(self):
        return self.cx is not None and self.cy is not None

    def setExtent(self, xmin, ymin, xmax, ymax, sref=None):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        if sref is not None:
            assert self.sref is None or self.sref == sref
            self.sref = sref
        return self

    def hasExtent(self):
        return (self.xmin is not None and self.ymin is not None and
                self.xmax is not None and self.ymax is not None)

    def __repr__(self):
        return f"Location {self.id}: type={self.type}, name={self.name}"

    def __str__(self):
        return f"{self.name} ({self.type})"

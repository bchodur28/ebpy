
from enum import Enum

class MeshBackend(str, Enum):
    BMESH = "BMESH"
    AUTO = "AUTO"
    FAST = "FAST"
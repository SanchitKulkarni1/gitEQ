from enum import Enum

class ChatIntent(str, Enum):
    STRUCTURE = "structure"
    CHANGE_IMPACT = "change_impact"
    ARCHITECTURE = "architecture"
    STRESS = "stress"
    CODE_LOOKUP = "code_lookup"
    UNKNOWN = "unknown"

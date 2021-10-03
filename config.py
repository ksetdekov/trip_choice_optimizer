from enum import Enum


class States(Enum):
    S_START = "0"
    S_ENTER_DAY = "1"
    S_COUNTRY_OR_REGION = "2"
    S_ENTER_COUNTRY_OR_REGION = "3"
    S_ENTER_FIELD_LIST = "4"

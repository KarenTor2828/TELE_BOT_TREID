from enum import Enum
import os
token = os.environ.get('Token')
db_file = 'database.vdb'


class States(Enum):
    S_START = "1"
    S_ENTER_FIRM = "2"
    S_CHOOSE_FIRM = "3"
    S_ENTER_NUM_NEWS = "4"
    S_ENTER_END_NEWS = "5"
import conf
from vedis import Vedis
from vedis import Vedis


def get_current_state(user_id):
    with Vedis(conf.db_file) as db:
        try:
            return db[user_id].decode()
        except KeyError:
            return conf.States.S_START.value


def get_current_property(user_state):
    with Vedis(conf.db_file) as db:
        try:
            return db[user_state].decode()
        except KeyError:
            return False


def del_state(user_id):
    with Vedis(conf.db_file) as db:
        try:
            del (db[user_id])
            return True
        except:
            return False


def set_state(user_id, value):
    with Vedis(conf.db_file) as db:
        try:
            db[user_id] = value
            return True
        except:
            return False


def set_property(user_state, value):
    with Vedis(conf.db_file) as db:
        try:
            db[user_state] = value
            return True
        except:
            return False

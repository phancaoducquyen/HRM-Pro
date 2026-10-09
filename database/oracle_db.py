import oracledb
from config import ORACLE_USER, ORACLE_PASSWORD, ORACLE_DSN


def get_oracle_connection():
    return oracledb.connect(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=ORACLE_DSN
    )

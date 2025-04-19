import datetime

import pandas as pd


MKT_OPEN: datetime.time = datetime.time(13, 30)
MKT_CLOSE: datetime.time = datetime.time(20, 0)


def is_mkt_open(ts: pd.Timestamp) -> bool:
    return ts.weekday() < 5 and MKT_OPEN <= ts.time() <= MKT_CLOSE

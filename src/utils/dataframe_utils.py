from collections.abc import Iterable
from typing import Any

import pandas as pd


def make_dataframe(rows: Iterable[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(list(rows))
    return df if not df.empty else pd.DataFrame()

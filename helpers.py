from typing import List
from typing import Optional

import pandas as pd


def join_csvs(file_paths: List[str], output_path: str, sort_by: Optional[str] = None) -> None:
    dfs: List[pd.DataFrame] = [pd.read_csv(fp) for fp in file_paths]
    df = pd.concat(dfs, ignore_index=True)
    if sort_by:
        df = df.sort_values(by=sort_by, ascending=True)
    df.to_csv(output_path, index=False)

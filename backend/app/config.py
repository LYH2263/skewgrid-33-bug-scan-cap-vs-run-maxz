import os
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", "./data")).resolve()
DB_PATH = DATA_DIR / "skewgrid.db"

# 扫描实际使用的 max_z 永远不超过这个上限，即使 settings 里缺失或被写坏。
SCAN_MAX_Z_CAP_DEFAULT = 6
# valid_coord 允许的最大 zoom，防止设置被写成天文数字。
SCAN_MAX_Z_CAP_HARD_MAX = 8

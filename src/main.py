import os
import sys

from src.actions import save_kingdoms_data, save_kvk_data, save_kvk_history_data, save_match_data, update_kvk_info, update_next_run_time
from src.utility import (
    check_tokens
)

HANDLERS = {
    "save_kvk_data": save_kvk_data,
    "save_match_data": lambda: save_match_data(*sys.argv[1:3]),
    "save_kingdoms_data": lambda: save_kingdoms_data(*sys.argv[1:3]),
    "update_next_run_time": update_next_run_time,
    "save_kvk_history_data": save_kvk_history_data,
    "update_kvk_info": update_kvk_info,
}


def main():
    mode = os.environ.get("MODE")
    if not mode:
        raise RuntimeError("MODE environment variable is required.")
    check_tokens()
    handler = HANDLERS.get(mode)
    if not handler:
        raise RuntimeError(f"Unsupported MODE: {mode}")
    handler()


if __name__ == "__main__":
    main()

import sys
from engine_core import run_engine

if __name__ == "__main__":
    cam_arg = sys.argv[1] if len(sys.argv) > 1 else "0"
    run_engine(auto=True, source_arg=cam_arg)

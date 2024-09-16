import pathlib
import os

def sibpath(fname):
    """Resolve fname to an absolute path corresponding to the file in the
    same directory as this file which has the given fname.
    """
    pwd = Path(__file__).parent.resolve()
    path = os.path.join(pwd, fname)
    return path

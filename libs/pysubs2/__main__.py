import sys
from .cli import Pysubs2CLI

if __name__ == "__main__":
    cli = Pysubs2CLI()
    rv = cli(sys.argv[1:])
    sys.exit(rv)

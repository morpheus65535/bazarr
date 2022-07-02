import os
import logging

os.environ["NO_CLI"] = "true"
os.environ["SZ_USER_AGENT"] = "test"

logging.getLogger("rebulk").setLevel(logging.WARNING)

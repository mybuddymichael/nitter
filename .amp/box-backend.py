#!/usr/bin/env python3
"""Run Nitter with private data and the Box deployment's current origin."""

import configparser
import json
import os
from pathlib import Path
from urllib.parse import urlsplit


root = Path(__file__).resolve().parent.parent
data = Path(os.environ["AMP_DEPLOYMENT_DATA_DIRECTORY"])
origin = urlsplit(os.environ["AMP_DEPLOYMENT_URL"])

configuration = configparser.ConfigParser(interpolation=None)
configuration.optionxform = str
with (data / "nitter.conf").open() as source:
    configuration.read_file(source)

# Preserve the imported configuration except for deployment-specific addresses.
configuration["Server"].update(
    hostname=json.dumps(origin.netloc),
    https=str(origin.scheme == "https").lower(),
    address='"127.0.0.1"',
    port="18080",
    staticDir=json.dumps(str(root / "public")),
)
configuration["Cache"].update(redisHost='"127.0.0.1"', redisPort="16379")

os.umask(0o077)
runtime_configuration = data / "runtime.conf"
with runtime_configuration.open("w") as destination:
    configuration.write(destination)
runtime_configuration.chmod(0o600)

os.environ["NITTER_CONF_FILE"] = str(runtime_configuration)
os.environ["NITTER_SESSIONS_FILE"] = str(data / "sessions.jsonl")
os.environ["LD_LIBRARY_PATH"] = str(root / "box-runtime")
os.chdir(root)
os.execv(str(root / "nitter"), [str(root / "nitter")])

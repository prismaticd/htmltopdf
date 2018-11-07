#!/usr/bin/env python
# -*- coding: utf-8 -*-


import subprocess
import os
import sys
import json
import yaml
from pathlib import Path

os.environ["CLOUDSDK_PYTHON"] = sys.executable
gcloud_executable = os.environ.get("GCLOUD_PATH", "/home/benoit/tmp/google-cloud-sdk/bin/gcloud")
os.chdir(os.path.dirname(os.path.abspath(__file__)))

config = {}
with Path("headless_config.yml").open() as f:
    y = yaml.safe_load(f)
    config = y.get("environment").get("staging")


def get_last_commit():
    res = subprocess.run(["git", "log", "-n1", "--pretty=%H", "."], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        res.check_returncode()
    except subprocess.CalledProcessError:
        print(res.stderr)
        raise

    return res.stdout.decode("utf-8").strip()


def run_gcloud(*args: [str]) -> dict:
    res = subprocess.run(
        [gcloud_executable, "--format=json"] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    try:
        res.check_returncode()
    except subprocess.CalledProcessError:
        print(res.stderr)
        raise

    loaded = json.loads(res.stdout)

    return loaded


last_commit = get_last_commit()

a = run_gcloud(f"--project={config.get('project')}", "functions", "describe", config.get("function_name"))
if a.get("labels").get("commit") != last_commit:
    print("New commit in headless_chrome")

    a = run_gcloud(
        f"--project={config.get('project')}",
        "functions",
        "deploy",
        config.get("function_name"),
        f"--entry-point={config.get('entrypoint', 'main')}",
        "--runtime=python37",
        "--trigger-http",
        f"--region={config.get('region')}",
        f"--update-labels=commit={last_commit}",
        f"--memory={config.get('memory')}",
    )
    import pprint

    pprint.pprint(a)
else:
    print("Already deployed")

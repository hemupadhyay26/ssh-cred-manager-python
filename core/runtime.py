"""Environment for system tools launched from a frozen application."""
import os
import sys


def external_environment():
    environment = os.environ.copy()
    if getattr(sys, "frozen", False):
        original = environment.get("LD_LIBRARY_PATH_ORIG")
        if original is not None:
            environment["LD_LIBRARY_PATH"] = original
        else:
            environment.pop("LD_LIBRARY_PATH", None)
    return environment

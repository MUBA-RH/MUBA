"""Deprecated compatibility import.

The production implementation is the modular muba_core package reached through
muba_brain. This file remains only so historical deployments fail safely rather
than loading an obsolete monolith.
"""
from muba_brain import *  # noqa: F401,F403

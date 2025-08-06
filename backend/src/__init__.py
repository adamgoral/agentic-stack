"""Agentic Stack - Multi-agent orchestration system."""

__version__ = "1.0.0"
__author__ = "Adam"

# Make src a proper package
from . import api, application, core, domain, infrastructure

__all__ = [
    "api",
    "application",
    "core",
    "domain",
    "infrastructure",
    "__version__",
    "__author__",
]
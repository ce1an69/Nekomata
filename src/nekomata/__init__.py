"""Nekomata — Pixel-art cat tarot divination app."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("nekomata-tarot")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

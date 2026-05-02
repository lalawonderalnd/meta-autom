"""Selectors package."""

from accfarm_ig.selectors.registry import IGSelectors, get_selectors, register_selectors

__all__ = ["IGSelectors", "get_selectors", "register_selectors"]

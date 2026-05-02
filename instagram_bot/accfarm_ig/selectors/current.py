"""Current/latest IG selectors - always points to the latest known working version."""

from accfarm_ig.selectors.registry import IGSelectors

# This module re-exports the current/default selectors
# Update this when IG releases a major UI change

current_selectors = IGSelectors()

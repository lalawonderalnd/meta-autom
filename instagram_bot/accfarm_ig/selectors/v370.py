"""IG v370.x.x specific selectors."""

from accfarm_ig.selectors.registry import IGSelectors

# v370 has some updated selectors compared to v360

v370_selectors = IGSelectors(
    # Override selectors that changed in v370
    story_tray="com.instagram.android:id/story_tray",  # Changed from reel_recycler_view
    # Add any other v370-specific overrides here
)

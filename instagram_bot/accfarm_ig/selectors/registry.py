"""Instagram UI selectors registry - maps IG version to resource IDs."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class IGSelectors:
    """Resource IDs and text patterns for a specific IG version range."""

    # Navigation tabs
    home_tab: str = "com.instagram.android:id/tab_home"
    explore_tab: str = "com.instagram.android:id/tab_explore"
    reels_tab: str = "com.instagram.android:id/tab_reels"
    profile_tab: str = "com.instagram.android:id/tab_profile"

    # Feed elements
    feed_recycler: str = "com.instagram.android:id/feed_recycler_view"
    story_tray: str = "com.instagram.android:id/reel_recycler_view"

    # Post interaction buttons (within post container)
    like_button: str = "com.instagram.android:id/like_button_icon"
    save_button: str = "com.instagram.android:id/save_button_icon"
    comment_button: str = "com.instagram.android:id/comment_button_icon"
    share_button: str = "com.instagram.android:id/share_button_icon"

    # Follow buttons
    follow_button_text: tuple[str, ...] = ("Follow", "Folgen", "Suivre", "Seguir", "Segui", "Volgen")
    unfollow_button_text: tuple[str, ...] = ("Following", "Folgst", "Abonné", "Siguiendo", "Segui già")

    # Creation flow
    new_post_button: str = "com.instagram.android:id/action_bar_new_post_button"
    create_reel_button: str = "com.instagram.android:id/clips_creation_button"

    # Search
    search_input: str = "com.instagram.android:id/search_edit_text"
    search_results: str = "com.instagram.android:id/search_results_list"

    # Profile elements
    profile_username: str = "com.instagram.android:id/profile_header_username"
    profile_followers: str = "com.instagram.android:id/profile_header_followers"
    profile_following: str = "com.instagram.android:id/profile_header_following"
    profile_posts_count: str = "com.instagram.android:id/profile_header_posts"
    profile_bio: str = "com.instagram.android:id/profile_header_biography"
    profile_grid: str = "com.instagram.android:id/profile_content_feed"

    # Notifications
    notifications_list: str = "com.instagram.android:id/notification_list"

    # DM / Messages
    messages_inbox: str = "com.instagram.android:id/direct_inbox_list"
    message_compose: str = "com.instagram.android:id/compose_button"
    message_input: str = "com.instagram.android:id/message_composer_edit_text"
    message_send: str = "com.instagram.android:id/send_button"

    # Comment input
    comment_input: str = "com.instagram.android:id/comment_composer_edit_text"
    comment_post: str = "com.instagram.android:id/post_comment_button"

    # Caption input (for posting)
    caption_input: str = "com.instagram.android:id/caption_edit_text"
    share_button_post: str = "com.instagram.android:id/share_button"

    # Checkpoint / warning screens
    dialog_title: str = "com.instagram.android:id/dialog_title"
    dialog_message: str = "com.instagram.android:id/dialog_message"
    dialog_positive_button: str = "com.instagram.android:id/button_primary"
    dialog_negative_button: str = "com.instagram.android:id/button_secondary"

    # Gallery picker (for posting)
    gallery_grid: str = "com.instagram.android:id/gallery_picker_grid"
    gallery_item: str = "com.instagram.android:id/gallery_item_image"

    # Progress indicators
    upload_progress: str = "com.instagram.android:id/upload_progress"
    loading_spinner: str = "com.instagram.android:id/loading_spinner"

    # Tab bar container
    tab_bar: str = "com.instagram.android:id/tab_bar"

    # Extra selectors for various flows
    more_options: str = "com.instagram.android:id/more_options"
    settings: str = "com.instagram.android:id/settings_button"
    edit_profile: str = "com.instagram.android:id/edit_profile_button"
    change_photo: str = "com.instagram.android:id/change_profile_photo"

    # Hashtag browsing
    hashtag_posts: str = "com.instagram.android:id/hashtag_feed"
    hashtag_top_posts: str = "com.instagram.android:id/top_posts_section"
    hashtag_recent_posts: str = "com.instagram.android:id/recent_posts_section"

    # Explore page
    explore_grid: str = "com.instagram.android:id/explore_grid"

    def __post_init__(self):
        # Validate that required fields are set
        pass


# Registry of selectors by IG version range
SELECTORS_BY_VERSION: dict[str, IGSelectors] = {
    "v370.x.x": IGSelectors(
        # v370 has slightly different IDs
        feed_recycler="com.instagram.android:id/feed_recycler_view",
        story_tray="com.instagram.android:id/story_tray",
    ),
    "v360.x.x": IGSelectors(
        # v360 baseline
        feed_recycler="com.instagram.android:id/feed_recycler_view",
    ),
}

# Default/fallback selectors - always points to latest known working version
CURRENT_SELECTORS = IGSelectors()


def get_selectors(ig_version: str | None = None) -> IGSelectors:
    """
    Get selectors for the given IG version.

    Args:
        ig_version: Version string like "370.0.0.23.109" or None/unknown

    Returns:
        IGSelectors instance for the matching version range
    """
    if not ig_version or ig_version == "unknown":
        logger.warning("Unknown IG version, using current/default selectors")
        return CURRENT_SELECTORS

    # Extract major version number
    try:
        major_version = int(ig_version.split(".")[0])
    except (ValueError, IndexError):
        logger.warning(f"Could not parse IG version: {ig_version}, using defaults")
        return CURRENT_SELECTORS

    # Match to known version ranges
    if major_version >= 370:
        return SELECTORS_BY_VERSION.get("v370.x.x", CURRENT_SELECTORS)
    elif major_version >= 360:
        return SELECTORS_BY_VERSION.get("v360.x.x", CURRENT_SELECTORS)
    else:
        logger.warning(f"IG version {ig_version} is older than supported ranges")
        return CURRENT_SELECTORS


def register_selectors(version_range: str, selectors: IGSelectors) -> None:
    """Register new selectors for a version range (used by update_selectors.py script)."""
    SELECTORS_BY_VERSION[version_range] = selectors
    logger.info(f"Registered selectors for version range: {version_range}")

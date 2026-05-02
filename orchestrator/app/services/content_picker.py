"""Content picker - selects next content_item for an account."""

import random
from datetime import datetime, timezone
from uuid import UUID


class ContentPicker:
    """Selects the next content item for an account to post."""

    def __init__(self, db):
        self.db = db

    async def pick_next(
        self,
        account_id: UUID,
        niche: str | None = None,
        kind: str = "post",
    ) -> dict | None:
        """
        Pick the next content item for an account.

        Considers:
        - Account's niche
        - Content not yet posted by this account
        - Content not quarantined
        - Variety (don't post same content twice in a row)
        """
        # TODO: Implement
        # Query content_items table with filters
        return None

    async def mark_posted(self, account_id: UUID, content_id: UUID) -> None:
        """Mark a content item as posted by an account."""
        # TODO: Implement
        pass

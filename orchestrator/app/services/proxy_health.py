"""Proxy health checker - periodic proxy liveness checks."""

import structlog

logger = structlog.get_logger()


class ProxyHealth:
    """Periodic proxy liveness checks."""

    def __init__(self, db):
        self.db = db

    async def check_all(self) -> dict:
        """Check all proxies are alive."""
        # TODO: Implement - test each proxy connection
        # Mark dead proxies as inactive
        return {"proxies_checked": 0, "proxies_healthy": 0, "proxies_failed": 0}

    async def check_proxy(self, proxy_id) -> bool:
        """Check a single proxy is alive."""
        # TODO: Implement
        return True

    async def mark_burned(self, proxy_id, reason: str) -> None:
        """Mark a proxy as burned (do not reuse)."""
        # TODO: Implement
        logger.warning("proxy_marked_burned", proxy_id=str(proxy_id), reason=reason)

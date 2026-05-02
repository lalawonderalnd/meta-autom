"""Proxy configuration and management for different providers."""

import structlog
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote

logger = structlog.get_logger()


@dataclass
class ProxyConfig:
    """Proxy configuration for a single clone."""
    
    provider: str
    protocol: str  # 'http' or 'socks5'
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    carrier: Optional[str] = None
    sticky_session_id: Optional[str] = None
    
    @property
    def url(self) -> str:
        """Build proxy URL for requests."""
        if self.username and self.password:
            user_pass = f"{quote(self.username)}:{quote(self.password)}@"
        elif self.username:
            user_pass = f"{quote(self.username)}@"
        else:
            user_pass = ""
        
        return f"{self.protocol}://{user_pass}{self.host}:{self.port}"
    
    @property
    def curl_format(self) -> str:
        """Return curl-compatible proxy format."""
        if self.username and self.password:
            return f"{self.protocol}://{quote(self.username)}:{quote(self.password)}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    def to_app_cloner_proxy_config(self) -> dict:
        """Format for App Cloner Yellow package proxy settings."""
        return {
            "enabled": True,
            "protocol": self.protocol.upper(),
            "host": self.host,
            "port": self.port,
            "username": self.username or "",
            "password": self.password or "",
        }


class ProxyProvider:
    """Base class for proxy providers."""
    
    PROVIDER_NAME: str = "generic"
    
    def build_username(
        self,
        session_id: str,
        country: Optional[str] = None,
        lifetime_hours: int = 720,
    ) -> str:
        """Build provider-specific username with sticky session."""
        raise NotImplementedError
    
    def verify_ip(self, expected_country: str) -> bool:
        """Verify that current IP matches expected country."""
        raise NotImplementedError


class IPRoyalProvider(ProxyProvider):
    """IPRoyal mobile residential proxy provider."""
    
    PROVIDER_NAME = "iproyal"
    
    def __init__(self, base_username: str, password: str):
        """
        Initialize IPRoyal provider.
        
        Args:
            base_username: Your IPRoyal username (without session params)
            password: Your IPRoyal password
        """
        self.base_username = base_username
        self.password = password
    
    def build_username(
        self,
        session_id: str,
        country: Optional[str] = None,
        lifetime_hours: int = 720,
    ) -> str:
        """
        Build IPRoyal username with sticky session.
        
        Format: user-{clone_id}-country-{cc}-session-{sticky_id}-lifetime-{hours}h
        
        Args:
            session_id: Unique sticky session ID per clone
            country: Two-letter country code (e.g., 'de', 'us')
            lifetime_hours: Session lifetime in hours (default 720 = 30 days)
        
        Returns:
            Full username string for proxy auth
        """
        parts = [self.base_username]
        
        if country:
            parts.append(f"country-{country.lower()}")
        
        parts.append(f"session-{session_id}")
        parts.append(f"lifetime-{lifetime_hours}h")
        
        return "-".join(parts)
    
    def build_proxy_config(
        self,
        clone_id: str,
        country: str,
        sticky_session_id: str,
        lifetime_hours: int = 720,
    ) -> ProxyConfig:
        """Build complete ProxyConfig for a clone."""
        username = self.build_username(
            session_id=sticky_session_id,
            country=country,
            lifetime_hours=lifetime_hours,
        )
        
        return ProxyConfig(
            provider=self.PROVIDER_NAME,
            protocol="http",
            host="geo.iproyal.com",
            port=12321,
            username=username,
            password=self.password,
            country_code=country.upper(),
            sticky_session_id=sticky_session_id,
        )
    
    async def verify_ip(self, expected_country: str, proxy_url: str) -> bool:
        """Verify IP location via httpbin or similar."""
        import httpx
        
        try:
            async with httpx.AsyncClient(proxy=proxy_url, timeout=10.0) as client:
                response = await client.get("https://api.ipify.org?format=json")
                response.raise_for_status()
                data = response.json()
                ip = data.get("ip")
                
                # Get IP info
                geo_response = await client.get(f"https://ipapi.co/{ip}/json/")
                geo_response.raise_for_status()
                geo_data = geo_response.json()
                
                actual_country = geo_data.get("country_code", "").lower()
                is_match = actual_country == expected_country.lower()
                
                if not is_match:
                    logger.warning(
                        "proxy_ip_mismatch",
                        expected=expected_country,
                        actual=actual_country,
                        ip=ip,
                    )
                
                return is_match
                
        except Exception as e:
            logger.error("proxy_verification_failed", error=str(e))
            return False


class SmartproxyProvider(ProxyProvider):
    """Smartproxy mobile residential proxy provider."""
    
    PROVIDER_NAME = "smartproxy"
    
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
    
    def build_username(
        self,
        session_id: str,
        country: Optional[str] = None,
        lifetime_hours: int = 720,
    ) -> str:
        """
        Smartproxy uses session parameter in username.
        
        Format: sp-user-{session_id}
        """
        return f"sp-user-{session_id}"
    
    def build_proxy_config(
        self,
        clone_id: str,
        country: str,
        sticky_session_id: str,
        lifetime_hours: int = 720,
    ) -> ProxyConfig:
        """Build complete ProxyConfig for a clone."""
        username = self.build_username(
            session_id=sticky_session_id,
            country=country,
            lifetime_hours=lifetime_hours,
        )
        
        # Smartproxy gateway
        return ProxyConfig(
            provider=self.PROVIDER_NAME,
            protocol="http",
            host="gateway.smartproxy.com",
            port=10000,
            username=username,
            password=self.password,
            country_code=country.upper(),
            sticky_session_id=sticky_session_id,
        )
    
    async def verify_ip(self, expected_country: str, proxy_url: str) -> bool:
        """Verify IP location."""
        import httpx
        
        try:
            async with httpx.AsyncClient(proxy=proxy_url, timeout=10.0) as client:
                response = await client.get("https://api.ipify.org?format=json")
                response.raise_for_status()
                data = response.json()
                ip = data.get("ip")
                
                geo_response = await client.get(f"https://ipapi.co/{ip}/json/")
                geo_response.raise_for_status()
                geo_data = geo_response.json()
                
                actual_country = geo_data.get("country_code", "").lower()
                return actual_country == expected_country.lower()
                
        except Exception as e:
            logger.error("proxy_verification_failed", error=str(e))
            return False


def get_proxy_provider(
    provider_name: str,
    username: str,
    password: str,
) -> ProxyProvider:
    """Factory function to get appropriate proxy provider."""
    providers = {
        "iproyal": IPRoyalProvider,
        "smartproxy": SmartproxyProvider,
    }
    
    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Unknown proxy provider: {provider_name}")
    
    return provider_class(username, password)


# Example usage for App Cloner configuration
def generate_app_cloner_proxy_settings(proxy_config: ProxyConfig) -> str:
    """
    Generate App Cloner proxy configuration string.
    
    This can be used when cloning apps programmatically or via intent extras.
    """
    settings = {
        "proxy_enabled": True,
        "proxy_type": proxy_config.protocol.upper(),
        "proxy_host": proxy_config.host,
        "proxy_port": proxy_config.port,
        "proxy_username": proxy_config.username or "",
        "proxy_password": proxy_config.password or "",
    }
    
    # Format as JSON for App Cloner intent extras
    import json
    return json.dumps(settings)

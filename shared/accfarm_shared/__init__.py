"""AccFarm v2 Shared Package - Database schema, enums, and Pydantic models."""

from accfarm_shared.models import (
    Account,
    Device,
    Job,
    Proxy,
    Client,
    Session,
    Action,
    ContentItem,
)
from accfarm_shared.enums import (
    AccountStatus,
    DeviceStatus,
    JobStatus,
    JobKind,
    Platform,
)
from accfarm_shared.encryption import encrypt_password, decrypt_password
from accfarm_shared.db_models import (
    Base,
    Client as ClientModel,
    Proxy as ProxyModel,
    Device as DeviceModel,
    Account as AccountModel,
    Job as JobModel,
    Session as SessionModel,
    Action as ActionModel,
    ContentItem as ContentItemModel,
)
from accfarm_shared.proxy import (
    ProxyConfig,
    ProxyProvider,
    IPRoyalProvider,
    SmartproxyProvider,
    get_proxy_provider,
    generate_app_cloner_proxy_settings,
)

__all__ = [
    # Pydantic Models
    "Account",
    "Device",
    "Job",
    "Proxy",
    "Client",
    "Session",
    "Action",
    "ContentItem",
    # SQLAlchemy ORM Models
    "Base",
    "ClientModel",
    "ProxyModel",
    "DeviceModel",
    "AccountModel",
    "JobModel",
    "SessionModel",
    "ActionModel",
    "ContentItemModel",
    # Enums
    "AccountStatus",
    "DeviceStatus",
    "JobStatus",
    "JobKind",
    "Platform",
    # Encryption
    "encrypt_password",
    "decrypt_password",
    # Proxy
    "ProxyConfig",
    "ProxyProvider",
    "IPRoyalProvider",
    "SmartproxyProvider",
    "get_proxy_provider",
    "generate_app_cloner_proxy_settings",
]

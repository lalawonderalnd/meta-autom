"""
Configuration as Code for Meta Autom Farm.

YAML-based configuration profiles for different farm strategies,
allowing version-controlled, reproducible deployments.
"""

import yaml
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class WarmupConfig:
    """Warmup strategy configuration."""
    enabled: bool = True
    duration_days: int = 7
    daily_actions_min: int = 5
    daily_actions_max: int = 15
    like_ratio: float = 0.6
    comment_ratio: float = 0.1
    follow_ratio: float = 0.1
    browse_ratio: float = 0.2
    randomize_order: bool = True
    rest_days_per_week: int = 1


@dataclass
class ProxyConfig:
    """Proxy configuration."""
    provider: str = "iproyal"
    type: str = "mobile_residential"
    sticky_session: bool = True
    rotation_interval_hours: int = 720
    retry_on_failure: bool = True
    max_retries: int = 3
    timeout_seconds: int = 30
    countries: List[str] = field(default_factory=lambda: ["us", "uk", "de"])


@dataclass
class DeviceConfig:
    """Device-level configuration."""
    max_clones_per_device: int = 15
    heartbeat_interval_seconds: int = 60
    screen_timeout_minutes: int = 30
    charging_required: bool = True
    max_temperature_celsius: int = 50
    auto_reboot_on_error: bool = True
    wifi_sleep_policy: str = "never"


@dataclass
class AccountConfig:
    """Account behavior configuration."""
    sessions_per_day_min: int = 2
    sessions_per_day_max: int = 5
    session_duration_minutes_min: int = 5
    session_duration_minutes_max: int = 20
    actions_per_session_min: int = 10
    actions_per_session_max: int = 30
    humanize_touch: bool = True
    randomize_timing: bool = True
    avoid_ban_patterns: bool = True


@dataclass
class AlertConfig:
    """Alerting configuration."""
    telegram_enabled: bool = True
    telegram_chat_id: Optional[str] = None
    alert_on_device_offline: bool = True
    alert_on_account_banned: bool = True
    alert_on_high_error_rate: bool = True
    error_rate_threshold: float = 0.3
    daily_report_enabled: bool = True
    daily_report_hour: int = 9


@dataclass
class FarmProfile:
    """Complete farm configuration profile."""
    name: str
    description: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0"
    
    warmup: WarmupConfig = field(default_factory=WarmupConfig)
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    device: DeviceConfig = field(default_factory=DeviceConfig)
    account: AccountConfig = field(default_factory=AccountConfig)
    alert: AlertConfig = field(default_factory=AlertConfig)
    
    target_accounts: int = 50
    accounts_per_device: int = 10
    growth_rate_per_week: int = 10
    
    target_creators: List[str] = field(default_factory=list)
    content_categories: List[str] = field(default_factory=lambda: ["lifestyle", "tech"])
    
    panic_mode_enabled: bool = True
    auto_heal_enabled: bool = True
    analytics_enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_yaml(self) -> str:
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FarmProfile":
        if "warmup" in data:
            data["warmup"] = WarmupConfig(**data["warmup"])
        if "proxy" in data:
            data["proxy"] = ProxyConfig(**data["proxy"])
        if "device" in data:
            data["device"] = DeviceConfig(**data["device"])
        if "account" in data:
            data["account"] = AccountConfig(**data["account"])
        if "alert" in data:
            data["alert"] = AlertConfig(**data["alert"])
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
            
        return cls(**data)
    
    @classmethod
    def from_yaml(cls, yaml_str: str) -> "FarmProfile":
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)
    
    @classmethod
    def load(cls, path: str) -> "FarmProfile":
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Profile not found: {path}")
        
        with open(path, "r") as f:
            yaml_str = f.read()
        
        logger.info(f"Loaded farm profile: {path}")
        return cls.from_yaml(yaml_str)
    
    def save(self, path: str):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w") as f:
            f.write(self.to_yaml())
        
        logger.info(f"Saved farm profile: {path}")


def get_conservative_profile() -> FarmProfile:
    """Conservative profile for maximum account safety."""
    return FarmProfile(
        name="conservative",
        description="Maximum safety, slow growth",
        warmup=WarmupConfig(
            enabled=True,
            duration_days=14,
            daily_actions_min=3,
            daily_actions_max=8,
            rest_days_per_week=2
        ),
        account=AccountConfig(
            sessions_per_day_min=1,
            sessions_per_day_max=3,
            session_duration_minutes_min=3,
            session_duration_minutes_max=10,
            actions_per_session_min=5,
            actions_per_session_max=15
        ),
        target_accounts=25,
        accounts_per_device=5
    )


def get_aggressive_profile() -> FarmProfile:
    """Aggressive profile for rapid scaling."""
    return FarmProfile(
        name="aggressive",
        description="Rapid scaling, higher risk",
        warmup=WarmupConfig(
            enabled=True,
            duration_days=5,
            daily_actions_min=10,
            daily_actions_max=25,
            rest_days_per_week=0
        ),
        account=AccountConfig(
            sessions_per_day_min=3,
            sessions_per_day_max=8,
            session_duration_minutes_min=10,
            session_duration_minutes_max=30,
            actions_per_session_min=20,
            actions_per_session_max=50
        ),
        target_accounts=200,
        accounts_per_device=20
    )


def get_balanced_profile() -> FarmProfile:
    """Balanced profile for most use cases."""
    return FarmProfile(
        name="balanced",
        description="Balanced safety and growth",
        warmup=WarmupConfig(
            enabled=True,
            duration_days=7,
            daily_actions_min=5,
            daily_actions_max=15,
            rest_days_per_week=1
        ),
        account=AccountConfig(
            sessions_per_day_min=2,
            sessions_per_day_max=5,
            session_duration_minutes_min=5,
            session_duration_minutes_max=20,
            actions_per_session_min=10,
            actions_per_session_max=30
        ),
        target_accounts=50,
        accounts_per_device=10
    )


PROFILE_DIR = Path("profiles")


def list_profiles() -> List[str]:
    """List available profile files."""
    if not PROFILE_DIR.exists():
        return []
    
    profiles = []
    for path in PROFILE_DIR.glob("*.yaml"):
        profiles.append(path.stem)
    
    return sorted(profiles)


def create_profile(name: str, preset: str = "balanced", **overrides) -> FarmProfile:
    """Create a new profile from a preset with optional overrides."""
    presets = {
        "conservative": get_conservative_profile(),
        "balanced": get_balanced_profile(),
        "aggressive": get_aggressive_profile()
    }
    
    if preset not in presets:
        raise ValueError(f"Unknown preset: {preset}. Available: {list(presets.keys())}")
    
    profile = presets[preset]
    profile.name = name
    
    if "target_accounts" in overrides:
        profile.target_accounts = overrides["target_accounts"]
    if "accounts_per_device" in overrides:
        profile.accounts_per_device = overrides["accounts_per_device"]
    
    return profile


def validate_profile(profile: FarmProfile) -> List[str]:
    """Validate a profile configuration."""
    issues = []
    
    if profile.warmup.duration_days < 5:
        issues.append("WARNING: Warmup < 5 days increases ban risk")
    if profile.warmup.duration_days > 30:
        issues.append("NOTE: Warmup > 30 days may be overly conservative")
    
    total_ratio = (
        profile.warmup.like_ratio +
        profile.warmup.comment_ratio +
        profile.warmup.follow_ratio +
        profile.warmup.browse_ratio
    )
    if abs(total_ratio - 1.0) > 0.01:
        issues.append(f"ERROR: Action ratios sum to {total_ratio}, should be 1.0")
    
    if profile.device.max_clones_per_device > 20:
        issues.append("WARNING: > 20 clones/device may cause performance issues")
    if profile.device.max_clones_per_device < 5:
        issues.append("NOTE: < 5 clones/device may be underutilizing hardware")
    
    if profile.alert.telegram_enabled and not profile.alert.telegram_chat_id:
        issues.append("ERROR: Telegram alerts enabled but no chat_id provided")
    
    return issues

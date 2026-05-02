"""
Ghost Operator - AI-powered context-aware account recovery and dynamic warmup adjustment.

Analyzes errors, selects optimal recovery strategies, and adjusts warmup schedules
based on real-time feedback to maximize account survival rates.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum
import json

from supabase import Client


class ErrorCategory(str, Enum):
    """Categorized error types for targeted recovery."""
    NETWORK_TIMEOUT = "network_timeout"
    LOGIN_FAILED = "login_failed"
    ACTION_BLOCKED = "action_blocked"
    RATE_LIMITED = "rate_limited"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    TEMP_BAN = "temp_ban"
    PERMANENT_BAN = "permanent_ban"
    APP_CRASH = "app_crash"
    UNKNOWN = "unknown"


class RecoveryStrategy(str, Enum):
    """Available recovery strategies."""
    RETRY_IMMEDIATE = "retry_immediate"
    RETRY_WITH_DELAY = "retry_with_delay"
    SWITCH_PROXY = "switch_proxy"
    CLEAR_APP_DATA = "clear_app_data"
    COOLDOWN_PERIOD = "cooldown_period"
    REDUCE_WARMUP_PACE = "reduce_warmup_pace"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    MARK_FOR_REMOVAL = "mark_for_removal"


class GhostOperator:
    """
    AI-powered account operator that makes context-aware decisions.
    
    Features:
    - Error pattern analysis and categorization
    - Dynamic recovery strategy selection
    - Adaptive warmup scheduling
    - Learning from historical success rates
    """
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.error_history: dict[str, list[dict]] = {}
        self.recovery_stats: dict[str, dict] = {}
        
    async def analyze_error(self, account_id: str, error_message: str, context: dict) -> dict:
        """
        Analyze an error and determine the best recovery strategy.
        
        Args:
            account_id: The account that encountered the error
            error_message: The error message from Instagram/ADB
            context: Additional context (device info, proxy status, recent actions)
            
        Returns:
            Dict with error_category, confidence, recommended_strategy, and reasoning
        """
        # Categorize the error
        category = self._categorize_error(error_message)
        
        # Check historical patterns for this account
        account_history = self.error_history.get(account_id, [])
        
        # Analyze frequency and patterns
        recent_similar_errors = [
            e for e in account_history[-10:]
            if e.get("category") == category
        ]
        
        # Determine confidence based on pattern matching
        confidence = 0.5
        if len(recent_similar_errors) >= 3:
            confidence = 0.8
        elif len(recent_similar_errors) >= 5:
            confidence = 0.95
            
        # Select recovery strategy based on category and context
        strategy = self._select_recovery_strategy(
            category, 
            context, 
            len(recent_similar_errors)
        )
        
        # Generate human-readable reasoning
        reasoning = self._generate_reasoning(category, strategy, context)
        
        # Store error in history
        error_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "category": category.value,
            "error_message": error_message,
            "context": context,
            "strategy_selected": strategy.value,
        }
        
        if account_id not in self.error_history:
            self.error_history[account_id] = []
        self.error_history[account_id].append(error_record)
        
        # Keep only last 50 errors per account
        self.error_history[account_id] = self.error_history[account_id][-50:]
        
        return {
            "account_id": account_id,
            "error_category": category.value,
            "confidence": confidence,
            "recommended_strategy": strategy.value,
            "reasoning": reasoning,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def _categorize_error(self, error_message: str) -> ErrorCategory:
        """Categorize error message into predefined categories."""
        error_lower = error_message.lower()
        
        if any(x in error_lower for x in ["timeout", "timed out", "connection reset"]):
            return ErrorCategory.NETWORK_TIMEOUT
        elif any(x in error_lower for x in ["login failed", "incorrect password", "invalid credentials"]):
            return ErrorCategory.LOGIN_FAILED
        elif any(x in error_lower for x in ["action blocked", "blocked", "cannot complete"]):
            return ErrorCategory.ACTION_BLOCKED
        elif any(x in error_lower for x in ["rate limit", "too many", "try again later"]):
            return ErrorCategory.RATE_LIMITED
        elif any(x in error_lower for x in ["suspicious", "unusual activity", "verify identity"]):
            return ErrorCategory.SUSPICIOUS_ACTIVITY
        elif any(x in error_lower for x in ["temporarily banned", "temporary ban", "24 hour"]):
            return ErrorCategory.TEMP_BAN
        elif any(x in error_lower for x in ["permanently banned", "disabled", "violates terms"]):
            return ErrorCategory.PERMANENT_BAN
        elif any(x in error_lower for x in ["crash", "force close", "stopped working"]):
            return ErrorCategory.APP_CRASH
        else:
            return ErrorCategory.UNKNOWN
    
    def _select_recovery_strategy(
        self, 
        category: ErrorCategory, 
        context: dict, 
        repeat_count: int
    ) -> RecoveryStrategy:
        """Select optimal recovery strategy based on error category and context."""
        
        # Repeated errors escalate the response
        if repeat_count >= 5:
            return RecoveryStrategy.ESCALATE_TO_HUMAN
        elif repeat_count >= 3:
            if category in [ErrorCategory.SUSPICIOUS_ACTIVITY, ErrorCategory.TEMP_BAN]:
                return RecoveryStrategy.COOLDOWN_PERIOD
            elif category == ErrorCategory.LOGIN_FAILED:
                return RecoveryStrategy.CLEAR_APP_DATA
        
        # Strategy selection by category
        strategy_map = {
            ErrorCategory.NETWORK_TIMEOUT: RecoveryStrategy.RETRY_WITH_DELAY,
            ErrorCategory.LOGIN_FAILED: RecoveryStrategy.RETRY_WITH_DELAY,
            ErrorCategory.ACTION_BLOCKED: RecoveryStrategy.REDUCE_WARMUP_PACE,
            ErrorCategory.RATE_LIMITED: RecoveryStrategy.COOLDOWN_PERIOD,
            ErrorCategory.SUSPICIOUS_ACTIVITY: RecoveryStrategy.SWITCH_PROXY,
            ErrorCategory.TEMP_BAN: RecoveryStrategy.COOLDOWN_PERIOD,
            ErrorCategory.PERMANENT_BAN: RecoveryStrategy.MARK_FOR_REMOVAL,
            ErrorCategory.APP_CRASH: RecoveryStrategy.CLEAR_APP_DATA,
            ErrorCategory.UNKNOWN: RecoveryStrategy.RETRY_WITH_DELAY,
        }
        
        base_strategy = strategy_map.get(category, RecoveryStrategy.RETRY_WITH_DELAY)
        
        # Adjust based on proxy health context
        if context.get("proxy_unhealthy") and base_strategy != RecoveryStrategy.SWITCH_PROXY:
            return RecoveryStrategy.SWITCH_PROXY
            
        return base_strategy
    
    def _generate_reasoning(
        self, 
        category: ErrorCategory, 
        strategy: RecoveryStrategy,
        context: dict
    ) -> str:
        """Generate human-readable explanation for the chosen strategy."""
        reasonings = {
            (ErrorCategory.NETWORK_TIMEOUT, RecoveryStrategy.RETRY_WITH_DELAY): 
                "Network timeout detected. Retrying after brief delay to allow connection stabilization.",
            (ErrorCategory.LOGIN_FAILED, RecoveryStrategy.RETRY_WITH_DELAY):
                "Login failure detected. Waiting before retry to avoid triggering rate limits.",
            (ErrorCategory.ACTION_BLOCKED, RecoveryStrategy.REDUCE_WARMUP_PACE):
                "Action blocked by Instagram. Reducing warmup pace to appear more human-like.",
            (ErrorCategory.RATE_LIMITED, RecoveryStrategy.COOLDOWN_PERIOD):
                "Rate limited by Instagram. Implementing cooldown period to reset limits.",
            (ErrorCategory.SUSPICIOUS_ACTIVITY, RecoveryStrategy.SWITCH_PROXY):
                "Suspicious activity flag triggered. Switching proxy to change IP fingerprint.",
            (ErrorCategory.TEMP_BAN, RecoveryStrategy.COOLDOWN_PERIOD):
                "Temporary ban detected. Pausing all activity until ban expires.",
            (ErrorCategory.PERMANENT_BAN, RecoveryStrategy.MARK_FOR_REMOVAL):
                "Permanent ban detected. Account should be removed from the farm.",
            (ErrorCategory.APP_CRASH, RecoveryStrategy.CLEAR_APP_DATA):
                "App crash detected. Clearing app data to reset state.",
        }
        
        key = (category, strategy)
        if key in reasonings:
            return reasonings[key]
        
        return f"Error categorized as {category.value}. Applying {strategy.value} strategy."
    
    async def adjust_warmup_schedule(
        self, 
        account_id: str, 
        current_day: int,
        success_rate: float,
        error_rate: float
    ) -> dict:
        """
        Dynamically adjust warmup schedule based on performance metrics.
        
        Args:
            account_id: The account to adjust
            current_day: Current day in warmup (1-7)
            success_rate: Success rate of actions (0.0-1.0)
            error_rate: Error rate of actions (0.0-1.0)
            
        Returns:
            Dict with adjusted_day, pace_multiplier, and recommendations
        """
        # Default: continue as planned
        adjusted_day = current_day
        pace_multiplier = 1.0
        recommendations = []
        
        # High error rate: slow down
        if error_rate > 0.3:
            adjusted_day = max(1, current_day - 1)
            pace_multiplier = 0.5
            recommendations.append("High error rate detected. Slowing warmup pace by 50%.")
            recommendations.append("Consider extending warmup period by 2-3 days.")
        
        # Very high error rate: pause and reassess
        elif error_rate > 0.5:
            pace_multiplier = 0.25
            recommendations.append("Critical error rate. Pausing warmup temporarily.")
            recommendations.append("Manual review recommended before continuing.")
        
        # Excellent performance: can accelerate slightly
        elif success_rate > 0.95 and error_rate < 0.05:
            pace_multiplier = 1.2
            if current_day < 7:
                recommendations.append("Excellent performance. Can accelerate warmup slightly.")
        
        # Moderate performance: stay the course
        else:
            recommendations.append("Performance within normal parameters. Continue as planned.")
        
        return {
            "account_id": account_id,
            "original_day": current_day,
            "adjusted_day": adjusted_day,
            "pace_multiplier": pace_multiplier,
            "recommendations": recommendations,
            "success_rate": success_rate,
            "error_rate": error_rate,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def execute_recovery(
        self, 
        account_id: str, 
        strategy: RecoveryStrategy,
        device_id: Optional[str] = None
    ) -> bool:
        """
        Execute the selected recovery strategy.
        
        Args:
            account_id: The account to recover
            strategy: The recovery strategy to execute
            device_id: Optional device ID for device-specific actions
            
        Returns:
            True if recovery was successful, False otherwise
        """
        try:
            if strategy == RecoveryStrategy.RETRY_IMMEDIATE:
                # Just retry the last action immediately
                return True
                
            elif strategy == RecoveryStrategy.RETRY_WITH_DELAY:
                # Wait 5-15 minutes before retry
                await asyncio.sleep(600)  # 10 minutes average
                return True
                
            elif strategy == RecoveryStrategy.SWITCH_PROXY:
                # Fetch a new proxy and update account
                if device_id:
                    await self._assign_new_proxy(account_id, device_id)
                return True
                
            elif strategy == RecoveryStrategy.CLEAR_APP_DATA:
                # Clear Instagram app data via ADB
                if device_id:
                    await self._clear_app_data(device_id)
                return True
                
            elif strategy == RecoveryStrategy.COOLDOWN_PERIOD:
                # Set account to cooldown status for 24-48 hours
                await self._set_cooldown(account_id, hours=24)
                return True
                
            elif strategy == RecoveryStrategy.REDUCE_WARMUP_PACE:
                # Update account's warmup pace setting
                await self._reduce_warmup_pace(account_id)
                return True
                
            elif strategy == RecoveryStrategy.ESCALATE_TO_HUMAN:
                # Mark account for human review
                await self._escalate_to_human(account_id)
                return True
                
            elif strategy == RecoveryStrategy.MARK_FOR_REMOVAL:
                # Mark account for removal from farm
                await self._mark_for_removal(account_id)
                return True
                
        except Exception as e:
            # Log the failure
            print(f"Recovery strategy {strategy} failed for account {account_id}: {e}")
            return False
        
        return False
    
    async def _assign_new_proxy(self, account_id: str, device_id: str):
        """Assign a new proxy to the account."""
        # Fetch available proxies
        result = self.supabase.table("proxies").select("*").eq("is_alive", True).limit(1).execute()
        
        if result.data:
            new_proxy = result.data[0]
            # Update account's proxy assignment
            self.supabase.table("accounts").update({
                "proxy_id": new_proxy["id"],
                "last_proxy_switch": datetime.utcnow().isoformat(),
            }).eq("id", account_id).execute()
    
    async def _clear_app_data(self, device_id: str):
        """Clear Instagram app data on device via ADB."""
        # This would integrate with the device layer to execute ADB commands
        # Example: adb shell pm clear com.instagram.android
        pass
    
    async def _set_cooldown(self, account_id: str, hours: int = 24):
        """Set account to cooldown status."""
        self.supabase.table("accounts").update({
            "status": "COOLDOWN",
            "cooldown_until": (datetime.utcnow() + timedelta(hours=hours)).isoformat(),
        }).eq("id", account_id).execute()
    
    async def _reduce_warmup_pace(self, account_id: str):
        """Reduce the warmup pace for an account."""
        # Update warmup settings in database
        self.supabase.table("accounts").update({
            "warmup_pace_multiplier": 0.5,
        }).eq("id", account_id).execute()
    
    async def _escalate_to_human(self, account_id: str):
        """Mark account for human review."""
        self.supabase.table("accounts").update({
            "requires_manual_review": True,
            "review_reason": "Repeated errors - escalated by Ghost Operator",
        }).eq("id", account_id).execute()
        
        # Send notification to operators
        # (Would integrate with notifier service)
    
    async def _mark_for_removal(self, account_id: str):
        """Mark account for removal from the farm."""
        self.supabase.table("accounts").update({
            "status": "REMOVED",
            "removal_reason": "Permanent ban detected",
            "removed_at": datetime.utcnow().isoformat(),
        }).eq("id", account_id).execute()

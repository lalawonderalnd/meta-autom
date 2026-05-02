"""
Honeypot System - Sacrificial accounts for early ban detection.

Monitors sacrificial "honeypot" accounts to detect Instagram's
anti-bot measures before they affect the main farm accounts.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum

from supabase import Client


class HoneypotStatus(str, Enum):
    """Status of a honeypot account."""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    COMPROMISED = "compromised"
    RETIRED = "retired"


class ThreatLevel(str, Enum):
    """Threat level detected by honeypot."""
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HoneypotSystem:
    """
    Sacrificial honeypot account monitoring system.
    
    Uses dedicated accounts to probe Instagram's defenses and detect
    new anti-bot measures before they impact production accounts.
    
    Features:
    - Early warning system for bans/shadowbans
    - Detection of new rate limits
    - Monitoring of action thresholds
    - Automatic panic mode trigger
    """
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.honeypot_accounts: list[dict] = []
        self.last_check: Optional[datetime] = None
        self.threat_history: list[dict] = []
        
    async def register_honeypot(
        self,
        account_id: str,
        device_id: str,
        proxy_id: str,
        purpose: str = "general"
    ) -> dict:
        """
        Register an account as a honeypot.
        
        Args:
            account_id: The account to use as honeypot
            device_id: Device running the honeypot
            proxy_id: Proxy for the honeypot
            purpose: Purpose type (general, rate_limit_test, ban_test, shadowban_test)
            
        Returns:
            Registration result
        """
        # Mark account as honeypot in database
        result = self.supabase.table("accounts").update({
            "is_honeypot": True,
            "honeypot_purpose": purpose,
            "honeypot_registered_at": datetime.utcnow().isoformat(),
            "status": "WARMING",  # Keep in warmup to appear normal
        }).eq("id", account_id).execute()
        
        if not result.data:
            return {"success": False, "error": "Failed to register honeypot"}
        
        honeypot_record = {
            "account_id": account_id,
            "device_id": device_id,
            "proxy_id": proxy_id,
            "purpose": purpose,
            "registered_at": datetime.utcnow(),
            "status": HoneypotStatus.ACTIVE,
            "last_check": None,
            "threats_detected": [],
        }
        
        self.honeypot_accounts.append(honeypot_record)
        
        # Store in database for persistence
        self.supabase.table("honeypots").insert({
            "account_id": account_id,
            "device_id": device_id,
            "proxy_id": proxy_id,
            "purpose": purpose,
            "status": HoneypotStatus.ACTIVE.value,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
        
        return {
            "success": True,
            "account_id": account_id,
            "message": f"Honeypot registered for purpose: {purpose}",
        }
    
    async def probe_action_limit(
        self,
        honeypot_account_id: str,
        action_type: str,
        max_actions: int = 100
    ) -> dict:
        """
        Probe Instagram's action rate limits using a honeypot.
        
        Args:
            honeypot_account_id: The honeypot account to use
            action_type: Type of action to test (like, follow, comment, view)
            max_actions: Maximum actions to attempt
            
        Returns:
            Dict with detected limits and recommendations
        """
        results = {
            "action_type": action_type,
            "attempted": 0,
            "successful": 0,
            "blocked": 0,
            "error_messages": [],
            "detected_limit": None,
            "recommendation": None,
        }
        
        consecutive_failures = 0
        
        for i in range(max_actions):
            results["attempted"] += 1
            
            # Simulate action (in real implementation, this would execute via ADB)
            # For now, we'll simulate based on typical Instagram limits
            
            # Typical limits (these would be discovered through actual testing):
            # - Likes: ~60-100 per hour for new accounts
            # - Follows: ~20-40 per hour for new accounts
            # - Comments: ~10-20 per hour
            # - Views: ~200-500 per hour
            
            simulated_limit = {
                "like": 80,
                "follow": 30,
                "comment": 15,
                "view": 300,
            }.get(action_type, 50)
            
            if i < simulated_limit:
                # Action succeeds
                results["successful"] += 1
                consecutive_failures = 0
            else:
                # Action blocked
                results["blocked"] += 1
                consecutive_failures += 1
                
                error_msg = f"Action blocked after {i} attempts"
                results["error_messages"].append(error_msg)
                
                if consecutive_failures >= 3:
                    results["detected_limit"] = i
                    break
        
        # Generate recommendation
        if results["detected_limit"]:
            safe_limit = int(results["detected_limit"] * 0.7)  # 70% of detected limit
            results["recommendation"] = (
                f"Limit detected at ~{results['detected_limit']} {action_type}s. "
                f"Recommend staying under {safe_limit} for production accounts."
            )
        else:
            results["recommendation"] = (
                f"No hard limit detected up to {max_actions}. "
                f"Monitor for soft limits (shadowbans)."
            )
        
        # Store results
        await self._store_probe_result(honeypot_account_id, results)
        
        return results
    
    async def check_shadowban_status(self, honeypot_account_id: str) -> dict:
        """
        Check if a honeypot account has been shadowbanned.
        
        Shadowban indicators:
        - Posts don't appear in hashtag feeds
        - Engagement drops to near-zero from non-followers
        - Profile doesn't appear in search
        
        Args:
            honeypot_account_id: The honeypot account to check
            
        Returns:
            Dict with shadowban status and indicators
        """
        indicators = {
            "hashtag_visibility": None,
            "search_visibility": None,
            "non_follower_engagement": None,
            "reach_drop_percentage": None,
        }
        
        # In real implementation, these checks would:
        # 1. Post with unique hashtag, check if it appears in hashtag feed
        # 2. Search for account username from different account, check visibility
        # 3. Compare engagement from followers vs non-followers
        # 4. Compare reach to historical baseline
        
        # Simulated checks for now
        indicators["hashtag_visibility"] = True  # Would actually check
        indicators["search_visibility"] = True
        indicators["non_follower_engagement"] = 0.15  # 15% from non-followers
        indicators["reach_drop_percentage"] = 10  # 10% drop from baseline
        
        # Determine shadowban status
        is_shadowbanned = False
        reasons = []
        
        if not indicators["hashtag_visibility"]:
            is_shadowbanned = True
            reasons.append("Posts not appearing in hashtag feeds")
        
        if not indicators["search_visibility"]:
            is_shadowbanned = True
            reasons.append("Profile not appearing in search")
        
        if indicators["non_follower_engagement"] and indicators["non_follower_engagement"] < 0.05:
            is_shadowbanned = True
            reasons.append("Near-zero engagement from non-followers")
        
        if indicators["reach_drop_percentage"] and indicators["reach_drop_percentage"] > 80:
            is_shadowbanned = True
            reasons.append("Severe reach drop (>80%)")
        
        result = {
            "account_id": honeypot_account_id,
            "is_shadowbanned": is_shadowbanned,
            "confidence": 0.9 if is_shadowbanned else 0.5,
            "indicators": indicators,
            "reasons": reasons,
            "checked_at": datetime.utcnow().isoformat(),
        }
        
        # Update honeypot status if shadowbanned
        if is_shadowbanned:
            await self._mark_honeypot_triggered(honeypot_account_id, "shadowban")
        
        return result
    
    async def run_all_checks(self) -> dict:
        """
        Run all honeypot checks across all registered honeypots.
        
        Returns:
            Summary of all honeypot statuses and any threats detected
        """
        results = {
            "total_honeypots": len(self.honeypot_accounts),
            "active": 0,
            "triggered": 0,
            "compromised": 0,
            "threats_detected": [],
            "overall_threat_level": ThreatLevel.NONE,
            "recommendations": [],
            "checked_at": datetime.utcnow().isoformat(),
        }
        
        for honeypot in self.honeypot_accounts:
            if honeypot["status"] != HoneypotStatus.ACTIVE:
                continue
            
            results["active"] += 1
            
            # Check shadowban status
            shadowban_result = await self.check_shadowban_status(honeypot["account_id"])
            
            if shadowban_result["is_shadowbanned"]:
                results["triggered"] += 1
                threat = {
                    "type": "shadowban",
                    "account_id": honeypot["account_id"],
                    "severity": ThreatLevel.MEDIUM,
                    "details": shadowban_result["reasons"],
                }
                results["threats_detected"].append(threat)
                self.threat_history.append(threat)
        
        # Determine overall threat level
        if results["triggered"] == 0:
            results["overall_threat_level"] = ThreatLevel.NONE
        elif results["triggered"] <= 1:
            results["overall_threat_level"] = ThreatLevel.LOW
            results["recommendations"].append("One honeypot triggered. Monitor closely.")
        elif results["triggered"] <= 3:
            results["overall_threat_level"] = ThreatLevel.MEDIUM
            results["recommendations"].append(
                "Multiple honeypots triggered. Consider reducing activity across farm."
            )
        else:
            results["overall_threat_level"] = ThreatLevel.HIGH
            results["recommendations"].append(
                "CRITICAL: Multiple honeypots compromised. Recommend immediate activity reduction."
            )
        
        self.last_check = datetime.utcnow()
        
        return results
    
    async def _mark_honeypot_triggered(self, account_id: str, reason: str):
        """Mark a honeypot as triggered/compromised."""
        # Update in-memory status
        for honeypot in self.honeypot_accounts:
            if honeypot["account_id"] == account_id:
                honeypot["status"] = HoneypotStatus.TRIGGERED
                honeypot["threats_detected"].append({
                    "reason": reason,
                    "timestamp": datetime.utcnow().isoformat(),
                })
                break
        
        # Update in database
        self.supabase.table("honeypots").update({
            "status": HoneypotStatus.TRIGGERED.value,
            "last_triggered_at": datetime.utcnow().isoformat(),
        }).eq("account_id", account_id).execute()
        
        # Update account status
        self.supabase.table("accounts").update({
            "status": "WARNING",
            "warning_reason": f"Honeypot triggered: {reason}",
        }).eq("id", account_id).execute()
    
    async def _store_probe_result(self, account_id: str, results: dict):
        """Store probe results in database."""
        self.supabase.table("honeypot_probes").insert({
            "account_id": account_id,
            "action_type": results["action_type"],
            "attempted": results["attempted"],
            "successful": results["successful"],
            "blocked": results["blocked"],
            "detected_limit": results.get("detected_limit"),
            "recommendation": results["recommendation"],
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
    
    async def trigger_panic_mode(self, reason: str) -> dict:
        """
        Trigger panic mode across the entire farm when honeypots detect critical threats.
        
        Args:
            reason: Reason for triggering panic mode
            
        Returns:
            Result of panic mode activation
        """
        # Mark all honeypots as compromised
        for honeypot in self.honeypot_accounts:
            honeypot["status"] = HoneypotStatus.COMPROMISED
        
        # Update all honeypots in database
        self.supabase.table("honeypots").update({
            "status": HoneypotStatus.COMPROMISED.value,
            "compromised_at": datetime.utcnow().isoformat(),
            "compromise_reason": reason,
        }).eq("status", HoneypotStatus.ACTIVE.value).execute()
        
        # Flag all production accounts for review
        self.supabase.table("accounts").update({
            "requires_manual_review": True,
            "review_reason": f"Panic mode triggered: {reason}",
        }).eq("is_honeypot", False).eq("status", "ACTIVE").execute()
        
        # Pause all running jobs (would integrate with job dispatcher)
        # This is a placeholder - actual implementation would call job dispatcher
        
        threat_record = {
            "type": "panic_mode_triggered",
            "reason": reason,
            "severity": ThreatLevel.CRITICAL.value,
            "timestamp": datetime.utcnow().isoformat(),
            "honeypots_compromised": len(self.honeypot_accounts),
        }
        self.threat_history.append(threat_record)
        
        return {
            "success": True,
            "panic_mode": True,
            "reason": reason,
            "affected_accounts": len(self.honeypot_accounts),
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def get_honeypot_dashboard(self) -> dict:
        """
        Get a dashboard summary of all honeypot activity.
        
        Returns:
            Dashboard data for UI display
        """
        # Fetch from database
        db_honeypots = self.supabase.table("honeypots").select("""
            *,
            accounts(username, status),
            devices(name, adb_status)
        """).order("created_at", desc=True).execute()
        
        # Fetch recent probes
        recent_probes = self.supabase.table("honeypot_probes").select("*").order("created_at", desc=True).limit(20).execute()
        
        # Calculate stats
        total = len(db_honeypots.data or [])
        active = sum(1 for h in (db_honeypots.data or []) if h.get("status") == HoneypotStatus.ACTIVE.value)
        triggered = sum(1 for h in (db_honeypots.data or []) if h.get("status") == HoneypotStatus.TRIGGERED.value)
        compromised = sum(1 for h in (db_honeypots.data or []) if h.get("status") == HoneypotStatus.COMPROMISED.value)
        
        return {
            "summary": {
                "total_honeypots": total,
                "active": active,
                "triggered": triggered,
                "compromised": compromised,
                "health_percentage": (active / total * 100) if total > 0 else 0,
            },
            "recent_threats": self.threat_history[-10:],
            "recent_probes": recent_probes.data or [],
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "honeypots": db_honeypots.data or [],
        }

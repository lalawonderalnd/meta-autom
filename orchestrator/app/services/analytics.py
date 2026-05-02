"""
Success Rate Heatmaps and Analytics for Meta Autom Farm.

Tracks and visualizes success rates across devices, proxies, accounts,
and time periods to identify patterns and optimize operations.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """A single data point for analytics."""
    timestamp: datetime
    device_id: int
    account_id: int
    proxy_id: int
    action_type: str
    success: bool
    duration_ms: Optional[int] = None
    error_code: Optional[str] = None


class AnalyticsEngine:
    """
    Analytics engine for tracking and analyzing farm performance.
    
    Features:
    - Success rate heatmaps by device/hour
    - Proxy performance comparison
    - Account failure pattern detection
    - Content engagement tracking
    - Cost-per-account calculations
    """
    
    def __init__(self):
        self.metrics: List[MetricPoint] = []
        self.max_history_days = 30
    
    async def record_action(
        self,
        device_id: int,
        account_id: int,
        proxy_id: int,
        action_type: str,
        success: bool,
        duration_ms: Optional[int] = None,
        error_code: Optional[str] = None
    ):
        """Record an action result for analytics."""
        point = MetricPoint(
            timestamp=datetime.utcnow(),
            device_id=device_id,
            account_id=account_id,
            proxy_id=proxy_id,
            action_type=action_type,
            success=success,
            duration_ms=duration_ms,
            error_code=error_code
        )
        self.metrics.append(point)
        
        # Trim old data
        self._trim_old_data()
    
    def _trim_old_data(self):
        """Remove metrics older than max_history_days."""
        cutoff = datetime.utcnow() - timedelta(days=self.max_history_days)
        self.metrics = [m for m in self.metrics if m.timestamp > cutoff]
    
    def get_success_rate_by_device(
        self,
        hours: int = 24
    ) -> Dict[int, Dict[str, float]]:
        """
        Get success rates grouped by device.
        
        Returns:
            {device_id: {"total": N, "success": M, "rate": 0.XX}}
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [m for m in self.metrics if m.timestamp > cutoff]
        
        device_stats = defaultdict(lambda: {"total": 0, "success": 0})
        
        for metric in recent:
            device_stats[metric.device_id]["total"] += 1
            if metric.success:
                device_stats[metric.device_id]["success"] += 1
        
        result = {}
        for device_id, stats in device_stats.items():
            rate = stats["success"] / stats["total"] if stats["total"] > 0 else 0
            result[device_id] = {
                "total": stats["total"],
                "success": stats["success"],
                "rate": round(rate, 3)
            }
        
        return result
    
    def get_success_rate_heatmap(
        self,
        days: int = 7
    ) -> Dict[int, Dict[int, float]]:
        """
        Get success rate heatmap by device and hour of day.
        
        Returns:
            {device_id: {hour: success_rate}}
            
        This helps identify if certain devices perform poorly at specific times.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [m for m in self.metrics if m.timestamp > cutoff]
        
        # Group by device and hour
        buckets = defaultdict(lambda: defaultdict(lambda: {"total": 0, "success": 0}))
        
        for metric in recent:
            hour = metric.timestamp.hour
            buckets[metric.device_id][hour]["total"] += 1
            if metric.success:
                buckets[metric.device_id][hour]["success"] += 1
        
        result = {}
        for device_id, hours in buckets.items():
            result[device_id] = {}
            for hour, stats in hours.items():
                rate = stats["success"] / stats["total"] if stats["total"] > 0 else 0
                result[device_id][hour] = round(rate, 3)
        
        return result
    
    def get_proxy_performance(
        self,
        hours: int = 24
    ) -> Dict[int, Dict[str, Any]]:
        """
        Get performance metrics by proxy.
        
        Returns:
            {proxy_id: {"total": N, "success": M, "rate": X, "avg_duration_ms": Y}}
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [m for m in self.metrics if m.timestamp > cutoff]
        
        proxy_stats = defaultdict(lambda: {"total": 0, "success": 0, "durations": []})
        
        for metric in recent:
            proxy_stats[metric.proxy_id]["total"] += 1
            if metric.success:
                proxy_stats[metric.proxy_id]["success"] += 1
            if metric.duration_ms:
                proxy_stats[metric.proxy_id]["durations"].append(metric.duration_ms)
        
        result = {}
        for proxy_id, stats in proxy_stats.items():
            rate = stats["success"] / stats["total"] if stats["total"] > 0 else 0
            avg_duration = (
                sum(stats["durations"]) / len(stats["durations"])
                if stats["durations"] else None
            )
            
            result[proxy_id] = {
                "total": stats["total"],
                "success": stats["success"],
                "failed": stats["total"] - stats["success"],
                "rate": round(rate, 3),
                "avg_duration_ms": round(avg_duration) if avg_duration else None
            }
        
        return result
    
    def get_failing_accounts(
        self,
        hours: int = 24,
        min_failures: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get accounts with high failure rates.
        
        Returns list of accounts that may need attention.
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [m for m in self.metrics if m.timestamp > cutoff]
        
        account_stats = defaultdict(lambda: {"total": 0, "success": 0, "errors": []})
        
        for metric in recent:
            account_stats[metric.account_id]["total"] += 1
            if metric.success:
                account_stats[metric.account_id]["success"] += 1
            elif metric.error_code:
                account_stats[metric.account_id]["errors"].append(metric.error_code)
        
        failing = []
        for account_id, stats in account_stats.items():
            failures = stats["total"] - stats["success"]
            if failures >= min_failures:
                rate = stats["success"] / stats["total"] if stats["total"] > 0 else 0
                failing.append({
                    "account_id": account_id,
                    "total": stats["total"],
                    "success": stats["success"],
                    "failures": failures,
                    "rate": round(rate, 3),
                    "common_errors": self._get_top_errors(stats["errors"])
                })
        
        return sorted(failing, key=lambda x: x["failures"], reverse=True)
    
    def _get_top_errors(self, errors: List[str], top_n: int = 3) -> List[Dict[str, int]]:
        """Get most common error codes."""
        from collections import Counter
        counter = Counter(errors)
        return [{"code": code, "count": count} for code, count in counter.most_common(top_n)]
    
    def get_content_performance(
        self,
        creator_id: Optional[int] = None,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get engagement metrics for content.
        
        Tracks which creators/content types generate most successful interactions.
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent = [m for m in self.metrics if m.timestamp > cutoff]
        
        # Filter by creator if specified
        if creator_id:
            # Would need to join with content table in real implementation
            pass
        
        content_stats = defaultdict(lambda: {"likes": 0, "comments": 0, "follows": 0})
        
        for metric in recent:
            if metric.success:
                if metric.action_type == "like":
                    content_stats["engagement"]["likes"] += 1
                elif metric.action_type == "comment":
                    content_stats["engagement"]["comments"] += 1
                elif metric.action_type == "follow":
                    content_stats["engagement"]["follows"] += 1
        
        return [{
            "period_days": days,
            "total_likes": content_stats["engagement"]["likes"],
            "total_comments": content_stats["engagement"]["comments"],
            "total_follows": content_stats["engagement"]["follows"],
            "engagement_rate": self._calculate_engagement_rate(content_stats)
        }]
    
    def _calculate_engagement_rate(self, stats: Dict) -> float:
        """Calculate overall engagement rate."""
        total = (
            stats["engagement"]["likes"] +
            stats["engagement"]["comments"] +
            stats["engagement"]["follows"]
        )
        # Normalize by some factor (would be actions attempted in real impl)
        return round(total / 100, 2) if total > 0 else 0
    
    def get_cost_per_account(
        self,
        proxy_cost_per_month: float,
        sms_cost_per_account: float,
        total_accounts: int
    ) -> Dict[str, float]:
        """
        Calculate cost breakdown per account.
        
        Args:
            proxy_cost_per_month: Total monthly proxy cost
            sms_cost_per_account: One-time SMS cost per account
            total_accounts: Number of active accounts
            
        Returns:
            Breakdown of costs
        """
        monthly_proxy_per_account = proxy_cost_per_month / total_accounts if total_accounts > 0 else 0
        
        # Amortize SMS cost over 6 months (typical account lifespan target)
        amortized_sms = sms_cost_per_account / 6
        
        return {
            "monthly_proxy_cost": round(monthly_proxy_per_account, 2),
            "amortized_sms_cost": round(amortized_sms, 2),
            "total_monthly_cost": round(monthly_proxy_per_account + amortized_sms, 2),
            "one_time_sms_cost": sms_cost_per_account
        }
    
    def get_device_health_scores(
        self,
        hours: int = 24
    ) -> Dict[int, Dict[str, Any]]:
        """
        Calculate health scores for each device.
        
        Score is based on:
        - Success rate (50% weight)
        - Average response time (30% weight)
        - Error diversity (20% weight - fewer unique errors = better)
        
        Returns scores 0-100.
        """
        proxy_perf = self.get_proxy_performance(hours)
        device_rates = self.get_success_rate_by_device(hours)
        
        scores = {}
        
        # Calculate device scores
        for device_id, stats in device_rates.items():
            # Success rate component (0-50 points)
            rate_score = stats["rate"] * 50
            
            # Get avg duration for this device (simplified - would need device-specific timing)
            duration_score = 30  # Default if no timing data
            
            # Error diversity (fewer unique errors = higher score)
            # Simplified: assume moderate diversity
            diversity_score = 20
            
            total_score = rate_score + duration_score + diversity_score
            
            scores[device_id] = {
                "health_score": round(total_score, 1),
                "success_rate": stats["rate"],
                "total_actions": stats["total"],
                "status": self._score_to_status(total_score)
            }
        
        return scores
    
    def _score_to_status(self, score: float) -> str:
        """Convert health score to status string."""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 50:
            return "fair"
        else:
            return "poor"


# Singleton instance for global access
_analytics_engine: Optional[AnalyticsEngine] = None


def get_analytics_engine() -> AnalyticsEngine:
    """Get or create the global analytics engine."""
    global _analytics_engine
    if _analytics_engine is None:
        _analytics_engine = AnalyticsEngine()
    return _analytics_engine

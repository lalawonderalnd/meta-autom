"""
Content Intelligence - Viral pattern detection, trust network building, and DM auto-responder.

Analyzes content performance across the farm to identify viral patterns,
builds cross-account trust networks, and provides NLP-powered DM responses.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict
import re

from supabase import Client


class ContentIntelligence:
    """
    AI-powered content analysis and engagement system.
    
    Features:
    - Viral pattern detection from successful posts
    - Cross-account trust network building
    - NLP-powered DM auto-responder with filtering
    - Content performance analytics
    """
    
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.performance_cache: dict[str, list[dict]] = {}
        self.trust_network: dict[str, set[str]] = defaultdict(set)
        
    async def analyze_viral_patterns(
        self, 
        account_id: Optional[str] = None,
        limit: int = 100
    ) -> dict:
        """
        Analyze posts to identify viral patterns.
        
        Args:
            account_id: Optional account ID to analyze (None = all accounts)
            limit: Number of posts to analyze
            
        Returns:
            Dict with viral patterns including optimal posting times,
            content types, caption styles, and hashtag strategies
        """
        # Fetch posts with high engagement
        query = self.supabase.table("posts_log").select("""
            *,
            accounts(username, status)
        """).order("view_count", desc=True).limit(limit)
        
        if account_id:
            query = query.eq("account_id", account_id)
            
        result = query.execute()
        posts = result.data
        
        if not posts:
            return {"patterns": [], "message": "No posts found to analyze"}
        
        # Analyze patterns
        patterns = {
            "optimal_posting_hours": self._analyze_posting_times(posts),
            "top_performing_content_types": self._analyze_content_types(posts),
            "caption_length_insights": self._analyze_caption_lengths(posts),
            "hashtag_strategies": self._analyze_hashtags(posts),
            "engagement_velocity": self._analyze_engagement_velocity(posts),
        }
        
        # Store insights in database
        await self._store_insights(patterns)
        
        return {
            "analyzed_posts": len(posts),
            "patterns": patterns,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def _analyze_posting_times(self, posts: list[dict]) -> list[dict]:
        """Analyze which posting times get best engagement."""
        hour_performance = defaultdict(list)
        
        for post in posts:
            # Extract hour from posted_at
            posted_at = post.get("posted_at", "")
            if posted_at:
                try:
                    dt = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
                    hour = dt.hour
                    engagement = post.get("view_count", 0) + post.get("like_count", 0) * 3
                    hour_performance[hour].append(engagement)
                except (ValueError, TypeError):
                    continue
        
        # Calculate average engagement per hour
        hour_averages = []
        for hour, engagements in hour_performance.items():
            avg = sum(engagements) / len(engagements) if engagements else 0
            hour_averages.append({
                "hour": hour,
                "avg_engagement": avg,
                "post_count": len(engagements),
            })
        
        # Sort by engagement
        hour_averages.sort(key=lambda x: x["avg_engagement"], reverse=True)
        
        return hour_averages[:5]  # Top 5 hours
    
    def _analyze_content_types(self, posts: list[dict]) -> list[dict]:
        """Analyze which content types perform best."""
        # This would require content type metadata
        # For now, analyze by like/view ratio as proxy for quality
        type_performance = []
        
        for post in posts:
            view_count = post.get("view_count", 0)
            like_count = post.get("like_count", 0)
            
            if view_count > 0:
                ratio = like_count / view_count
                type_performance.append({
                    "post_id": post["id"],
                    "view_count": view_count,
                    "like_count": like_count,
                    "engagement_ratio": ratio,
                })
        
        type_performance.sort(key=lambda x: x["engagement_ratio"], reverse=True)
        return type_performance[:10]
    
    def _analyze_caption_lengths(self, posts: list[dict]) -> dict:
        """Analyze optimal caption lengths."""
        length_buckets = {
            "short (0-50)": [],
            "medium (51-150)": [],
            "long (151-300)": [],
            "very_long (300+)": [],
        }
        
        for post in posts:
            caption = post.get("caption", "") or ""
            length = len(caption)
            engagement = post.get("view_count", 0) + post.get("like_count", 0)
            
            if length <= 50:
                length_buckets["short (0-50)"].append(engagement)
            elif length <= 150:
                length_buckets["medium (51-150)"].append(engagement)
            elif length <= 300:
                length_buckets["long (151-300)"].append(engagement)
            else:
                length_buckets["very_long (300+)"].append(engagement)
        
        # Calculate averages
        results = {}
        for bucket, engagements in length_buckets.items():
            avg = sum(engagements) / len(engagements) if engagements else 0
            results[bucket] = {
                "avg_engagement": avg,
                "post_count": len(engagements),
            }
        
        return results
    
    def _analyze_hashtags(self, posts: list[dict]) -> dict:
        """Analyze hashtag strategies."""
        hashtag_performance = defaultdict(list)
        
        for post in posts:
            caption = post.get("caption", "") or ""
            hashtags = re.findall(r"#\w+", caption.lower())
            engagement = post.get("view_count", 0) + post.get("like_count", 0)
            
            # Analyze hashtag count
            count_bucket = min(len(hashtags), 30)  # IG max is 30
            hashtag_performance[f"count_{count_bucket}"].append(engagement)
            
            # Track individual hashtag performance
            for tag in hashtags:
                hashtag_performance[f"tag_{tag}"].append(engagement)
        
        return {
            "by_count": {
                k.replace("count_", ""): sum(v) / len(v) if v else 0
                for k, v in hashtag_performance.items()
                if k.startswith("count_")
            },
            "top_tags": sorted([
                {"tag": k.replace("tag_", ""), "avg_engagement": sum(v) / len(v)}
                for k, v in hashtag_performance.items()
                if k.startswith("tag_") and len(v) >= 3
            ], key=lambda x: x["avg_engagement"], reverse=True)[:20],
        }
    
    def _analyze_engagement_velocity(self, posts: list[dict]) -> list[dict]:
        """Analyze how quickly posts gain engagement."""
        velocity_data = []
        
        for post in posts:
            # This would require timestamp data for when likes/views came in
            # For now, use total engagement as proxy
            view_count = post.get("view_count", 0)
            like_count = post.get("like_count", 0)
            
            velocity_data.append({
                "post_id": post["id"],
                "total_engagement": view_count + like_count,
                "like_to_view_ratio": like_count / view_count if view_count > 0 else 0,
            })
        
        velocity_data.sort(key=lambda x: x["total_engagement"], reverse=True)
        return velocity_data[:20]
    
    async def _store_insights(self, patterns: dict):
        """Store insights in database for future reference."""
        try:
            self.supabase.table("content_insights").insert({
                "insights": patterns,
                "created_at": datetime.utcnow().isoformat(),
            }).execute()
        except Exception:
            # Table might not exist yet
            pass
    
    async def build_trust_network(
        self, 
        seed_account_ids: list[str],
        depth: int = 2
    ) -> dict:
        """
        Build a trust network between accounts for natural engagement.
        
        Args:
            seed_account_ids: Starting accounts to build network from
            depth: How many degrees of connection to build
            
        Returns:
            Dict with network graph and engagement recommendations
        """
        network = defaultdict(set)
        
        # Build network by analyzing existing interactions
        for account_id in seed_account_ids:
            # Find accounts this account has interacted with
            interactions = self.supabase.table("actions").select("""
                target_account_id,
                kind,
                created_at
            """).eq("actor_account_id", account_id).order("created_at", desc=True).limit(100).execute()
            
            for interaction in interactions.data or []:
                target_id = interaction.get("target_account_id")
                if target_id and target_id != account_id:
                    network[account_id].add(target_id)
                    network[target_id].add(account_id)
        
        # Expand network to specified depth
        current_layer = set(seed_account_ids)
        for _ in range(depth - 1):
            next_layer = set()
            for account_id in current_layer:
                next_layer.update(network.get(account_id, set()))
            current_layer = next_layer
        
        # Generate engagement recommendations
        recommendations = []
        for account_id, connections in network.items():
            # Suggest accounts to engage with that aren't already connected
            all_accounts = set(seed_account_ids) | current_layer
            potential_connections = all_accounts - connections - {account_id}
            
            if potential_connections:
                recommendations.append({
                    "account_id": account_id,
                    "suggested_engagements": list(potential_connections)[:5],
                    "current_connections": len(connections),
                })
        
        # Store network in cache
        self.trust_network = network
        
        return {
            "network_size": len(network),
            "total_connections": sum(len(v) for v in network.values()) // 2,
            "recommendations": recommendations[:20],
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def generate_dm_response(
        self, 
        message_text: str,
        context: Optional[dict] = None
    ) -> dict:
        """
        Generate an appropriate DM response using NLP filtering.
        
        Args:
            message_text: The incoming DM message
            context: Optional context (sender info, conversation history)
            
        Returns:
            Dict with suggested response, confidence, and action recommendation
        """
        message_lower = message_text.lower()
        
        # Detect spam/scam patterns
        spam_indicators = [
            r"\b(crypto|bitcoin|investment|double your money)\b",
            r"\b(onlyfans|subscribe|link in bio)\b",
            r"\b(won|winner|prize|congratulations)\b",
            r"http[s]?://\S+",
            r"\b(dm me|check my profile|click link)\b",
        ]
        
        spam_score = 0
        for pattern in spam_indicators:
            if re.search(pattern, message_lower):
                spam_score += 1
        
        # Detect common questions
        question_patterns = {
            "collaboration": r"\b(collab|collaboration|partnership|sponsor)\b",
            "pricing": r"\b(price|cost|rate|how much)\b",
            "location": r"\b(where|location|city|based)\b",
            "compliment": r"\b(love|amazing|great|awesome|beautiful)\b",
            "greeting": r"\b(hi|hello|hey|sup|yo)\b",
        }
        
        detected_intent = None
        for intent, pattern in question_patterns.items():
            if re.search(pattern, message_lower):
                detected_intent = intent
                break
        
        # Generate response based on analysis
        if spam_score >= 2:
            return {
                "suggested_action": "ignore",
                "response": None,
                "confidence": 0.9,
                "reason": "High spam score detected",
                "spam_score": spam_score,
            }
        elif detected_intent == "greeting":
            return {
                "suggested_action": "respond",
                "response": "Hey! Thanks for reaching out 😊",
                "confidence": 0.85,
                "reason": "Friendly greeting detected",
            }
        elif detected_intent == "compliment":
            return {
                "suggested_action": "respond",
                "response": "Thank you so much! That means a lot ❤️",
                "confidence": 0.8,
                "reason": "Compliment detected",
            }
        elif detected_intent == "collaboration":
            return {
                "suggested_action": "flag_for_review",
                "response": "Thanks for your interest! I'll have my manager reach out.",
                "confidence": 0.7,
                "reason": "Collaboration inquiry - requires human review",
            }
        elif detected_intent == "pricing":
            return {
                "suggested_action": "flag_for_review",
                "response": "I'll send you our rate card. Give me a moment!",
                "confidence": 0.75,
                "reason": "Pricing inquiry - requires human review",
            }
        else:
            # Generic safe response
            return {
                "suggested_action": "respond",
                "response": "Thanks for the message! 🙏",
                "confidence": 0.6,
                "reason": "No specific intent detected - generic response",
            }
    
    async def auto_respond_to_dm(
        self,
        account_id: str,
        dm_id: str,
        message_text: str,
        auto_approve_threshold: float = 0.8
    ) -> dict:
        """
        Automatically respond to DMs if confidence is high enough.
        
        Args:
            account_id: The account receiving the DM
            dm_id: The DM message ID
            message_text: The message content
            auto_approve_threshold: Minimum confidence for auto-response
            
        Returns:
            Dict with action taken and response details
        """
        # Generate response
        response_data = await self.generate_dm_response(message_text)
        
        # Check if we should auto-respond
        if response_data["confidence"] >= auto_approve_threshold and response_data["suggested_action"] == "respond":
            # Send response via device layer (would integrate with ADB)
            # For now, just record the intended action
            return {
                "action": "auto_responded",
                "response": response_data["response"],
                "confidence": response_data["confidence"],
                "dm_id": dm_id,
                "account_id": account_id,
            }
        elif response_data["suggested_action"] == "ignore":
            return {
                "action": "ignored",
                "reason": response_data["reason"],
                "spam_score": response_data.get("spam_score", 0),
                "dm_id": dm_id,
                "account_id": account_id,
            }
        else:
            return {
                "action": "flagged_for_human",
                "reason": response_data["reason"],
                "suggested_response": response_data.get("response"),
                "dm_id": dm_id,
                "account_id": account_id,
            }
    
    async def get_account_performance_summary(
        self,
        account_id: str,
        days: int = 7
    ) -> dict:
        """
        Get a performance summary for an account over the specified period.
        
        Args:
            account_id: The account to analyze
            days: Number of days to analyze
            
        Returns:
            Dict with performance metrics and trends
        """
        since = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Fetch recent posts
        posts = self.supabase.table("posts_log").select("*").eq("account_id", account_id).gte("posted_at", since).execute()
        
        # Fetch recent actions
        actions = self.supabase.table("actions").select("*").eq("actor_account_id", account_id).gte("created_at", since).execute()
        
        # Calculate metrics
        total_posts = len(posts.data or [])
        total_actions = len(actions.data or [])
        total_views = sum(p.get("view_count", 0) for p in (posts.data or []))
        total_likes = sum(p.get("like_count", 0) for p in (posts.data or []))
        
        avg_views = total_views / total_posts if total_posts > 0 else 0
        avg_likes = total_likes / total_posts if total_posts > 0 else 0
        
        return {
            "account_id": account_id,
            "period_days": days,
            "posts_count": total_posts,
            "actions_count": total_actions,
            "total_views": total_views,
            "total_likes": total_likes,
            "avg_views_per_post": avg_views,
            "avg_likes_per_post": avg_likes,
            "engagement_rate": (total_likes / total_views * 100) if total_views > 0 else 0,
            "timestamp": datetime.utcnow().isoformat(),
        }

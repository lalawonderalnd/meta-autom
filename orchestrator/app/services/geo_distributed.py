"""
Geo-Distributed Orchestrator Coordination.

Coordinates multiple orchestrator instances across different regions
for redundancy, load balancing, and geographic distribution.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from enum import Enum
import hashlib

from supabase import Client


class OrchestratorStatus(str, Enum):
    """Status of an orchestrator instance."""
    ACTIVE = "active"
    STANDBY = "standby"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class Region(str, Enum):
    """Supported deployment regions."""
    EU_CENTRAL = "eu-central-1"      # Frankfurt
    EU_WEST = "eu-west-1"            # Ireland
    US_EAST = "us-east-1"            # Virginia
    US_WEST = "us-west-1"            # California
    ASIA_SOUTHEAST = "ap-southeast-1"  # Singapore


class GeoDistributedCoordinator:
    """
    Coordinates multiple orchestrator instances across regions.
    
    Features:
    - Leader election for coordinated actions
    - Load balancing across instances
    - Failover handling
    - Regional affinity for accounts/devices
    """
    
    def __init__(self, supabase: Client, instance_id: str, region: Region):
        self.supabase = supabase
        self.instance_id = instance_id
        self.region = region
        self.is_leader = False
        self.last_heartbeat: Optional[datetime] = None
        self.known_instances: list[dict] = []
        
    async def register_instance(self, metadata: dict) -> dict:
        """
        Register this orchestrator instance in the cluster.
        
        Args:
            metadata: Instance metadata (capacity, capabilities, etc.)
            
        Returns:
            Registration result
        """
        instance_record = {
            "instance_id": self.instance_id,
            "region": self.region.value,
            "status": OrchestratorStatus.ACTIVE.value,
            "is_leader": False,
            "metadata": metadata,
            "last_heartbeat": datetime.utcnow().isoformat(),
            "registered_at": datetime.utcnow().isoformat(),
        }
        
        # Upsert instance record
        result = self.supabase.table("orchestrator_instances").upsert(instance_record).execute()
        
        return {
            "success": True,
            "instance_id": self.instance_id,
            "region": self.region.value,
        }
    
    async def send_heartbeat(self) -> dict:
        """
        Send heartbeat to indicate this instance is alive.
        
        Returns:
            Heartbeat result with leadership status
        """
        now = datetime.utcnow()
        
        # Update heartbeat
        self.supabase.table("orchestrator_instances").update({
            "last_heartbeat": now.isoformat(),
            "status": OrchestratorStatus.ACTIVE.value,
        }).eq("instance_id", self.instance_id).execute()
        
        self.last_heartbeat = now
        
        # Check if we should become leader
        await self._run_leader_election()
        
        return {
            "instance_id": self.instance_id,
            "is_leader": self.is_leader,
            "timestamp": now.isoformat(),
        }
    
    async def _run_leader_election(self):
        """Run leader election using timestamp-based selection."""
        # Fetch all active instances
        result = self.supabase.table("orchestrator_instances").select("*").eq(
            "status", OrchestratorStatus.ACTIVE.value
        ).order("registered_at", desc=True).execute()
        
        instances = result.data or []
        self.known_instances = instances
        
        if not instances:
            self.is_leader = False
            return
        
        # Leader is the instance with earliest registration (stable election)
        # that has sent a heartbeat in the last 30 seconds
        cutoff = datetime.utcnow() - timedelta(seconds=30)
        
        eligible_instances = [
            inst for inst in instances
            if datetime.fromisoformat(inst["last_heartbeat"]) > cutoff
        ]
        
        if not eligible_instances:
            self.is_leader = False
            return
        
        # Sort by registration time (earliest wins)
        eligible_instances.sort(key=lambda x: x.get("registered_at", ""))
        leader = eligible_instances[0]
        
        self.is_leader = (leader["instance_id"] == self.instance_id)
        
        # Update leader status in database
        for inst in instances:
            is_this_leader = inst["instance_id"] == self.instance_id and self.is_leader
            self.supabase.table("orchestrator_instances").update({
                "is_leader": is_this_leader,
            }).eq("instance_id", inst["instance_id"]).execute()
    
    async def get_cluster_status(self) -> dict:
        """
        Get status of the entire cluster.
        
        Returns:
            Cluster status summary
        """
        # Refresh instance list
        result = self.supabase.table("orchestrator_instances").select("*").order(
            "region"
        ).execute()
        
        instances = result.data or []
        
        # Categorize by status
        by_region = {}
        by_status = {}
        leaders = []
        
        for inst in instances:
            # By region
            region = inst.get("region", "unknown")
            if region not in by_region:
                by_region[region] = []
            by_region[region].append(inst)
            
            # By status
            status = inst.get("status", "unknown")
            if status not in by_status:
                by_status[status] = 0
            by_status[status] += 1
            
            # Leaders
            if inst.get("is_leader"):
                leaders.append(inst)
        
        # Check for stale instances (no heartbeat in 60s)
        now = datetime.utcnow()
        stale_count = 0
        for inst in instances:
            last_hb = inst.get("last_heartbeat")
            if last_hb:
                hb_time = datetime.fromisoformat(last_hb)
                if now - hb_time > timedelta(seconds=60):
                    stale_count += 1
                    # Mark as degraded
                    self.supabase.table("orchestrator_instances").update({
                        "status": OrchestratorStatus.DEGRADED.value,
                    }).eq("instance_id", inst["instance_id"]).execute()
        
        return {
            "total_instances": len(instances),
            "active_instances": by_status.get(OrchestratorStatus.ACTIVE.value, 0),
            "degraded_instances": by_status.get(OrchestratorStatus.DEGRADED.value, 0),
            "offline_instances": by_status.get(OrchestratorStatus.OFFLINE.value, 0),
            "stale_instances": stale_count,
            "leaders": leaders,
            "by_region": {
                region: len(insts) for region, insts in by_region.items()
            },
            "this_instance": {
                "id": self.instance_id,
                "region": self.region.value,
                "is_leader": self.is_leader,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    async def assign_account_to_region(
        self, 
        account_id: str, 
        preferred_region: Optional[Region] = None
    ) -> dict:
        """
        Assign an account to the best region/orchestrator.
        
        Args:
            account_id: Account to assign
            preferred_region: Optional preferred region
            
        Returns:
            Assignment result with target instance
        """
        # Get available instances
        result = self.supabase.table("orchestrator_instances").select("*").eq(
            "status", OrchestratorStatus.ACTIVE.value
        ).execute()
        
        instances = result.data or []
        
        if not instances:
            return {"success": False, "error": "No active orchestrators"}
        
        # Filter by preferred region if specified
        if preferred_region:
            regional_instances = [
                inst for inst in instances 
                if inst.get("region") == preferred_region.value
            ]
            if regional_instances:
                instances = regional_instances
        
        # Select instance with lowest load (simple round-robin for now)
        # In production, would use actual load metrics
        instance_hash = int(hashlib.md5(account_id.encode()).hexdigest(), 16)
        selected = instances[instance_hash % len(instances)]
        
        # Update account assignment
        self.supabase.table("accounts").update({
            "orchestrator_id": selected["instance_id"],
            "assigned_region": selected.get("region"),
        }).eq("id", account_id).execute()
        
        return {
            "success": True,
            "account_id": account_id,
            "assigned_instance": selected["instance_id"],
            "assigned_region": selected.get("region"),
        }
    
    async def broadcast_command(self, command: str, params: dict) -> dict:
        """
        Broadcast a command to all orchestrator instances (leader only).
        
        Args:
            command: Command to broadcast
            params: Command parameters
            
        Returns:
            Broadcast result
        """
        if not self.is_leader:
            return {
                "success": False,
                "error": "Only leader can broadcast commands",
            }
        
        # Store command in database for instances to poll
        command_record = {
            "command": command,
            "params": params,
            "issued_by": self.instance_id,
            "issued_at": datetime.utcnow().isoformat(),
            "acknowledged_by": [],
        }
        
        result = self.supabase.table("orchestrator_commands").insert(command_record).execute()
        
        return {
            "success": True,
            "command_id": result.data[0]["id"] if result.data else None,
            "broadcast_to": len(self.known_instances),
        }
    
    async def acknowledge_command(self, command_id: int) -> dict:
        """
        Acknowledge receipt of a broadcast command.
        
        Args:
            command_id: ID of the command to acknowledge
            
        Returns:
            Acknowledgment result
        """
        # Fetch current command
        result = self.supabase.table("orchestrator_commands").select("*").eq(
            "id", command_id
        ).execute()
        
        if not result.data:
            return {"success": False, "error": "Command not found"}
        
        command = result.data[0]
        acknowledged_by = command.get("acknowledged_by", [])
        
        if self.instance_id not in acknowledged_by:
            acknowledged_by.append(self.instance_id)
            self.supabase.table("orchestrator_commands").update({
                "acknowledged_by": acknowledged_by,
            }).eq("id", command_id).execute()
        
        return {
            "success": True,
            "command_id": command_id,
            "total_acknowledged": len(acknowledged_by),
        }
    
    async def failover_leadership(self) -> dict:
        """
        Voluntarily relinquish leadership (for graceful shutdown).
        
        Returns:
            Failover result
        """
        if not self.is_leader:
            return {"success": False, "error": "Not the leader"}
        
        # Clear our leader status
        self.supabase.table("orchestrator_instances").update({
            "is_leader": False,
            "status": OrchestratorStatus.STANDBY.value,
        }).eq("instance_id", self.instance_id).execute()
        
        self.is_leader = False
        
        # Trigger new election by updating heartbeat of other instances
        # The next heartbeat cycle will elect a new leader
        
        return {
            "success": True,
            "message": "Leadership relinquished. New election will occur.",
        }
    
    async def get_regional_load(self) -> dict:
        """
        Get load distribution across regions.
        
        Returns:
            Load statistics by region
        """
        # Count accounts per region
        result = self.supabase.table("accounts").select("assigned_region, status").execute()
        
        accounts = result.data or []
        
        by_region = {}
        for account in accounts:
            region = account.get("assigned_region", "unassigned")
            if region not in by_region:
                by_region[region] = {"total": 0, "active": 0, "warming": 0, "other": 0}
            
            by_region[region]["total"] += 1
            status = account.get("status", "")
            if status == "ACTIVE":
                by_region[region]["active"] += 1
            elif status == "WARMING":
                by_region[region]["warming"] += 1
            else:
                by_region[region]["other"] += 1
        
        return {
            "regions": by_region,
            "timestamp": datetime.utcnow().isoformat(),
        }

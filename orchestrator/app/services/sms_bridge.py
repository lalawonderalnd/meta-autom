"""
SMS Verification Bridge for Meta Autom Farm.

Integrates with 5sim and SMS-Activate APIs to automatically receive
Instagram verification codes during account creation and recovery.
"""

import httpx
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class SMSProvider(Enum):
    """Supported SMS providers."""
    FIVSIM = "5sim"
    SMS_ACTIVATE = "sms_activate"


class SMSProviderError(Exception):
    """Error from SMS provider API."""
    pass


class CodeNotFoundError(Exception):
    """No verification code received within timeout."""
    pass


class SMSBridge:
    """
    Bridge to SMS verification services.
    
    Supports:
    - 5sim.net
    - SMS-Activate.org
    
    Usage:
        bridge = SMSBridge(provider="5sim", api_key="your_key")
        
        # Order a number for Instagram
        order = await bridge.order_number(service="instagram", country="any")
        
        # Wait for code
        code = await bridge.wait_for_code(order_id=order.id, timeout=300)
        
        # Cleanup
        await bridge.cancel_order(order_id=order.id)
    """
    
    def __init__(self, provider: SMSProvider, api_key: str):
        self.provider = provider
        self.api_key = api_key
        self.base_url = self._get_base_url(provider)
        self.active_orders: Dict[str, Dict[str, Any]] = {}
        
    def _get_base_url(self, provider: SMSProvider) -> str:
        """Get API base URL for provider."""
        urls = {
            SMSProvider.FIVSIM: "https://5sim.net/v1",
            SMSProvider.SMS_ACTIVATE: "https://api.sms-activate.ru/stubs/handler_api.php"
        }
        return urls.get(provider)
    
    async def order_number(
        self,
        service: str,
        country: str = "any",
        operator: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Order a phone number for receiving SMS.
        
        Args:
            service: Service name (e.g., "instagram", "whatsapp")
            country: Country code or "any" (e.g., "us", "uk", "de")
            operator: Specific mobile operator (optional)
            
        Returns:
            Order details including phone number and order ID
        """
        if self.provider == SMSProvider.FIVSIM:
            return await self._5sim_order(service, country, operator)
        else:
            return await self._sms_activate_order(service, country, operator)
    
    async def _5sim_order(
        self,
        service: str,
        country: str,
        operator: Optional[str]
    ) -> Dict[str, Any]:
        """Order number from 5sim."""
        url = f"{self.base_url}/user/buy-number/{country}/{service}"
        
        params = {}
        if operator:
            params["operator"] = operator
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, headers=headers, timeout=30.0)
            
        if response.status_code != 200:
            raise SMSProviderError(f"5sim API error: {response.text}")
            
        data = response.json()
        
        if not data.get("phone"):
            raise SMSProviderError(f"5sim returned no phone: {data}")
        
        order_info = {
            "order_id": str(data["id"]),
            "phone": data["phone"],
            "country": data["country"],
            "operator": data.get("operator"),
            "price": data.get("price"),
            "created_at": datetime.utcnow()
        }
        
        self.active_orders[order_info["order_id"]] = order_info
        logger.info(f"5sim order created: {order_info['phone']} for ${order_info['price']}")
        
        return order_info
    
    async def _sms_activate_order(
        self,
        service: str,
        country: str,
        operator: Optional[str]
    ) -> Dict[str, Any]:
        """Order number from SMS-Activate."""
        # Map service names
        service_map = {
            "instagram": "ig",
            "whatsapp": "wa",
            "telegram": "tg"
        }
        sms_service = service_map.get(service, service)
        
        params = {
            "api_key": self.api_key,
            "action": "getNumber",
            "service": sms_service
        }
        
        if country and country != "any":
            params["country"] = country
            
        if operator:
            params["operator"] = operator
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params, timeout=30.0)
            
        text = response.text
        
        # SMS-Activate returns "ACCESS_NUMBER:id:phone" on success
        if not text.startswith("ACCESS_NUMBER:"):
            raise SMSProviderError(f"SMS-Activate error: {text}")
            
        parts = text.split(":")
        order_id = parts[1]
        phone = parts[2]
        
        order_info = {
            "order_id": order_id,
            "phone": phone,
            "country": country,
            "operator": None,
            "price": None,
            "created_at": datetime.utcnow()
        }
        
        self.active_orders[order_id] = order_info
        logger.info(f"SMS-Activate order created: {phone}")
        
        return order_info
    
    async def wait_for_code(
        self,
        order_id: str,
        timeout: int = 300,
        poll_interval: int = 5
    ) -> str:
        """
        Wait for and retrieve the verification code.
        
        Args:
            order_id: The order ID from order_number()
            timeout: Maximum seconds to wait (default: 5 minutes)
            poll_interval: Seconds between polling attempts
            
        Returns:
            The verification code (digits only)
            
        Raises:
            CodeNotFoundError: No code received within timeout
        """
        deadline = datetime.utcnow() + timedelta(seconds=timeout)
        
        while datetime.utcnow() < deadline:
            code = await self.check_for_code(order_id)
            
            if code:
                logger.info(f"Code received for order {order_id}: {code}")
                return code
            
            await asyncio.sleep(poll_interval)
        
        raise CodeNotFoundError(
            f"No code received for order {order_id} within {timeout}s"
        )
    
    async def check_for_code(self, order_id: str) -> Optional[str]:
        """
        Check if a code is available for the order.
        
        Returns:
            The code if available, None otherwise
        """
        if self.provider == SMSProvider.FIVSIM:
            return await self._5sim_check_code(order_id)
        else:
            return await self._sms_activate_check_code(order_id)
    
    async def _5sim_check_code(self, order_id: str) -> Optional[str]:
        """Check for code from 5sim."""
        url = f"{self.base_url}/check/{order_id}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            
        if response.status_code != 200:
            return None
            
        data = response.json()
        
        if data.get("sms"):
            # Extract code from SMS text
            sms_text = data["sms"][0]["text"]
            code = self._extract_code_from_sms(sms_text)
            return code
            
        return None
    
    async def _sms_activate_check_code(self, order_id: str) -> Optional[str]:
        """Check for code from SMS-Activate."""
        params = {
            "api_key": self.api_key,
            "action": "getStatus",
            "id": order_id
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params, timeout=10.0)
            
        text = response.text
        
        # Status codes: STATUS_WAIT_CODE, STATUS_OK, etc.
        if text.startswith("STATUS_OK:"):
            sms_text = text.split(":", 1)[1]
            code = self._extract_code_from_sms(sms_text)
            return code
            
        return None
    
    def _extract_code_from_sms(self, sms_text: str) -> Optional[str]:
        """
        Extract numeric verification code from SMS text.
        
        Handles formats like:
        - "Your Instagram code: 123456"
        - "123456 is your verification code"
        - "IG code: 123456"
        """
        import re
        
        # Look for 4-8 digit sequences
        patterns = [
            r'\b(\d{4,8})\b',  # Any 4-8 digits
            r'code[:\s]+(\d{4,8})',  # "code: 123456"
            r'(\d{4,8})\s*is\s*your',  # "123456 is your"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, sms_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Fallback: return first number sequence
        match = re.search(r'\d{4,8}', sms_text)
        if match:
            return match.group(0)
            
        return None
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an active order."""
        if self.provider == SMSProvider.FIVSIM:
            return await self._5sim_cancel(order_id)
        else:
            return await self._sms_activate_cancel(order_id)
    
    async def _5sim_cancel(self, order_id: str) -> bool:
        """Cancel 5sim order."""
        url = f"{self.base_url}/cancel/{order_id}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10.0)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to cancel 5sim order {order_id}: {e}")
            return False
    
    async def _sms_activate_cancel(self, order_id: str) -> bool:
        """Cancel SMS-Activate order."""
        params = {
            "api_key": self.api_key,
            "action": "setStatus",
            "status": "8",  # Status 8 = cancel
            "id": order_id
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params, timeout=10.0)
            return response.text == "ACCESS_CANCEL"
        except Exception as e:
            logger.error(f"Failed to cancel SMS-Activate order {order_id}: {e}")
            return False
    
    async def finish_order(self, order_id: str) -> bool:
        """Mark order as complete (after successful verification)."""
        if self.provider == SMSProvider.FIVSIM:
            return await self._5sim_finish(order_id)
        else:
            return await self._sms_activate_finish(order_id)
    
    async def _5sim_finish(self, order_id: str) -> bool:
        """Finish 5sim order."""
        url = f"{self.base_url}/finish/{order_id}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10.0)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to finish 5sim order {order_id}: {e}")
            return False
    
    async def _sms_activate_finish(self, order_id: str) -> bool:
        """Finish SMS-Activate order."""
        params = {
            "api_key": self.api_key,
            "action": "setStatus",
            "status": "6",  # Status 6 = complete
            "id": order_id
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params, timeout=10.0)
            return response.text == "ACCESS_READY"
        except Exception as e:
            logger.error(f"Failed to finish SMS-Activate order {order_id}: {e}")
            return False
    
    async def get_balance(self) -> float:
        """Get account balance from provider."""
        if self.provider == SMSProvider.FIVSIM:
            return await self._5sim_balance()
        else:
            return await self._sms_activate_balance()
    
    async def _5sim_balance(self) -> float:
        """Get 5sim balance."""
        url = f"{self.base_url}/user/profile"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            
        if response.status_code != 200:
            raise SMSProviderError(f"5sim balance check failed: {response.text}")
            
        data = response.json()
        return float(data.get("balance", 0))
    
    async def _sms_activate_balance(self) -> float:
        """Get SMS-Activate balance."""
        params = {
            "api_key": self.api_key,
            "action": "getBalance"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params, timeout=10.0)
            
        # Returns "ACCESS_BALANCE:123.45"
        if not response.text.startswith("ACCESS_BALANCE:"):
            raise SMSProviderError(f"SMS-Activate balance check failed: {response.text}")
            
        return float(response.text.split(":")[1])


# Convenience function
async def get_instagram_code(
    provider: SMSProvider,
    api_key: str,
    country: str = "any",
    timeout: int = 300
) -> tuple[str, str, str]:
    """
    Complete flow: order number, wait for code, return (phone, code, order_id).
    
    Caller should call finish_order() or cancel_order() after using the code.
    """
    bridge = SMSBridge(provider, api_key)
    
    # Order number
    order = await bridge.order_number("instagram", country)
    phone = order["phone"]
    order_id = order["order_id"]
    
    # Wait for code
    code = await bridge.wait_for_code(order_id, timeout)
    
    return phone, code, order_id


import asyncio

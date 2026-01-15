"""
Turnstile 驗證服務
"""
import os
import httpx
from typing import Optional, Tuple


class TurnstileService:
    """Cloudflare Turnstile 驗證服務"""
    
    TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    
    @staticmethod
    def get_secret_key() -> str:
        """取得 Turnstile Secret Key"""
        return os.getenv(
            "TURNSTILE_SECRET_KEY",
            "1x0000000000000000000000000000000AA"  # 測試模式預設金鑰
        )
    
    @staticmethod
    async def verify_token(token: str, remote_ip: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        驗證 Turnstile token
        
        Args:
            token: Turnstile token
            remote_ip: 使用者 IP（可選）
            
        Returns:
            Tuple[bool, Optional[str]]: (是否驗證成功, 錯誤訊息)
        """
        if not token:
            return (False, "MISSING_TOKEN")
        
        secret_key = TurnstileService.get_secret_key()
        
        # 準備驗證請求
        data = {
            "secret": secret_key,
            "response": token
        }
        
        if remote_ip:
            data["remoteip"] = remote_ip
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    TurnstileService.TURNSTILE_VERIFY_URL,
                    data=data
                )
                response.raise_for_status()
                result = response.json()
                
                # 檢查驗證結果
                if result.get("success"):
                    return (True, None)
                else:
                    error_codes = result.get("error-codes", [])
                    error_msg = ", ".join(error_codes) if error_codes else "VERIFICATION_FAILED"
                    return (False, error_msg)
                    
        except httpx.TimeoutException:
            return (False, "TIMEOUT")
        except httpx.RequestError as e:
            return (False, f"REQUEST_ERROR: {str(e)}")
        except Exception as e:
            return (False, f"UNKNOWN_ERROR: {str(e)}")

import time
import requests
from typing import Optional


class GigaChatClient:
    """
    Минимальный клиент GigaChat:
    - берёт access_token по вашему авторизационному токену (client secret / API key)
    - отправляет запрос в chat/completions
    """

    def __init__(
        self,
        auth_token: str,
        scope: str = "GIGACHAT_API_PERS",
        timeout: int = 60,
        base_url: str = "https://gigachat.devices.sberbank.ru/api/v1",
        auth_url: str = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        verify_ssl: bool = False,
    ):
        self.auth_token = auth_token
        self.scope = scope
        self.timeout = timeout
        self.base_url = base_url
        self.auth_url = auth_url
        self.verify_ssl = verify_ssl

        self._access_token: Optional[str] = None
        self._expires_at: float = 0.0

    def _get_access_token(self) -> str:
        # кешируем токен
        now = time.time()
        if self._access_token and now < self._expires_at - 30:
            return self._access_token

        if not self.auth_token:
            raise RuntimeError("GIGACHAT_TOKEN is not set (env var). Put it into secrets/env.")

        headers = {
            "Authorization": f"Basic {self.auth_token}",
            "RqUID": "00000000-0000-0000-0000-000000000000",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        data = {"scope": self.scope}

        r = requests.post(
            self.auth_url,
            headers=headers,
            data=data,
            timeout=self.timeout,
            verify=self.verify_ssl,
        )
        if r.status_code != 200:
            raise RuntimeError(f"Failed to get access token: {r.status_code} {r.text}")

        payload = r.json()
        access = payload.get("access_token")
        expires_in = payload.get("expires_in", 300)

        if not access:
            raise RuntimeError(f"No access_token in response: {payload}")

        self._access_token = access
        self._expires_at = now + float(expires_in)
        return access

    def chat_completion(self, model: str, prompt: str, temperature: float = 0.2, max_tokens: int = 800) -> str:
        token = self._get_access_token()
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        body = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": "Ты строгий оценщик. Отвечай только JSON по схеме."},
                {"role": "user", "content": prompt},
            ],
        }

        r = requests.post(url, headers=headers, json=body, timeout=self.timeout, verify=self.verify_ssl)
        if r.status_code != 200:
            raise RuntimeError(f"Chat completion failed: {r.status_code} {r.text}")

        data = r.json()
        # стандартно: choices[0].message.content
        try:
            return data["choices"][0]["message"]["content"]
        except Exception:
            raise RuntimeError(f"Unexpected response format: {data}")

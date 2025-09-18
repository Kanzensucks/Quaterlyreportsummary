import requests
from typing import Dict, Optional

class OllamaClient:
    """Tiny wrapper around Ollama's HTTP API with health & model checks."""

    def __init__(self, host: str = "http://127.0.0.1:11434", timeout: int = 60):
        self.host = host.rstrip("/")
        self.timeout = timeout

    def is_alive(self) -> bool:
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=self.timeout)
            return r.ok
        except requests.RequestException:
            return False

    def has_model(self, name: str) -> bool:
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=self.timeout)
            r.raise_for_status()
            tags = r.json().get("models", [])
            return any(m.get("name") == name for m in tags)
        except requests.RequestException:
            return False

    def ensure_model(self, name: str) -> None:
        if self.has_model(name):
            return
        try:
            resp = requests.post(
                f"{self.host}/api/pull",
                json={"name": name, "stream": False},
                timeout=max(self.timeout, 300),
            )
            if not resp.ok:
                raise RuntimeError(resp.text)
        except requests.RequestException as e:
            raise RuntimeError(
                f"Model '{name}' not available and pull failed: {e}\n"
                f"Run: ollama pull {name} (and ensure ollama serve is running)."
            )

    def generate(
        self, model: str, prompt: str, system: Optional[str] = None, options: Optional[Dict] = None
    ) -> str:
        payload = {
            "model": model,
            "prompt": prompt if system is None else f"<SYS>\n{system}\n</SYS>\n{prompt}",
            "stream": False,
        }
        if options:
            payload["options"] = options
        r = requests.post(f"{self.host}/api/generate", json=payload, timeout=max(self.timeout, 120))
        r.raise_for_status()
        data = r.json()
        return data.get("response", "")

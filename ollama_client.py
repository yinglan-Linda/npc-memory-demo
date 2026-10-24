"""Local Ollama transport; no cloud credentials or parent project required."""
import json
import logging
import os
from pathlib import Path
import requests

class Config:
    def __init__(self):
        self.settings = json.loads((Path(__file__).resolve().parent / "config.json").read_text(encoding="utf-8-sig"))
    def get(self, key, default=None):
        if key == "ollama.base_url":
            return os.environ.get("OLLAMA_BASE_URL", self.settings.get("base_url", default))
        return self.settings.get(key.removeprefix("ollama."), default)

config = Config()
logger = logging.getLogger(__name__)
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", config.get("ollama.base_url")).rstrip("/")

def fallback_to_ollama(prompt, *, stage="generation", run_id=None):
    """Call the configured local Ollama model."""
    local_model = config.get("ollama.model", "qwen2.5:3b")
    num_predict = config.get("ollama.num_predict", 512)
    timeout = config.get("ollama.timeout", 180)
    
    payload = {
        "model": local_model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": num_predict}
    }
    try:
        response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=timeout)
        if response.status_code == 200:
            result = response.json()
            content = result.get("response") if isinstance(result, dict) else None
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Missing Ollama response text")
            logger.info("Ollama success: model=%s", local_model)
            metadata = {
                "configured_model": local_model, "actual_model": result.get("model"),
                "effective_max_tokens": num_predict, "stage": stage,
                "finish_reason": result.get("done_reason"),
                "native_finish_reason": result.get("done_reason"),
                "usage": {key: result[key] for key in ("prompt_eval_count", "eval_count") if key in result} or None,
            }
            logger.info("[COMPLETION] run_id=%s %s", run_id, metadata)
            return {"content": content, "model": local_model, "source": "ollama", **metadata}
        else:
            error = f"Ollama returned HTTP {response.status_code}."
            if response.status_code == 404:
                error += (f" Model '{local_model}' may not be installed on this server. "
                          f"Run: ollama pull {local_model}; check ollama.base_url.")
    except requests.Timeout as e:
        error = (f"Ollama request or response failed ({type(e).__name__}). "
                 f"Model '{local_model}' did not finish within {timeout}s. "
                 "Increase ollama.timeout in config.json; "
                 "check Ollama service load and try again.")
    except requests.ConnectionError:
        error = ("Ollama request or response failed (ConnectionError). "
                 "Cannot connect to the configured server; start it with ollama serve "
                 "and check ollama.base_url.")
    except Exception as e:
        error = f"Ollama request or response failed ({type(e).__name__})."
    return {"content": "", "model": local_model, "source": "error", "error": error}

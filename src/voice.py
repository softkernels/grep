import os
import hashlib
import logging
import threading
import subprocess
from pathlib import Path
import requests

log = logging.getLogger(__name__)


class Voice:
    def __init__(self, config):
        self.config = config
        self.voice_id = config.get("voice_id", "N2lVS1w4EtoT3dr4eOWO")
        self.model = config.get("model", "eleven_turbo_v2")
        self.cache_dir = Path(config.get("cache_dir", "cache/wav"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._speaking = False
        self._lock = threading.Lock()
        self._api_key = os.environ.get(config.get("api_key_env", "ELEVENLABS_API_KEY"), "")
        if not self._api_key:
            log.warning("no elevenlabs api key set")

    def _cache_path(self, text: str) -> Path:
        # hash includes voice_id to prevent collision across voices
        key = f"{self.voice_id}:{text}"
        h = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self.cache_dir / f"{h}.mp3"

    def speak(self, text: str, block: bool = True):
        path = self._cache_path(text)
        if not path.exists():
            ok = self._tts_fetch(text, path)
            if not ok:
                log.error("tts fetch failed for: %s", text[:40])
                return False

        if block:
            self._play(path)
        else:
            t = threading.Thread(target=self._play, args=(path,), daemon=True)
            t.start()
        return True

    def _tts_fetch(self, text: str, out_path: Path) -> bool:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            "model_id": self.model,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            },
        }
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=10)
            r.raise_for_status()
            out_path.write_bytes(r.content)
            log.debug("tts cached: %s", out_path.name)
            return True
        except Exception as e:
            log.error("tts error: %s", e)
            return False

    def _play(self, path: Path):
        with self._lock:
            self._speaking = True
            try:
                subprocess.run(
                    ["mpg123", "-q", str(path)],
                    check=True,
                    timeout=60,
                )
            except subprocess.CalledProcessError as e:
                log.error("playback error: %s", e)
            except FileNotFoundError:
                # fallback to aplay if mpg123 missing
                subprocess.run(["aplay", str(path)], check=False)
            finally:
                self._speaking = False

    def is_speaking(self) -> bool:
        return self._speaking

    def clear_cache(self):
        for f in self.cache_dir.glob("*.mp3"):
            f.unlink()
        log.info("voice cache cleared")

    def shutdown(self):
        pass

    def cache_stats(self) -> dict:
        files = list(self.cache_dir.glob("*.mp3"))
        total = sum(f.stat().st_size for f in files)
        return {"count": len(files), "bytes": total}

    def evict_oldest(self, keep: int = 100):
        files = sorted(self.cache_dir.glob("*.mp3"), key=lambda f: f.stat().st_mtime)
        for f in files[:-keep]:
            f.unlink()

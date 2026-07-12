"""通过 subprocess 隔离执行 Python 爬虫"""
import asyncio
import json
import os
import sys
import tempfile
from loguru import logger


class SpiderPyRuntime:
    async def call(self, method: str, script_path: str, *args) -> dict:
        if not os.path.isfile(script_path):
            return {"error": f"Script not found: {script_path}"}

        payload = json.dumps({"method": method, "args": [str(a) for a in args]})

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write(payload)
            tmp_path = f.name

        try:
            cmd = [sys.executable, script_path, tmp_path]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=60
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                logger.error(f"Python spider timeout: {script_path}")
                return {"error": "timeout"}

            if proc.returncode != 0:
                err_msg = stderr.decode("utf-8", errors="replace")[:500]
                logger.error(f"Python spider error: {err_msg}")
                return {"error": err_msg}

            text = stdout.decode("utf-8", errors="replace").strip()
            if not text:
                return {}
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"raw": text}
        finally:
            os.unlink(tmp_path)

import gzip
import signal
import stat
from pathlib import Path
from subprocess import Popen, TimeoutExpired
from time import sleep
from typing import Optional

import requests
from loguru import logger


class MihomoCore:
    VERSION = "1.19.1"
    MIHOMO_CORE_URL = f"https://github.com/MetaCubeX/mihomo/releases/download/v{VERSION}/mihomo-linux-amd64-v{VERSION}.gz"
    PATH = Path(__file__).parent.parent / "mihomo.gz"
    CORE_PATH = Path(__file__).parent.parent / "mihomo"
    CHUNK_SIZE = 8192

    def __init__(self):
        self.process: Optional[Popen] = None
        result = self.download_mihomo_core()
        if not result:
            raise Exception("Download mihomo core failed")
        self.unzip_mihomo_core()

    def download_mihomo_core(self):
        if self.PATH.exists():
            return True
        logger.info(f"Downloading mihomo core from {self.PATH}...")
        response = requests.get(self.MIHOMO_CORE_URL, stream=True)
        if response.status_code != 200:
            return False
        with open(self.PATH, 'wb') as f:
            for i, chunk in enumerate(response.iter_content(chunk_size=self.CHUNK_SIZE)):
                if not chunk:
                    break
                f.write(chunk)
                if i % 20 == 0:
                    logger.info(f"Downloading({(self.CHUNK_SIZE * (i + 1))}/{response.headers.get('Content-Length')})")
            f.flush()
        logger.info(f"Downloaded mihomo core from {self.PATH}...")
        return True

    def unzip_mihomo_core(self):
        if self.CORE_PATH.exists():
            return
        with gzip.open(self.PATH, 'rb') as f:
            with open(self.CORE_PATH, 'wb') as f_out:
                f_out.write(f.read())
                f_out.flush()
        self.CORE_PATH.chmod(self.CORE_PATH.stat().st_mode | stat.S_IEXEC)

    def start_mihomo_core_process(self):
        self.process = Popen([self.CORE_PATH])

    @property
    def is_running(self):
        if self.process is None:
            return False
        return self.process.poll() is None

    def stop(self):
        if self.process is None:
            return
        self.process.send_signal(signal.SIGINT)
        try:
            self.process.wait(timeout=5)
        except TimeoutExpired:
            self.process.terminate()
        self.process = None


if __name__ == '__main__':
    core = MihomoCore()
    print(core.is_running)
    core.start_mihomo_core_process()
    print(core.is_running)
    sleep(3)
    core.stop()
    print(core.is_running)

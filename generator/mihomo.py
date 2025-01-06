import gzip
import signal
import stat
import sys
import urllib.parse
from pathlib import Path
from subprocess import Popen, TimeoutExpired
from time import sleep
from typing import Optional

import requests
import requests_unixsocket
import yaml
from loguru import logger


class MihomoCore:
    VERSION = "1.19.1"
    MIHOMO_CORE_URL = f"https://github.com/MetaCubeX/mihomo/releases/download/v{VERSION}/mihomo-linux-amd64-v{VERSION}.gz"
    PATH = Path(__file__).parent.parent / "mihomo.gz"
    CORE_PATH = Path(__file__).parent.parent / "mihomo"
    SOCKET_PATH = '/tmp/mihomo.sock'
    CHUNK_SIZE = 8192

    def __init__(self):
        self.process: Optional[Popen] = None
        result = self.download_mihomo_core()
        if not result:
            raise Exception("Download mihomo core failed")
        self.unzip_mihomo_core()
        self.session = requests_unixsocket.Session()

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
        self.process = Popen([self.CORE_PATH, '-ext-ctl-unix', self.SOCKET_PATH, '-f', '../example/generated.yml'])
        self.wait_for_unix_socket_ready()

    @property
    def is_running(self):
        if self.process is None:
            return False
        return self.process.poll() is None

    def stop(self):
        if self.session is not None:
            self.session.close()
            self.session = None
        if self.process is None:
            return
        self.process.send_signal(signal.SIGINT)
        try:
            self.process.wait(timeout=5)
        except TimeoutExpired:
            self.process.terminate()
        self.process = None

    def version(self):
        try:
            response = self.session.get(f'http+unix://{urllib.parse.quote(self.SOCKET_PATH, safe="")}/version')
            return response.json()
        except Exception as e:
            logger.warning(f'Error accessing api version: {e}')
            return None

    def put_configs(self, configs):
        try:
            print(configs)
            response = self.session.put(
                f'http+unix://{urllib.parse.quote(self.SOCKET_PATH, safe="")}/configs?force=true',
                json=configs)
            return response.text
        except Exception as e:
            logger.warning(f'Error accessing api put_configs: {e}')
            return None

    def configs(self):
        try:
            response = self.session.get(f'http+unix://{urllib.parse.quote(self.SOCKET_PATH, safe="")}/configs')
            return response.json()
        except Exception as e:
            logger.warning(f'Error accessing api configs: {e}')
            return None

    def put_proxy(self, proxy_data):
        try:
            print(proxy_data)
            response = self.session.put(
                f'http+unix://{urllib.parse.quote(self.SOCKET_PATH, safe="")}/providers/proxies/default',
                json=proxy_data)
            print(response)
            return response.text
        except Exception as e:
            logger.warning(f'Error accessing api put_proxy: {e}')
            return None

    def proxy_delay(self, proxy_name):
        try:
            url = 'http://www.gstatic.com/generate_204'
            response = self.session.get(
                f'http+unix://{urllib.parse.quote(self.SOCKET_PATH, safe="")}/proxies/{proxy_name}/delay?url={urllib.parse.quote(url)}&timeout=5000')
            return response.json()
        except Exception as e:
            logger.warning(f'Error accessing api proxy_delay: {e}')
            return None

    def proxies(self):
        try:
            response = self.session.get(
                f'http+unix://{urllib.parse.quote(self.SOCKET_PATH, safe="")}/proxies')
            return response.json()
        except Exception as e:
            logger.warning(f'Error accessing api proxies: {e}')
            return None

    def wait_for_unix_socket_ready(self):
        for i in range(50):
            if not self.is_running:
                logger.error(f'Mihomo process exited unexpectedly ({self.process.returncode})')
                sys.exit(99)
            logger.info(f"Waiting for mihomo socket to come online ({i})...")
            sleep(5)
            if self.version() is not None:
                return


if __name__ == '__main__':
    core = MihomoCore()
    print(core.is_running)
    core.start_mihomo_core_process()
    print(core.is_running)
    print(core.version())
    with open(Path(__file__).parent.parent / "example" / "generated.yml", 'r') as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        core.put_configs(data)
    sleep(5)
    print("==============================")
    for k, v in core.proxies()['proxies'].items():
        if k in ('COMPATIBLE', 'DIRECT', 'GLOBAL', 'PASS', 'PROXY', 'REJECT', 'REJECT-DROP'):
            continue
        print(k, '=>', core.proxy_delay(k))
    sleep(10)
    core.stop()
    print(core.is_running)

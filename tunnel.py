import os
import sys
import time
import re
import threading
import subprocess
import logging

logger = logging.getLogger('TunnelManager')

class TunnelManager:
    _instance = None
    
    def __init__(self, port=8787):
        self.port = port
        self.public_url = None
        self.process = None
        self.is_running = False
        self.thread = None
        self.lock = threading.Lock()
        
    @classmethod
    def get_instance(cls, port=8787):
        if cls._instance is None:
            cls._instance = cls(port=port)
        return cls._instance
        
    def start(self):
        with self.lock:
            if self.is_running and self.process and self.process.poll() is None:
                return self.public_url
                
            self.thread = threading.Thread(target=self._run_tunnel, daemon=True)
            self.thread.start()
            
            # Wait up to 15 seconds for public URL
            start_t = time.time()
            while time.time() - start_t < 15:
                if self.public_url:
                    break
                time.sleep(0.5)
                
            return self.public_url
            
    def _run_tunnel(self):
        cloudflared_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cloudflared.exe')
        if not os.path.exists(cloudflared_exe):
            logger.error(f'cloudflared.exe not found at {cloudflared_exe}')
            return
            
        while True:
            try:
                cmd = [cloudflared_exe, 'tunnel', '--url', f'http://127.0.0.1:{self.port}']
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                self.is_running = True
                logger.info(f'Cloudflare Tunnel process started for port {self.port}')
                
                for line in self.process.stdout:
                    if not line:
                        break
                    match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                    if match:
                        url = match.group(0)
                        if url != self.public_url:
                            self.public_url = url
                            logger.info(f'🌐 Global Cloudflare HTTPS URL ready: {self.public_url}')
                            
                self.process.wait()
            except Exception as e:
                logger.error(f'Tunnel process exception: {e}')
                
            self.is_running = False
            time.sleep(5)  # Reconnect delay if tunnel drops
            
    def get_url(self):
        return self.public_url
        
    def stop(self):
        with self.lock:
            if self.process and self.process.poll() is None:
                try:
                    self.process.terminate()
                    self.process.wait(timeout=3)
                except Exception:
                    pass
            self.is_running = False
            self.public_url = None

tunnel_manager = TunnelManager.get_instance()

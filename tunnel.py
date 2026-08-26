import os
import sys
import time
import re
import threading
import subprocess
import logging
import urllib.request
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger('TunnelManager')

class TunnelManager:
    _instance = None
    
    def __init__(self, port=8787):
        self.port = port
        self.fixed_url = "https://investpro.loca.lt"
        self.cloudflare_url = None
        self.pages_url = "https://investpro-6jp.pages.dev"
        self.public_ip = "103.113.2.97"
        self.cf_process = None
        self.cf_named_process = None
        self.lt_process = None
        self.is_running = False
        self.lock = threading.Lock()
        
    @classmethod
    def get_instance(cls, port=8787):
        if cls._instance is None:
            cls._instance = cls(port=port)
        return cls._instance
        
    def start(self):
        with self.lock:
            if self.is_running:
                return self.cloudflare_url or self.pages_url or self.fixed_url
                
            self.is_running = True
            
            # If running on Linux (Render Cloud), no local subprocess tunnels needed
            if sys.platform != 'win32' or os.getenv("RENDER"):
                return self.pages_url

            # Fetch public IP
            threading.Thread(target=self._fetch_public_ip, daemon=True).start()
            
            # Launch permanent named tunnel (investpro.loca.lt)
            threading.Thread(target=self._run_localtunnel, daemon=True).start()
            
            # Launch Cloudflare Quick Direct Tunnel (Zero passcodes)
            threading.Thread(target=self._run_cloudflare_quick, daemon=True).start()
            
            # Launch Cloudflare Named Zero Trust Tunnel if token exists
            if os.getenv("CLOUDFLARE_TUNNEL_TOKEN"):
                threading.Thread(target=self._run_cloudflare_named, daemon=True).start()
            
            return self.pages_url

    def _fetch_public_ip(self):
        try:
            ip = urllib.request.urlopen('https://api.ipify.org', timeout=5).read().decode('utf-8').strip()
            if ip:
                self.public_ip = ip
        except Exception:
            pass

    def _run_localtunnel(self):
        """Launch permanent fixed subdomain (https://investpro.loca.lt)"""
        while self.is_running:
            try:
                cmd = ['cmd.exe', '/c', 'npx', '-y', 'localtunnel', '--port', str(self.port), '--subdomain', 'investpro']
                self.lt_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                for line in self.lt_process.stdout:
                    if not line:
                        break
                    match = re.search(r'https://[a-zA-Z0-9-]+\.loca\.lt', line)
                    if match:
                        self.fixed_url = match.group(0)
                        logger.info(f"⚡ Localtunnel URL: {self.fixed_url}")
                self.lt_process.wait()
            except Exception as e:
                logger.error(f"Localtunnel error: {e}")
            time.sleep(3)

    def _run_cloudflare_quick(self):
        """Launch direct Cloudflare quick tunnel (Zero passwords, Zero IP prompts)"""
        cloudflared_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cloudflared.exe')
        if not os.path.exists(cloudflared_exe):
            return
            
        while self.is_running:
            try:
                cmd = [cloudflared_exe, 'tunnel', '--url', f'http://127.0.0.1:{self.port}']
                self.cf_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                for line in self.cf_process.stdout:
                    if not line:
                        break
                    match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                    if match:
                        self.cloudflare_url = match.group(0)
                        logger.info(f"🌐 Cloudflare Direct URL Ready: {self.cloudflare_url}")
                self.cf_process.wait()
            except Exception as e:
                logger.error(f"Cloudflare quick tunnel error: {e}")
            time.sleep(5)

    def _run_cloudflare_named(self):
        """Launch Cloudflare Zero Trust Named Tunnel"""
        cloudflared_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cloudflared.exe')
        cf_token = os.getenv("CLOUDFLARE_TUNNEL_TOKEN")
        if not os.path.exists(cloudflared_exe) or not cf_token:
            return
            
        while self.is_running:
            try:
                cmd = [cloudflared_exe, 'tunnel', 'run', '--token', cf_token]
                self.cf_named_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                self.cf_named_process.wait()
            except Exception as e:
                logger.error(f"Cloudflare named tunnel error: {e}")
            time.sleep(5)
            
    def get_urls(self):
        return {
            'fixed_url': self.fixed_url,
            'cloudflare_url': self.cloudflare_url,
            'pages_url': self.pages_url,
            'public_ip': self.public_ip
        }
        
    def stop(self):
        self.is_running = False
        for p in [self.cf_process, self.cf_named_process, self.lt_process]:
            if p and p.poll() is None:
                try:
                    p.terminate()
                except Exception:
                    pass

tunnel_manager = TunnelManager.get_instance()

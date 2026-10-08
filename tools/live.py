"""Live thumbnails: drive headless Chrome over the DevTools protocol, so a thumbnail can catch a game mid-animation.

thumbs.py uses this for games with "thumb_live" in games.json. The game is first played into position with reduced
motion on ("thumb_steps", instant), then motion is switched on, "thumb_live": {"steps": [...], "after": ms} is played
in real time, and the play area is captured `after` ms later: planes in flight, crates in the air.
Standard library only: a minimal WebSocket client for the one local DevTools connection.
"""
import base64
import json
import os
import socket
import struct
import subprocess
import tempfile
import time
import urllib.request


class DevTools:
    def __init__(self, chrome, width, height, scale):
        self.port = 9300 + os.getpid() % 500
        self.profile = tempfile.TemporaryDirectory()
        self.proc = subprocess.Popen([chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars',
                                      f'--remote-debugging-port={self.port}', f'--user-data-dir={self.profile.name}',
                                      f'--window-size={width},{height}', f'--force-device-scale-factor={scale}', 'about:blank'],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(80):
            try:
                pages = json.load(urllib.request.urlopen(f'http://127.0.0.1:{self.port}/json', timeout=1))
                url = next(p['webSocketDebuggerUrl'] for p in pages if p['type'] == 'page')
                break
            except Exception:
                time.sleep(.25)
        else:
            raise RuntimeError('Chrome DevTools did not start')
        host, path = url[len('ws://'):].split('/', 1)
        hostname, port = host.split(':')
        self.sock = socket.create_connection((hostname, int(port)))
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((f'GET /{path} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n'
                           f'Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n').encode())
        reply = b''
        while b'\r\n\r\n' not in reply:
            reply += self.sock.recv(4096)
        assert b' 101 ' in reply.split(b'\r\n')[0], reply[:80]
        self.buffer = reply.split(b'\r\n\r\n', 1)[1]
        self.next_id = 0

    def _read(self, n):
        while len(self.buffer) < n:
            chunk = self.sock.recv(1 << 16)
            if not chunk:
                raise ConnectionError('DevTools closed')
            self.buffer += chunk
        data, self.buffer = self.buffer[:n], self.buffer[n:]
        return data

    def _frame(self):
        message = b''
        while True:
            b0, b1 = self._read(2)
            length = b1 & 0x7F
            if length == 126:
                length = struct.unpack('>H', self._read(2))[0]
            elif length == 127:
                length = struct.unpack('>Q', self._read(8))[0]
            message += self._read(length)
            if b0 & 0x80:
                return message.decode()

    def send(self, method, **params):
        self.next_id += 1
        payload = json.dumps({'id': self.next_id, 'method': method, 'params': params}).encode()
        mask = os.urandom(4)
        n = len(payload)
        header = bytes([0x81]) + (bytes([0x80 | n]) if n < 126 else bytes([0x80 | 126]) + struct.pack('>H', n) if n < 65536
                                  else bytes([0x80 | 127]) + struct.pack('>Q', n))
        self.sock.sendall(header + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(payload)))
        while True:
            reply = json.loads(self._frame())
            if reply.get('id') == self.next_id:
                if 'error' in reply:
                    raise RuntimeError(f'{method}: {reply["error"]}')
                return reply.get('result', {})

    def evaluate(self, expression):
        result = self.send('Runtime.evaluate', expression=expression, awaitPromise=True, returnByValue=True)
        return result.get('result', {}).get('value')

    def reduce_motion(self, on):
        self.send('Emulation.setEmulatedMedia', features=[{'name': 'prefers-reduced-motion', 'value': 'reduce' if on else 'no-preference'}])

    def close(self):
        try:
            self.sock.close()
        finally:
            self.proc.kill()
            self.proc.wait()
            self.profile.cleanup()


# Plays steps one after another, 400 ms apart: a selector to click (SVG elements too), {"set": selector, "value": v}
# for a slider, or {"key": selector, "press": key, "times": n} for keyboard controls.
STEPS_JS = '''(async steps=>{const wait=ms=>new Promise(r=>setTimeout(r,ms));
for(const t of steps){if(typeof t==='string'){const e=document.querySelector(t);if(e&&e.click)e.click();else if(e)e.dispatchEvent(new MouseEvent('click',{bubbles:true}));}
else if(t.key){const e=document.querySelector(t.key);for(let i=0;i<(t.times||1);i++)e&&e.dispatchEvent(new KeyboardEvent('keydown',{key:t.press,bubbles:true,cancelable:true}));}
else{const e=document.querySelector(t.set);if(e){e.value=t.value;e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));}}
await wait(%d);}return true;})(%s)'''


def capture(chrome, url, play, steps, live, out_png, box, size):
    """Play the game into position, then live, and save a PNG of the play area (box() turns its rect into a clip)."""
    width, height, scale = size
    dev = DevTools(chrome, width, height, scale)
    try:
        dev.send('Page.enable')
        dev.reduce_motion(True)
        dev.send('Page.navigate', url=url)
        time.sleep(1.5)
        dev.evaluate(STEPS_JS % (400, json.dumps(steps)))
        time.sleep(.8)
        dev.reduce_motion(False)
        dev.evaluate(STEPS_JS % (0, json.dumps(live.get('steps', []))))
        time.sleep(live.get('after', 1000) / 1000)
        rect = dev.evaluate(f'(()=>{{const r=document.querySelector({json.dumps(play)}).getBoundingClientRect();return [r.left+scrollX,r.top+scrollY,r.width,r.height];}})()')
        x, y, w, h = box(*rect)
        shot = dev.send('Page.captureScreenshot', format='png', captureBeyondViewport=True,
                        clip={'x': x / scale, 'y': y / scale, 'width': w / scale, 'height': h / scale, 'scale': 1})
        with open(out_png, 'wb') as f:
            f.write(base64.b64decode(shot['data']))
    finally:
        dev.close()

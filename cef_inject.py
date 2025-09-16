# cef_inject.py
import requests, json, time
from websocket import create_connection

DEVTOOLS_HOST = "127.0.0.1"
DEVTOOLS_PORT = 8080

def get_ws_url():
    r = requests.get(f"http://{DEVTOOLS_HOST}:{DEVTOOLS_PORT}/json")
    r.raise_for_status()
    j = r.json()
    # just pick first target for now
    return j[0]["webSocketDebuggerUrl"]

def eval_js(expression):
    ws_url = get_ws_url()
    ws = create_connection(ws_url)
    try:
        msg = {
            "id": int(time.time()),
            "method": "Runtime.evaluate",
            "params": {"expression": expression, "awaitPromise": False},
        }
        ws.send(json.dumps(msg))
        return ws.recv()
    finally:
        ws.close()

def inject_style(css, style_id="decky_inject_style"):
    css_escaped = json.dumps(css)[1:-1]
    js = f"""
(function(){{
  let s=document.getElementById("{style_id}");
  if(!s){{s=document.createElement('style');s.id="{style_id}";document.head.appendChild(s);}}
  s.textContent="{css_escaped}";
}})();
"""
    return eval_js(js)

def set_css_var(varname, value):
    var_escaped = json.dumps(value)
    js = f"document.documentElement.style.setProperty('{varname}', {var_escaped});"
    return eval_js(js)

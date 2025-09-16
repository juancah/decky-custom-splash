import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

# The decky plugin module is located at decky-loader/plugin
# For easy intellisense checkout the decky-loader code repo
# and add the `decky-loader/plugin/imports` path to `python.analysis.extraPaths` in `.vscode/settings.json`
import decky
import asyncio
import json
import requests
import re
from websocket import create_connection

DEVTOOLS_HOST = "127.0.0.1"
DEVTOOLS_PORT = 8080

# Global mapping (populated from css_translations.json)
CLASS_MAPPINGS = {}

class Plugin:
    # A normal method. It can be called from the TypeScript side using @decky/api.
    async def add(self, left: int, right: int) -> int:
        return left + right

    async def long_running(self, css):
        await asyncio.sleep(1)
        # Passing through a bunch of random data, just as an example
      

    # Asyncio-compatible long-running code, executed in a task when the plugin is loaded
    async def _main(self):
        self.loop = asyncio.get_event_loop()
        decky.logger.info("Hello World!")
        # Initial load of the class mappings
        try:
            self._load_class_mappings()
        except Exception as e:
            decky.logger.error(f"Failed initial css translations load: {e}")

    # Function called first during the unload process, utilize this to handle your plugin being stopped, but not
    # completely removed
    async def _unload(self):
        decky.logger.info("Goodnight World!")
        pass

    # Function called after `_unload` during uninstall, utilize this to clean up processes and other remnants of your
    # plugin that may remain on the system
    async def _uninstall(self):
        decky.logger.info("Goodbye World!")
        pass

    # -------------------------
    # CSS translations utilities
    # -------------------------
    def _css_translations_path(self) -> str:
        # css_translations.json lives in /home/deck/homebrew/themes/css_translations.json
        # Use decky.DECKY_USER_HOME as the base (should be /home/deck)
        return os.path.join(decky.DECKY_USER_HOME, "homebrew", "themes", "css_translations.json")

    def _load_class_mappings(self) -> None:
        """
        Loads / refreshes CLASS_MAPPINGS from css_translations.json.
        Mimics Decky's CSS loader translation logic: for each uid, the last entry is the
        latest hashed classname; map earlier readable names -> latest hashed name.
        """
        try:
            path = self._css_translations_path()
            if not os.path.exists(path):
                decky.logger.warning(f"css_translations.json not found at {path}")
                return

            with open(path, "r", encoding="utf-8") as fp:
                data: dict = json.load(fp)

            CLASS_MAPPINGS.clear()
            for uid in data:
                latest_value = data[uid][-1]
                # map all previous versions (readable) to the latest hashed value
                for readable in data[uid][:-1]:
                    CLASS_MAPPINGS[readable] = latest_value

            decky.logger.info(f"Loaded {len(CLASS_MAPPINGS)} css translations")
        except Exception as e:
            decky.logger.error(f"Failed to load css translations: {e}")

    def _translate_css(self, css: str) -> str:
        """
        Replace occurrences of .readableClass and [class="readableClass"] with the latest hashed classnames.
        Uses same regex splitting approach as Decky.
        """
        try:
            if not CLASS_MAPPINGS:
                return css

            # Replace .ClassName tokens
            split_css = re.split(r"(\.[_a-zA-Z]+[_a-zA-Z0-9-]*)", css)
            for i in range(len(split_css)):
                token = split_css[i]
                if token.startswith("."):
                    key = token[1:]
                    if key in CLASS_MAPPINGS:
                        split_css[i] = "." + CLASS_MAPPINGS[key]

            partial = "".join(split_css)

            # Replace [class="ClassName"] or attribute selectors that match mapping
            split_css2 = re.split(r"(\[class[*^|~]=\"[_a-zA-Z0-9-]*\"\])", partial)
            for i in range(len(split_css2)):
                token = split_css2[i]
                if token.startswith("[class") and token.endswith("\"]"):
                    # token like [class*="SomeClass"]
                    # find the inner value (after the =")
                    # approximate extraction as Decky did
                    # find the start of the quoted classname
                    start = token.find('="') + 2
                    end = token.rfind('"')
                    if start >= 0 and end > start:
                        key = token[start:end]
                        if key in CLASS_MAPPINGS:
                            new_token = token[:start] + CLASS_MAPPINGS[key] + token[end:]
                            split_css2[i] = new_token

            translated = "".join(split_css2)
            return translated
        except Exception as e:
            decky.logger.error(f"CSS translation failed: {e}")
            return css

    # -------------------------
    # DevTools websocket helpers
    # -------------------------
    def _get_ws_url(self) -> str:
        """
        Select the Steam Big Picture Mode target's websocket URL from /json.
        """
        r = requests.get(f"http://{DEVTOOLS_HOST}:{DEVTOOLS_PORT}/json")
        r.raise_for_status()
        targets = r.json()
        # prefer exact title match
        for t in targets:
            if t.get("title") == "Steam Big Picture Mode":
                return t["webSocketDebuggerUrl"]
        # fallback: try to heuristically find one that contains 'Big Picture' or 'Steam'
        for t in targets:
            title = t.get("title", "")
            if "Big Picture" in title or "Steam" in title:
                return t["webSocketDebuggerUrl"]
        # last resort, return first if any
        if targets:
            return targets[0]["webSocketDebuggerUrl"]
        raise RuntimeError("No DevTools targets found")

    async def _eval_js(self, expression: str):
        """
        Evaluate JS in the selected DevTools target via websocket.
        Note: uses blocking create_connection; it's fine inside Decky plugin environment.
        """
        try:
            ws_url = self._get_ws_url()
            decky.logger.info(f"Connecting to DevTools WS: {ws_url}")
      
            ws = create_connection(ws_url)
            try:
                msg = {
                    "id": 1,
                    "method": "Runtime.evaluate",
                    "params": {"expression": expression, "awaitPromise": False},
                }
                ws.send(json.dumps(msg))
                res = ws.recv()
                
                return res
            finally:
                ws.close()
        except Exception as e:
            decky.logger.error(f"_eval_js error: {e}")
            raise

    # --- modified start_timer: now injects CSS (and translates classnames)---
    async def start_timer(self, css: str):
        """
        Called from TS (callable). Accepts a CSS string that may use readable classnames.
        Injects the translated CSS once (no MutationObserver).
        """
        try:
            # refresh mapping each injection (keeps up with Decky updates)
            try:
                self._load_class_mappings()
            except Exception as e:
                decky.logger.warning(f"Failed to refresh class mappings: {e}")

            # translate classes
            translated_css = self._translate_css(css)
            decky.logger.info(f"Translated CSS prefix: {translated_css[:120]}")
         
            # Safely encode CSS for JS
            css_json = json.dumps(translated_css)

            # JS that injects style ONCE (if not already present). No observer.
            js = f"""
            (function(){{
            try {{
                const parent = document.head || document.documentElement || document.body;
                if (!parent) return "err:no-parent";

                let s = document.getElementById("decky_inject_style");
                if (!s) {{
                s = document.createElement('style');
                s.id = "decky_inject_style";
                s.className = "pog";
                parent.appendChild(s);
                }}
                // ALWAYS overwrite the stylesheet contents (this is the change)
                s.textContent = {css_json};
                "ok";
            }} catch(e) {{
                "err:"+e.toString();
            }}
            }})();
            """

           
            await self._eval_js(js)
            await decky.emit("timer_event", "injected")
        except Exception as e:
            decky.logger.error(f"Failed to inject CSS: {e}")
            await decky.emit("timer_event", f"inject failed: {e}")

    # Migrations that should be performed before entering `_main()`.
    async def _migration(self):
        decky.logger.info("Migrating")
        # Here's a migration example for logs:
        # - `~/.config/decky-template/template.log` will be migrated to `decky.decky_LOG_DIR/template.log`
        decky.migrate_logs(os.path.join(decky.DECKY_USER_HOME,
                                               ".config", "decky-template", "template.log"))
        # Here's a migration example for settings:
        # - `~/homebrew/settings/template.json` is migrated to `decky.decky_SETTINGS_DIR/template.json`
        # - `~/.config/decky-template/` all files and directories under this root are migrated to `decky.decky_SETTINGS_DIR/`
        decky.migrate_settings(
            os.path.join(decky.DECKY_HOME, "settings", "template.json"),
            os.path.join(decky.DECKY_USER_HOME, ".config", "decky-template"))
        # Here's a migration example for runtime data:
        # - `~/homebrew/template/` all files and directories under this root will be migrated to `decky.decky_RUNTIME_DIR/`
        decky.migrate_runtime(
            os.path.join(decky.DECKY_HOME, "template"),
            os.path.join(decky.DECKY_USER_HOME, ".local", "share", "decky-template"))

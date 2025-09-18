import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))

# The decky plugin module is located at decky-loader/plugin
# For easy intellisense checkout the decky-loader code repo
# and add the `decky-loader/plugin/imports` path to `python.analysis.extraPaths` in `.vscode/settings.json`
import decky
import asyncio
import json
import glob
import requests
import re
import mimetypes
import base64
from websocket import create_connection

DEVTOOLS_HOST = "127.0.0.1"
DEVTOOLS_PORT = 8080

# Global mapping (populated from css_translations.json)
CLASS_MAPPINGS = {}
_HERO_CACHE = {}  # appid -> data_url

#HERO CLASS:.sharedappdetailsheader_ImgSrc

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
    def _find_hero_image(self, appid: str) -> str | None:
        """
        Search for the hero image for a given appid under:
        /home/deck/.steam/steam/userdata/<USER_ID>/config/grid/<APPID>_hero.*
        Scans all user IDs inside userdata.
        """
        base_dir = "/home/deck/.steam/steam/userdata"
        if not os.path.isdir(base_dir):
            return None
        print("HERO DATA HERO BASE DIR",os.listdir(base_dir))
        try:
            for user_id in os.listdir(base_dir):
                grid_dir = os.path.join(base_dir, user_id, "config", "grid")
                if not os.path.isdir(grid_dir):
                    continue
                pattern = os.path.join(grid_dir, f"{appid}_hero.*")
                matches = glob.glob(pattern)
                if matches:
                    return matches[0]  # first valid match
        except Exception as e:
            decky.logger.debug(f"_find_hero_image error: {e}")

        return None
    def _make_data_url(self, path: str) -> str | None:
        """
        Read file at `path` and return a data: URL string like data:image/png;base64,....
        Returns None on failure.
        """
        try:
            ctype, _ = mimetypes.guess_type(path)
            if not ctype:
                ctype = "application/octet-stream"
            with open(path, "rb") as f:
                b = f.read()
            b64 = base64.b64encode(b).decode("ascii")
            return f"data:{ctype};base64,{b64}"
        except Exception as e:
            decky.logger.error(f"_make_data_url failed for {path}: {e}")
            return None
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
    def _build_hashed_css(
        self,
        selectors: list[str],
        declarations: str,
        suffix: str = ""  # e.g. "::before", " img", etc.
    ) -> str:
        css_lines = []
        for sel in selectors:
            hashed = CLASS_MAPPINGS.get(sel)
            if hashed:
                full_selector = f".{hashed}{suffix}"
            else:
                full_selector = f'[class*="{sel}"]{suffix}'
            css_block = f"{full_selector} {{\n{declarations}\n}}"
            css_lines.append(css_block)
        return "\n".join(css_lines)


    # --- modified start_timer: now injects CSS (and translates classnames)---
    async def start_timer(self, css: str, appinfo: dict = None):
        
        """
        Inject CSS where:
        - `css` is the client-provided container CSS (human-readable names OK)
        - backend will append the hero image CSS automatically when appinfo.appid is provided
        """
        try:
            #await decky.emit("timer_event", "start_timer: begin")

            # refresh mapping (safe)
            try:
                self._load_class_mappings()
            except Exception as e:
                decky.logger.warning(f"Failed to refresh class mappings: {e}")

            # make sure css is a string
            if css is None:
                css = ""
            else:
                css = str(css)

            # translate client CSS -> hashed classes
            translated_css = self._translate_css(css)
            decky.logger.info(f"Translated CSS len={len(translated_css)}")
            #await decky.emit("timer_event", "translated_css_ready")

            # prepare hero override CSS if we have appinfo with appid
            hero_css = ""
            display_text = ""
            appid = None
            hero_data_url = None
            print('HERODATA App info', appinfo)
            if appinfo:
                try:
                    if isinstance(appinfo, str):
                        try:
                            appinfo = json.loads(appinfo)
                        except Exception:
                            appinfo = None

                    if isinstance(appinfo, dict):
                        display_text = appinfo.get("display_name") or appinfo.get("name") or ""
                        appid = str(appinfo.get("appid") or appinfo.get("appId") or appinfo.get("id") or "")
                        print('HERODATA App ID', appid)
                        if appid:
                            # cached lookup first
                            hero_data_url = _HERO_CACHE.get(appid)
                            if not hero_data_url:
                                # find local hero file
                                print('HERODATA prefind hero image', appid)
                                path = self._find_hero_image(appid)
                                if path:
                                    hero_data_url = self._make_data_url(path)
                                    if hero_data_url:
                                        _HERO_CACHE[appid] = hero_data_url
                                        decky.logger.info(f"Cached hero data url for {appid}")
                                        #await decky.emit("timer_event", f"hero_cached:{appid}")
                except Exception as e:
                    decky.logger.warning(f"appinfo processing failed: {e}")

            if hero_data_url:
                # normal image override
                declarations_img = (
                    f'  content: url("{hero_data_url}") !important;\n'
                    "  opacity: 1 !important;\n"
                    "  width: 100% !important;\n"
                    "  height:100% !important;\n"
                    "  z-index: 100 !important;\n"
                    "  display: none !important;"
                )

                hero_img_css = self._build_hashed_css(
                    ["loadingthrobber_Container_3sa1N"],
                    declarations_img,
                    suffix=" img"
                )

                # blurred background pseudo-element
                declarations_blur = (
                    "  content: \"\";\n"
                    "  position: absolute;\n"
                    "  top: 12%;\n"
                    "  left: 0;\n"
                    "  right: 0;\n"
                    "  bottom: 0;\n"
                    "  height: 76%;\n"
                    "  z-index: 1;\n"
                    f'  background-image: url("{hero_data_url}");\n'
                    "  background-size: cover;\n"
                    "  background-position: left;\n"
                    "  opacity: 0.8;\n"
                    "  animation: ps5-zoom 20s ease-in-out infinite alternate;"
                )

                hero_blur_css = self._build_hashed_css(
                    ["loadingthrobber_ContainerBackground_2ngG3"],
                    declarations_blur,
                    suffix="::after"
                )
                bars_declarations_blur = (
                    "  content: '';\n"
                    "  display: block;\n"
                    "  opacity: 0.4;\n"
                    "  width: 100%;\n"
                    f'  background-image: url("{hero_data_url}");\n'
                    "  height: 100%;\n"
                    "  position: absolute;\n"
                    "  background-size: cover;\n"
                    "  background-position: center;\n"
                    "  top: 0;\n"
                    "  z-index: 0;\n"
                    "  left: 0;\n"
                    "  right: 0;\n"
                    "  filter: blur(3px);\n"
                    "  bottom: 0;\n"
                )


                bars_blur_css = self._build_hashed_css(
                    ["loadingthrobber_ContainerBackground_2ngG3"],
                    bars_declarations_blur,
                    suffix="::before"
                )


                # combine everything
                hero_css = hero_img_css + "\n" + hero_blur_css + "\n" + bars_blur_css

                decky.logger.info("Prepared hero CSS override with blur")
                #await decky.emit("timer_event", "hero_css_prepared")

                combined_css = translated_css + "\n" + hero_css

                # JSON-encode to safely embed into JS string
                css_json = json.dumps(combined_css)
                loading_readable = "loadingthrobber_LoadingStatus_3rAIy"
                container_hashed = CLASS_MAPPINGS.get(loading_readable)
                if container_hashed:
                    container_selector_js = f"document.querySelectorAll('.{container_hashed}')"
                else:
                    container_selector_js = 'document.querySelectorAll(\'[class*="loadingthrobber_LoadingStatus_3rAIy"]\')'
                
                parent_container_class = 'loadingthrobber_Container'
                parent_container_hashed = CLASS_MAPPINGS.get(parent_container_class)
                if parent_container_hashed:
                    parent_container_selector_js = f"document.querySelector('.{parent_container_hashed}')"
                else:
                    parent_container_selector_js = 'document.querySelector(\'[class*="loadingthrobber_SpinnerLoaderContainer"]\')'
                display_json = json.dumps(display_text or "")

                print('HERODATA', css_json)

                js = f"""
                (function() {{
                    try {{
                        const parent = document.head || document.documentElement || document.body;
                        if (!parent) return 'err:no-parent';

                        let s = document.getElementById("decky_inject_style");
                        if (!s) {{
                            s = document.createElement('style');
                            s.id = "decky_inject_style";
                            s.className = "pog";
                            parent.appendChild(s);
                        }}
                        // inject/overwrite CSS immediately
                        s.textContent = {css_json};

                        // container selector
                        const selector = '.{container_hashed or "[class*=loadingthrobber_LoadingStatus_3rAIy]"}';
                        const parentSelector = {parent_container_selector_js};
                        const displayText = {display_json};

                        // cleanup any existing observer first
                        if (window.__deckyObserver) {{
                            try {{ window.__deckyObserver.disconnect(); }} catch(e){{}}
                            window.__deckyObserver = null;
                        }}

                        function injectInto(container) {{
                            if (!container) return;

                            // H1
                            let h = container.querySelector('#decky_inject_h1');
                            if (!h) {{
                                h = document.createElement('h1');
                                h.id = "decky_inject_h1";
                                container.appendChild(h);
                            }}
                            h.innerText = displayText;

                            // cinema bars
                            const innerJsContentContainer = parentSelector;
                            if (innerJsContentContainer) {{
                                let topBar = innerJsContentContainer.querySelector('.cinema-bar-top');
                                if (!topBar) {{
                                    topBar = document.createElement('div');
                                    topBar.className = 'cinema-bar-top';
                                    innerJsContentContainer.appendChild(topBar);
                                }}
                                let bottomBar = innerJsContentContainer.querySelector('.cinema-bar-bottom');
                                if (!bottomBar) {{
                                    bottomBar = document.createElement('div');
                                    bottomBar.className = 'cinema-bar-bottom';
                                    innerJsContentContainer.appendChild(bottomBar);
                                }}
                            }}

                            // loop-wrapper
                            let existingLoop = container.querySelector('.loop-wrapper');
                            if (!existingLoop) {{
                                const loopWrapper = document.createElement('div');
                                loopWrapper.className = 'loop-wrapper';
                                loopWrapper.innerHTML =
                                    '<div class="mountain"></div>' +
                                    '<div class="hill"></div>' +
                                    '<div class="tree"></div>' +
                                    '<div class="tree"></div>' +
                                    '<div class="tree"></div>' +
                                    '<div class="rock"></div>' +
                                    '<div class="truck"></div>' +
                                    '<div class="wheels"></div>';
                                h.insertAdjacentElement('afterend', loopWrapper);
                            }}
                        }}

                        // inject immediately for existing containers
                        document.querySelectorAll(selector).forEach(injectInto);

                        // watch for new containers
                        const observer = new MutationObserver((mutations) => {{
                            for (const m of mutations) {{
                                for (const node of m.addedNodes) {{
                                    if (!(node instanceof Element)) continue;
                                    if (node.matches && node.matches(selector)) {{
                                        injectInto(node);
                                    }}
                                    const inner = node.querySelectorAll ? node.querySelectorAll(selector) : [];
                                    inner.forEach(injectInto);
                                }}
                            }}
                        }});
                        observer.observe(document.body, {{ childList: true, subtree: true }});
                        window.__deckyObserver = observer;

                        return 'observer-started';
                    }} catch(e) {{
                        return 'err:'+e.toString();
                    }}
                }})();
                """



                #await decky.emit("timer_event", "injecting css+h1")
                await self._eval_js(js)
                await decky.emit("timer_event", "injected css+h1")
        except Exception as e:
            decky.logger.error(f"start_timer injection failed: {e}")
            await decky.emit("timer_event", f"inject failed: {e}")

    async def stop_timer(self):
        try:
            print('BACKEND stopping timer')
            js = """
            (function(){
                if (window.__deckyStopObserver) {
                    window.__deckyStopObserver();
                    return 'observer-stopped';
                }
                return 'no-observer';
            })();
            """
            await self._eval_js(js)
            await decky.emit("timer_event", "observer stopped")
        except Exception as e:
            decky.logger.error(f"stop_timer failed: {e}")
            await decky.emit("timer_wevent", f"stop failed: {e}")


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

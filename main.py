import time
from pathlib import Path
from playwright.sync_api import sync_playwright

from action import Action, get_autohu, get_click_list
from majsoul2mjai import MajsoulBridge
from proto.parser import LiqiParser

class MajsoulAutomator:
    def __init__(self):
        self.playwright_width = 1280
        self.playwright_height = 720
        self.scale = self.playwright_width / 16
        self.playwright_context = None
        self.action = Action()
        self.bridge = MajsoulBridge()
        self.parser = LiqiParser()
        self.gm_msgs = []

    def launch_browser(self):
        self.playwright_context = sync_playwright().start()
        
        # 默认使用chromium
        chromium = self.playwright_context.chromium
        browser = chromium.launch_persistent_context(
            # 使用edge
            channel="msedge",
            # 使用chrome
            # channel="chrome",
            user_data_dir=Path(__file__).parent / 'data',
            headless=False,
            viewport={'width': self.playwright_width, 'height': self.playwright_height},
            ignore_default_args=['--enable-automation'],
        )
        
        return browser

    def close_browser(self):
        if self.playwright_context:
            self.playwright_context.stop()

    def handle_websocket_event(self, websocket):
        def on_frame_sent(frame):
            gm_msg = self.parser.parse(frame)
            self.gm_msgs.append(gm_msg)
            # print("sent", gm_msg)

        def on_received(frame):
            gm_msg = self.parser.parse(frame)
            self.gm_msgs.append(gm_msg)
            # print("received", gm_msg)

        websocket.on("framesent", on_frame_sent)
        websocket.on("framereceived", on_received)

    def main_loop(self):
        try:
            browser = self.launch_browser()
            page = browser.new_page()
            page.goto('https://game.maj-soul.com/1/')
            # https://stackoverflow.com/questions/73209567/close-or-switch-tabs-in-playwright-python
            all_pages = page.context.pages
            all_pages[0].close()

            # https://blog.csdn.net/freeking101/article/details/110213782
            page.on("websocket", lambda websocket: self.handle_websocket_event(websocket))

            while True:
                if len(self.gm_msgs) > 0:
                    self.handle_gm_message()
                click_list = get_click_list()
                if len(click_list) > 0:
                    self.handle_click_list(page, click_list)
                else:
                    page.wait_for_timeout(100)
        except KeyboardInterrupt:
            self.close_browser()

    def handle_gm_message(self):
        gm_msg = self.gm_msgs.pop(0)
        # 处理消息...
        if gm_msg.get("method") == '.lq.ActionPrototype':
            if 'operation' in gm_msg.get("data").get('data'):
                if 'operation_list' in gm_msg.get("data").get('data').get('operation'):
                    self.action.latest_operation_list = gm_msg.get("data").get('data').get('operation').get('operation_list') 
            if gm_msg.get("data").get('name') == 'ActionDiscardTile':
                self.action.isNewRound = False
            if gm_msg.get("data").get('name') == 'ActionNewRound':
                self.action.isNewRound = True
                self.action.reached = False     
        mjai_msg = self.bridge.input(gm_msg)    
        if mjai_msg is not None:
            # 处理 mjai_msg，如果 reach 为真，则将 type 改为 "reach"
            if self.bridge.reach and mjai_msg["type"] == "dahai":
                mjai_msg["type"] = "reach"
                self.bridge.reach = False
            print('-'*65)
            print(mjai_msg)
            self.action.mjai2action(mjai_msg, self.bridge.my_tehais, self.bridge.my_tsumohai)

    def handle_click_list(self, page, click_list):
        xy = click_list.pop(0)
        xy_scale = {"x": xy[0] * self.scale, "y": xy[1] * self.scale}
        page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
        time.sleep(0.1)
        page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
        print(f"page_clicker: {xy_scale}")
        do_autohu = get_autohu()
        if do_autohu:
            page.evaluate("() => view.DesktopMgr.Inst.setAutoHule(true)")
            do_autohu = False

if __name__ == "__main__":
    automator = MajsoulAutomator()
    automator.main_loop()



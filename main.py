import time
from pathlib import Path
from playwright.sync_api import sync_playwright
import random
from loguru import logger
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
        self.LOCATION = {
            "endGameStage": [
                (14.35, 8.12),      # 点击确定按钮，此坐标位于大厅的"商家"和"寻觅"按钮之间
                (6.825, 6.8),       # 点击好感度礼物
                (11.5, 2.75),       # 点击段位场
            ],
            "rankStage": [
                (11.5, 6.15),  # 金之间: gold
                (11.5, 4.825),  # 银之间: silver
                (11.5, 3.375),  # 铜之间: copper
                (11.5, 5.425),  # 玉之间: jade
                (11.5, 6.825),  # 王座之间: king
            ],
            "roomsAndRoundsStage": [
                (11.5, 4.7625),  # 四人南
                (11.5, 3.475),  # 四人东
                (11.5, 6.15),   # 移动位置点
                (11.5, 6.5625),  # 三人南
                (11.5, 5.4),    # 三人东
            ],
            "emotions": [
                (12.4, 3.5), (13.65, 3.5), (14.8, 3.5),    # 1 2 3
                (12.4, 5.0), (13.65, 5.0), (14.8, 5.0),    # 4 5 6
                (12.4, 6.5), (13.65, 6.5), (14.8, 6.5),    # 7 8 9
            ]
        }
        self.next_game_Rank = 'silver' # 可以选 铜之间: copper 银之间: silver 金之间: gold 玉之间: jade 王座之间: king
        self.next_game_number = '4p' # 可以选 3p 4p
        self.next_game_rounds = 'south' # 可以选 南风: south 东风: east

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
            viewport={'width': self.playwright_width,
                      'height': self.playwright_height},
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

    def randomEmotion(self, page, scale, parse_msg):
        # print("111111111111111111111111",parse_msg['method'])
        # if parse_msg['method'] == '.lq.NotifyGameBroadcast':
        randomN = random.uniform(0.0, 100.0)
        # 5%
        if randomN <= 5.0:
            time.sleep(0.1)
            xy = (15.675, 4.9625)
            xy_scale = {"x": xy[0]*scale, "y": xy[1]*scale}
            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
            time.sleep(0.1)
            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
            logger.debug(f"page_clicker: {xy_scale} click emotions")
            time.sleep(0.3)
            index = random.randint(0, 8)
            # index = 2
            xy = self.LOCATION["emotions"][index]
            xy_scale = {"x": xy[0]*scale, "y": xy[1]*scale}
            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
            time.sleep(0.1)
            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
            logger.debug(
                f"page_clicker: {xy_scale} click the {index} emotion")

    def auto_next(self, page, scale, parse_msg):
        if parse_msg['method'] == '.lq.NotifyGameEndResult':
            # 1.等待结算
            time.sleep(30)

            # 2.最终顺位界面点击"确认"
            xy_scale = {"x": self.LOCATION['endGameStage'][0][0] * scale,
                        "y": self.LOCATION['endGameStage'][0][1] * scale}
            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
            time.sleep(1)
            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
            time.sleep(5)

            # 3. 段位pt结算界面点击"确认"
            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
            time.sleep(10)

            if self.next_game_Rank != 'copper':
                # 4. 开启宝匣礼物
                xy_scale = {"x": self.LOCATION['endGameStage'][1][0] * scale,
                            "y": self.LOCATION['endGameStage'][1][1] * scale}
                page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                time.sleep(1)
                page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                time.sleep(5)

                # 5. 宝匣好感度界面点击"确认"
                xy_scale = {"x": self.LOCATION['endGameStage'][0][0] * scale,
                            "y": self.LOCATION['endGameStage'][0][1] * scale}
                page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                time.sleep(1)
                page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                time.sleep(5)

            # 6. 每日任务界面点击"确认"
            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
            time.sleep(8)

            # 活动多了一个页面，临时添加的，不用时注释掉
            # page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
            # time.sleep(10)

            # 7. 大厅界面点击段位场
            xy_scale = {"x": self.LOCATION['endGameStage'][2][0] * scale,
                        "y": self.LOCATION['endGameStage'][2][1] * scale}
            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
            time.sleep(0.5)
            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
            logger.debug(f"page_clicker_next_game: {xy_scale}")
            time.sleep(2)
        elif parse_msg['method'] == '.lq.NotifyGameTerminate':
            time.sleep(8)
            xy_scale = {"x": self.LOCATION['endGameStage'][2][0] * scale,
                        "y": self.LOCATION['endGameStage'][2][1] * scale}
            page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
            time.sleep(0.5)
            page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
            logger.debug(f"page_clicker_next_game: {xy_scale}")
            time.sleep(2)

        if parse_msg['method'] == '.lq.NotifyGameEndResult' or parse_msg[
                'method'] == '.lq.NotifyGameTerminate':
            if self.next_game_Rank == 'gold':
                xy_scale = {"x": self.LOCATION['rankStage'][0][0] * scale,
                            "y": self.LOCATION['rankStage'][0][1] * scale}
                page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                time.sleep(0.5)
                page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                logger.debug(f"page_clicker_next_game_gold: {xy_scale}")
                time.sleep(2)
            elif self.next_game_Rank == 'silver':
                xy_scale = {"x": self.LOCATION['rankStage'][1][0] * scale,
                            "y": self.LOCATION['rankStage'][1][1] * scale}
                page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                time.sleep(0.5)
                page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                logger.debug(f"page_clicker_next_game_silver: {xy_scale}")
                time.sleep(2)
            elif self.next_game_Rank == 'copper':
                xy_scale = {"x": self.LOCATION['rankStage'][2][0] * scale,
                            "y": self.LOCATION['rankStage'][2][1] * scale}
                page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                time.sleep(0.5)
                page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                logger.debug(f"page_clicker_next_game_copper: {xy_scale}")
                time.sleep(2)
            elif self.next_game_Rank == 'jade':
                xy_scale = {"x": self.LOCATION['rankStage'][0][0] * scale,
                            "y": self.LOCATION['rankStage'][0][1] * scale}
                page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                time.sleep(0.5)
                page.mouse.wheel(0, 100)
                page.mouse.wheel(0, 100)
                page.mouse.wheel(0, 100)
                page.mouse.wheel(0, 100)
                time.sleep(2)
                xy_scale = {"x": self.LOCATION['rankStage'][3][0] * scale,
                            "y": self.LOCATION['rankStage'][3][1] * scale}
                page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                time.sleep(0.5)
                page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                logger.debug(f"page_clicker_next_game_jade: {xy_scale}")
                time.sleep(2)
            elif self.next_game_Rank == 'king':
                xy_scale = {"x": self.LOCATION['rankStage'][0][0] * scale,
                            "y": self.LOCATION['rankStage'][0][1] * scale}
                page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                time.sleep(0.5)
                page.mouse.wheel(0, 100)
                page.mouse.wheel(0, 100)
                page.mouse.wheel(0, 100)
                page.mouse.wheel(0, 100)
                time.sleep(2)
                xy_scale = {"x": self.LOCATION['rankStage'][4][0] * scale,
                            "y": self.LOCATION['rankStage'][4][1] * scale}
                page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                time.sleep(0.5)
                page.mouse.click(x=xy_scale["x"], y=xy_scale["y"], delay=100)
                logger.debug(f"page_clicker_next_game_king: {xy_scale}")
                time.sleep(2)

            if self.next_game_number == '4p':
                if self.next_game_rounds == 'south':
                    xy_scale = {"x": self.LOCATION['roomsAndRoundsStage'][0][0] * scale,
                                "y": self.LOCATION['roomsAndRoundsStage'][0][1] * scale}
                    page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                    time.sleep(0.5)
                    page.mouse.click(
                        x=xy_scale["x"], y=xy_scale["y"], delay=100)
                    logger.debug(
                        f"page_clicker_next_game_4p_south: {xy_scale}")
                    time.sleep(1)
                elif self.next_game_rounds == 'east':
                    xy_scale = {"x": self.LOCATION['roomsAndRoundsStage'][1][0] * scale,
                                "y": self.LOCATION['roomsAndRoundsStage'][1][1] * scale}
                    page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                    time.sleep(0.5)
                    page.mouse.click(
                        x=xy_scale["x"], y=xy_scale["y"], delay=100)
                    logger.debug(f"page_clicker_next_game_4p_east: {xy_scale}")
                    time.sleep(1)
            elif self.next_game_number == '3p':
                if self.next_game_rounds == 'south':
                    xy_scale = {"x": self.LOCATION['rankStage'][2][0] * scale,
                                "y": self.LOCATION['rankStage'][2][1] * scale}
                    page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                    time.sleep(0.5)
                    page.mouse.wheel(0, 100)
                    page.mouse.wheel(0, 100)
                    page.mouse.wheel(0, 100)
                    page.mouse.wheel(0, 100)
                    time.sleep(2)
                    xy_scale = {"x": self.LOCATION['roomsAndRoundsStage'][3][0] * scale,
                                "y": self.LOCATION['roomsAndRoundsStage'][3][1] * scale}
                    page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                    time.sleep(0.5)
                    page.mouse.click(
                        x=xy_scale["x"], y=xy_scale["y"], delay=100)
                    logger.debug(
                        f"page_clicker_next_game_3p_south: {xy_scale}")
                    time.sleep(1)
                elif self.next_game_rounds == 'east':
                    xy_scale = {"x": self.LOCATION['rankStage'][2][0] * scale,
                                "y": self.LOCATION['rankStage'][2][1] * scale}
                    page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                    time.sleep(0.5)
                    page.mouse.wheel(0, 100)
                    page.mouse.wheel(0, 100)
                    page.mouse.wheel(0, 100)
                    page.mouse.wheel(0, 100)
                    time.sleep(2)
                    xy_scale = {"x": self.LOCATION['roomsAndRoundsStage'][4][0] * scale,
                                "y": self.LOCATION['roomsAndRoundsStage'][4][1] * scale}
                    page.mouse.move(x=xy_scale["x"], y=xy_scale["y"])
                    time.sleep(0.5)
                    page.mouse.click(
                        x=xy_scale["x"], y=xy_scale["y"], delay=100)
                    logger.debug(f"page_clicker_next_game_3p_east: {xy_scale}")
                    time.sleep(1)

    def main_loop(self):
        try:
            browser = self.launch_browser()
            page = browser.new_page()
            # 国服
            page.goto('https://game.maj-soul.com/1/')
            # 国际服
            # page.goto('https://mahjongsoul.game.yo-star.com/')
            # 日服
            # page.goto('https://game.mahjongsoul.com/index.html')
            # https://stackoverflow.com/questions/73209567/close-or-switch-tabs-in-playwright-python
            all_pages = page.context.pages
            all_pages[0].close()

            # https://blog.csdn.net/freeking101/article/details/110213782
            page.on("websocket",
                    lambda websocket: self.handle_websocket_event(websocket))

            # 设置更改
            # 可以选 铜之间: copper 银之间: silver 金之间: gold 玉之间: jade 王座之间: king
            self.next_game_Rank = 'silver'
            # 可以选 3p 4p
            self.next_game_number = '4p'
            # 可以选 南风: south 东风: east
            self.next_game_rounds = 'south'
            self.playwright_width = 1280
            self.playwright_height = 720
            self.scale = self.playwright_width / 16

            while True:
                if len(self.gm_msgs) > 0:
                    gm_msg = self.gm_msgs.pop(0)
                    self.handle_gm_message(gm_msg)
                    # 开启自动下一局
                    self.auto_next(page, self.scale, gm_msg)
                click_list = get_click_list()
                if len(click_list) > 0:
                    self.handle_click_list(page, click_list)
                    # 开启随机发送表情
                    self.randomEmotion(page, self.scale, gm_msg)
                else:
                    page.wait_for_timeout(100)
        except KeyboardInterrupt:
            self.close_browser()

    def handle_gm_message(self, gm_msg):
        # 处理消息...
        if gm_msg.get("method") == '.lq.ActionPrototype':
            if 'operation' in gm_msg.get("data").get('data'):
                if 'operation_list' in gm_msg.get("data").get('data').get('operation'):
                    self.action.latest_operation_list = gm_msg.get("data").get(
                        'data').get('operation').get('operation_list')
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
            # print('-'*65)
            # print(mjai_msg)
            self.action.mjai2action(
                mjai_msg, self.bridge.my_tehais, self.bridge.my_tsumohai)

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

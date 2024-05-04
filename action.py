import time
import random
from convert import MS_TILE_2_MJAI_TILE
from functools import cmp_to_key
from majsoul2mjai import compare_pai
from libriichi_helper import meta_to_recommend, state_to_tehai
from loguru import logger

click_list = []
do_autohu = False
first_pai_count = 0
all_pai_count = 0

# Coordinates here is on the resolution of 16x9
LOCATION = {
    "tiles": [
        (2.23125, 8.3625),
        (3.021875, 8.3625),
        (3.8125, 8.3625),
        (4.603125, 8.3625),
        (5.39375, 8.3625),
        (6.184375, 8.3625),
        (6.975, 8.3625),
        (7.765625, 8.3625),
        (8.55625, 8.3625),
        (9.346875, 8.3625),
        (10.1375, 8.3625),
        (10.928125, 8.3625),
        (11.71875, 8.3625),
        (12.509375, 8.3625),
    ],
    "tsumo_space": 0.246875,
    "actions": [
        (10.875, 7),  # none       #
        (8.6375, 7),  # 5   4   3
        (6.4, 7),             #
        (10.875, 5.9),  # 2   1   0
        (8.6375, 5.9),           #
        (6.4, 5.9),
        (10.875, 4.8),           # Not used
        (8.6375, 4.8),           # Not used
        (6.4, 4.8),           # Not used
    ],
    "candidates": [
        (3.6625,  6.3),         # (-(len/2)+idx+0.5)*2+5
        (4.49625, 6.3),
        (5.33,   6.3),
        (6.16375, 6.3),
        (6.9975,  6.3),
        (7.83125, 6.3),         # 5 mid
        (8.665,   6.3),
        (9.49875, 6.3),
        (10.3325, 6.3),
        (11.16625, 6.3),
        (12,      6.3),
    ],
    "candidates_kan": [
        (4.325,   6.3),         #
        (5.4915,  6.3),
        (6.6583,  6.3),
        (7.825,   6.3),         # 3 mid
        (8.9917,  6.3),
        (10.1583, 6.3),
        (11.325,  6.3),
    ],
}

# Refer to majsoul2mjai.Operation
ACTION_PIORITY = [
    0,  # none      #
    99,  # Discard   # There is no discard button
    4,  # Chi       # Opponent Discard
    3,  # Pon       # Opponent Discard
    # Ankan     # Self Discard      # If Ankan and Kakan are both available, use only kakan.
    3,
    2,  # Daiminkan # Opponent Discard
    3,  # Kakan     # Self Discard
    2,  # Reach     # Self Discard
    1,  # Zimo      # Self Discard
    1,  # Rong      # Opponent Discard
    5,  # Ryukyoku  # Self Discard
    4,  # Nukidora  # Self Discard
]

ACTION2TYPE = {
    "none": 0,
    "chi": 2,
    "pon": 3,
    "daiminkan": 5,
    "hora": 9,
    # ^^^^^^^^^^^^^^^^Opponent Discard^^^^^^^^^^^^^^^^
    "ryukyoku": 10,
    "nukidora": 11,
    "ankan": 4,
    "kakan": 6,
    "reach": 7,
    "zimo": 8,
    # ^^^^^^^^^^^^^^^^Self Discard^^^^^^^^^^^^^^^^
}


def get_click_list():
    return click_list


def get_autohu():
    return do_autohu

# with open("settings.json", "r") as f:
#     settings = json.load(f)
#     PLAYWRIGHT_RESOLUTION = (settings['Playwright']['width'], settings['Playwright']['height'])
#     SCALE = PLAYWRIGHT_RESOLUTION[0]/16


class Action:
    def __init__(self):
        self.isNewRound = True
        self.reached = False
        self.latest_operation_list = []
        pass

    def page_clicker(self, coord: tuple[float, float]):
        global click_list
        click_list.append(coord)

    def do_autohu(self):
        global do_autohu
        do_autohu = True

    def decide_random_time(self):
        if self.isNewRound:
            return random.uniform(3.5, 4.8)
        return random.uniform(1.9, 3.9)

    def click_chiponkan(self, mjai_msg: dict | None, tehai: list[str], tsumohai: str | None):
        latest_operation_list_temp = self.latest_operation_list.copy()
        latest_operation_list_temp.append({'type': 0, 'combination': []})
        can_ankan = False
        can_kakan = False
        ankan_combination = None
        # if both Ankan (type 4) and Kakan (type 6) are available
        for operation in self.latest_operation_list:
            if operation['type'] == 4:
                can_ankan = True
                ankan_combination = operation['combination']
            if operation['type'] == 6:
                can_kakan = True
        if can_ankan and can_kakan:
            for idx, operation in enumerate(self.latest_operation_list):
                if operation['type'] == 6:
                    latest_operation_list_temp[idx]['combination'] += ankan_combination
                if operation['type'] == 4:
                    latest_operation_list_temp.remove(operation)

        # Sort latest_operation_list by ACTION_PIORITY
        # logger.debug(f"latest_operation_list_temp: {latest_operation_list_temp}")
        latest_operation_list_temp.sort(
            key=lambda x: ACTION_PIORITY[x['type']])

        if tsumohai != '?' and mjai_msg['type'] == 'hora':
            mjai_msg['type'] = 'zimo'

        for idx, operation in enumerate(latest_operation_list_temp):
            if operation['type'] == ACTION2TYPE[mjai_msg['type']]:
                self.page_clicker(LOCATION['actions'][idx])
                self.do_autohu()
                self.isNewRound = False
                break

        if mjai_msg['type'] == 'reach':
            self.reached = True
            time.sleep(0.5)
            self.click_dahai(mjai_msg, tehai, tsumohai)
            return

        if mjai_msg['type'] in ['chi', 'pon', 'ankan', 'kakan']:
            consumed_pais_mjai = mjai_msg['consumed']
            consumed_pais_mjai = sorted(
                consumed_pais_mjai, key=cmp_to_key(compare_pai))
            if mjai_msg['type'] == 'chi':
                for operation in self.latest_operation_list:
                    if operation['type'] == 2:
                        combination_len = len(operation['combination'])
                        if combination_len == 1:
                            return  # No need to click
                        for idx, combination in enumerate(operation['combination']):
                            consumed_pais_liqi = [
                                MS_TILE_2_MJAI_TILE[pai] for pai in combination.split('|')]
                            consumed_pais_liqi = sorted(
                                consumed_pais_liqi, key=cmp_to_key(compare_pai))
                            if consumed_pais_mjai == consumed_pais_liqi:
                                time.sleep(0.3)
                                candidate_idx = int(
                                    (-(combination_len/2)+idx+0.5)*2+5)
                                self.page_clicker(
                                    LOCATION['candidates'][candidate_idx])
                                return
            elif mjai_msg['type'] == 'pon':
                for operation in self.latest_operation_list:
                    if operation['type'] == 3:
                        combination_len = len(operation['combination'])
                        if combination_len == 1:
                            return
                        for idx, combination in enumerate(operation['combination']):
                            consumed_pais_liqi = [
                                MS_TILE_2_MJAI_TILE[pai] for pai in combination.split('|')]
                            consumed_pais_liqi = sorted(
                                consumed_pais_liqi, key=cmp_to_key(compare_pai))
                            if consumed_pais_mjai == consumed_pais_liqi:
                                time.sleep(0.3)
                                candidate_idx = int(
                                    (-(combination_len/2)+idx+0.5)*2+5)
                                self.page_clicker(
                                    LOCATION['candidates'][candidate_idx])
                                return
            # If both Ankan (type 4) and Kakan (type 6) are available, only one kan button will be shown, and candidates = [kakan, ankan]
            elif mjai_msg['type'] in ['ankan', 'kakan']:
                if can_ankan and can_kakan:
                    for operation in latest_operation_list_temp:
                        if operation['type'] == 6:
                            combination_len = len(operation['combination'])
                            if combination_len == 1:
                                # impossible
                                return
                            for idx, combination in enumerate(operation['combination']):
                                consumed_pais_liqi = [
                                    MS_TILE_2_MJAI_TILE[pai] for pai in combination.split('|')]
                                consumed_pais_liqi = sorted(
                                    consumed_pais_liqi, key=cmp_to_key(compare_pai))
                                if consumed_pais_mjai == consumed_pais_liqi:
                                    time.sleep(0.3)
                                    candidate_idx = int(
                                        (-(combination_len/2)+idx+0.5)*2+3)
                                    self.page_clicker(
                                        LOCATION['candidates_kan'][candidate_idx])
                                    return
                elif mjai_msg['type'] == 'ankan':
                    for operation in self.latest_operation_list:
                        if operation['type'] == 4:
                            combination_len = len(operation['combination'])
                            if combination_len == 1:
                                return
                            for idx, combination in enumerate(operation['combination']):
                                consumed_pais_liqi = [
                                    MS_TILE_2_MJAI_TILE[pai] for pai in combination.split('|')]
                                consumed_pais_liqi = sorted(
                                    consumed_pais_liqi, key=cmp_to_key(compare_pai))
                                if consumed_pais_mjai == consumed_pais_liqi:
                                    time.sleep(0.3)
                                    candidate_idx = int(
                                        (-(combination_len/2)+idx+0.5)*2+3)
                                    self.page_clicker(
                                        LOCATION['candidates_kan'][candidate_idx])
                                    return
                elif mjai_msg['type'] == 'kakan':
                    for operation in self.latest_operation_list:
                        if operation['type'] == 6:
                            combination_len = len(operation['combination'])
                            if combination_len == 1:
                                return
                            for idx, combination in enumerate(operation['combination']):
                                consumed_pais_liqi = [
                                    MS_TILE_2_MJAI_TILE[pai] for pai in combination.split('|')]
                                consumed_pais_liqi = sorted(
                                    consumed_pais_liqi, key=cmp_to_key(compare_pai))
                                if consumed_pais_mjai == consumed_pais_liqi:
                                    time.sleep(0.3)
                                    candidate_idx = int(
                                        (-(combination_len/2)+idx+0.5)*2+3)
                                    self.page_clicker(
                                        LOCATION['candidates_kan'][candidate_idx])
                                    return

    def get_pai_coord(self, idx: int, tehais: list[str]):
        tehai_count = 0
        for tehai in tehais:
            if tehai != '?':
                tehai_count += 1
        if tehai_count >= 14:
            tehai_count = 13
        if idx == 13:
            pai_cord = (LOCATION['tiles'][tehai_count][0] +
                        LOCATION['tsumo_space'], LOCATION['tiles'][tehai_count][1])
        else:
            pai_cord = LOCATION['tiles'][idx]

        return pai_cord

    # tehai: 手牌 tsumohai：表示摸切的牌，即从牌山摸到的牌，并立刻打出。
    def click_dahai(self, mjai_msg: dict | None, tehai: list[str], tsumohai: str | None):

        # 获取每个操作的ai推荐率
        ai_pais = meta_to_recommend(mjai_msg['meta'])
        selected_pai = mjai_msg['pai']

        # 废弃的方法
        # global first_pai_count
        # global all_pai_count
        # all_pai_count += 1
        # # 至少两个选项(如果立直就只剩一个选项)
        # # 如果第一与第二的概率差距小于0.02
        # if len(ai_pais) > 1 and ai_pais[0][1] - ai_pais[1][1] < 0.02:
        #     # 以95%的概率选择第二个，5%的概率选择第一个
        #     if random.random() < 0.05:
        #         first_pai_count += 1
        #         selected_pai = ai_pais[0][0]
        #     else:
        #         selected_pai = ai_pais[1][0]
        # # 如果第一与第二的概率差距小于0.04
        # if len(ai_pais) > 1 and ai_pais[0][1] - ai_pais[1][1] < 0.06:
        #     # 以90%的概率选择第二个，10%的概率选择第一个
        #     if random.random() < 0.1:
        #         first_pai_count += 1
        #         selected_pai = ai_pais[0][0]
        #     else:
        #         selected_pai = ai_pais[1][0]
        # # 如果第一与第二的概率差距小于0.08
        # elif len(ai_pais) > 1 and ai_pais[0][1] - ai_pais[1][1] < 0.08:
        #     # 以80%的概率选择第二个，20%的概率选择第一个
        #     if random.random() < 0.2:
        #         first_pai_count += 1
        #         selected_pai = ai_pais[0][0]
        #     else:
        #         selected_pai = ai_pais[1][0]
        # # 如果第一与第二的概率差距小于0.11
        # elif len(ai_pais) > 1 and ai_pais[0][1] - ai_pais[1][1] < 0.11:
        #     # 以65%的概率选择第二个，35%的概率选择第一个
        #     if random.random() < 0.35:
        #         first_pai_count += 1
        #         selected_pai = ai_pais[0][0]
        #     else:
        #         selected_pai = ai_pais[1][0]
        # # 如果第一与第二的概率差距小于0.18
        # elif len(ai_pais) > 1 and ai_pais[0][1] - ai_pais[1][1] < 0.18:
        #     # 以35%的概率选择第二个，65%的概率选择第一个
        #     if random.random() < 0.65:
        #         first_pai_count += 1
        #         selected_pai = ai_pais[0][0]
        #     else:
        #         selected_pai = ai_pais[1][0]
        # # 如果第一与第二的概率差距小于0.24
        # elif len(ai_pais) > 1 and ai_pais[0][1] - ai_pais[1][1] < 0.24:
        #     # 以20%的概率选择第二个，80%的概率选择第一个
        #     if random.random() < 0.8:
        #         first_pai_count += 1
        #         selected_pai = ai_pais[0][0]
        #     else:
        #         selected_pai = ai_pais[1][0]
        # # 如果第一与第二的概率差距小于0.28
        # elif len(ai_pais) > 1 and ai_pais[0][1] - ai_pais[1][1] < 0.28:
        #     # 以10%的概率选择第二个，90%的概率选择第一个
        #     if random.random() < 0.9:
        #         first_pai_count += 1
        #         selected_pai = ai_pais[0][0]
        #     else:
        #         selected_pai = ai_pais[1][0]
        # # 如果第一与第二的概率差距小于0.35
        # elif len(ai_pais) > 1 and ai_pais[0][1] - ai_pais[1][1] < 0.35:
        #     # 以8%的概率选择第二个，92%的概率选择第一个
        #     if random.random() < 0.92:
        #         first_pai_count += 1
        #         selected_pai = ai_pais[0][0]
        #     else:
        #         selected_pai = ai_pais[1][0]
        # # 如果第一与第二的概率差距小于0.4
        # elif len(ai_pais) > 1 and ai_pais[0][1] - ai_pais[1][1] < 0.4:
        #     # 以5%的概率选择第二个，95%的概率选择第一个
        #     if random.random() < 0.95:
        #         first_pai_count += 1
        #         selected_pai = ai_pais[0][0]
        #     else:
        #         selected_pai = ai_pais[1][0]
        # else:
        #     first_pai_count += 1
        #     selected_pai = ai_pais[0][0]
        # print(str(first_pai_count), " / ", str(all_pai_count))

        # 废弃的方法
        # if len(ai_pais) > 1 and ai_pais[0][1] < 0.63:
        #     # 以13%的概率选择第二个，87%的概率选择第一个
        #     if random.random() < 0.87:
        #         selected_pai = ai_pais[0][0]
        #     else:
        #         selected_pai = ai_pais[1][0]
        # else:
        #     selected_pai = ai_pais[0][0]

        # # 用此方法随机，表现过好，若注释此段则一直一选
        # if ai_pais[0][1] < 0.7:
        #     # 增加非一选的概率:
        #     ex_weight = 2.0
        #     # 筛选出概率大于0.2的元组
        #     filtered_list = [(pai, prob + ex_weight) for pai, prob in ai_pais if prob > 0.2]
        #     # # 给非一选增加ex_weight概率
        #     # for i, (pai, prob) in enumerate(filtered_list):
        #     #     if i != 0:
        #     #         filtered_list[i] = (pai, prob + ex_weight)
        #     # 计算总权重
        #     total_weight = sum(prob for _, prob in filtered_list)
        #     # 随机选择一个操作
        #     random_value = random.uniform(0, total_weight)
        #     cumulative_weight = 0
        #     for pai, prob in filtered_list:
        #         cumulative_weight += prob
        #         if random_value <= cumulative_weight:
        #             selected_pai = pai
        #             break

        # 用此方法随机，rating在92左右，重合率73%左右，有恶手，若注释此段则一直一选
        # if ai_pais[0][1] < 0.96:
        #     # 改变一选的概率: 0~1.0时，越接近0非一选的概率越大 ; 大于1.0时，越大一选的概率越大(一般取1~5)
        #     ex_power = 0.8 # 取0.8时重合率73%左右,rating在92左右;取0.9时重合率80%左右,rating在93左右;
        #     # 筛选出概率大于0.04的元组
        #     filtered_list = [(pai, prob ** ex_power)
        #                      for pai, prob in ai_pais if prob > 0.04]
        #     # 计算总权重
        #     total_weight = sum(prob for _, prob in filtered_list)
        #     # 随机选择一个操作
        #     random_value = random.uniform(0, total_weight)
        #     cumulative_weight = 0
        #     for pai, prob in filtered_list:
        #         cumulative_weight += prob
        #         if random_value <= cumulative_weight:
        #             selected_pai = pai
        #             break

        # 用此方法随机，若注释此段则一直一选
        # if len(ai_pais) > 1 and ai_pais[0][1] - ai_pais[1][1] < 0.3:
        #     # 改变一选的概率: 0~1.0时，越接近0非一选的概率越大 ; 大于1.0时，越大一选的概率越大(一般取1~5)
        #     ex_power = 1.7
        #     # 筛选出概率大于0.04的元组,不含第一个元素
        #     filtered_list = [(pai, prob ** ex_power)
        #                      for pai, prob in ai_pais[1:] if prob > 0.1]
        #     # 计算总权重
        #     total_weight = sum(prob for _, prob in filtered_list)
        #     # 随机选择一个操作
        #     random_value = random.uniform(0, total_weight)
        #     cumulative_weight = 0
        #     for pai, prob in filtered_list:
        #         cumulative_weight += prob
        #         if random_value <= cumulative_weight:
        #             selected_pai = pai
        #             break

        # 用此方法随机，金之间上分，玉之间掉分，rating稍高95左右，重合率75%左右，若注释此段则一直一选
        if ai_pais[0][1] < 0.85:
            # 改变一选的概率: 0~1.0时，越接近0非一选的概率越大 ; 大于1.0时，越大一选的概率越大(一般取1~5)
            ex_power = 0.4  # 取0.45时重合率71%~81%,分数92~95;取0.4时重合率68%~75%,分数90~94;取0.5时重合率84%~85.5%,分数94~95
            # 筛选出概率大于0.12的元组
            filtered_list = [(pai, prob ** ex_power)
                             for pai, prob in ai_pais if prob > 0.12]
            # 计算总权重
            total_weight = sum(prob for _, prob in filtered_list)
            # 随机选择一个操作
            random_value = random.uniform(0, total_weight)
            cumulative_weight = 0
            for pai, prob in filtered_list:
                cumulative_weight += prob
                if random_value <= cumulative_weight:
                    selected_pai = pai
                    break

        # TODO 若注释此段则一直一选
        if selected_pai not in ['none', 'chi', 'pon', 'daiminkan', 'ankan', 'kakan', 'hora', 'reach', 'ryukyoku', 'nukidora']:
            mjai_msg['pai'] = selected_pai

        dahai = mjai_msg['pai']
        if self.isNewRound:
            # In Majsoul, if you are the first dealer, there is no tsumohai, but 14 tehai.
            # However, in MJAI, there is 13 tehai and 1 tsumohai.
            temp_tehai = tehai.copy()
            temp_tehai.append(tsumohai)
            temp_tehai = sorted(temp_tehai, key=cmp_to_key(compare_pai))
            for i in range(14):
                if dahai == temp_tehai[i]:
                    logger.debug(
                        f"dahai:{dahai} tehai:{tehai} tsumohai:{tsumohai} isNewRound:{self.isNewRound} i:{i}")
                    pai_coord = self.get_pai_coord(i, temp_tehai)
                    self.page_clicker(pai_coord)
                    self.do_autohu()
                    self.isNewRound = False
                    return
        if tsumohai != '?':
            if dahai == tsumohai:
                logger.debug(
                    f"dahai:{dahai} tehai:{tehai} tsumohai:{tsumohai} isNewRound:{self.isNewRound} dahai== tsumohai")
                pai_coord = self.get_pai_coord(13, tehai)
                self.page_clicker(pai_coord)
                return
        for i in range(13):
            if dahai == tehai[i]:
                logger.debug(
                    f"dahai:{dahai} tehai:{tehai} tsumohai:{tsumohai} isNewRound:{self.isNewRound} i:{i}")
                pai_coord = self.get_pai_coord(i, tehai)
                self.page_clicker(pai_coord)
                break

    def mjai2action(self, mjai_msg: dict | None, tehai: list[str], tsumohai: str | None):
        # print(f"mjai2action: mjai_msg:{mjai_msg} tehai:{tehai} tsomohai:{tsumohai}")
        # TODO 打印4p场每个操作ai的推荐率
        print(meta_to_recommend(mjai_msg['meta']))
        # 将字符串解析为字典
        dahai_delay = self.decide_random_time()
        if mjai_msg is None:
            return
        mtype = mjai_msg['type']
        if mtype == 'dahai' and not self.reached:
            time.sleep(dahai_delay)
            self.click_dahai(mjai_msg, tehai, tsumohai)
            return
        # 这里是mjai的events
        # https://mjai.app/docs/mjai-protocol#:~:text=Flowchart-,Events,-Start%20Game
        if mtype in ['none', 'chi', 'pon', 'daiminkan', 'ankan', 'kakan', 'hora', 'reach', 'ryukyoku', 'nukidora']:
            time.sleep(random.uniform(1.8, 2.8))
            self.click_chiponkan(mjai_msg, tehai, tsumohai)
            # kan can have multiple candidates too! ex: tehai=1111m 1111p 111s 11z, tsumohai=1s

# script/NoAddOne/main.py

import logging
import os
import sys
import random  # 新增导入

# 添加项目根目录到sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.config import owner_id
from app.api import *
from app.switch import load_switch, save_switch

# 数据存储路径，实际开发时，请将NoAddOne替换为具体的数据存放路径
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "NoAddOne",
)

# 为每个群维护状态
group_states = {}


# 查看功能开关状态
def load_function_status(group_id):
    return load_switch(group_id, "打断复读")


# 保存功能开关状态
def save_function_status(group_id, status):
    save_switch(group_id, "打断复读", status)


# 处理消息函数
def process_message(group_id, message):
    if group_id not in group_states:
        group_states[group_id] = {"last_message": None, "message_count": 0}

    state = group_states[group_id]

    if message == state["last_message"]:
        state["message_count"] += 1
        if state["message_count"] == 2:
            shuffled_message = message
            while shuffled_message == message:
                shuffled_message = "".join(random.sample(message, len(message)))
            state["message_count"] = 0
            return shuffled_message
    else:
        state["last_message"] = message
        state["message_count"] = 1

    return None


# 群消息处理函数
async def handle_NoAddOne_group_message(websocket, msg):
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        raw_message = str(msg.get("raw_message"))
        role = str(msg.get("sender", {}).get("role"))
        message_id = str(msg.get("message_id"))

        # 鉴权
        if is_authorized(role, user_id):
            # 管理员命令
            if raw_message == "nacon":
                save_function_status(group_id, True)
                await send_group_msg(
                    websocket, group_id, f"[CQ:reply,id={message_id}]已开启打断复读"
                )
            elif raw_message == "naoff":
                save_function_status(group_id, False)
                await send_group_msg(
                    websocket, group_id, f"[CQ:reply,id={message_id}]已关闭打断复读"
                )

        # 检查开关
        if not load_function_status(group_id):
            return

        # 处理消息
        result = process_message(group_id, raw_message)
        if result:
            logging.info(f"打断复读: {result}")
            await send_group_msg(websocket, group_id, result)

    except Exception as e:
        logging.error(f"处理NoAddOne群消息失败: {e}")
        return

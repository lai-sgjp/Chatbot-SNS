"""OneBot v11 协议常量和工具函数。"""

# === 消息动作 ===
ACTION_SEND_PRIVATE_MSG = "send_private_msg"
ACTION_SEND_GROUP_MSG = "send_group_msg"
ACTION_SEND_MSG = "send_msg"
ACTION_DELETE_MSG = "delete_msg"

# === 事件类型 ===
POST_TYPE_MESSAGE = "message"
POST_TYPE_NOTICE = "notice"
POST_TYPE_REQUEST = "request"
POST_TYPE_META_EVENT = "meta_event"

# === 消息类型 ===
MESSAGE_TYPE_PRIVATE = "private"
MESSAGE_TYPE_GROUP = "group"

# === 元事件类型 ===
META_EVENT_LIFECYCLE = "lifecycle"
META_EVENT_HEARTBEAT = "heartbeat"


def build_action(action: str, params: dict) -> dict:
    """构建 OneBot 动作请求。"""
    return {
        "action": action,
        "params": params,
    }


def build_send_private_msg(user_id: int, message: str) -> dict:
    return build_action(ACTION_SEND_PRIVATE_MSG, {
        "user_id": user_id,
        "message": message,
    })


def build_send_group_msg(group_id: int, message: str) -> dict:
    return build_action(ACTION_SEND_GROUP_MSG, {
        "group_id": group_id,
        "message": message,
    })

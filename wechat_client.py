from gewechat_client import GewechatClient
from logger import logger

class WeChatBot:
    def __init__(self):
        # 配置参数
        self.base_url = "http://127.0.0.1:2531/v2/api"  # 无需修改
        self.token = "xxx"
        self.app_id = "xxx"
        # 创建 GewechatClient 实例
        self.client = GewechatClient(self.base_url, self.token)

    def login(self):
        # 登录, 自动创建二维码，扫码后自动登录
        self.app_id, error_msg = self.client.login(app_id=self.app_id)
        if error_msg:
            logger.error(f"登录失败: {error_msg}")
            return False
        logger.info("登录成功")
        return True

    def set_callback(self, callback_url):
        resp = self.client.set_callback(self.token, callback_url)
        if resp.get('ret') != 200:
            logger.error(f"设置回调地址失败: {resp}")
            return False
        logger.info("设置回调地址成功")
        return True
    
    def get_brief_info(self, wxids):
        resp = self.client.get_brief_info(self.app_id, wxids)
        if resp.get('ret') != 200:
            logger.error(f"获取好友简要信息失败: {resp}")
            return
        logger.info("获取好友简要信息成功")
        return resp

    def get_chatroom_announcement(self, chatroom_id):
        resp = self.client.get_chatroom_announcement(self.app_id, chatroom_id)
        if resp.get('ret') != 200:
            logger.error(f"获取群公告失败: {resp}")
            return
        logger.info("获取群公告成功")
        return resp
    
    def set_chatroom_announcement(self, chatroom_id, content):
        resp = self.client.set_chatroom_announcement(self.app_id, chatroom_id, content)
        if resp.get('ret') != 200:
            logger.error(f"设置群公告失败: {resp}")
            return False
        logger.info("设置群公告成功")
        return True
    
    def post_text(self, to_wxid, content, ats=""):
        resp = self.client.post_text(self.app_id, to_wxid, content, ats)
        if resp.get('ret') != 200:
            logger.error(f"发送消息失败: {resp}")
            return False
        logger.info("发送消息成功")
        return True
    
    def fetch_contacts_list(self):
        resp = self.client.fetch_contacts_list(self.app_id)
        if resp.get('ret') != 200:
            logger.error(f"获取通讯录列表消息失败: {resp}")
            return
        logger.info("获取通讯录列表成功")
        return resp
    
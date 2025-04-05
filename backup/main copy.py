from gewechat_client import GewechatClient
from flask import Flask, request, jsonify
import json
import requests
import json
import re
import traceback
import time

global_conversation_id = ""

def llm_chat(query):
    global global_conversation_id

    url = "http://rag.gsbot.net/v1/chat-messages"

    payload = json.dumps({
    "inputs": {},
    "query": query,
    "response_mode": "blocking",
    "conversation_id": global_conversation_id,
    "user": "abc-123",
    "files": []
    })
    headers = {
    'Authorization': 'Bearer app-EK7JRHbsOxOVPfNwn8AZeN1c',
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    print('llm_chat_response_text', response.text)
    resp_json = response.json()
    
    global_conversation_id = resp_json.get('conversation_id')
    return response.json()


class WeChatBot:
    def __init__(self):
        # 配置参数
        self.base_url = "http://127.0.0.1:2531/v2/api"
        self.token = "76e2b8c15d3a4995a6cecbb7e4557967"
        self.app_id = "wx_cwKfioy9eh8E3RcgPXxXx"
        
        # 创建 GewechatClient 实例
        self.client = GewechatClient(self.base_url, self.token)
        # 接龙信息
        self.jielong_content = ""
    def login(self):
        # 登录, 自动创建二维码，扫码后自动登录
        self.app_id, error_msg = self.client.login(app_id=self.app_id)
        if error_msg:
            print("登录失败")
            return
        try:
            print("登录成功")
            # time.sleep(10)
            # 设置回调地址
            resp = self.client.set_callback(self.token, "http://10.12.10.28:9919/v2/api/callback/collect")
            print(f"设置回调地址 - {resp}")
            if resp.get('ret') != 200:
                print("设置回调地址失败:", resp)
                return
            print("设置回调地址成功:", resp)

            # 获取好友列表
            fetch_contacts_list_result = self.client.fetch_contacts_list(self.app_id)
            if fetch_contacts_list_result.get('ret') != 200 or not fetch_contacts_list_result.get('data'):
                print("获取通讯录列表失败:", fetch_contacts_list_result)
                return
            # {'ret': 200, 'msg': '操作成功', 'data': {'friends': ['weixin', 'fmessage', 'medianote', 'floatbottle', 'wxid_abcxx'], 'chatrooms': ['1234xx@chatroom'], 'ghs': ['gh_xx']}}
            friends = fetch_contacts_list_result['data'].get('friends', [])
            if not friends:
                print("获取到的好友列表为空")
                return
            print("获取到的好友列表:", friends)

            # 获取好友的简要信息
            friends_info = self.client.get_brief_info(self.app_id, friends)
            if friends_info.get('ret') != 200 or not friends_info.get('data'):
                print("获取好友简要信息失败:", friends_info)
                return
            friends_info_list = friends_info['data']
            if not friends_info_list:
                print("获取到的好友简要信息列表为空")
                return
            wxid = None
            for friend_info in friends_info_list:
                if friend_info.get('nickName') == "超人不会飞":
                    print("找到好友:", friend_info)
                    wxid = friend_info.get('userName')
                    break
            if not wxid:
                print(f"没有找到好友: 超人不会飞 的wxid")
                return
            print("找到好友:", wxid)

            # 发送消息
            send_msg_result = self.client.post_text(self.app_id, wxid, "你好啊")
            if send_msg_result.get('ret') != 200:
                print("发送消息失败:", send_msg_result)
                return
            print("发送消息成功:", send_msg_result)
        except Exception as e:
            # print("Failed to fetch contacts list:", str(e))
            print(f"Failed to fetch contacts list:: {__name__} -> [line: {traceback.extract_tb(e.__traceback__)[-1].lineno}] error msg: \r\n{traceback.format_exc()}")


    def handle_callback(self, request_data):
        # 将原来的 wechat_callback 函数逻辑移到这里
        try:
            datas = request_data
            # 打印日志，方便调试
            print(f"收到数据: {json.dumps(datas, ensure_ascii=False)}")
            data = datas.get('Data')

            if not data.get('FromUserName'):
                print("不是好友消息")
                return jsonify({"ret": "500", "msg": "不是好友消息"}), 200

            _from_username = data.get('FromUserName').get("string")
            _to_username = data.get('ToUserName').get("string")
            _content = data.get('Content').get('string')

            if "@chatroom" in _from_username:
                from_username_wxid = _content.split(":")[0]
                brief_info = self.client.get_brief_info(app_id=self.app_id, wxids=[from_username_wxid,])
                nick_name = brief_info.get('data')[0].get('nickName')
                
                if ":\n@" in _content:
                    from_username_content = _content.split("@AI机器人")[-1]
                    print(f"群聊@消息: {from_username_wxid} -> {from_username_content}")
                    if from_username_content.strip() == "公告":
                        resp = self.client.get_chatroom_announcement(app_id=self.app_id, chatroom_id=_from_username)
                        announcement = resp.get('data').get('announcement')
                        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                        if "机器人自动更新：" in announcement:
                            announcement = announcement.rsplit("：",1)[0] + "：" + current_time
                        else:
                            announcement = announcement + "\n机器人自动更新：" + current_time
                        self.client.set_chatroom_announcement(app_id=self.app_id, chatroom_id=_from_username, content=announcement)
                        return jsonify({"status": "success", "message": "Received"}), 200
                    elif from_username_content.strip() == "接龙":
                        content = self.jielong_content if self.jielong_content else "暂无接龙"
                        send_msg_result = self.client.post_text(app_id=self.app_id, to_wxid=_from_username, content=content, ats=from_username_wxid)
                        return jsonify({"status": "success", "message": "Received"}), 200
                    else:
                        llm_response = llm_chat(query=from_username_content)
                        if llm_response:
                            llm_answer = llm_response.get('answer')
                        else:
                            llm_answer = "自动回复：无法回答"
                    
                        send_msg_result = self.client.post_text(app_id=self.app_id, to_wxid=_from_username, content=f"@{nick_name} {llm_answer}", ats=from_username_wxid)
                        if send_msg_result.get('ret') != 200:
                            print("发送消息失败:", send_msg_result)
                            return
                        print("发送消息成功:", send_msg_result)

                else:
                    if '<sysmsg' in _content:
                        # 撤回消息或者其他
                        print("系统消息，不处理！")
                        return jsonify({"status": "success", "message": "Received"}), 200
                    
                    from_username_content = _content.split(":")[-1].replace("\n", "")
                    print(f"群聊不@消息: {from_username_wxid} -> {from_username_content}")
                    llm_response = llm_chat(query=from_username_content)
                    llm_answer = llm_response.get('answer')
                    if "请注意言辞，警告一次" in llm_answer:
                        print("警告消息，不处理！")
                        llm_answer = llm_answer
                        send_msg_result = self.client.post_text(app_id=self.app_id, to_wxid=_from_username, content=f"@{nick_name} {llm_answer}", ats=from_username_wxid)
                        if send_msg_result.get('ret') != 200:
                            print("发送消息失败:", send_msg_result)
                            return jsonify({"status": "error", "message": send_msg_result}), 500
                        print("发送消息成功:", send_msg_result)
                    
                    if '<?xml version="1.0"?>' in from_username_content and '<title>#接龙' in from_username_content:
                        self.jielong_content = from_username_content

                return jsonify({"status": "success", "message": "Received"}), 200
            else:
                print("私聊")
                return jsonify({"status": "success", "message": "Received"}), 200

            return jsonify({"status": "success", "message": "Received"}), 200
        except Exception as e:
            print(f"处理回调时发生错误:: {__name__} -> [line: {traceback.extract_tb(e.__traceback__)[-1].lineno}] error msg: \r\n{traceback.format_exc()}")
            return jsonify({"status": "error", "message": str(e)}), 500

app = Flask(__name__)
bot = WeChatBot()

@app.route('/v2/api/callback/collect', methods=['POST'])
def wechat_callback():
    return bot.handle_callback(request.get_json())


if __name__ == "__main__":
    # bot.login()
    app.run(host='0.0.0.0', port=9919, debug=True)
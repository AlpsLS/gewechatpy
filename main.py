import json
from datetime import datetime
import json
import traceback
import time
import os
import argparse

import dashscope
import requests
from flask import Flask, request, jsonify

from wechat_client import WeChatBot
from logger import logger

global_conversation_id = ""

app = Flask(__name__)
bot = WeChatBot()

SCHEDULER_URL = "http://127.0.0.1:9920"

def add_scheduler_task(task_type, run_date, task_id, **params):
    """添加调度任务"""
    try:
        response = requests.post(
            f"{SCHEDULER_URL}/scheduler/add_task",
            json={
                'task_type': task_type,
                'run_date': run_date,
                'task_id': task_id,
                'params': params
            }
        )
        if response.status_code == 200:
            return True
        else:
            logger.error(f"添加任务失败: {response.text}")
            return False
    except Exception as e:
        logger.error(f"请求调度器服务失败: {str(e)}")
        return False
    
def list_scheduler_task():
    """查询调度任务"""
    try:
        response = requests.get(
            f"{SCHEDULER_URL}/scheduler/list_tasks"
        )
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"查询任务失败: {response.text}")
            return None
    except Exception as e:
        logger.error(f"请求调度器服务失败: {str(e)}")
        return False
    
def delete_scheduler_task(task_id):
    """删除调度任务"""
    try:
        response = requests.delete(
            f"{SCHEDULER_URL}/scheduler/remove_task/{task_id}"
        )
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"删除任务失败: {response.text}")
            return None
    except Exception as e:
        logger.error(f"请求调度器服务失败: {str(e)}")
        return False

@app.route('/v2/api/callback/collect', methods=['POST'])
def wechat_callback():
    datas = request.get_json()
    callback_client = HandleCallback(datas=datas)
    callback_client.handle_callback()
    return jsonify({"msg": "ok"})

def llm_chat_dify(query):
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
    logger.debug(f'llm answer响应: {response.text}')
    resp_json = response.json()
    if resp_json:
        llm_answer = resp_json.get('answer')
    else:
        llm_answer = "自动回复：无法回答"
    # global_conversation_id = resp_json.get('conversation_id')
    return llm_answer


def llm_chat(query, only_check=False):
    try:
        # 只检查是否包含脏话、粗口、侮辱性语言、威胁性语言
        if only_check:
            system_prompt = f"""你是一个专业的微信助手，需要遵循以下规则：

1. 如果用户输入包含严重的脏话、粗口、侮辱性语言、威胁性语言、敏感政治话题, 不包括调侃口吻（如"傻瓜"、"笨蛋"等轻微玩笑话）：
   只回复："警告，注意言辞！"，其他多余的信息一律不回复

2. 对于正常提问：
   只回复："OK"，其他多余的信息一律不回复

请根据用户的问题给出合适的回答：
{query}"""
        else:
            system_prompt = f"""你是一个专业的微信助手，需要遵循以下规则：

1. 如果用户输入包含严重的脏话、粗口、侮辱性语言、威胁性语言：
   只回复："警告，注意言辞！"，其他多余的信息一律不回复
   
2. 如果用户使用调侃口吻（如"傻瓜"、"笨蛋"等轻微玩笑话）：
   - 用轻松幽默的语气回应
   - 不要警告，保持对话轻松愉快

3. 如果用户谈论敏感政治话题：
   只回复："警告，注意言辞！"，其他多余的信息一律不回复

4. 对于正常提问：
   - 保持友善、专业的语气
   - 回答要简洁，控制在200字以内
   - 使用口语化表达，易于理解
   - 如果不确定的问题，诚实说明"这个问题我不太确定"

请根据用户的问题给出合适的回答：
{query}"""

        response = dashscope.Generation.call(
            model='qwen-plus',
            prompt=system_prompt,
            api_key='sk-50b4dee6e5ef4f78ba79a33d0fac2bca',
            verify=False  # 禁用 SSL 验证
        )
        
        if response.status_code == 200:
            logger.info(f"LLM响应: {response.output.text}")
            return response.output.text
        else:
            logger.error(f"调用LLM失败: {response.status_code}")
            return "自动回复：无法回答"
            
    except Exception as e:
        logger.info(f"调用LLM异常:: {__name__} -> [line: {traceback.extract_tb(e.__traceback__)[-1].lineno}] error msg: \r\n{traceback.format_exc()}")
        return "自动回复：无法回答"
    

class HandleCallback:
    def __init__(self, datas):
        self.datas = datas

    def handle_callback(self):
        try:
            datas = self.datas
            logger.info(f"回调数据: {json.dumps(datas, ensure_ascii=False)}")
            
            if not datas.get('Data'):
                logger.info("异常数据，不处理")
                return

            robot_wxid = datas.get('Wxid')
            data = datas.get('Data')
            msg_type = data.get('MsgType')
            if msg_type == 1:
                logger.info("文本消息")
            else:
                logger.info("其他消息，不处理")
                return
                
            _from_username = data.get('FromUserName').get("string")
            
            if robot_wxid == _from_username:
                logger.info("自己发的消息，不处理")
                return
            # _to_username = data.get('ToUserName').get("string")
            _content = data.get('Content').get('string')
            _push_content = data.get('PushContent') or ""

            if "@chatroom" in _from_username:
                from_username_wxid = _content.split(":")[0]
                brief_info = bot.get_brief_info(wxids=[from_username_wxid,])
                nick_name = brief_info.get('data')[0].get('nickName')
                
                if "在群聊中@了你" in _push_content:
                    from_username_content = _content.split("\n")[-1]
                    logger.info(f"群聊@消息: {nick_name} -> {from_username_content}")
                    if from_username_content.strip()[-2:] == "公告" or from_username_content.split(':\n')[-1].split('@')[0] == "公告":
                        resp = bot.get_chatroom_announcement(chatroom_id=_from_username)
                        announcement = resp.get('data').get('announcement')
                        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                        if "机器人自动更新：" in announcement:
                            announcement = announcement.rsplit("：",1)[0] + "：" + current_time
                        else:
                            announcement = announcement + "\n机器人自动更新：" + current_time
                        bot.set_chatroom_announcement(chatroom_id=_from_username, content=announcement)
                        return
                    else:
                        llm_answer = llm_chat(query=from_username_content)
                        bot.post_text(to_wxid=_from_username, content=f"@{nick_name} {llm_answer}", ats=from_username_wxid)
                        return

                else:           
                    from_username_content = _content.split(":")[-1].replace("\n", "")
                    logger.info(f"群聊不@我: {nick_name} -> {from_username_content}")
                    llm_answer = llm_chat(query=from_username_content, only_check=True)
                    if "警告，注意言辞" in llm_answer:
                        logger.info("警告消息，不处理！")
                        bot.post_text(to_wxid=_from_username, content=f"@{nick_name} {llm_answer}", ats=from_username_wxid)

                return
            else:
                logger.info("私聊")
                
                if "添加定时任务" in _content and "#" in _content:
                    content_list = _content.split("#")
                    content_list = [c.strip() for c in content_list if c.strip() != '\n' and c.strip() != '']
                    logger.info(f"定时任务信息: {content_list}")
                    description = content_list[1]
                    chatroom_id = content_list[2]
                    schedule_time = content_list[3]
                    content = content_list[-1]
                    content = "@所有人\n" + content
                    
                    # 注册定时任务
                    task_id = f"{int(time.time()*1000)}"
                    success = add_scheduler_task(
                        task_type='send_text',
                        run_date=schedule_time,
                        task_id=task_id,
                        to_wxid=chatroom_id,
                        content=content,
                        ats="notify@all"
                    )
                    
                    if success:
                        logger.info(f"已添加群定时任务: {task_id} -> {schedule_time}")
                        bot.post_text(to_wxid=_from_username, content=f"已设置定时任务[{task_id}]，将在 {schedule_time} 执行定时任务：{description}。 内容：\n{content}")

                    else:
                        logger.error("添加定时任务失败")
                        bot.post_text(to_wxid=_from_username, content="设置定时任务失败，请稍后重试")
                    return
                
                elif "查询定时任务" in _content and "#" in _content:
                    # 查询定时任务
                    success = list_scheduler_task()
                    bot.post_text(to_wxid=_from_username, content=f"定时任务列表:\n{json.dumps(success, ensure_ascii=False, indent=4)}")
                    return
                
                elif "删除定时任务" in _content and "#" in _content:
                    # 删除定时任务
                    content_list = _content.split("#")
                    content_list = [c.strip() for c in content_list if c.strip() != '\n' and c.strip() != '']
                    task_id = content_list[1]
                    success = delete_scheduler_task(task_id=content_list[1])
                    bot.post_text(to_wxid=_from_username, content=f"删除定时: {success}")
                    return

                elif "查询群聊" in _content and "#" in _content:
                    # 查询群聊信息
                    chatroom_ids = bot.fetch_contacts_list().get("data").get('chatrooms')
                    print(chatroom_ids)
                    chatrooms_info = bot.get_brief_info(wxids=chatroom_ids)
                    chatrooms_info = [{"userName": chatroom.get('userName'), "nickName": chatroom.get('nickName')} for chatroom in chatrooms_info.get('data')]
                    bot.post_text(to_wxid=_from_username, content=f"通讯录群聊信息:\n{json.dumps(chatrooms_info, ensure_ascii=False, indent=4)}")
                    return
                
                llm_answer = llm_chat(query=_content)
                bot.post_text(to_wxid=_from_username, content=llm_answer)
                return

        except Exception as e:
            logger.info(f"处理回调时发生错误:: {__name__} -> [line: {traceback.extract_tb(e.__traceback__)[-1].lineno}] error msg: \r\n{traceback.format_exc()}")
            return


def parse_args():
    parser = argparse.ArgumentParser(description='WeChat Bot 控制脚本')
    parser.add_argument('-l', '--login', action='store_true', help='登录微信')
    parser.add_argument('-s', '--scheduler', action='store_true', help='启动调度器服务（另启动一个终端）')
    parser.add_argument('-r', '--run', action='store_true', help='启动主服务')
    parser.add_argument('-c', '--callback', action='store_true', help='设置回调（另启动一个终端，需要启动主服务后）')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    if args.login:
        logger.info("执行登录操作...")
        bot.login()
    
    elif args.scheduler:
        logger.info("启动调度器服务...")
        os.system("python scheduler_service.py")

    elif args.run:
        logger.info("启动 Flask 服务...")
        import gunicorn.app.base
        
        class GunicornApp(gunicorn.app.base.BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                for key, value in self.options.items():
                    self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        options = {
            'bind': '0.0.0.0:9919',
            'workers': 4,
            'worker_class': 'sync',
            'accesslog': './logs/access.log',
            'errorlog': './logs/error.log'
        }
        
        GunicornApp(app, options).run()
        
    elif args.callback:
        logger.info("设置回调地址...")
        bot.set_callback(callback_url="http://10.12.10.28:9919/v2/api/callback/collect")
    
    else:
        logger.info("请按顺序依次启动：")
        logger.info("  -l 或 --login     : 登录微信")
        logger.info("  -s 或 --scheduler : 启动调度器服务（另启一个终端）")
        logger.info("  -r 或 --run       : 启动主服务（另启动一个终端）")
        logger.info("  -c 或 --callback  : 设置回调（另启动一个终端）")
    
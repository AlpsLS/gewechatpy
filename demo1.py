from gewechat_client import GewechatClient
from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

def main():
    # 配置参数
    base_url = os.environ.get("BASE_URL", "http://127.0.0.1:2531/v2/api")
    token = os.environ.get("GEWECHAT_TOKE", "76e2b8c15d3a4995a6cecbb7e4557967")
    app_id = os.environ.get("APP_ID", "wx_cwKfioy9eh8E3RcgPXxXx")
    send_msg_nickname = "超人不会飞" # 要发送消息的好友昵称

    # 创建 GewechatClient 实例
    client = GewechatClient(base_url, token)

    # 登录, 自动创建二维码，扫码后自动登录
    app_id, error_msg = client.login(app_id=app_id)
    if error_msg:
        print("登录失败")
        return
    try:
        # 设置回调地址
        resp = client.set_callback(token, "http://10.12.10.28:9919/v2/api/callback/collect")
        if resp.get('ret') != 200:
            print("设置回调地址失败:", resp)
            return
        print("设置回调地址成功:", resp)

        # 获取好友列表
        fetch_contacts_list_result = client.fetch_contacts_list(app_id)
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
        friends_info = client.get_brief_info(app_id, friends)
        if friends_info.get('ret') != 200 or not friends_info.get('data'):
            print("获取好友简要信息失败:", friends_info)
            return
        # {
        #     "ret": 200,
        #     "msg": "获取联系人信息成功",
        #     "data": [
        #         {
        #             "userName": "weixin",
        #             "nickName": "微信团队",
        #             "pyInitial": "WXTD",
        #             "quanPin": "weixintuandui",
        #             "sex": 0,
        #             "remark": "",
        #             "remarkPyInitial": "",
        #             "remarkQuanPin": "",
        #             "signature": null,
        #             "alias": "",
        #             "snsBgImg": null,
        #             "country": "",
        #             "bigHeadImgUrl": "https: //wx.qlogo.cn/mmhead/Q3auHgzwzM6H8bJKHKyGY2mk0ljLfodkWnrRbXLn3P11f68cg0ePxA/0",
        #             "smallHeadImgUrl": "https://wx.qlogo.cn/mmhead/Q3auHgzwzM6H8bJKHKyGY2mk0ljLfodkWnrRbXLn3P11f68cg0ePxA/132",
        #             "description": null,
        #             "cardImgUrl": null,
        #             "labelList": null,
        #             "province": "",
        #             "city": "",
        #             "phoneNumList": null
        #         }
        #     ]
        # }
        
        # 找对目标好友的wxid
        friends_info_list = friends_info['data']
        if not friends_info_list:
            print("获取到的好友简要信息列表为空")
            return
        wxid = None
        for friend_info in friends_info_list:
            if friend_info.get('nickName') == send_msg_nickname:
                print("找到好友:", friend_info)
                wxid = friend_info.get('userName')
                break
        if not wxid:
            print(f"没有找到好友: {send_msg_nickname} 的wxid")
            return
        print("找到好友:", wxid)

        # 发送消息
        send_msg_result = client.post_text(app_id, wxid, "你好啊")
        if send_msg_result.get('ret') != 200:
            print("发送消息失败:", send_msg_result)
            return
        print("发送消息成功:", send_msg_result)
    except Exception as e:
        print("Failed to fetch contacts list:", str(e))

@app.route('/v2/api/callback/collect', methods=['POST'])
def wechat_callback():
    """
    处理 Gewechat 发送的回调请求
    """
    try:
        data = request.get_json()  # 获取 JSON 数据
        event = data.get("event")  # 获取事件类型
        event_data = data.get("data")  # 具体事件数据

        # 打印日志，方便调试
        print(f"收到数据: {json.dumps(data, ensure_ascii=False)}")
        print(f"收到事件: {event}")
        print(f"事件数据: {event_data}")


        return jsonify({"status": "success", "message": "Received"}), 200
    except Exception as e:
        print(f"处理回调时发生错误: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    # main()
    
    app.run(host='0.0.0.0', port=9919, debug=True)

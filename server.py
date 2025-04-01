from flask import Flask, request, jsonify
import json
from gewechat_client import GewechatClient

app = Flask(__name__)

base_url = "http://127.0.0.1:2531/v2/api"
token = "76e2b8c15d3a4995a6cecbb7e4557967"
app_id = "wx_cwKfioy9eh8E3RcgPXxXx"

client = GewechatClient(base_url, token)

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9919, debug=True)

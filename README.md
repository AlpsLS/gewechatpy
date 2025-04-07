# GeweChatPy - 微信机器人

基于 Python 的微信机器人，支持群消息定时发送、群消息敏感词检查、智能对话等功能。

## 功能特点

- 微信消息自动回复
- 群群消息定时发送
- 智能对话（基于通义千问）
- 定时任务管理
- 多进程支持
- 完整的日志记录

## 环境要求

- Python 3.8+
- pip
- 微信客户端（用于登录）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 项目结构

```
gewechatpy/
├── main.py              # 主程序入口
├── scheduler.py         # 调度器实现
├── scheduler_service.py # 调度器服务
├── wechat_client.py     # 微信客户端
├── logger.py           # 日志模块
├── logs/               # 日志目录
└── requirements.txt    # 依赖列表
```

## 部署步骤

### 提前先获取token和appId

先获取token，返回值里的data就是token
```bash
curl --location --request POST 'http://127.0.0.1:2531/v2/api/tools/getTokenId'
```

返回
```json
{
    "ret": 200,
    "msg": "执行成功",
    "data": "76e2b8c15d3a4995a6cecbb7e4557967"
}
```

获取app_id（header里换成上一步获取到的token），返回值里的data里的appid。
首次登录传空，会自动触发创建设备，掉线后重新登录则必须传接口返回的appId，注意同一个号避免重复创建设备，以免触发官方风控
```bash
curl --location 'http://127.0.0.1:2531/v2/api/login/getLoginQrCode' \
--header 'X-GEWE-TOKEN: 76e2b8c15d3a4995a6cecbb7e4557967' \
--header 'Content-Type: application/json' \
--data '{
  "appId": ""
}'
```

返回示例：
```json
{
  "ret": 200,
  "msg": "操作成功",
  "data": {
    "appId": "wx_wR_U4zPj2M_OTS3BCyoE4",
    "qrData": "http://weixin.qq.com/x/4dmHZZMtoLbHoLZwd1wE",
    "qrImgBase64": "xxxx",
    "uuid": "4dmHZZMtoLbHoLZwd1wE"
  }
}
```

获取到token和appId后，修改wechat_client.py里的token和appId，以后都不用修改了。
```python
    def __init__(self):
        # 配置参数
        self.base_url = "http://127.0.0.1:2531/v2/api"
        self.token = "xxx"
        self.app_id = "xxx"
```

```python
python main.py 
2025-04-07 14:28:32 [INFO] main.py:346 - 请按顺序依次启动：
2025-04-07 14:28:32 [INFO] main.py:347 -   -l 或 --login     : 登录微信
2025-04-07 14:28:32 [INFO] main.py:348 -   -s 或 --scheduler : 启动调度器服务（另启一个终端）
2025-04-07 14:28:32 [INFO] main.py:349 -   -r 或 --run       : 启动主服务（另启动一个终端）
2025-04-07 14:28:32 [INFO] main.py:350 -   -c 或 --callback  : 设置回调（另启动一个终端）
```
### 1. 登录微信

启动服务，扫码登录
```bash
python main.py -l
```

按照提示扫描二维码登录微信。


### 2. 启动调度器服务

```bash
python main.py -s
```

调度器服务将在本地 9920 端口运行，用于管理定时任务。

### 3. 启动主服务

使用 Gunicorn 启动主服务：

```bash
python main.py -r
```

主服务将在 9919 端口运行，处理微信消息和回调。

### 4. 设置微信回调（只需设置一次）

先修改main.py这个地方的配置，改成本地ip地址，不要使用127.0.0.1（微信登录成功之后才能设置成功）
```python
      bot.set_callback(callback_url=f"http://{ip}:9919/v2/api/callback/collect")
```
```bash
python main.py -c
```

这将设置微信消息的回调地址。


## 使用方法

### 查询群聊信息

发送消息格式：
```
# 查询群聊
```


### 查询定时任务

发送消息格式：
```
# 查询定时任务
```


### 设置定时任务

发送消息格式：
```
# 添加定时任务 #
# 任务描述
# 群ID #
# 执行时间 #
消息内容
```

示例：
```
# 添加定时任务 #
# 提醒群成员签到
# 群ID #
# 执行时间 #
大家记得签到了
```

### 删除定时任务

发送消息格式：
```
# 删除定时任务 #
# 任务ID #
```

## 日志查看

日志文件位于 `logs` 目录：
- `app_YYYYMMDD.log` - 应用日志
- `access.log` - 访问日志
- `error.log` - 错误日志

## 配置说明

### 调度器配置

在 `scheduler_service.py` 中：
```python
class Config:
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "Asia/Shanghai"
    SCHEDULER_EXECUTORS = {
        'default': {'type': 'threadpool', 'max_workers': 20}
    }
    SCHEDULER_JOB_DEFAULTS = {
        'coalesce': False,
        'max_instances': 3
    }
```

### 主服务配置

在 `main.py` 中：
```python
options = {
    'bind': '0.0.0.0:9919',
    'workers': 4,
    'worker_class': 'sync',
    'accesslog': './logs/access.log',
    'errorlog': './logs/error.log'
}
```

## 常见问题

1. 定时任务不执行
   - 检查调度器服务是否正常运行
   - 查看调度器服务日志
   - 确认时间格式是否正确

2. 微信登录失败
   - 确保微信客户端已登录
   - 检查网络连接
   - 查看日志文件中的错误信息

3. 消息未响应
   - 检查主服务是否正常运行
   - 确认回调地址设置正确
   - 查看日志文件中的错误信息

## 维护说明

1. 日志轮转
   - 日志文件大小超过 10MB 会自动轮转
   - 最多保留 5 个备份文件

2. 进程管理
   - 使用 supervisor 或 systemd 管理进程
   - 配置自动重启

3. 监控建议
   - 监控服务进程状态
   - 监控日志文件大小
   - 设置错误告警

## 开发计划

- [ ] 添加更多智能对话功能
- [ ] 支持更多定时任务类型
- [ ] 添加管理界面
- [ ] 支持多机器人管理

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License

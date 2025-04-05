from flask import Flask, request, jsonify
from scheduler import scheduler
from logger import logger
from datetime import datetime
import time

app = Flask(__name__)

# 配置 Flask-APScheduler
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

app.config.from_object(Config())

# 初始化调度器
scheduler.init_app(app)
scheduler.start()

def schedule_announcement_task(chatroom_id, content):
    """设置群公告的定时任务"""
    try:
        logger.info(f"定时任务触发：设置群公告 chatroom_id={chatroom_id}")
        from wechat_client import WeChatBot
        bot = WeChatBot()
        bot.set_chatroom_announcement(chatroom_id=chatroom_id, content=content)
        logger.info("群公告设置成功")
    except Exception as e:
        logger.error(f"设置群公告失败: {str(e)}")

@app.route('/scheduler/add_task', methods=['POST'])
def add_task():
    """添加定时任务的API接口"""
    try:
        data = request.get_json()
        task_type = data.get('task_type')
        run_date = data.get('run_date')
        task_id = data.get('task_id')
        params = data.get('params', {})

        if task_type == 'announcement':
            scheduler.add_date_task(
                func=schedule_announcement_task,
                run_date=run_date,
                task_id=task_id,
                **params
            )
            return jsonify({
                'status': 'success',
                'message': f'任务已添加: {task_id} -> {run_date}'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'未知的任务类型: {task_type}'
            }), 400

    except Exception as e:
        logger.error(f"添加任务失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/scheduler/list_tasks', methods=['GET'])
def list_tasks():
    """获取所有任务"""
    try:
        jobs = scheduler.get_jobs()
        tasks = [{
            'id': job.id,
            'next_run_time': str(job.next_run_time),
            'func': job.func.__name__,
        } for job in jobs]
        return jsonify({
            'status': 'success',
            'tasks': tasks
        })
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/scheduler/remove_task/<task_id>', methods=['DELETE'])
def remove_task(task_id):
    """删除指定任务"""
    try:
        scheduler.remove_task(task_id)
        return jsonify({
            'status': 'success',
            'message': f'任务已删除: {task_id}'
        })
    except Exception as e:
        logger.error(f"删除任务失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == "__main__":
    try:
        logger.info("启动调度器服务...")
        # 使用简单的HTTP服务来管理调度器
        app.run(
            host='0.0.0.0',  # 只监听本地
            port=9920,         # 使用不同端口
            threaded=True
        )
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown() 
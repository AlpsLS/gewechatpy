from flask_apscheduler import APScheduler
from datetime import datetime
from logger import logger

class CustomScheduler(APScheduler):
    def add_date_task(self, func, run_date, task_id=None, **kwargs):
        """
        添加一次性定时任务
        
        参数示例：
        scheduler.add_date_task(task_func, "2024-03-15 14:30:00", name="测试任务")
        """
        if isinstance(run_date, str):
            run_date = datetime.strptime(run_date, "%Y-%m-%d %H:%M:%S")
            
        task_id = task_id or func.__name__
        
        self.add_job(
            func=func,
            trigger='date',
            run_date=run_date,
            id=task_id,
            replace_existing=True,
            kwargs=kwargs
        )
        logger.info(f"已注册一次性任务: {task_id} - {run_date}")
        return func
    
    def add_cron_task(self, func, task_id=None, **kwargs):
        """
        添加 Cron 定时任务
        
        参数示例：
        scheduler.add_cron_task(task_func, hour=8, name="测试任务")  # 每天早上8点
        scheduler.add_cron_task(task_func, day_of_week='mon', hour=10)  # 每周一10点
        scheduler.add_cron_task(task_func, hour='9-18', minute='*/30')  # 朝九晚六每半小时
        """
        # 分离 cron 参数和函数参数
        cron_fields = ['year', 'month', 'day', 'week', 'day_of_week', 'hour', 'minute', 'second']
        cron_kwargs = {k: v for k, v in kwargs.items() if k in cron_fields}
        func_kwargs = {k: v for k, v in kwargs.items() if k not in cron_fields}
        
        task_id = task_id or func.__name__
        
        self.add_job(
            func=func,
            trigger='cron',
            id=task_id,
            replace_existing=True,
            kwargs=func_kwargs,
            **cron_kwargs
        )
        logger.info(f"已注册Cron任务: {task_id}")
        return func
    
    def add_interval_task(self, func, task_id=None, **kwargs):
        """
        添加间隔定时任务
        
        参数示例：
        scheduler.add_interval_task(task_func, hours=1, name="测试任务")  # 每隔1小时
        scheduler.add_interval_task(task_func, minutes=30)  # 每隔30分钟
        scheduler.add_interval_task(task_func, seconds=15)  # 每隔15秒
        """
        # 分离间隔参数和函数参数
        interval_fields = ['weeks', 'days', 'hours', 'minutes', 'seconds']
        interval_kwargs = {k: v for k, v in kwargs.items() if k in interval_fields}
        func_kwargs = {k: v for k, v in kwargs.items() if k not in interval_fields}
        
        task_id = task_id or func.__name__
        
        self.add_job(
            func=func,
            trigger='interval',
            id=task_id,
            replace_existing=True,
            kwargs=func_kwargs,
            **interval_kwargs
        )
        logger.info(f"已注册间隔任务: {task_id}")
        return func
    
    def remove_task(self, task_id):
        """移除指定任务"""
        try:
            self.remove_job(task_id)
            logger.info(f"已移除任务: {task_id}")
        except Exception as e:
            logger.error(f"移除任务失败: {task_id} - {str(e)}")

# 创建调度器实例
scheduler = CustomScheduler()

if __name__ == "__main__":
    # 示例任务函数
    def one_time_task(name="default", count=0):
        """一次性任务示例"""
        try:
            logger.info(f"执行一次性任务: name={name}, count={count}")
            # 这里写具体任务代码
        except Exception as e:
            logger.error(f"一次性任务执行失败: {str(e)}")
    
    def morning_task(user="default"):
        """每天定时任务示例"""
        try:
            logger.info(f"执行早上任务: user={user}")
            # 这里写具体任务代码
        except Exception as e:
            logger.error(f"早上任务执行失败: {str(e)}")
    
    # Flask应用示例
    from flask import Flask
    
    app = Flask(__name__)
    
    # 配置 Flask-APScheduler
    class Config:
        SCHEDULER_API_ENABLED = True
        SCHEDULER_TIMEZONE = "Asia/Shanghai"
    
    app.config.from_object(Config())
    
    # 初始化调度器
    scheduler.init_app(app)
    scheduler.start()
    
    try:
        # 注册示例任务
        scheduler.add_date_task(
            one_time_task, 
            "2025-04-05 19:49:55",
            task_id="test_task_1",
            name="测试任务",
            count=1
        )
        
        scheduler.add_cron_task(
            morning_task,
            hour=15,
            minute=20,
            task_id="morning_task_1",
            user="张三"
        )
        
        logger.info("定时任务已启动...")
        
        # 启动 Flask 应用
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
            
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
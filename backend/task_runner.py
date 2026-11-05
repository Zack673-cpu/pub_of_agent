# 队列＋worker 线程＋执行逻辑
import queue
import threading
import logging
from backend.database import SessionLocal
from sqlalchemy.orm import Session
from backend.models import Task,TasksStatusEnum,TasksKindEnum
logger = logging.getLogger(__name__)

q=queue.Queue()


def start_worker() -> None:
    # app startup 时调：创建守护线程跑 _worker_loop
    try:
        session=SessionLocal()
        record=session.query(Task).filter(Task.status==TasksStatusEnum.pending).all()
    except Exception as e:
        raise Exception(f"数据库链接错误：{e}")
    
    try:
        for task in record:
            q.put(task.id)
    except Exception as e:
            raise Exception(f"取pending任务出错:{e}")
    
    try:
        threading.Thread(target=_worker_loop,daemon=True).start()
        #`target=_worker_loop` 是“把函数交给线程去跑” daemon=True是开守护，主程序退出这边跟着退出
        return
    except Exception as e:
        raise Exception(f"启动守护线程出错:{e}")
    finally:
        session.close()
    
def submit_task(task_id: int) -> None:
    # 端点调：task_id 入队
    q.put(task_id)
def _worker_loop() -> None:
    # 线程主体：死循环取 task_id → 调 run_task；异常必须落日志、不许让线程死掉
    while(True):
        try:
            task_id=q.get() #q.get() 是阻塞取号，基本不会炸
            run_task(task_id)
        except Exception as e:
           logger.error(f"任务{task_id}执行出错：{e}",exc_info=True)#`exc_info=True` 是让这条日志 附带完整的异常堆栈 （报错回溯：哪一行炸的、调用链长什么样）
        #`_worker_loop` 的 except： 机制级故障 → 保命记日志
    


def run_task(task_id: int) -> None:
    # 自己开自己关 session（SessionLocal）
    # status 改 running → 按 kind 分发到对应执行函数 → done/failed
    try:
        session=SessionLocal()
        record=session.query(Task).filter(task_id==Task.id).first()
    except Exception as e:
        raise e #这部分异常归worker_loop管，只有在执行第一个sql的时候才会链接

    try:
        if record is None:
            logger.error(f"任务{task_id}未查询到")#这里没有抛异常,也就没有完整报错堆栈了
            return
        record.status=TasksStatusEnum.running
        session.commit()
        if record.kind == TasksKindEnum.outline:
            run_outline(session, record)   # 执行函数，下一任务写
        else:
            logger.warning(f"任务{task_id}的kind={record.kind}暂不支持")
        record.status=TasksStatusEnum.done
        session.commit()
        return
    except Exception as e:
        record.status=TasksStatusEnum.failed
        session.commit()
        logger.error(f"任务{task_id}执行出错：{e}",exc_info=True)
    finally:
        session.close()

    
    
def update_progress(session: Session, task_id: int, payload: dict) -> None:...
    # payload 形状固定：{"step": str, "current": int, "total": int}
    # 大纲单步任务 current=1, total=1；36f 整本时 current=第几节


def run_outline(session: Session, task: Task) -> None:...
    # 大纲任务执行函数：调 36b 的 pipeline 函数干活，边干边 update_progress
import sys
import os
import mysql.connector
from datetime import datetime, timedelta

# --- 配置和路径设置（假设这里的导入路径是正确的） ---

# 确保项目根目录在Python路径中
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 假设这个导入是成功的，并包含数据库配置
# 注意：此处的 DATABASE_CONFIG 变量必须存在于 configs.general_constants 模块中
try:
    from configs.general_constants import DATABASE_CONFIG
except ImportError:
    # 提供一个安全的默认配置，以防导入失败，实际使用时应替换为真实配置
    DATABASE_CONFIG = {
        'host': 'your_host',
        'user': 'your_user',
        'password': 'your_password',
        'database': 'your_db'
    }
    print("⚠️ 警告: 无法导入 configs.general_constants。使用默认配置。")


# --- 数据库连接函数 ---

def connect_to_database():
    """建立数据库连接并返回连接对象"""
    try:
        conn = mysql.connector.connect(**DATABASE_CONFIG)
        return conn
    except Exception as e:
        # 失败时打印错误并重新抛出异常
        print(f"❌ 数据库连接失败: {e}")
        raise


# --- 🎯 修正后的更新函数：处理过去 24 小时内的数据 ---

def update_scores_in_last_24_hours(conn):
    """
    更新 parse_library 表中，创建时间在 '过去 24 小时内' 且 score > 100 的记录，
    将它们的 score 设为 50。

    使用本地系统时间计算，并使用正确的字段名 create_at。
    """
    cursor = conn.cursor()

    # **关键修改：使用 datetime.now() 获取系统本地时间 (Naive Datetime)**
    now_local = datetime.now()
    time_24_hours_ago = now_local - timedelta(hours=24)

    # 转换为 MySQL 接受的格式字符串 (YYYY-MM-DD HH:MM:SS)
    now_local_str = now_local.strftime('%Y-%m-%d %H:%M:%S')
    time_24_hours_ago_str = time_24_hours_ago.strftime('%Y-%m-%d %H:%M:%S')

    # **改进的日志输出，显示当前时间 (本地)**
    print(f"⏰ 当前系统时间 (本地): {now_local_str}")
    print(f"🕒 正在执行更新。查询起始时间点 (本地): {time_24_hours_ago_str}")
    print("----------------------------------------")

    # **关键修正：将 created_at 修正为 create_at**
    # updated_at 设为数据库服务器的当前时间 (NOW())
    query = """
        UPDATE parse_library
        SET score = 50, updated_at = NOW()
        WHERE score > 100
        AND create_at >= %s 
    """

    try:
        # 传入本地时间字符串进行查询
        cursor.execute(query, (time_24_hours_ago_str,))

        affected_rows = cursor.rowcount
        conn.commit()  # 提交事务

        print(f"✅ 成功更新 {affected_rows} 条记录。")
        print(f"条件: create_at >= {time_24_hours_ago_str} (过去 24 小时，基于本地时间) 且 score > 100。")

    except mysql.connector.Error as e:
        # 捕获数据库错误，回滚并打印
        print(f"❌ 数据库更新错误: {e}")
        conn.rollback()
        raise
    except Exception as e:
        # 捕获其他错误，回滚并打印
        print(f"❌ 发生了其他错误: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()


# --- 主执行函数 ---

def execute_score_update():
    """主函数，调用数据库连接和分数更新操作"""
    conn = None
    try:
        conn = connect_to_database()
        update_scores_in_last_24_hours(conn)

    except Exception:
        # 捕获并处理所有异常，确保后续流程不会被中断，并且保证连接关闭
        # 详细错误已经在 update_scores_in_last_24_hours 内部打印
        pass

    finally:
        if conn and conn.is_connected():
            conn.close()
            print("🔗 数据库连接已关闭。")


# --- 调用执行函数 ---

if __name__ == '__main__':
    execute_score_update()
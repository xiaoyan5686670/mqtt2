#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
删除指定设备的传感器数据脚本
用于删除数据库中device_id为1和2的传感器数据
"""

from sqlalchemy import create_engine, and_
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import sys
import os

# 添加项目根目录到路径中
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.models import SensorDataModel
from src.database import SQLALCHEMY_DATABASE_URL


def delete_sensor_data_by_device_ids(device_ids):
    """
    删除指定设备ID的传感器数据
    
    Args:
        device_ids: 设备ID列表，例如 [1, 2]
    """
    # 创建数据库引擎和会话
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    with SessionLocal() as db:
        try:
            # 查询要删除的记录数量
            query = db.query(SensorDataModel).filter(SensorDataModel.device_id.in_(device_ids))
            count = query.count()
            
            if count == 0:
                print(f"没有找到device_id为 {device_ids} 的传感器数据")
                return
            
            print(f"找到 {count} 条device_id为 {device_ids} 的传感器数据，开始删除...")
            
            # 执行删除操作
            deleted_count = query.delete(synchronize_session=False)
            db.commit()
            
            print(f"成功删除 {deleted_count} 条传感器数据，这些数据的device_id在 {device_ids} 中")
            
        except Exception as e:
            db.rollback()
            print(f"删除数据时发生错误: {e}")
            raise
        finally:
            db.close()


def confirm_and_delete():
    """确认并删除数据"""
    device_ids = [1, 2]
    print(f"即将删除device_id为 {device_ids} 的所有传感器数据")
    print("此操作不可撤销！")
    
    response = input("确定要继续吗？(yes/no): ")
    if response.lower() in ['yes', 'y']:
        delete_sensor_data_by_device_ids(device_ids)
        print("数据删除成功")
    else:
        print("操作已取消")


if __name__ == "__main__":
    confirm_and_delete()
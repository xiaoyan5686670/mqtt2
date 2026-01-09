import sqlite3

# 连接到数据库
conn = sqlite3.connect('e:/work1/mqtt2/mqtt_iot.db')
cursor = conn.cursor()

# 查询所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("数据库中存在的表:", tables)

# 检查传感器表是否存在
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sensors';")
sensors_table = cursor.fetchall()
print("传感器表是否存在:", sensors_table)

if sensors_table:
    # 检查传感器表的数据
    cursor.execute("SELECT COUNT(*) FROM sensors;")
    count = cursor.fetchone()[0]
    print("传感器表中的记录数:", count)
    
    if count > 0:
        # 显示一些样本数据
        cursor.execute("SELECT * FROM sensors LIMIT 5;")
        sample_data = cursor.fetchall()
        print("传感器表中的样本数据:", sample_data)

# 关闭连接
conn.close()
# IOT管理系统

基于Python 3.12 + FastAPI + Vue 3 + SQLite的MQTT协议管理系统

## 技术栈

- 后端: FastAPI (Python 3.12)
- 前端: Vue 3 + Bootstrap
- 数据库: SQLite
- 协议: MQTT

## 功能特性

- 用户认证系统
- 设备监控仪表板
- 实时传感器数据更新
- 响应式界面设计
- MQTT服务器配置管理

## 快速开始

1. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

2. 运行应用:
   ```bash
   python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

3. 访问应用:
   - 地址: http://localhost:8000
   - 默认账户: 系统通过前端界面进行操作

## 项目结构

```
mqttv2/
├── src/
│   └── main.py         # FastAPI应用主文件
├── requirements.txt    # 项目依赖
├── static/             # 静态资源目录
├── templates/          # HTML模板
├── models.py           # 数据模型定义
└── README.md
```

## 功能说明

- 设备管理: 添加、编辑、删除和查看设备
- 传感器监控: 实时显示传感器数据
- 自动更新: 每3秒自动刷新传感器数据
- MQTT配置: 管理MQTT服务器连接参数
- 响应式界面: 适配不同屏幕尺寸

## 开发计划

- 集成更多MQTT协议功能
- 添加设备告警功能
- 实现数据存储和历史查询
- 增加更完善的用户管理系统

## 重要说明

项目使用FastAPI作为后端框架，集成了Vue 3前端界面，实现了设备管理和传感器监控功能。系统还包含MQTT服务器配置管理功能，可以配置、测试和激活不同的MQTT服务器连接。
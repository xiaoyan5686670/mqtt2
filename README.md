

基于Python 3.12 + Flask + Vue 3 + SQLite的MQTT协议管理系统

## 技术栈

- 后端: Flask (Python 3.12)
- 前端: Vue 3 + Bootstrap
- 数据库: SQLite
- 协议: MQTT (待实现)

## 功能特性

- 用户认证系统
- 设备监控仪表板
- 实时传感器数据更新
- 响应式界面设计

## 快速开始

1. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

2. 运行应用:
   ```bash
   python server.py
   ```

3. 访问应用:
   - 地址: http://localhost:5000
   - 默认账户: admin/admin123

## 项目结构

```
mqttv2/
├── server.py           # 统一应用入口（推荐使用）
├── requirements.txt    # 项目依赖
├── static/             # 静态资源目录
├── templates/          # HTML模板
│   ├── login.html      # 登录页面
│   ├── dashboard.html  # 传统仪表板
│   └── vue_dashboard.html # Vue 3仪表板
└── README.md
```

## 功能说明

- 登录验证: 用户需要登录才能访问系统功能
- 设备监控: 实时显示设备状态和传感器数据
- 自动更新: 每3秒自动刷新设备数据
- 响应式界面: 适配不同屏幕尺寸

## 开发计划

- 集成MQTT协议支持
- 添加设备管理功能
- 实现数据存储和历史查询
- 增加告警功能

## 重要说明

现在，项目中的`server.py`是整合后的完整应用，包含了所有必要的功能和修复了导入问题。建议只使用这个文件运行应用，其他文件是为了保持项目结构完整性而保留的。

要运行项目，请使用命令：
```bash
python server.py
```

访问 `http://localhost:5000` 即可使用系统。

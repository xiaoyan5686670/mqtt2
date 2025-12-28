# 贡献指南

我们欢迎任何形式的贡献，包括但不限于功能开发、错误修复、文档完善和建议反馈。

## 开发环境设置

1. 克隆仓库
   ```bash
   git clone https://github.com/your-username/mqttv2.git
   cd mqttv2
   ```

2. 创建虚拟环境并安装依赖
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # 或
   venv\Scripts\activate  # Windows
   
   pip install -r requirements.txt
   ```

3. 启动开发服务器
   ```bash
   python -m uvicorn src.main:app --reload --port 8000
   ```

## 代码规范

- 遵循 PEP 8 代码风格
- 使用类型提示（Type Hints）
- 为公共函数和类编写文档字符串（docstring）
- 遵循项目架构规范，保持分层架构清晰

## 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范进行提交信息格式化：

- `feat`: 新功能
- `fix`: 错误修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具变动

示例：
```
feat: 添加设备状态监控功能

- 实现设备在线/离线状态检测
- 添加状态变更通知
- 更新前端UI显示设备状态
```

## 分支管理

- `main`: 主分支，稳定版本
- `develop`: 开发分支，日常开发
- `feature/*`: 功能分支，开发新功能
- `bugfix/*`: 修复分支，修复错误
- `release/*`: 发布分支，准备发布版本

## Pull Request 流程

1. Fork 仓库
2. 从 `develop` 分支创建功能分支
3. 提交修改
4. 更新 README.md 或其他文档（如果需要）
5. 确保测试通过
6. 提交 PR 并描述变更内容

## 问题报告

请提供以下信息以帮助我们快速定位问题：

1. 环境信息（操作系统、Python 版本等）
2. 重现步骤
3. 预期行为
4. 实际行为
5. 相关错误日志

## 联系方式

如有问题，请通过以下方式联系：
- 邮箱：[your-email@example.com](mailto:your-email@example.com)
- GitHub Issues: [https://github.com/your-username/mqttv2/issues](https://github.com/your-username/mqttv2/issues)

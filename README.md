# 联邦学习示例框架

一个完整的联邦学习示例框架，集成了前端用户界面和后端API服务，支持横向和纵向联邦学习的完整流程。

## ✨ 功能特性

### 🎯 核心功能
- **横向联邦学习**: 适用于不同机构拥有相同特征但不同样本的场景
- **纵向联邦学习**: 适用于不同机构拥有相同样本但不同特征的场景
- **智能合作方匹配**: 基于特征相似度或互补性自动匹配合作伙伴
- **实时训练监控**: 可视化训练进度和性能指标
- **模型管理**: 完整的模型库和下载功能

### 🔄 完整流程
1. **数据输入和意愿上传**: 填写数据特征和参与意愿
2. **合作方发现**: 系统自动匹配合适的合作伙伴
3. **联邦训练**: 选择合作方并启动联邦学习训练
4. **进度监控**: 实时查看训练进度和性能指标
5. **模型下载**: 训练完成后下载模型文件

### 🔔 智能通知
- 合作机会通知
- 训练进度更新
- 训练完成提醒

## 🏗️ 系统架构

```
联邦学习示例框架/
├── frontend/                    # React前端应用
│   ├── src/
│   │   ├── pages/              # 页面组件
│   │   │   ├── IntentUpload.tsx    # 意愿上传页面
│   │   │   ├── Training.tsx        # 训练监控页面
│   │   │   ├── Notifications.tsx   # 通知页面
│   │   │   └── ModelLibrary.tsx    # 模型库页面
│   │   ├── services/
│   │   │   └── api.ts          # API服务层
│   │   └── App.tsx             # 主应用组件
│   └── package.json            # 前端依赖
├── federated_learning_tutorial/ # 后端服务
│   ├── api_server.py           # Flask API服务器
│   ├── horizontal_fl/          # 横向联邦学习
│   ├── vertical_fl/            # 纵向联邦学习
│   └── requirements.txt        # 后端依赖
├── start_system.py             # 系统启动脚本
└── README.md                   # 说明文档
```

## 🚀 快速开始

### 前置要求
- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 一键启动

使用系统启动脚本，自动安装依赖并启动前后端服务：

```bash
python start_system.py
```

启动成功后，访问：
- 前端界面: http://localhost:3000
- 后端API: http://localhost:5000
- API健康检查: http://localhost:5000/api/health

### 手动启动

#### 启动后端

```bash
cd federated_learning_tutorial
pip install -r requirements.txt
python api_server.py
```

#### 启动前端

```bash
cd frontend
npm install
npm start
```

## 📖 使用指南

### 1. 上传参与意愿

1. 访问前端界面 http://localhost:3000
2. 选择联邦学习类型（横向或纵向）
3. 填写数据特征信息
4. 设置数据量和可用时间窗口
5. 提交并等待系统匹配合作方

### 2. 选择合作方

1. 系统会自动显示匹配的合作方
2. 查看相似度/互补性评分和数据信息
3. 选择一个或多个合作方
4. 点击"开始训练"启动联邦学习

### 3. 监控训练过程

1. 系统会自动跳转到训练页面
2. 实时查看训练进度和轮次
3. 监控准确率、损失值等性能指标
4. 训练完成后可下载模型

### 4. 查看通知

1. 访问通知页面查看系统消息
2. 合作机会、训练进度等实时更新
3. 点击通知可快速跳转到相关页面

### 5. 管理模型

1. 在模型库页面查看所有训练完成的模型
2. 查看模型详细信息和性能指标
3. 下载模型文件进行部署使用

## 🔧 API文档

### 主要接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/upload-intent` | POST | 上传参与意愿 |
| `/api/collaborations/{user_id}` | GET | 获取合作机会 |
| `/api/start-training` | POST | 开始训练 |
| `/api/training-status/{job_id}` | GET | 获取训练状态 |
| `/api/download-model/{job_id}` | GET | 下载模型 |
| `/api/models` | GET | 获取模型库 |
| `/api/notifications/{user_id}` | GET | 获取通知 |

### 数据格式示例

**上传意愿**:
```json
{
  "federation_type": "horizontal",
  "features": [
    {
      "name": "age",
      "format": "int",
      "range": "18-65"
    }
  ],
  "data_amount": 10000,
  "start_time": "2025-01-10T22:00:00Z",
  "end_time": "2025-01-18T05:00:00Z"
}
```

## 🎯 应用场景

### 横向联邦学习场景
- **医疗**: 多个医院联合训练疾病诊断模型
- **金融**: 多个银行联合训练风控模型
- **教育**: 多个学校联合训练学习行为分析模型

### 纵向联邦学习场景
- **金融风控**: 银行+电商联合用户信用评估
- **精准营销**: 电商+广告平台联合用户画像
- **智慧城市**: 政府+企业联合城市治理模型

## 🔒 隐私保护

- 数据本地化：原始数据不离开本地
- 模型参数交换：只传输模型参数或梯度
- 差分隐私：可选的隐私保护机制
- 同态加密：支持加密计算（扩展功能）

## 🛠️ 技术栈

### 前端
- React 18
- TypeScript
- Material-UI (MUI)
- React Router

### 后端
- Python Flask
- Flask-CORS
- NumPy, Pandas
- scikit-learn

### 联邦学习框架（可扩展）
- FATE (联邦学习框架)
- PySyft
- TensorFlow Federated

## 📝 开发说明

### 扩展新的联邦学习算法

1. 在 `federated_learning_tutorial/` 下创建新的算法目录
2. 实现训练pipeline类
3. 在 `api_server.py` 中添加对应的API接口
4. 更新前端页面支持新算法

### 添加新的性能指标

1. 在后端训练函数中计算新指标
2. 更新API响应格式
3. 在前端页面中显示新指标

### 集成真实联邦学习框架

1. 安装对应的联邦学习框架
2. 替换模拟训练逻辑为真实算法
3. 更新配置和参数设置

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙋‍♂️ 支持

如有问题或建议，请：
1. 查看文档和示例
2. 创建 Issue 描述问题
3. 参与讨论和开发

---

**享受联邦学习的乐趣！🎉** 
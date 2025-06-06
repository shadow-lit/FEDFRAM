# FATE 联邦学习完整教程

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FATE 2.2.0](https://img.shields.io/badge/FATE-2.2.0-green.svg)](https://github.com/FederatedAI/FATE)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

这是一个完整的FATE（Federated AI Technology Enabler）联邦学习教程项目，包含从安装到实践的全套指南和示例代码。

## 🚀 快速开始

### 1. 安装FATE
请先按照 [`INSTALLATION_GUIDE.md`](INSTALLATION_GUIDE.md) 完成FATE的安装和配置。

### 2. 运行快速入门示例
```bash
cd federated_learning_tutorial
python3 quick_start.py
```

### 3. 探索更多示例
- **纵向联邦学习**: `python3 vertical_fl/vertical_lr_pipeline.py`
- **横向联邦学习**: `python3 horizontal_fl/horizontal_nn_pipeline.py`
- **模型使用示例**: `python3 model_usage_example.py`

## 📚 项目概述

### ✅ 项目状态
- **✅ 安装指南**: 完整的FATE + FATE Client安装步骤
- **✅ 纵向联邦学习**: 银行+电商风控场景，已测试成功
- **✅ 横向联邦学习**: 多医院诊断场景，已测试成功  
- **✅ 模型管理**: 模型使用和管理示例
- **✅ 工具脚本**: 数据上传和结果查看工具

### 🎯 适用人群
- **🎓 学术研究者**: 联邦学习算法研究、隐私保护机器学习
- **💼 企业开发者**: 业务场景POC验证、联邦学习技术选型
- **📚 学生和初学者**: 联邦学习入门学习、课程作业和项目

## 🏗️ 项目结构

```
federated_learning_tutorial/
├── README.md                           # 项目主文档（本文件）
├── INSTALLATION_GUIDE.md               # 详细安装指南
├── LICENSE                             # 开源许可证
├── quick_start.py                      # 快速入门示例
├── model_usage_example.py              # 模型使用示例
├── upload_with_correct_identity.py     # 数据上传工具
├── show_results.py                     # 结果查看工具
├── check_project.py                    # 项目完整性检查
├── vertical_fl/                        # 纵向联邦学习示例
│   └── vertical_lr_pipeline.py
├── horizontal_fl/                      # 横向联邦学习示例
│   └── horizontal_nn_pipeline.py
├── upload_configs/                     # 数据上传配置
│   ├── guest_hetero.json              # 纵向学习guest配置
│   ├── host_hetero.json               # 纵向学习host配置
│   ├── guest_homo.json                # 横向学习guest配置
│   └── host_homo.json                 # 横向学习host配置
└── results/                           # 训练结果存储目录
```

## 💡 核心概念

### 联邦学习类型

| 类型 | 数据分布 | 应用场景 | 示例 |
|------|----------|----------|------|
| **纵向联邦** | 相同用户，不同特征 | 跨行业合作 | 银行+电商风控 |
| **横向联邦** | 不同用户，相同特征 | 同行业合作 | 多医院诊断 |

### 实践示例

#### 🔗 纵向联邦学习 (Vertical FL)
- **场景**: 银行+电商联合风控
- **算法**: 逻辑回归 + PSI样本对齐
- **文件**: [`vertical_fl/vertical_lr_pipeline.py`](vertical_fl/vertical_lr_pipeline.py)
- **特点**: 不同机构拥有同一批用户的不同特征

#### ↔️ 横向联邦学习 (Horizontal FL)
- **场景**: 多医院联合疾病诊断
- **算法**: 神经网络 + 联邦平均
- **文件**: [`horizontal_fl/horizontal_nn_pipeline.py`](horizontal_fl/horizontal_nn_pipeline.py)
- **特点**: 不同机构拥有相似特征的不同用户

#### 🎯 模型管理与使用
- **功能**: 模型部署、预测、性能分析
- **文件**: [`model_usage_example.py`](model_usage_example.py)
- **包含**: 模型导出、在线预测、批量预测

### 工具脚本
- **[数据上传工具](upload_with_correct_identity.py)** - 正确配置数据上传身份
- **[结果查看工具](show_results.py)** - 查看和分析训练结果
- **[项目检查工具](check_project.py)** - 验证项目完整性

## 🖥️ 单机模拟说明

### 什么是Standalone模式？

FATE的standalone模式是在单机上模拟多方联邦学习的环境，这是学习和测试联邦学习的理想方式。

### 核心特点

1. **🖥️ 单机运行**: 所有参与方（Guest、Host、Arbiter）都在同一台机器上运行
2. **🔒 完整隐私保护**: 虽然是模拟，但包含完整的加密和隐私保护协议
3. **📚 学习目的**: 专门用于学习、测试和原型开发
4. **🚀 真实算法**: 使用与生产环境相同的联邦学习算法

### 模拟原理

```
┌─────────────────────────────────────────────────────────────┐
│                    单机环境 (Standalone)                      │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Guest方       │    Host方       │      Arbiter方          │
│   (party_id:    │   (party_id:    │    (party_id:           │
│    9999/10000)  │    10000)       │     10000)              │
├─────────────────┼─────────────────┼─────────────────────────┤
│ • 拥有标签      │ • 拥有特征      │ • 协调计算              │
│ • 部分特征      │ • 无标签        │ • 聚合参数              │
│ • 发起训练      │ • 参与训练      │ • 安全计算              │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### 数据隔离

即使在同一台机器上，FATE也确保：
- **逻辑隔离**: 不同参与方的数据在逻辑上完全分离
- **加密通信**: 参与方之间的通信都经过加密
- **隐私保护**: 原始数据永远不会直接共享

### 与真实部署的区别

| 方面 | Standalone模式 | 真实多方部署 |
|------|----------------|--------------|
| **物理环境** | 单机 | 多机/多地 |
| **网络通信** | 本地通信 | 跨网络通信 |
| **数据隔离** | 逻辑隔离 | 物理+逻辑隔离 |
| **算法协议** | 完全相同 | 完全相同 |
| **隐私保护** | 完全相同 | 完全相同 |
| **学习价值** | 高 | 高 |

## 🎯 学习路径

### 初学者路径 (1-2天)
1. 📖 阅读本README了解概念
2. 🔧 按照[安装指南](INSTALLATION_GUIDE.md)安装FATE
3. 🚀 运行[快速入门示例](quick_start.py)
4. 📊 查看训练结果和模型性能

### 进阶路径 (3-5天)
1. 🔗 学习[纵向联邦学习](vertical_fl/vertical_lr_pipeline.py)
2. ↔️ 学习[横向联邦学习](horizontal_fl/horizontal_nn_pipeline.py)
3. 🎯 掌握[模型管理和使用](model_usage_example.py)
4. 🛠️ 自定义数据和算法参数

### 专家路径 (1-2周)
1. 🔧 修改算法参数和网络结构
2. 📈 实现自定义评估指标
3. 🌐 部署到真实的多方环境
4. 🔒 深入理解隐私保护机制

## 🔧 自定义配置

### 修改数据路径
编辑上传配置文件 `upload_configs/*.json`:
```json
{
    "file": "path/to/your/data.csv",
    "head": 1,
    "partition": 10,
    "work_mode": 0,
    "table_name": "your_table_name",
    "namespace": "your_namespace"
}
```

### 调整算法参数
在Pipeline脚本中修改组件参数:
```python
lr_param = {
    "penalty": "L2",
    "optimizer": "sgd",
    "tol": 1e-05,
    "alpha": 0.01,
    "max_iter": 20,
    "early_stop": "diff",
    "batch_size": 320,
    "learning_rate": 0.15
}
```

## 📊 性能监控

### 使用FATEBoard
1. 访问 `http://localhost:8080`
2. 登录 (admin/admin)
3. 查看任务状态和训练指标

### 命令行查看
```bash
# 查看任务状态
flow job query -j <job_id>

# 查看组件输出
flow component output-data -j <job_id> -p <party_id> -r <role> -cpn <component_name>
```

## 🐛 常见问题

### Q: 任务失败怎么办？
A: 检查日志文件，通常在 `logs/` 目录下，或使用 `flow job query` 查看详细错误信息。

### Q: 如何使用自己的数据？
A: 参考 `upload_with_correct_identity.py`，准备CSV格式数据并正确配置上传参数。

### Q: 单机模拟和真实部署有什么区别？
A: 单机模拟在逻辑上完全分离数据，保持隐私保护协议，但物理上在同一台机器。真实部署需要网络配置和多机协调。

### Q: 如何选择纵向还是横向联邦学习？
A: 根据数据分布特点：相同用户不同特征选纵向，不同用户相同特征选横向。

### Q: FATE Client安装失败怎么办？
A: 参考安装指南中的故障排除部分，通常需要正确设置环境变量和Python路径。

## 📦 项目分享

### GitHub分享（推荐）
```bash
# 创建GitHub仓库后
git init
git add .
git commit -m "Initial commit: FATE federated learning tutorial"
git branch -M main
git remote add origin https://github.com/yourusername/fate-federated-learning-tutorial.git
git push -u origin main
```

### 压缩包分享
```bash
cd ..
tar -czf fate_federated_learning_tutorial.tar.gz federated_learning_tutorial/
```

### 分享建议
- 仓库描述: "Complete FATE federated learning tutorial with installation guide and examples"
- 标签: `federated-learning`, `fate`, `machine-learning`, `privacy-preserving`, `tutorial`

## 🔧 技术栈

- **框架**: FATE 2.2.0
- **语言**: Python 3.8+
- **算法**: 逻辑回归、神经网络、PSI
- **部署**: Standalone单机模式
- **可视化**: FATEBoard Web界面

## 🌟 项目亮点

1. **完整性**: 从安装到实践的完整流程
2. **实用性**: 真实业务场景的示例
3. **易用性**: 详细的文档和注释
4. **可扩展性**: 易于修改和扩展
5. **教育性**: 适合学习和教学

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 📄 许可证

本项目采用Apache 2.0许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [FATE团队](https://github.com/FederatedAI/FATE) 提供优秀的联邦学习框架
- 联邦学习社区的贡献和支持

## 📞 联系方式

- **问题反馈**: 请在GitHub Issues中提出
- **讨论交流**: 欢迎在GitHub Discussions中参与讨论
- **官方文档**: https://fate.readthedocs.io/

---

⭐ 如果这个项目对你有帮助，请给个Star支持一下！ 
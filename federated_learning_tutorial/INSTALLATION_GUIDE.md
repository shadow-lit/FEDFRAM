# FATE 联邦学习框架安装指南

本指南将帮助你从零开始安装和配置FATE（Federated AI Technology Enabler）联邦学习框架。

## 系统要求

### 基本要求
- **操作系统**: Linux (推荐 Ubuntu 18.04+, CentOS 7+) 或 macOS
- **Python**: 3.8+ (推荐 3.8.10)
- **内存**: 至少 8GB RAM
- **存储**: 至少 20GB 可用空间
- **网络**: 稳定的互联网连接

### 可选要求
- **Docker**: 用于容器化部署 (可选但推荐)
- **Java**: JDK 8+ (某些组件需要)

## 安装步骤

### 步骤 1: 环境准备

#### 1.1 检查Python版本
```bash
python3 --version
# 应该显示 Python 3.8.x 或更高版本
```

如果Python版本不符合要求，请先安装Python 3.8+：

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.8 python3.8-pip python3.8-venv
```

**CentOS/RHEL:**
```bash
sudo yum install python38 python38-pip
```

#### 1.2 安装必要的系统依赖
**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y wget curl git build-essential
```

**CentOS/RHEL:**
```bash
sudo yum install -y wget curl git gcc gcc-c++ make
```

### 步骤 2: 下载FATE Standalone

#### 2.1 创建工作目录
```bash
mkdir -p ~/fate_workspace
cd ~/fate_workspace
```

#### 2.2 下载FATE安装包
```bash
# 下载FATE 2.2.0 standalone版本
wget https://webank-ai-1251170195.cos.ap-guangzhou.myqcloud.com/fate/2.2.0/release/standalone_fate_install_2.2.0_release.tar.gz

# 如果wget下载失败，可以尝试curl
# curl -O https://webank-ai-1251170195.cos.ap-guangzhou.myqcloud.com/fate/2.2.0/release/standalone_fate_install_2.2.0_release.tar.gz
```

#### 2.3 解压安装包
```bash
tar -xzf standalone_fate_install_2.2.0_release.tar.gz
cd standalone_fate_install_2.2.0_release
```

### 步骤 3: 安装FATE

#### 3.1 运行安装脚本
```bash
# 初始化FATE环境
bash bin/init.sh init

# 等待安装完成，这可能需要几分钟时间
```

安装过程中会自动：
- 安装Python依赖包
- 配置FATE环境
- 初始化数据库
- 设置默认配置

#### 3.2 启动FATE服务
```bash
# 启动所有FATE服务
bash bin/init.sh start
```

### 步骤 4: 安装FATE Client

**重要**: FATE 2.2.0需要单独安装FATE Client才能使用Python API进行编程。

#### 4.1 设置FATE环境变量
```bash
# 进入FATE安装目录
cd ~/fate_workspace/standalone_fate_install_2.2.0_release

# 设置环境变量
source bin/init_env.sh
```

#### 4.2 安装FATE Client
```bash
# 方法1: 使用pip安装（推荐）
pip install fate-client

# 方法2: 如果方法1失败，尝试指定版本
pip install fate-client==2.2.0

# 方法3: 如果仍然失败，使用FATE内置的Python环境
cd ~/fate_workspace/standalone_fate_install_2.2.0_release
./python/miniconda3/bin/pip install fate-client
```

#### 4.3 验证FATE Client安装
```bash
# 测试FATE Client是否正确安装
python3 -c "
try:
    from fate_client.pipeline import FateFlowPipeline
    print('✅ FATE Client安装成功！')
except ImportError as e:
    print('❌ FATE Client安装失败:', e)
"
```

### 步骤 5: 验证安装

#### 5.1 检查服务状态
```bash
# 检查服务是否正常运行
bash bin/init.sh status
```

你应该看到类似以下的输出：
```
FATE service status:
- FATEBoard: running
- FATEFlow: running
- MySQL: running
```

#### 5.2 运行测试任务
```bash
# 运行官方测试任务
flow test toy -gid 10000 -hid 10000
```

如果看到类似以下输出，说明安装成功：
```
toy test job finished successfully
```

#### 5.3 测试Python API
```bash
# 创建简单的测试脚本
cat > test_fate_client.py << 'EOF'
#!/usr/bin/env python3
"""测试FATE Client是否正常工作"""

try:
    from fate_client.pipeline import FateFlowPipeline
    from fate_client.pipeline.components.fate import Reader
    
    print("✅ 成功导入FATE Client组件")
    
    # 创建简单的pipeline测试
    pipeline = FateFlowPipeline()
    print("✅ 成功创建FateFlowPipeline")
    
    print("🎉 FATE Client安装验证通过！")
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请检查FATE Client是否正确安装")
except Exception as e:
    print(f"⚠️  其他错误: {e}")
    
EOF

# 运行测试
python3 test_fate_client.py
```

### 步骤 6: 访问FATE Board (可选)

FATE Board是FATE的Web界面，可以用来监控和管理联邦学习任务。

1. 打开浏览器
2. 访问: `http://localhost:8080`
3. 默认用户名/密码: `admin/admin`

## 常见问题解决

### 问题 1: FATE Client安装失败

**错误**: `pip install fate-client` 失败
**解决方案**:
```bash
# 方案1: 升级pip并重试
python3 -m pip install --upgrade pip
pip install fate-client

# 方案2: 使用FATE内置Python环境
cd ~/fate_workspace/standalone_fate_install_2.2.0_release
./python/miniconda3/bin/pip install fate-client

# 方案3: 手动设置Python路径
export PYTHONPATH=$PYTHONPATH:~/fate_workspace/standalone_fate_install_2.2.0_release/python
```

### 问题 2: 导入FATE Client模块失败

**错误**: `ImportError: No module named 'fate_client'`
**解决方案**:
```bash
# 确保设置了正确的环境变量
cd ~/fate_workspace/standalone_fate_install_2.2.0_release
source bin/init_env.sh

# 检查Python路径
python3 -c "import sys; print('\n'.join(sys.path))"

# 重新安装FATE Client
pip uninstall fate-client -y
pip install fate-client
```

### 问题 3: 权限错误
如果遇到权限问题，确保你有足够的权限：
```bash
# 如果需要，给脚本添加执行权限
chmod +x bin/init.sh

# 或者使用sudo运行（不推荐，除非必要）
sudo bash bin/init.sh init
```

### 问题 4: 端口冲突
如果端口被占用，可以修改配置：
```bash
# 查看端口占用情况
netstat -tlnp | grep :8080
netstat -tlnp | grep :9380

# 如果需要，可以修改配置文件中的端口设置
```

### 问题 5: Python依赖问题
如果遇到Python包依赖问题：
```bash
# 升级pip
python3 -m pip install --upgrade pip

# 手动安装可能缺失的包
pip3 install numpy pandas scikit-learn

# 如果使用FATE内置Python环境
cd ~/fate_workspace/standalone_fate_install_2.2.0_release
./python/miniconda3/bin/pip install numpy pandas scikit-learn
```

### 问题 6: 内存不足
如果系统内存不足：
- 关闭其他不必要的程序
- 考虑增加虚拟内存（swap）
- 或者使用更高配置的机器

## 环境变量设置

为了方便使用FATE命令，建议设置环境变量：

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
echo 'export FATE_HOME=~/fate_workspace/standalone_fate_install_2.2.0_release' >> ~/.bashrc
echo 'export PATH=$FATE_HOME/bin:$PATH' >> ~/.bashrc

# 添加FATE Client相关环境变量
echo 'source $FATE_HOME/bin/init_env.sh' >> ~/.bashrc

# 重新加载配置
source ~/.bashrc
```

## 验证完整安装

运行以下命令确保所有组件都正常工作：

```bash
# 1. 检查FATE服务状态
bash bin/init.sh status

# 2. 测试Flow命令
flow --help

# 3. 测试Python API
python3 -c "from fate_client.pipeline import FateFlowPipeline; print('FATE Client OK')"

# 4. 运行官方测试
flow test toy -gid 10000 -hid 10000
```

## 卸载FATE

如果需要卸载FATE：

```bash
cd ~/fate_workspace/standalone_fate_install_2.2.0_release

# 停止所有服务
bash bin/init.sh stop

# 卸载FATE Client
pip uninstall fate-client -y

# 删除安装目录
cd ..
rm -rf standalone_fate_install_2.2.0_release
rm -f standalone_fate_install_2.2.0_release.tar.gz
```

## 下一步

安装完成后，你可以：

1. 查看 `README.md` 了解项目概述
2. 运行 `quick_start.py` 体验快速入门示例
3. 学习 `standalone_simulation_explanation.md` 了解单机模拟原理
4. 尝试纵向联邦学习示例 (`vertical_fl/`)
5. 尝试横向联邦学习示例 (`horizontal_fl/`)

## 获取帮助

- **官方文档**: https://fate.readthedocs.io/
- **GitHub仓库**: https://github.com/FederatedAI/FATE
- **社区论坛**: https://github.com/FederatedAI/FATE/discussions

如果遇到问题，请先查看官方文档和GitHub Issues，或在社区论坛寻求帮助。 
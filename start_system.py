#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
联邦学习系统启动脚本
同时启动前端和后端服务
"""

import os
import subprocess
import sys
import time
import signal
import threading
from pathlib import Path

def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║              联邦学习示例框架启动器                           ║
    ║                                                              ║
    ║  🚀 启动前端和后端服务                                        ║
    ║  🔗 前端: http://localhost:3000                               ║
    ║  🔗 后端: http://localhost:5000                               ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_dependencies():
    """检查依赖"""
    print("🔍 检查系统依赖...")
    
    # 检查Python3
    try:
        python_cmd = 'python3' if subprocess.run(['which', 'python3'], capture_output=True).returncode == 0 else 'python'
        python_version = subprocess.check_output([python_cmd, '--version'], text=True)
        print(f"✅ Python: {python_version.strip()}")
    except Exception as e:
        print(f"❌ Python检查失败: {e}")
        return False, None
    
    # 检查Node.js
    try:
        node_version = subprocess.check_output(['node', '--version'], text=True)
        print(f"✅ Node.js: {node_version.strip()}")
    except Exception as e:
        print(f"❌ Node.js未安装或不在PATH中: {e}")
        return False, None
    
    # 检查npm
    try:
        npm_version = subprocess.check_output(['npm', '--version'], text=True)
        print(f"✅ NPM: {npm_version.strip()}")
    except Exception as e:
        print(f"❌ NPM未安装: {e}")
        return False, None
    
    return True, python_cmd

def install_backend_dependencies(python_cmd):
    """安装后端依赖"""
    print("📦 安装后端依赖...")
    
    backend_dir = Path("federated_learning_tutorial")
    requirements_file = backend_dir / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"❌ requirements.txt文件不存在: {requirements_file}")
        return False
    
    try:
        subprocess.run([
            python_cmd, '-m', 'pip', 'install', '-r', str(requirements_file)
        ], check=True, cwd=backend_dir)
        print("✅ 后端依赖安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 后端依赖安装失败: {e}")
        return False

def install_frontend_dependencies():
    """安装前端依赖"""
    print("📦 安装前端依赖...")
    
    frontend_dir = Path("frontend")
    package_json = frontend_dir / "package.json"
    
    if not package_json.exists():
        print(f"❌ package.json文件不存在: {package_json}")
        return False
    
    try:
        subprocess.run(['npm', 'install'], check=True, cwd=frontend_dir)
        print("✅ 前端依赖安装成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 前端依赖安装失败: {e}")
        return False

def start_backend(python_cmd):
    """启动后端服务"""
    print("🔧 启动后端API服务...")
    
    backend_dir = Path("federated_learning_tutorial")
    api_file = backend_dir / "api_server.py"
    
    if not api_file.exists():
        print(f"❌ API服务文件不存在: {api_file}")
        return None
    
    try:
        process = subprocess.Popen([
            python_cmd, str(api_file)
        ], cwd=backend_dir)
        print("✅ 后端服务启动成功 (PID: {})".format(process.pid))
        return process
    except Exception as e:
        print(f"❌ 后端服务启动失败: {e}")
        return None

def start_frontend():
    """启动前端服务"""
    print("🌐 启动前端React应用...")
    
    frontend_dir = Path("frontend")
    
    try:
        process = subprocess.Popen([
            'npm', 'start'
        ], cwd=frontend_dir)
        print("✅ 前端服务启动成功 (PID: {})".format(process.pid))
        return process
    except Exception as e:
        print(f"❌ 前端服务启动失败: {e}")
        return None

def wait_for_services():
    """等待服务启动"""
    print("⏳ 等待服务启动...")
    time.sleep(5)
    
    # 检查后端服务
    try:
        import requests
        response = requests.get('http://localhost:5000/api/health', timeout=10)
        if response.status_code == 200:
            print("✅ 后端服务运行正常")
        else:
            print("⚠️ 后端服务响应异常")
    except Exception as e:
        print(f"⚠️ 后端服务检查失败: {e}")
    
    print("🎉 系统启动完成！")
    print("🔗 前端地址: http://localhost:3000")
    print("🔗 后端地址: http://localhost:5000")
    print("📋 API健康检查: http://localhost:5000/api/health")

def cleanup_handler(signum, frame):
    """清理处理器"""
    print("\n🛑 收到停止信号，正在关闭服务...")
    sys.exit(0)

def main():
    """主函数"""
    print_banner()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, cleanup_handler)
    signal.signal(signal.SIGTERM, cleanup_handler)
    
    # 检查依赖
    deps_ok, python_cmd = check_dependencies()
    if not deps_ok:
        print("❌ 依赖检查失败，请安装必要的依赖")
        sys.exit(1)
    
    # 安装依赖
    print("\n📦 安装依赖...")
    if not install_backend_dependencies(python_cmd):
        print("❌ 后端依赖安装失败")
        sys.exit(1)
    
    if not install_frontend_dependencies():
        print("❌ 前端依赖安装失败")
        sys.exit(1)
    
    # 启动服务
    print("\n🚀 启动服务...")
    backend_process = start_backend(python_cmd)
    if not backend_process:
        sys.exit(1)
    
    # 等待后端启动
    time.sleep(5)
    
    frontend_process = start_frontend()
    if not frontend_process:
        backend_process.terminate()
        sys.exit(1)
    
    # 等待服务启动完成
    wait_for_services()
    
    try:
        # 主循环，保持程序运行
        while True:
            time.sleep(1)
            
            # 检查进程是否还在运行
            if backend_process.poll() is not None:
                print("❌ 后端进程意外终止")
                break
            
            if frontend_process.poll() is not None:
                print("❌ 前端进程意外终止")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 用户中断，正在停止服务...")
    
    finally:
        # 清理进程
        print("🧹 清理服务进程...")
        try:
            backend_process.terminate()
            frontend_process.terminate()
            
            # 等待进程结束
            backend_process.wait(timeout=5)
            frontend_process.wait(timeout=5)
            
        except subprocess.TimeoutExpired:
            print("⚠️ 强制终止进程...")
            backend_process.kill()
            frontend_process.kill()
        except Exception as e:
            print(f"⚠️ 清理过程中出现错误: {e}")
        
        print("✅ 服务已停止")

if __name__ == '__main__':
    main() 
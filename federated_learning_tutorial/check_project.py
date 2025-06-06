#!/usr/bin/env python3
"""
FATE联邦学习教程项目完整性检查脚本
检查项目是否准备好分享
"""

import os
import sys
from pathlib import Path

def check_file_exists(file_path, description):
    """检查文件是否存在"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path} (缺失)")
        return False

def check_directory_exists(dir_path, description):
    """检查目录是否存在"""
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        print(f"✅ {description}: {dir_path}")
        return True
    else:
        print(f"❌ {description}: {dir_path} (缺失)")
        return False

def check_python_syntax(file_path):
    """检查Python文件语法"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            compile(f.read(), file_path, 'exec')
        return True
    except SyntaxError as e:
        print(f"❌ 语法错误 {file_path}: {e}")
        return False
    except Exception as e:
        print(f"⚠️  检查 {file_path} 时出错: {e}")
        return True  # 不因为其他错误而失败

def check_fate_client():
    """检查FATE Client是否安装"""
    try:
        from fate_client.pipeline import FateFlowPipeline
        print("✅ FATE Client已安装并可正常导入")
        return True
    except ImportError:
        print("⚠️  FATE Client未安装或无法导入")
        print("   提示: 这是正常的，用户需要按照安装指南安装FATE Client")
        return True  # 不算作错误，因为这是用户需要安装的
    except Exception as e:
        print(f"⚠️  检查FATE Client时出错: {e}")
        return True

def main():
    """主检查函数"""
    print("🔍 FATE联邦学习教程项目完整性检查")
    print("=" * 50)
    
    all_good = True
    
    # 检查核心文档
    print("\n📚 核心文档检查:")
    core_docs = [
        ("README.md", "项目主文档（已整合所有内容）"),
        ("INSTALLATION_GUIDE.md", "安装指南"),
        ("LICENSE", "开源许可证")
    ]
    
    for file_path, desc in core_docs:
        if not check_file_exists(file_path, desc):
            all_good = False
    
    # 检查示例代码
    print("\n🐍 示例代码检查:")
    example_files = [
        ("quick_start.py", "快速入门示例"),
        ("model_usage_example.py", "模型使用示例"),
        ("upload_with_correct_identity.py", "数据上传工具"),
        ("show_results.py", "结果查看工具"),
        ("vertical_fl/vertical_lr_pipeline.py", "纵向联邦学习示例"),
        ("horizontal_fl/horizontal_nn_pipeline.py", "横向联邦学习示例")
    ]
    
    for file_path, desc in example_files:
        if check_file_exists(file_path, desc):
            if not check_python_syntax(file_path):
                all_good = False
        else:
            all_good = False
    
    # 检查目录结构
    print("\n📁 目录结构检查:")
    directories = [
        ("vertical_fl", "纵向联邦学习目录"),
        ("horizontal_fl", "横向联邦学习目录"),
        ("upload_configs", "上传配置目录")
    ]
    
    for dir_path, desc in directories:
        if not check_directory_exists(dir_path, desc):
            all_good = False
    
    # 检查配置文件
    print("\n⚙️  配置文件检查:")
    config_files = [
        ("upload_configs/guest_hetero.json", "纵向Guest配置"),
        ("upload_configs/host_hetero.json", "纵向Host配置"),
        ("upload_configs/guest_homo.json", "横向Guest配置"),
        ("upload_configs/host_homo.json", "横向Host配置")
    ]
    
    for file_path, desc in config_files:
        if not check_file_exists(file_path, desc):
            all_good = False
    
    # 检查文件大小（确保不是空文件）
    print("\n📏 文件大小检查:")
    important_files = [
        "README.md",
        "INSTALLATION_GUIDE.md", 
        "quick_start.py",
        "vertical_fl/vertical_lr_pipeline.py",
        "horizontal_fl/horizontal_nn_pipeline.py"
    ]
    
    for file_path in important_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            if size > 1000:  # 至少1KB
                print(f"✅ {file_path}: {size} bytes")
            else:
                print(f"⚠️  {file_path}: {size} bytes (可能太小)")
                all_good = False
    
    # 检查FATE Client（可选）
    print("\n🔧 FATE Client检查:")
    check_fate_client()
    
    # 总结
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 项目检查通过！准备好分享了！")
        print("\n📋 下一步:")
        print("1. 初始化Git仓库")
        print("2. 创建GitHub私密仓库")
        print("3. 推送代码到GitHub")
        print("\n💡 提醒:")
        print("- 用户需要按照 INSTALLATION_GUIDE.md 安装FATE和FATE Client")
        print("- README.md 已整合所有文档内容")
        return 0
    else:
        print("❌ 项目检查发现问题，请修复后再分享")
        print("\n🔧 建议:")
        print("1. 检查缺失的文件和目录")
        print("2. 修复Python语法错误")
        print("3. 确保重要文件内容完整")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 
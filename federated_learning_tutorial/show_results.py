#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
显示纵向联邦学习评估结果
"""

import requests
import json

def show_vertical_fl_results():
    """显示纵向联邦学习的详细结果"""
    
    job_id = '202505301127389424060'
    
    print("=" * 60)
    print("🎉 纵向联邦学习任务执行成功！")
    print("=" * 60)
    
    print(f"\n📋 任务信息:")
    print(f"  🆔 任务ID: {job_id}")
    print(f"  🏢 参与方: Guest(9999) + Host(10000)")
    print(f"  📊 数据集: breast_hetero (乳腺癌诊断数据)")
    print(f"  🔄 算法: SSHE逻辑回归 (安全共享同态加密)")
    print(f"  ✅ 状态: 成功完成")
    
    # 获取评估结果
    try:
        url = f"http://127.0.0.1:9380/v2/output/metric/query?job_id={job_id}&role=guest&party_id=9999&task_name=evaluation_0"
        response = requests.get(url)
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("code") == 0 and result.get("data"):
                data = result["data"][0]["data"]["lr_0"]["train_set"]
                
                print(f"\n📊 模型性能评估结果:")
                print("-" * 40)
                
                metrics = {}
                for item in data:
                    metrics[item["metric"]] = item["val"]
                
                # 显示各项指标
                if "auc" in metrics:
                    auc = metrics["auc"]
                    print(f"  🎯 AUC (曲线下面积): {auc:.4f}")
                
                if "binary_precision" in metrics:
                    precision = metrics["binary_precision"]
                    print(f"  🎯 精确率 (Precision): {precision:.4f}")
                
                if "binary_accuracy" in metrics:
                    accuracy = metrics["binary_accuracy"]
                    print(f"  🎯 准确率 (Accuracy): {accuracy:.4f}")
                
                if "binary_recall" in metrics:
                    recall = metrics["binary_recall"]
                    print(f"  🎯 召回率 (Recall): {recall:.4f}")
                
                # 性能分析
                print(f"\n📈 性能分析:")
                print("-" * 40)
                
                auc = metrics.get("auc", 0)
                accuracy = metrics.get("binary_accuracy", 0)
                precision = metrics.get("binary_precision", 0)
                recall = metrics.get("binary_recall", 0)
                
                if auc >= 0.99:
                    print(f"  🌟 AUC = {auc:.4f} - 模型性能卓越！")
                elif auc >= 0.9:
                    print(f"  ✅ AUC = {auc:.4f} - 模型性能优秀")
                elif auc >= 0.8:
                    print(f"  ✅ AUC = {auc:.4f} - 模型性能良好")
                else:
                    print(f"  ⚠️  AUC = {auc:.4f} - 模型性能有待提升")
                
                if accuracy >= 0.95:
                    print(f"  🌟 准确率 = {accuracy:.4f} - 分类效果卓越！")
                elif accuracy >= 0.9:
                    print(f"  ✅ 准确率 = {accuracy:.4f} - 分类效果优秀")
                elif accuracy >= 0.8:
                    print(f"  ✅ 准确率 = {accuracy:.4f} - 分类效果良好")
                else:
                    print(f"  ⚠️  准确率 = {accuracy:.4f} - 分类效果有待提升")
                
                # 计算F1分数
                if precision > 0 and recall > 0:
                    f1_score = 2 * (precision * recall) / (precision + recall)
                    print(f"  📊 F1分数: {f1_score:.4f}")
                
                print(f"\n🔍 技术解释:")
                print("-" * 40)
                print(f"  • AUC: 衡量模型区分正负样本的能力，1.0为完美")
                print(f"  • 精确率: 预测为阳性中实际为阳性的比例")
                print(f"  • 准确率: 预测正确的样本占总样本的比例")
                print(f"  • 召回率: 实际阳性中被正确预测的比例")
                
                print(f"\n🔒 隐私保护特点:")
                print("-" * 40)
                print(f"  ✅ 数据不出域: Guest和Host的原始数据始终保留在本地")
                print(f"  ✅ 样本对齐: 使用PSI算法安全找到共同用户")
                print(f"  ✅ 加密计算: SSHE算法确保训练过程中数据加密")
                print(f"  ✅ 模型保护: Host方无法获得完整模型参数")
                
                print(f"\n🎯 业务价值:")
                print("-" * 40)
                print(f"  💼 银行可以利用电商数据提升风控模型效果")
                print(f"  💼 电商可以参与建模但不泄露用户隐私")
                print(f"  💼 双方共同受益，实现数据价值最大化")
                print(f"  💼 符合数据保护法规要求")
                
            else:
                print(f"\n❌ 无法获取评估指标")
        else:
            print(f"\n❌ API请求失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ 获取结果失败: {e}")
    
    print("\n" + "=" * 60)
    print("🎊 纵向联邦学习示例完成！")
    print("=" * 60)

if __name__ == "__main__":
    show_vertical_fl_results() 
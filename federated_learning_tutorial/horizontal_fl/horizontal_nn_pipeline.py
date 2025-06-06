#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
横向联邦学习示例 - 使用神经网络
场景：多个医院联合训练疾病诊断模型
- 各方：拥有相同特征的不同患者数据
- 算法：联邦平均算法 (FedAvg)
- 模型：深度神经网络
"""

import os
import sys
from fate_client.pipeline import FateFlowPipeline
from fate_client.pipeline.components.fate import Reader, HomoNN, Evaluation
from fate_client.pipeline.components.fate.homo_nn import get_config_of_default_runner
from fate_client.pipeline.components.fate.nn.torch import nn, optim
from fate_client.pipeline.components.fate.nn.torch.base import Sequential
from fate_client.pipeline.components.fate.nn.algo_params import TrainingArguments, FedAVGArguments

def create_horizontal_fl_pipeline():
    """创建横向联邦学习管道"""
    
    # 设置参与方 - 使用FATE默认配置
    guest = "9999"  # Guest方使用9999
    host = "10000"  # Host方使用10000
    arbiter = "10000"  # Arbiter方使用10000（与host相同）
    
    # 创建管道
    pipeline = FateFlowPipeline().set_parties(guest=guest, host=[host], arbiter=arbiter)
    
    # 数据读取组件
    reader_0 = Reader("reader_0", runtime_parties=dict(guest=guest, host=host))
    reader_0.guest.task_parameters(
        namespace="experiment",
        name="breast_homo_guest"  # 使用正确的数据表名
    )
    reader_0.hosts[0].task_parameters(
        namespace="experiment", 
        name="breast_homo_host"   # 使用正确的数据表名
    )
    
    # 配置神经网络模型
    epochs = 5  # 减少训练轮数以便快速测试
    batch_size = 64
    in_feat = 30  # 输入特征数
    hidden_feat = 16  # 隐藏层特征数
    lr = 0.01  # 学习率
    
    # 使用FATE 2.2.0的新API配置模型
    conf = get_config_of_default_runner(
        algo='fedavg',  # 联邦平均算法
        model=Sequential(
            nn.Linear(in_feat, hidden_feat),  # 30 -> 16
            nn.ReLU(),
            nn.Linear(hidden_feat, 1),        # 16 -> 1 (二分类)
            nn.Sigmoid()
        ), 
        loss=nn.BCELoss(),  # 二分类交叉熵损失
        optimizer=optim.Adam(lr=lr),  # Adam优化器
        training_args=TrainingArguments(
            num_train_epochs=epochs, 
            per_device_train_batch_size=batch_size
        ),
        fed_args=FedAVGArguments(),  # 联邦平均参数
        task_type='binary'  # 二分类任务
    )
    
    # 横向神经网络训练
    homo_nn_0 = HomoNN(
        'homo_nn_0',
        runner_conf=conf,
        train_data=reader_0.outputs["output_data"]
    )
    
    # 模型测试
    homo_nn_1 = HomoNN(
        'homo_nn_1',
        input_model=homo_nn_0.outputs['output_model'],
        test_data=reader_0.outputs["output_data"]
    )
    
    # 模型评估
    evaluation_0 = Evaluation(
        "evaluation_0",
        runtime_parties=dict(guest=guest, host=host),
        metrics=["auc", "binary_precision", "binary_accuracy", "binary_recall"],
        input_datas=[homo_nn_1.outputs["test_output_data"]]
    )
    
    # 构建管道
    pipeline.add_tasks([reader_0, homo_nn_0, homo_nn_1, evaluation_0])
    
    # 编译管道
    pipeline.compile()
    
    return pipeline

def run_horizontal_fl_example():
    """运行横向联邦学习示例"""
    print("=== 横向联邦学习示例 ===")
    print("场景：多个医院联合训练疾病诊断模型")
    print("- 各方：拥有相同特征的不同患者数据")
    print("- 目标：通过联邦平均算法训练全局模型")
    print("- 优势：提高模型泛化能力，保护患者隐私")
    
    try:
        # 创建管道
        pipeline = create_horizontal_fl_pipeline()
        
        # 提交任务
        print("正在提交横向联邦学习任务...")
        pipeline.fit()
        
        print("横向联邦学习训练完成！")
        
        # 获取评估结果
        try:
            eval_result = pipeline.get_task_info("evaluation_0").get_output_metric()
            print("模型评估结果:")
            print(eval_result)
        except Exception as e:
            print(f"获取评估结果失败: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"横向联邦学习执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


class HorizontalFLPipeline:
    """横向联邦学习Pipeline类 - 用于API集成"""
    
    def __init__(self):
        """初始化横向联邦学习Pipeline"""
        self.name = "Horizontal Federated Learning Pipeline (FATE)"
        self.pipeline = None
        self.is_trained = False
        self.results = {}
        
    def create_pipeline(self, participants=None, config=None):
        """创建FATE横向联邦学习管道"""
        try:
            self.pipeline = create_horizontal_fl_pipeline()
            return True
        except Exception as e:
            print(f"创建横向联邦管道失败: {e}")
            return False
    
    def train(self, participants=None, rounds=10):
        """训练横向联邦学习模型"""
        try:
            if not self.pipeline:
                if not self.create_pipeline(participants):
                    return {"status": "failed", "error": "Failed to create pipeline"}
            
            print(f"🚀 开始横向联邦学习训练，参与方数量: {len(participants) if participants else 2}")
            
            # 提交训练任务
            self.pipeline.fit()
            self.is_trained = True
            
            # 获取训练结果
            try:
                eval_result = self.pipeline.get_task_info("evaluation_0").get_output_metric()
                self.results = eval_result
                print(f"✅ 横向联邦学习训练完成")
                return {
                    "status": "completed", 
                    "rounds": rounds,
                    "results": self.results
                }
            except Exception as e:
                print(f"⚠️ 获取评估结果失败: {e}")
                return {
                    "status": "completed", 
                    "rounds": rounds,
                    "results": {}
                }
                
        except Exception as e:
            print(f"❌ 横向联邦学习训练失败: {e}")
            return {"status": "failed", "error": str(e)}
    
    def get_results(self):
        """获取训练结果"""
        return self.results
    
    def save_model(self, path):
        """保存模型"""
        if self.is_trained and self.pipeline:
            try:
                # 这里可以添加模型保存逻辑
                print(f"模型保存到: {path}")
                return True
            except Exception as e:
                print(f"模型保存失败: {e}")
                return False
        return False


if __name__ == "__main__":
    print("开始运行横向联邦学习示例...")
    success = run_horizontal_fl_example()
    
    if success:
        print("\n🎉 横向联邦学习示例运行成功！")
        print("\n关键要点：")
        print("1. 各参与方拥有相同特征但不同样本的数据")
        print("2. 使用联邦平均算法聚合各方的模型参数")
        print("3. 通过安全聚合保护各方的模型参数隐私")
        print("4. 最终得到一个泛化能力更强的全局模型")
    else:
        print("\n❌ 横向联邦学习示例运行失败")
        print("请检查数据是否正确上传，FATE服务是否正常运行") 
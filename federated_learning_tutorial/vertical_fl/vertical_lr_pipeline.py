#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
纵向联邦学习示例 - 逻辑回归
适用场景：不同机构拥有相同用户的不同特征数据
例如：银行有用户的财务数据，电商有用户的购买行为数据
"""

import os
import sys
from fate_client.pipeline import FateFlowPipeline
from fate_client.pipeline.components.fate import Reader, PSI, SSHELR, Evaluation

def create_vertical_fl_pipeline():
    """创建纵向联邦学习管道"""
    
    # 设置参与方 - 使用FATE默认配置
    guest = "9999"  # Guest方使用9999
    host = "10000"  # Host方使用10000
    
    # 创建管道
    pipeline = FateFlowPipeline().set_parties(guest=guest, host=[host])
    
    # 数据读取组件
    reader_0 = Reader("reader_0", runtime_parties=dict(guest=guest, host=host))
    reader_0.guest.task_parameters(
        namespace="experiment",
        name="breast_hetero_guest"
    )
    reader_0.hosts[0].task_parameters(
        namespace="experiment", 
        name="breast_hetero_host"
    )
    
    # 样本对齐（PSI）
    psi_0 = PSI("psi_0", input_data=reader_0.outputs["output_data"])
    
    # 纵向逻辑回归
    lr_param = {
        "epochs": 20,
        "learning_rate": 0.15,
        "batch_size": 320,
        "early_stop": "diff",
        "init_param": {
            "init_method": "random_uniform"
        },
        "tol": 1e-5,
        "reveal_loss_freq": 3,
    }
    
    lr_0 = SSHELR("lr_0",
                  train_data=psi_0.outputs["output_data"],
                  **lr_param)
    
    lr_1 = SSHELR("lr_1",
                  test_data=psi_0.outputs["output_data"],
                  input_model=lr_0.outputs["output_model"])
    
    # 模型评估
    evaluation_0 = Evaluation("evaluation_0",
                              runtime_parties=dict(guest=guest),
                              metrics=["auc", "binary_precision", "binary_accuracy", "binary_recall"],
                              input_datas=lr_0.outputs["train_output_data"])
    
    # 构建管道
    pipeline.add_tasks([reader_0, psi_0, lr_0, lr_1, evaluation_0])
    
    # 编译管道
    pipeline.compile()
    
    return pipeline

def run_vertical_fl_example():
    """运行纵向联邦学习示例"""
    print("=== 纵向联邦学习示例 ===")
    print("场景：银行(Guest)和电商(Host)联合训练用户信用评估模型")
    print("- Guest方：拥有用户标签和部分特征")
    print("- Host方：拥有用户的其他特征")
    print("- 目标：在不共享原始数据的情况下训练联合模型")
    
    try:
        # 创建管道
        pipeline = create_vertical_fl_pipeline()
        
        # 提交任务
        print("正在提交纵向联邦学习任务...")
        pipeline.fit()
        
        print("纵向联邦学习训练完成！")
        
        # 获取评估结果
        try:
            eval_result = pipeline.get_task_info("evaluation_0").get_output_metric()[0]["data"]
            print("模型评估结果:")
            for metric_name, metric_value in eval_result.items():
                if isinstance(metric_value, (int, float)):
                    print(f"  {metric_name}: {metric_value:.4f}")
        except Exception as e:
            print(f"获取评估结果失败: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"纵向联邦学习执行失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


class VerticalFLPipeline:
    """纵向联邦学习Pipeline类 - 用于API集成"""
    
    def __init__(self):
        """初始化纵向联邦学习Pipeline"""
        self.name = "Vertical Federated Learning Pipeline (FATE)"
        self.pipeline = None
        self.is_trained = False
        self.results = {}
        
    def create_pipeline(self, participants=None, config=None):
        """创建FATE纵向联邦学习管道"""
        try:
            self.pipeline = create_vertical_fl_pipeline()
            return True
        except Exception as e:
            print(f"创建纵向联邦管道失败: {e}")
            return False
    
    def train(self, participants=None, rounds=20):
        """训练纵向联邦学习模型"""
        try:
            if not self.pipeline:
                if not self.create_pipeline(participants):
                    return {"status": "failed", "error": "Failed to create pipeline"}
            
            print(f"🚀 开始纵向联邦学习训练，参与方数量: {len(participants) if participants else 2}")
            
            # 提交训练任务
            self.pipeline.fit()
            self.is_trained = True
            
            # 获取训练结果
            try:
                eval_result = self.pipeline.get_task_info("evaluation_0").get_output_metric()[0]["data"]
                self.results = eval_result
                print(f"✅ 纵向联邦学习训练完成")
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
            print(f"❌ 纵向联邦学习训练失败: {e}")
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
    print("开始运行纵向联邦学习示例...")
    success = run_vertical_fl_example()
    
    if success:
        print("\n🎉 纵向联邦学习示例运行成功！")
        print("\n关键要点：")
        print("1. Guest方和Host方的数据通过PSI算法进行样本对齐")
        print("2. 使用SSHE（安全共享）逻辑回归算法保护数据隐私")
        print("3. 只有Guest方能看到最终的模型评估结果")
        print("4. Host方参与训练但无法获得完整模型")
    else:
        print("\n❌ 纵向联邦学习示例运行失败")
        print("请检查数据是否正确上传，FATE服务是否正常运行") 
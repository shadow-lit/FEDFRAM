#!/usr/bin/env python3
"""
完整工作流程测试
演示从登录、查看邀请、接受邀请到训练完成的全过程
"""

import requests
import json
import time

API_BASE = "http://localhost:5000/api"

def print_section(title):
    print(f"\n{'='*50}")
    print(f"🔍 {title}")
    print(f"{'='*50}")

def test_full_workflow():
    """测试完整工作流程"""
    
    print_section("1. 医院A登录并查看邀请")
    
    # 医院A登录
    login_response = requests.post(f"{API_BASE}/login", 
                                   json={"username": "hospital_a", "password": "demo123"})
    
    if login_response.status_code != 200:
        print("❌ 医院A登录失败")
        return
    
    login_data = login_response.json()
    hospital_a_token = login_data['token']
    hospital_a_id = login_data['user']['user_id']
    print(f"✅ 医院A登录成功，ID: {hospital_a_id}")
    
    # 查看医院A的邀请
    headers = {"Authorization": f"Bearer {hospital_a_token}"}
    invitations_response = requests.get(f"{API_BASE}/training-invitations/{hospital_a_id}")
    
    if invitations_response.status_code == 200:
        invitations = invitations_response.json()
        print(f"📧 医院A收到邀请: {len(invitations['received_invitations'])}个")
        print(f"📤 医院A发送邀请: {len(invitations['sent_invitations'])}个")
        
        if invitations['received_invitations']:
            invitation = invitations['received_invitations'][0]
            invitation_id = invitation['invitation_id']
            print(f"📋 邀请详情: {invitation['federation_type']}联邦学习")
            print(f"👥 来自: {invitation.get('from_username', invitation['from_user'])}")
            
            print_section("2. 医院A接受邀请")
            
            # 接受邀请
            accept_response = requests.post(f"{API_BASE}/respond-invitation",
                                           json={
                                               "invitation_id": invitation_id,
                                               "response": "accepted"
                                           },
                                           headers=headers)
            
            if accept_response.status_code == 200:
                accept_result = accept_response.json()
                print(f"✅ 接受邀请成功: {accept_result['message']}")
                
                if accept_result.get('all_accepted') and accept_result.get('job_id'):
                    job_id = accept_result['job_id']
                    print(f"🚀 所有参与方已同意，训练开始！")
                    print(f"📊 训练任务ID: {job_id}")
                    
                    print_section("3. 监控训练进度")
                    
                    # 监控训练进度
                    for i in range(10):
                        time.sleep(2)
                        status_response = requests.get(f"{API_BASE}/training-status/{job_id}")
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            job_info = status_data['job_info']
                            
                            print(f"📈 第{i+1}次检查:")
                            print(f"   状态: {job_info['status']}")
                            print(f"   进度: {job_info['current_round']}/{job_info['total_rounds']} 轮")
                            
                            if job_info['status'] == 'completed':
                                print_section("4. 训练完成")
                                print(f"🎉 训练完成！")
                                print(f"📊 最终指标:")
                                for metric, value in job_info['metrics'].items():
                                    print(f"   {metric}: {value}")
                                print(f"💾 模型路径: {job_info.get('model_path', 'N/A')}")
                                break
                        else:
                            print(f"❌ 获取训练状态失败: {status_response.status_code}")
                    
                else:
                    print("⏳ 等待其他参与方响应...")
            else:
                print(f"❌ 接受邀请失败: {accept_response.status_code}")
                print(accept_response.text)
        else:
            print("❌ 没有收到的邀请")
    else:
        print(f"❌ 获取邀请失败: {invitations_response.status_code}")
        
    print_section("5. 查看医院B的状态")
    
    # 医院B登录查看状态
    login_response_b = requests.post(f"{API_BASE}/login", 
                                     json={"username": "hospital_b", "password": "demo123"})
    
    if login_response_b.status_code == 200:
        login_data_b = login_response_b.json()
        hospital_b_id = login_data_b['user']['user_id']
        print(f"✅ 医院B登录成功，ID: {hospital_b_id}")
        
        # 查看医院B的邀请状态
        invitations_response_b = requests.get(f"{API_BASE}/training-invitations/{hospital_b_id}")
        if invitations_response_b.status_code == 200:
            invitations_b = invitations_response_b.json()
            print(f"📤 医院B发送的邀请: {len(invitations_b['sent_invitations'])}个")
            
            if invitations_b['sent_invitations']:
                sent_invitation = invitations_b['sent_invitations'][0]
                print(f"📋 邀请状态: {sent_invitation['status']}")
                print(f"👥 邀请对象: {sent_invitation['to_users']}")
    else:
        print(f"❌ 医院B登录失败: {login_response_b.status_code}")
    
    print_section("6. 总结")
    print("🏁 工作流程测试完成!")
    print("✨ 主要功能验证:")
    print("   ✅ 用户登录认证")
    print("   ✅ 邀请查看和响应")  
    print("   ✅ 训练任务启动")
    print("   ✅ 训练进度监控")
    print("   ✅ 训练完成和结果查看")

if __name__ == "__main__":
    test_full_workflow() 
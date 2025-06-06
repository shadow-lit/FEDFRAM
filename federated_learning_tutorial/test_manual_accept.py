#!/usr/bin/env python3
"""
手动测试邀请接受逻辑
"""

import requests
import json

API_BASE = "http://localhost:5000/api"

def test_manual_accept():
    """手动测试邀请接受"""
    
    print("🧪 手动测试邀请接受...")
    
    # 1. 登录医院A获取token
    print("\n1. 登录医院A...")
    login_response = requests.post(f"{API_BASE}/login", 
                                   json={"username": "hospital_a", "password": "demo123"})
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.text}")
        return
    
    login_data = login_response.json()
    token = login_data['token']
    user_id = login_data['user']['user_id']
    print(f"✅ 登录成功，用户ID: {user_id}")
    
    # 2. 获取邀请详情
    print("\n2. 获取邀请详情...")
    invitations_response = requests.get(f"{API_BASE}/debug-invitations")
    
    if invitations_response.status_code != 200:
        print("❌ 获取邀请失败")
        return
    
    invitations_data = invitations_response.json()
    if not invitations_data.get('invitations'):
        print("❌ 没有邀请")
        return
    
    invitation = invitations_data['invitations'][0]
    invitation_id = invitation['invitation_id']
    
    print(f"   邀请ID: {invitation_id}")
    print(f"   发送方: {invitation['from_user']}")
    print(f"   接收方: {invitation['to_users']}")
    print(f"   响应记录: {invitation['responses']}")
    print(f"   状态: {invitation['status']}")
    
    # 3. 分析逻辑
    to_users = invitation['to_users']
    responses = invitation['responses']
    
    print(f"\n3. 分析逻辑:")
    print(f"   被邀请用户数: {len(to_users)}")
    print(f"   已响应用户数: {len(responses)}")
    print(f"   是否所有人都响应: {len(responses) == len(to_users)}")
    
    if len(responses) == len(to_users):
        all_accepted = all(resp == 'accepted' for resp in responses.values())
        print(f"   是否所有人都接受: {all_accepted}")
        
        if all_accepted:
            print("   ✅ 理论上应该开始训练了！")
        else:
            print("   ❌ 有人拒绝了邀请")
    else:
        print("   ⏳ 还在等待其他人响应")
    
    # 4. 尝试再次接受邀请（可能触发训练开始逻辑）
    print("\n4. 尝试再次接受邀请...")
    
    headers = {'Authorization': f'Bearer {token}'}
    accept_response = requests.post(f"{API_BASE}/respond-invitation",
                                   json={
                                       "invitation_id": invitation_id,
                                       "response": "accepted"
                                   },
                                   headers=headers)
    
    print(f"   响应状态码: {accept_response.status_code}")
    if accept_response.status_code == 200:
        result = accept_response.json()
        print(f"   响应结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get('all_accepted'):
            print("   🎉 训练已开始！")
            print(f"   任务ID: {result.get('job_id')}")
        else:
            print("   ⏳ 仍在等待...")
            
    else:
        print(f"   ❌ 请求失败: {accept_response.text}")
    
    # 5. 再次检查邀请状态
    print("\n5. 检查更新后的邀请状态...")
    invitations_response = requests.get(f"{API_BASE}/debug-invitations")
    
    if invitations_response.status_code == 200:
        invitations_data = invitations_response.json()
        if invitations_data.get('invitations'):
            invitation = invitations_data['invitations'][0]
            print(f"   新状态: {invitation['status']}")
            print(f"   响应记录: {invitation['responses']}")
        else:
            print("   没有找到邀请")

if __name__ == "__main__":
    test_manual_accept() 
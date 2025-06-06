#!/usr/bin/env python3
"""
测试接受邀请功能
"""

import requests
import json
import time

API_BASE = "http://localhost:5000/api"

def test_accept_invitation():
    """测试接受邀请功能"""
    
    print("🧪 测试接受邀请功能...")
    
    # 1. 登录医院A
    print("\n1. 登录医院A...")
    login_response = requests.post(f"{API_BASE}/login", 
                                   json={"username": "hospital_a", "password": "demo123"})
    
    if login_response.status_code != 200:
        print("❌ 医院A登录失败")
        return
    
    login_data = login_response.json()
    hospital_a_token = login_data['token']
    hospital_a_id = login_data['user']['user_id']
    print(f"✅ 医院A登录成功，ID: {hospital_a_id}")
    
    # 2. 获取医院A的邀请
    print("\n2. 获取医院A的邀请...")
    invitations_response = requests.get(f"{API_BASE}/training-invitations/{hospital_a_id}")
    
    if invitations_response.status_code != 200:
        print("❌ 获取邀请失败")
        return
    
    invitations_data = invitations_response.json()
    if not invitations_data.get('received_invitations'):
        print("❌ 没有收到的邀请")
        return
    
    invitation = invitations_data['received_invitations'][0]
    invitation_id = invitation['invitation_id']
    print(f"✅ 找到邀请ID: {invitation_id}")
    print(f"   状态: {invitation['status']}")
    print(f"   已有响应: {invitation.get('user_response', 'None')}")
    
    # 3. 接受邀请（如果还没有接受）
    if not invitation.get('user_response'):
        print("\n3. 接受邀请...")
        
        headers = {'Authorization': f'Bearer {hospital_a_token}'}
        accept_response = requests.post(f"{API_BASE}/respond-invitation",
                                       json={
                                           "invitation_id": invitation_id,
                                           "response": "accepted"
                                       },
                                       headers=headers)
        
        print(f"   响应状态码: {accept_response.status_code}")
        if accept_response.status_code == 200:
            result = accept_response.json()
            print(f"   响应结果: {result}")
            
            if result.get('all_accepted'):
                print("🎉 所有参与方都已同意，训练已开始！")
                print(f"   任务ID: {result.get('job_id')}")
            else:
                print("⏳ 等待其他参与方响应...")
                
        else:
            print(f"❌ 接受邀请失败: {accept_response.text}")
    else:
        print(f"\n3. 邀请已被响应: {invitation['user_response']}")
    
    # 4. 再次检查邀请状态
    print("\n4. 检查更新后的邀请状态...")
    time.sleep(1)
    invitations_response = requests.get(f"{API_BASE}/training-invitations/{hospital_a_id}")
    
    if invitations_response.status_code == 200:
        invitations_data = invitations_response.json()
        if invitations_data.get('received_invitations'):
            invitation = invitations_data['received_invitations'][0]
            print(f"   邀请状态: {invitation['status']}")
            print(f"   用户响应: {invitation.get('user_response', 'None')}")
            print(f"   响应详情: {invitation.get('responses', {})}")
        else:
            print("   没有找到邀请")
    else:
        print("   获取邀请状态失败")

if __name__ == "__main__":
    test_accept_invitation() 
#!/usr/bin/env python3
"""
测试邀请显示功能
"""

import requests
import json

API_BASE = "http://localhost:5000/api"

def test_invitation_display():
    """测试邀请显示功能"""
    
    print("🧪 测试邀请显示功能...")
    
    # 首先登录获取用户信息
    print("\n1. 登录用户 hospital_a...")
    login_response = requests.post(f"{API_BASE}/login", 
                                   json={"username": "hospital_a", "password": "demo123"})
    
    if login_response.status_code == 200:
        login_data = login_response.json()
        hospital_a_id = login_data['user']['user_id']
        print(f"✅ 医院A登录成功，ID: {hospital_a_id}")
    else:
        print("❌ 医院A登录失败")
        return
    
    print("\n2. 登录用户 hospital_b...")
    login_response = requests.post(f"{API_BASE}/login", 
                                   json={"username": "hospital_b", "password": "demo123"})
    
    if login_response.status_code == 200:
        login_data = login_response.json()
        hospital_b_id = login_data['user']['user_id']
        print(f"✅ 医院B登录成功，ID: {hospital_b_id}")
    else:
        print("❌ 医院B登录失败")
        return
    
    # 测试获取医院A的邀请（应该有1个被邀请）
    print(f"\n3. 查询医院A的邀请...")
    invitations_response = requests.get(f"{API_BASE}/training-invitations/{hospital_a_id}")
    
    if invitations_response.status_code == 200:
        invitations_data = invitations_response.json()
        print(f"✅ 成功获取医院A的邀请数据")
        print(f"   收到的邀请数量: {len(invitations_data.get('received_invitations', []))}")
        print(f"   发送的邀请数量: {len(invitations_data.get('sent_invitations', []))}")
        
        # 检查收到的邀请详情
        if invitations_data.get('received_invitations'):
            invitation = invitations_data['received_invitations'][0]
            print(f"\n   收到的邀请详情:")
            print(f"   - 邀请ID: {invitation.get('invitation_id')}")
            print(f"   - 发送者ID: {invitation.get('from_user')}")
            print(f"   - 发送者用户名: {invitation.get('from_username', 'NOT_PROVIDED')}")
            print(f"   - 联邦类型: {invitation.get('federation_type')}")
            print(f"   - 状态: {invitation.get('status')}")
            print(f"   - 用户响应: {invitation.get('user_response', 'None')}")
        else:
            print("   ❌ 没有收到的邀请！")
    else:
        print(f"❌ 获取医院A邀请失败: {invitations_response.status_code}")
        print(f"   错误信息: {invitations_response.text}")
    
    # 测试获取医院B的邀请（应该有1个发送的）
    print(f"\n4. 查询医院B的邀请...")
    invitations_response = requests.get(f"{API_BASE}/training-invitations/{hospital_b_id}")
    
    if invitations_response.status_code == 200:
        invitations_data = invitations_response.json()
        print(f"✅ 成功获取医院B的邀请数据")
        print(f"   收到的邀请数量: {len(invitations_data.get('received_invitations', []))}")
        print(f"   发送的邀请数量: {len(invitations_data.get('sent_invitations', []))}")
        
        # 检查发送的邀请详情
        if invitations_data.get('sent_invitations'):
            invitation = invitations_data['sent_invitations'][0]
            print(f"\n   发送的邀请详情:")
            print(f"   - 邀请ID: {invitation.get('invitation_id')}")
            print(f"   - 发送者ID: {invitation.get('from_user')}")
            print(f"   - 发送者用户名: {invitation.get('from_username', 'NOT_PROVIDED')}")
            print(f"   - 联邦类型: {invitation.get('federation_type')}")
            print(f"   - 状态: {invitation.get('status')}")
            print(f"   - 已接受数量: {invitation.get('accepted_count', 0)}")
            print(f"   - 已拒绝数量: {invitation.get('rejected_count', 0)}")
            print(f"   - 待响应数量: {invitation.get('pending_count', 0)}")
        else:
            print("   ❌ 没有发送的邀请！")
    else:
        print(f"❌ 获取医院B邀请失败: {invitations_response.status_code}")
        print(f"   错误信息: {invitations_response.text}")

if __name__ == "__main__":
    test_invitation_display() 
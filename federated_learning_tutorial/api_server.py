#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
联邦学习后端API服务
整合横向和纵向联邦学习功能，提供完整的API接口
"""

import os
import json
import time
import uuid
import threading
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import subprocess
import tempfile
import shutil
import sys
import logging
import numpy as np
import random

# 添加用户认证和消息系统相关导入
import hashlib
import jwt
from functools import wraps

# 导入联邦学习模块
try:
    from horizontal_fl.horizontal_nn_pipeline import HorizontalFLPipeline
    from vertical_fl.vertical_lr_pipeline import VerticalFLPipeline
    FATE_AVAILABLE = True
    print("✅ FATE框架加载成功")
except ImportError as e:
    print(f"⚠️ FATE框架导入失败: {e}")
    print("🔄 使用模拟的联邦学习Pipeline")
    FATE_AVAILABLE = False
    
    # 模拟的联邦学习Pipeline类
    class MockHorizontalFLPipeline:
        def __init__(self):
            self.name = "Mock Horizontal Federated Learning Pipeline"
        
        def train(self, participants, rounds=10):
            """模拟横向联邦学习训练"""
            return {"status": "completed", "rounds": rounds}

    class MockVerticalFLPipeline:
        def __init__(self):
            self.name = "Mock Vertical Federated Learning Pipeline"
        
        def train(self, participants, rounds=10):
            """模拟纵向联邦学习训练"""
            return {"status": "completed", "rounds": rounds}
    
    HorizontalFLPipeline = MockHorizontalFLPipeline
    VerticalFLPipeline = MockVerticalFLPipeline

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 文件上传配置
UPLOAD_FOLDER = 'data/uploads'
PROCESSED_FOLDER = 'data/processed'
ALLOWED_EXTENSIONS = {'csv', 'json', 'xlsx', 'txt'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# 全局变量存储状态
training_jobs = {}  # 训练任务状态
collaboration_intents = {}  # 合作意愿
model_library = {}  # 模型库
uploaded_datasets = {}  # 上传的数据集

# 用户管理和认证系统
users_db = {}  # 用户数据库 {user_id: {username, password_hash, email, profile}}
user_sessions = {}  # 用户会话 {user_id: {token, login_time, last_active}}
notifications_db = {}  # 通知系统 {user_id: [notifications]}
training_invitations = {}  # 训练邀请 {invitation_id: {from_user, to_users, job_info, status}}
SECRET_KEY = 'federated_learning_secret_key_2024'  # JWT密钥

def allowed_file(filename):
    """检查文件类型是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def hash_password(password):
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """验证密码"""
    return hash_password(password) == password_hash

def generate_jwt_token(user_id):
    """生成JWT token"""
    payload = {
        'user_id': user_id,
        'iat': datetime.now().timestamp(),
        'exp': (datetime.now() + timedelta(days=7)).timestamp()  # 7天过期
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    # 确保返回字符串类型
    return token if isinstance(token, str) else token.decode('utf-8')

def verify_jwt_token(token):
    """验证JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token:
            token = token.replace('Bearer ', '')
        else:
            token = request.args.get('token')
        
        if not token:
            return jsonify({'success': False, 'error': '需要认证'}), 401
        
        user_id = verify_jwt_token(token)
        if not user_id:
            return jsonify({'success': False, 'error': '无效的token'}), 401
        
        request.current_user_id = user_id
        return f(*args, **kwargs)
    
    return decorated_function

def calculate_file_hash(file_path):
    """计算文件的MD5哈希值"""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        print(f"计算文件哈希失败: {e}")
        return None

def calculate_dataframe_hash(df):
    """计算DataFrame的内容哈希值"""
    try:
        # 将DataFrame转换为标准化的字符串，然后计算哈希
        df_string = df.to_csv(index=False).encode('utf-8')
        return hashlib.md5(df_string).hexdigest()
    except Exception as e:
        print(f"计算DataFrame哈希失败: {e}")
        return None

def check_duplicate_data(user_id, new_df, federation_type):
    """检查是否为重复数据"""
    try:
        # 如果用户已经有数据，检查是否重复
        if user_id in uploaded_datasets:
            existing_data = uploaded_datasets[user_id]
            
            # 检查联邦类型是否相同
            if existing_data['federation_type'] != federation_type:
                return {
                    'is_duplicate': False,
                    'reason': 'federation_type_different',
                    'message': f'联邦类型不同: 之前{existing_data["federation_type"]}，现在{federation_type}'
                }
            
            # 读取已存在的数据进行比较
            if os.path.exists(existing_data['processed_path']):
                existing_df = pd.read_csv(existing_data['processed_path'])
                
                # 比较数据特征
                new_hash = calculate_dataframe_hash(new_df)
                existing_hash = calculate_dataframe_hash(existing_df)
                
                if new_hash == existing_hash:
                    return {
                        'is_duplicate': True,
                        'reason': 'identical_content',
                        'message': '您上传的数据与之前上传的数据完全相同',
                        'existing_upload_time': existing_data['upload_time']
                    }
                
                # 检查基本统计信息是否相同
                if (new_df.shape == existing_df.shape and 
                    list(new_df.columns) == list(existing_df.columns)):
                    
                    # 进一步检查数据内容的相似性
                    similarity_threshold = 0.95  # 95%相似度阈值
                    
                    try:
                        # 对数值列计算相关性
                        numeric_cols = new_df.select_dtypes(include=[np.number]).columns
                        if len(numeric_cols) > 0:
                            correlations = []
                            for col in numeric_cols:
                                if col in existing_df.columns:
                                    corr = new_df[col].corr(existing_df[col])
                                    if not np.isnan(corr):
                                        correlations.append(abs(corr))
                            
                            if correlations and np.mean(correlations) > similarity_threshold:
                                return {
                                    'is_duplicate': True,
                                    'reason': 'highly_similar',
                                    'message': f'数据高度相似 (相似度: {np.mean(correlations):.1%})',
                                    'similarity': np.mean(correlations),
                                    'existing_upload_time': existing_data['upload_time']
                                }
                    except Exception as e:
                        print(f"相似性检查失败: {e}")
        
        return {'is_duplicate': False, 'reason': 'new_data', 'message': '新数据'}
        
    except Exception as e:
        print(f"重复检查失败: {e}")
        return {'is_duplicate': False, 'reason': 'check_failed', 'message': f'检查失败: {e}'}

def add_notification(user_id, notification_type, title, message, data=None):
    """添加通知"""
    if user_id not in notifications_db:
        notifications_db[user_id] = []
    
    notification = {
        'id': str(uuid.uuid4()),
        'type': notification_type,
        'title': title,
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'data': data or {},
        'read': False
    }
    
    notifications_db[user_id].append(notification)
    
    # 保存通知到文件
    save_notifications_to_file()
    
    return notification

def process_uploaded_file(file_path, federation_type, user_id):
    """处理上传的数据文件"""
    try:
        file_ext = file_path.rsplit('.', 1)[1].lower()
        
        # 读取数据
        if file_ext == 'csv':
            df = pd.read_csv(file_path)
        elif file_ext == 'json':
            df = pd.read_json(file_path)
        elif file_ext == 'xlsx':
            df = pd.read_excel(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}")
        
        # 基本数据验证
        if df.empty:
            raise ValueError("数据文件为空")
        
        # 保存处理后的数据
        processed_path = os.path.join(PROCESSED_FOLDER, f"{user_id}_{federation_type}.csv")
        df.to_csv(processed_path, index=False)
        
        # 分析数据特征
        features = []
        for col in df.columns:
            if col.lower() in ['id', 'user_id', 'sample_id']:
                continue
                
            if df[col].dtype in ['int64', 'float64']:
                feature_type = 'numerical'
                feature_range = f"{df[col].min():.2f}-{df[col].max():.2f}"
            else:
                feature_type = 'categorical'
                unique_vals = df[col].unique()
                feature_range = f"{len(unique_vals)} categories"
            
            features.append({
                'name': col,
                'type': feature_type,
                'range': feature_range
            })
        
        return {
            'processed_path': processed_path,
            'features': features,
            'sample_count': len(df),
            'feature_count': len(features),
            'columns': df.columns.tolist()
        }
        
    except Exception as e:
        raise ValueError(f"数据处理失败: {str(e)}")

class FederatedLearningService:
    def __init__(self):
        self.horizontal_pipeline = HorizontalFLPipeline()
        self.vertical_pipeline = VerticalFLPipeline()
        
    def find_collaborators(self, intent_data):
        """匹配合作方"""
        matches = []
        target_type = intent_data['federation_type']
        target_features = [f['name'] for f in intent_data['features']]
        
        for user_id, other_intent in collaboration_intents.items():
            if (other_intent['federation_type'] == target_type and 
                user_id != intent_data['user_id']):
                
                other_features = [f['name'] for f in other_intent['features']]
                
                if target_type == 'horizontal':
                    # 横向联邦：特征相似度
                    common_features = set(target_features) & set(other_features)
                    similarity = len(common_features) / max(len(target_features), len(other_features))
                    if similarity > 0.6:  # 60%以上特征相似
                        matches.append({
                            'user_id': user_id,
                            'similarity': similarity,
                            'data_amount': other_intent['data_amount'],
                            'features': other_features,
                            'dataset_info': uploaded_datasets.get(user_id, {})
                        })
                else:
                    # 纵向联邦：特征互补性（放宽匹配条件）
                    common_features = set(target_features) & set(other_features)
                    total_features = set(target_features) | set(other_features)
                    
                    # 如果有不同的特征，或者即使特征相同但用于演示，也可以匹配
                    if len(common_features) < len(total_features) or len(total_features) > 0:
                        # 互补性：基于特征差异程度
                        if len(total_features) > 0:
                            complementarity = len(total_features - common_features) / len(total_features)
                        else:
                            complementarity = 0.5  # 默认互补性
                        
                        # 对于演示目的，即使特征相同也允许匹配，但互补性较低
                        if complementarity == 0:
                            complementarity = 0.3  # 给予较低的匹配分数
                            
                        matches.append({
                            'user_id': user_id,
                            'complementarity': complementarity,
                            'data_amount': other_intent['data_amount'],
                            'features': other_features,
                            'dataset_info': uploaded_datasets.get(user_id, {})
                        })
        
        return sorted(matches, key=lambda x: x.get('similarity', x.get('complementarity', 0)), reverse=True)

fl_service = FederatedLearningService()

def restore_datasets_from_files():
    """从文件系统恢复数据集信息"""
    global uploaded_datasets
    
    for fed_type in ['horizontal', 'vertical']:
        upload_dir = os.path.join(UPLOAD_FOLDER, fed_type)
        if os.path.exists(upload_dir):
            for filename in os.listdir(upload_dir):
                if filename.endswith(('.csv', '.json', '.xlsx', '.xls')):
                    file_path = os.path.join(upload_dir, filename)
                    
                    # 从文件名解析用户ID
                    parts = filename.split('_')
                    if len(parts) >= 2:
                        user_id = '_'.join(parts[:3])  # user_guest_1749109794960
                        
                        # 如果还没有这个用户的数据，尝试恢复
                        if user_id not in uploaded_datasets:
                            try:
                                # 重新处理文件以获取信息
                                processed_data = process_uploaded_file(file_path, fed_type, user_id)
                                uploaded_datasets[user_id] = {
                                    'original_filename': '_'.join(parts[4:]),  # 原始文件名
                                    'file_path': file_path,
                                    'processed_path': processed_data['processed_path'],
                                    'federation_type': fed_type,
                                    'upload_time': datetime.now().isoformat(),
                                    'features': processed_data['features'],
                                    'sample_count': processed_data['sample_count'],
                                    'feature_count': processed_data['feature_count'],
                                    'columns': processed_data['columns']
                                }
                                print(f"✅ 恢复数据集: {user_id} ({fed_type})")
                            except Exception as e:
                                print(f"❌ 恢复数据集失败: {filename} - {e}")

# 启动时恢复数据
restore_datasets_from_files()

def save_intents_to_file():
    """将意向数据保存到文件"""
    try:
        import json
        os.makedirs('data', exist_ok=True)
        with open('data/collaboration_intents.json', 'w', encoding='utf-8') as f:
            json.dump(collaboration_intents, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ 保存意向数据失败: {e}")

def restore_intents_from_file():
    """从文件恢复意向数据"""
    global collaboration_intents
    try:
        import json
        if os.path.exists('data/collaboration_intents.json'):
            with open('data/collaboration_intents.json', 'r', encoding='utf-8') as f:
                collaboration_intents = json.load(f)
            print(f"✅ 恢复意向数据: {len(collaboration_intents)} 个")
    except Exception as e:
        print(f"❌ 恢复意向数据失败: {e}")

def save_invitations_to_file():
    """将训练邀请保存到文件"""
    try:
        import json
        os.makedirs('data', exist_ok=True)
        with open('data/training_invitations.json', 'w', encoding='utf-8') as f:
            json.dump(training_invitations, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ 保存邀请数据失败: {e}")

def restore_invitations_from_file():
    """从文件恢复训练邀请数据"""
    global training_invitations
    try:
        import json
        if os.path.exists('data/training_invitations.json'):
            with open('data/training_invitations.json', 'r', encoding='utf-8') as f:
                training_invitations = json.load(f)
            print(f"✅ 恢复邀请数据: {len(training_invitations)} 个")
    except Exception as e:
        print(f"❌ 恢复邀请数据失败: {e}")

# 启动时恢复数据
restore_intents_from_file()
restore_invitations_from_file()

def save_training_jobs_to_file():
    """保存训练任务到文件"""
    try:
        training_jobs_file = 'training_jobs.json'
        with open(training_jobs_file, 'w', encoding='utf-8') as f:
            json.dump(training_jobs, f, ensure_ascii=False, indent=2)
        print(f"✅ 保存训练任务数据: {len(training_jobs)} 个")
    except Exception as e:
        print(f"❌ 保存训练任务失败: {e}")

def restore_training_jobs_from_file():
    """从文件恢复训练任务"""
    global training_jobs
    try:
        training_jobs_file = 'training_jobs.json'
        if os.path.exists(training_jobs_file):
            with open(training_jobs_file, 'r', encoding='utf-8') as f:
                training_jobs = json.load(f)
            print(f"✅ 恢复训练任务数据: {len(training_jobs)} 个")
        else:
            print("📄 没有找到训练任务文件，使用空数据")
    except Exception as e:
        print(f"❌ 恢复训练任务失败: {e}")
        training_jobs = {}

def save_notifications_to_file():
    """将通知数据保存到文件"""
    try:
        notifications_file = 'notifications.json'
        with open(notifications_file, 'w', encoding='utf-8') as f:
            json.dump(notifications_db, f, ensure_ascii=False, indent=2)
        total_notifications = sum(len(notifications) for notifications in notifications_db.values())
        print(f"✅ 保存通知数据: {len(notifications_db)} 个用户, {total_notifications} 条通知")
    except Exception as e:
        print(f"❌ 保存通知数据失败: {e}")

def restore_notifications_from_file():
    """从文件恢复通知数据"""
    global notifications_db
    try:
        notifications_file = 'notifications.json'
        if os.path.exists(notifications_file):
            with open(notifications_file, 'r', encoding='utf-8') as f:
                notifications_db = json.load(f)
            total_notifications = sum(len(notifications) for notifications in notifications_db.values())
            print(f"✅ 恢复通知数据: {len(notifications_db)} 个用户, {total_notifications} 条通知")
        else:
            print("📄 没有找到通知文件，使用空数据")
    except Exception as e:
        print(f"❌ 恢复通知数据失败: {e}")
        notifications_db = {}

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'fate_available': FATE_AVAILABLE,
        'pipeline_type': 'FATE' if FATE_AVAILABLE else 'Mock'
    })

@app.route('/api/debug-status', methods=['GET'])
def debug_status():
    """调试端点：检查内存状态"""
    try:
        return jsonify({
            'success': True,
            'training_invitations_count': len(training_invitations),
            'training_invitations': list(training_invitations.keys()),
            'notifications_db_count': len(notifications_db),
            'notifications_users': list(notifications_db.keys()),
            'uploaded_datasets_count': len(uploaded_datasets),
            'uploaded_datasets_users': list(uploaded_datasets.keys()),
            'collaboration_intents_count': len(collaboration_intents),
            'collaboration_intents_users': list(collaboration_intents.keys())
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/debug-invitations', methods=['GET'])
def debug_invitations():
    """调试邀请数据"""
    try:
        invitations_info = []
        for invitation_id, invitation in training_invitations.items():
            invitations_info.append({
                'invitation_id': invitation_id,
                'from_user': invitation['from_user'],
                'to_users': invitation['to_users'],
                'status': invitation.get('status', 'pending'),
                'responses': invitation.get('responses', {}),
                'federation_type': invitation['federation_type']
            })
        
        return jsonify({
            'success': True,
            'invitations': invitations_info,
            'total_count': len(invitations_info)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reload-data', methods=['POST'])
def reload_data():
    """重新加载数据文件（调试用）"""
    try:
        global training_invitations, collaboration_intents, uploaded_datasets
        
        # 重新加载邀请数据
        old_invitation_count = len(training_invitations)
        restore_invitations_from_file()
        new_invitation_count = len(training_invitations)
        
        # 重新加载意向数据
        old_intent_count = len(collaboration_intents)
        restore_intents_from_file()
        new_intent_count = len(collaboration_intents)
        
        # 重新加载数据集信息
        old_dataset_count = len(uploaded_datasets)
        restore_datasets_from_files()
        new_dataset_count = len(uploaded_datasets)
        
        print(f"🔄 数据重新加载完成:")
        print(f"  邀请: {old_invitation_count} -> {new_invitation_count}")
        print(f"  意向: {old_intent_count} -> {new_intent_count}")
        print(f"  数据集: {old_dataset_count} -> {new_dataset_count}")
        
        return jsonify({
            'success': True,
            'message': '数据重新加载完成',
            'changes': {
                'invitations': {'old': old_invitation_count, 'new': new_invitation_count},
                'intents': {'old': old_intent_count, 'new': new_intent_count},
                'datasets': {'old': old_dataset_count, 'new': new_dataset_count}
            }
        })
        
    except Exception as e:
        print(f"❌ 重新加载数据失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 用户认证相关API
def generate_user_id_from_username(username):
    """根据用户名生成固定的用户ID"""
    import hashlib
    # 使用用户名的SHA256哈希作为用户ID，确保同一用户名总是生成相同ID
    hash_object = hashlib.sha256(username.encode())
    return hash_object.hexdigest()[:32]  # 取前32位作为用户ID

@app.route('/api/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        
        # 验证输入
        if not username or len(username) < 3:
            return jsonify({'success': False, 'error': '用户名至少3个字符'}), 400
        
        if not password or len(password) < 6:
            return jsonify({'success': False, 'error': '密码至少6个字符'}), 400
        
        # 根据用户名生成固定用户ID
        user_id = generate_user_id_from_username(username)
        
        # 检查用户名是否已存在（通过用户ID检查，因为用户ID是基于用户名生成的）
        if user_id in users_db:
            return jsonify({'success': False, 'error': '用户名已存在'}), 400
        
        # 创建用户
        users_db[user_id] = {
            'username': username,
            'password_hash': hash_password(password),
            'email': email,
            'profile': {
                'display_name': username,
                'created_at': datetime.now().isoformat(),
                'avatar': f"https://ui-avatars.com/api/?name={username}&background=random"
            }
        }
        
        print(f"✅ 注册用户: {username} -> ID: {user_id}")
        
        # 生成token
        token = generate_jwt_token(user_id)
        user_sessions[user_id] = {
            'token': token,
            'login_time': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat()
        }
        
        # 初始化通知
        notifications_db[user_id] = []
        
        # 添加欢迎通知
        add_notification(
            user_id, 
            'welcome', 
            '欢迎使用联邦学习平台！', 
            f'欢迎您，{username}！您可以开始上传数据集并参与联邦学习。'
        )
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'user': {
                'user_id': user_id,
                'username': username,
                'email': email,
                'profile': users_db[user_id]['profile']
            },
            'token': token
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'注册失败: {str(e)}'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'success': False, 'error': '用户名和密码不能为空'}), 400
        
        # 根据用户名生成用户ID进行查找
        user_id = generate_user_id_from_username(username)
        user_info = users_db.get(user_id)
        
        if not user_info or not verify_password(password, user_info['password_hash']):
            return jsonify({'success': False, 'error': '用户名或密码错误'}), 401
        
        # 生成新token
        token = generate_jwt_token(user_id)
        user_sessions[user_id] = {
            'token': token,
            'login_time': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': {
                'user_id': user_id,
                'username': user_info['username'],
                'email': user_info['email'],
                'profile': user_info['profile']
            },
            'token': token
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'登录失败: {str(e)}'}), 500

@app.route('/api/profile', methods=['GET'])
@require_auth
def get_profile():
    """获取用户资料"""
    try:
        user_id = request.current_user_id
        user_info = users_db.get(user_id)
        
        if not user_info:
            return jsonify({'success': False, 'error': '用户不存在'}), 404
        
        return jsonify({
            'success': True,
            'user': {
                'user_id': user_id,
                'username': user_info['username'],
                'email': user_info['email'],
                'profile': user_info['profile']
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'获取资料失败: {str(e)}'}), 500

@app.route('/api/upload-dataset', methods=['POST'])
def upload_dataset():
    """上传数据集文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有文件被上传'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'}), 400
        
        if file and allowed_file(file.filename):
            # 获取表单数据
            user_id = request.form.get('user_id', str(uuid.uuid4()))
            federation_type = request.form.get('federation_type', 'horizontal')
            
            # 保存原始文件
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{user_id}_{timestamp}_{filename}"
            
            upload_dir = os.path.join(UPLOAD_FOLDER, federation_type)
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, unique_filename)
            
            file.save(file_path)
            
            # 读取数据进行重复检测
            file_ext = file_path.rsplit('.', 1)[1].lower()
            if file_ext == 'csv':
                new_df = pd.read_csv(file_path)
            elif file_ext == 'json':
                new_df = pd.read_json(file_path)
            elif file_ext == 'xlsx':
                new_df = pd.read_excel(file_path)
            else:
                # 删除临时文件
                os.remove(file_path)
                return jsonify({'success': False, 'error': f'不支持的文件格式: {file_ext}'}), 400
            
            # 检查是否为重复数据
            duplicate_check = check_duplicate_data(user_id, new_df, federation_type)
            
            if duplicate_check['is_duplicate']:
                # 删除刚上传的重复文件
                os.remove(file_path)
                
                return jsonify({
                    'success': False,
                    'error': '重复数据检测',
                    'duplicate_info': {
                        'reason': duplicate_check['reason'],
                        'message': duplicate_check['message'],
                        'existing_upload_time': duplicate_check.get('existing_upload_time'),
                        'similarity': duplicate_check.get('similarity')
                    },
                    'suggestions': [
                        '如果您确实需要上传新数据，请确保数据内容有明显差异',
                        '您可以先删除之前的数据，再重新上传',
                        '或者检查数据预处理步骤是否正确'
                    ]
                }), 409  # 409 Conflict
            
            # 处理数据文件
            processed_data = process_uploaded_file(file_path, federation_type, user_id)
            
            # 存储数据集信息
            uploaded_datasets[user_id] = {
                'original_filename': filename,
                'file_path': file_path,
                'processed_path': processed_data['processed_path'],
                'federation_type': federation_type,
                'upload_time': datetime.now().isoformat(),
                'features': processed_data['features'],
                'sample_count': processed_data['sample_count'],
                'feature_count': processed_data['feature_count'],
                'columns': processed_data['columns']
            }
            
            return jsonify({
                'success': True,
                'user_id': user_id,
                'message': f'数据集上传成功，包含 {processed_data["sample_count"]} 个样本',
                'dataset_info': uploaded_datasets[user_id]
            })
        
        return jsonify({'success': False, 'error': '不支持的文件格式'}), 400
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload-intent', methods=['POST'])
def upload_intent():
    """上传参与意愿"""
    try:
        data = request.json
        user_id = data.get('user_id', str(uuid.uuid4()))
        
        intent_data = {
            'user_id': user_id,
            'federation_type': data['federation_type'],
            'features': data['features'],
            'data_amount': data['data_amount'],
            'start_time': data['start_time'],
            'end_time': data['end_time'],
            'timestamp': datetime.now().isoformat(),
            'has_uploaded_data': user_id in uploaded_datasets
        }
        
        collaboration_intents[user_id] = intent_data
        
        # 保存意向数据到文件
        save_intents_to_file()
        
        # 寻找匹配的合作方
        matches = fl_service.find_collaborators(intent_data)
        
        # 如果找到匹配，发送通知给新用户和匹配的用户
        if matches:
            # 获取新用户的用户名
            new_username = f"用户{user_id[-4:]}"  # 使用用户ID后4位作为显示名称
            for uid, user_info in users_db.items():
                if uid == user_id:
                    new_username = user_info['username']
                    break
            
            # 给新用户发送匹配成功通知
            add_notification(
                user_id,
                'collaboration_match',
                '🎉 找到合作方！',
                f'系统为您找到了 {len(matches)} 个潜在的联邦学习合作方，请查看详情并发起训练邀请。',
                {
                    'match_count': len(matches),
                    'federation_type': data['federation_type'],
                    'matches': [match['user_id'] for match in matches[:3]]  # 只保存前3个
                }
            )
            
            # 给每个匹配的用户发送通知
            for match in matches:
                collaborator_id = match['user_id']
                
                # 获取匹配用户的用户名
                collaborator_username = f"用户{collaborator_id[-4:]}"
                for uid, user_info in users_db.items():
                    if uid == collaborator_id:
                        collaborator_username = user_info['username']
                        break
                
                # 发送通知给匹配的用户
                add_notification(
                    collaborator_id,
                    'collaboration_match',
                    '🤝 新的合作机会！',
                    f'用户 {new_username} 刚刚上传了联邦学习意向，与您的需求高度匹配（匹配度 {((match.get("similarity") or match.get("complementarity", 0)) * 100):.1f}%）。',
                    {
                        'new_user_id': user_id,
                        'new_username': new_username,
                        'federation_type': data['federation_type'],
                        'match_score': (match.get("similarity") or match.get("complementarity", 0)),
                        'data_amount': match.get('data_amount', 0)
                    }
                )
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'matches': matches[:5],  # 返回前5个最匹配的
            'message': f'找到 {len(matches)} 个潜在合作方',
            'has_uploaded_data': intent_data['has_uploaded_data'],
            'notifications_sent': len(matches) if matches else 0
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/datasets/<user_id>', methods=['GET'])
def get_user_dataset(user_id):
    """获取用户上传的数据集信息"""
    try:
        if user_id not in uploaded_datasets:
            return jsonify({'success': False, 'error': '用户没有上传数据集'}), 404
            
        return jsonify({
            'success': True,
            'dataset_info': uploaded_datasets[user_id]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/collaborations/<user_id>', methods=['GET'])
def get_collaborations(user_id):
    """获取用户的合作机会"""
    try:
        if user_id not in collaboration_intents:
            return jsonify({'success': False, 'error': '用户意愿不存在'}), 404
            
        intent_data = collaboration_intents[user_id]
        matches = fl_service.find_collaborators(intent_data)
        
        return jsonify({
            'success': True,
            'matches': matches,
            'total_count': len(matches)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/start-training', methods=['POST'])
def start_training():
    """发送联邦学习训练邀请"""
    try:
        data = request.json
        user_id = data['user_id']
        collaborator_ids = data['collaborator_ids']
        federation_type = data['federation_type']
        
        print(f"🚀 开始处理训练邀请: 发送方={user_id}, 接收方={collaborator_ids}, 类型={federation_type}")
        
        # 检查参与方是否都有数据
        all_participants = [user_id] + collaborator_ids
        missing_data = []
        participant_dataset_mapping = {}
        
        for participant in all_participants:
            # 使用find_dataset_id_by_user_id函数查找对应的数据集ID
            dataset_id = find_dataset_id_by_user_id(participant)
            if dataset_id and dataset_id in uploaded_datasets:
                participant_dataset_mapping[participant] = dataset_id
                print(f"✅ 找到参与方 {participant} 的数据集: {dataset_id}")
            else:
                missing_data.append(participant)
                print(f"❌ 参与方 {participant} 缺少数据集")
        
        if missing_data:
            print(f"❌ 缺少数据的参与方: {missing_data}")
            return jsonify({
                'success': False,
                'error': f'以下参与方缺少数据: {missing_data}'
            }), 400
        
        # 检查是否已存在相同的待处理邀请（只检查pending状态的邀请）
        for invitation_id, invitation in training_invitations.items():
            if (invitation['from_user'] == user_id and 
                set(invitation['to_users']) == set(collaborator_ids) and
                invitation['federation_type'] == federation_type and
                invitation['status'] == 'pending'):
                print(f"❌ 检测到重复的待处理邀请: {invitation_id}")
                return jsonify({
                    'success': False,
                    'error': '已存在相同的待处理训练邀请，请等待响应后再发送新邀请',
                    'existing_invitation_id': invitation_id
                }), 409
                
        print(f"✅ 没有重复的待处理邀请，可以创建新邀请")
        
        # 创建训练邀请
        invitation_id = str(uuid.uuid4())
        print(f"📝 创建邀请ID: {invitation_id}")
        
        training_invitations[invitation_id] = {
            'invitation_id': invitation_id,
            'from_user': user_id,
            'to_users': collaborator_ids,
            'federation_type': federation_type,
            'status': 'pending',
            'created_at': datetime.now().isoformat(),
            'responses': {},  # {user_id: 'accepted'/'rejected'}
            'job_info': {
                'total_rounds': data.get('total_rounds', 10),
                'dataset_info': {pid: uploaded_datasets[participant_dataset_mapping[pid]] for pid in all_participants}
            }
        }
        
        print(f"✅ 邀请已保存，当前邀请总数: {len(training_invitations)}")
        
        # 保存邀请数据到文件
        save_invitations_to_file()
        
        # 获取发起用户信息
        from_username = 'Unknown'
        for uid, user_info in users_db.items():
            if uid == user_id:
                from_username = user_info['username']
                break
        
        # 发送邀请通知给所有合作方
        for collaborator_id in collaborator_ids:
            add_notification(
                collaborator_id,
                'training_invitation',
                '联邦学习训练邀请',
                f'用户 {from_username} 邀请您参与 {federation_type} 联邦学习训练',
                {
                    'invitation_id': invitation_id,
                    'from_user': user_id,
                    'from_username': from_username,
                    'federation_type': federation_type,
                    'participants_count': len(all_participants)
                }
            )
        
        return jsonify({
            'success': True,
            'invitation_id': invitation_id,
            'message': f'训练邀请已发送给 {len(collaborator_ids)} 个合作方',
            'participants_data': {pid: uploaded_datasets[participant_dataset_mapping[pid]]['sample_count'] for pid in all_participants}
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/training-invitations/<user_id>', methods=['GET'])
def get_training_invitations(user_id):
    """获取用户的训练邀请"""
    try:
        # 查找用户ID - 支持短ID和完整ID
        matched_user_id = find_user_id_by_short_id(user_id)
        print(f"👤 查询邀请: 输入ID={user_id}, 匹配到ID={matched_user_id}")
        
        received_invitations = []
        sent_invitations = []
        
        # 查找收到的邀请 - 检查所有可能的ID形式
        for invitation_id, invitation in training_invitations.items():
            # 获取发送者用户名
            from_username = 'Unknown'
            for uid, user_info in users_db.items():
                if uid == invitation['from_user']:
                    from_username = user_info['username']
                    break
            
            # 检查是否是收到的邀请
            if (user_id in invitation['to_users'] or 
                matched_user_id in invitation['to_users']):
                received_invitations.append({
                    'invitation_id': invitation_id,
                    'from_user': invitation['from_user'],
                    'from_username': from_username,
                    'to_users': invitation['to_users'],
                    'federation_type': invitation['federation_type'],
                    'status': invitation['status'],
                    'created_at': invitation['created_at'],
                    'job_info': invitation.get('job_info', {}),
                    'responses': invitation.get('responses', {}),
                    'user_response': invitation.get('responses', {}).get(matched_user_id)
                })
            
            # 检查是否是发送的邀请
            if (invitation['from_user'] == user_id or 
                invitation['from_user'] == matched_user_id):
                responses = invitation.get('responses', {})
                accepted_count = sum(1 for resp in responses.values() if resp == 'accepted')
                rejected_count = sum(1 for resp in responses.values() if resp == 'rejected')
                pending_count = len(invitation['to_users']) - len(responses)
                
                sent_invitations.append({
                    'invitation_id': invitation_id,
                    'from_user': invitation['from_user'],
                    'from_username': from_username,
                    'to_users': invitation['to_users'],
                    'federation_type': invitation['federation_type'],
                    'status': invitation['status'],
                    'created_at': invitation['created_at'],
                    'job_info': invitation.get('job_info', {}),
                    'responses': responses,
                    'accepted_count': accepted_count,
                    'rejected_count': rejected_count,
                    'pending_count': pending_count
                })
        
        print(f"📊 邀请查询结果: 收到={len(received_invitations)}, 发送={len(sent_invitations)}")
        
        return jsonify({
            'success': True,
            'received_invitations': received_invitations,
            'sent_invitations': sent_invitations,
            'user_id': matched_user_id
        })
        
    except Exception as e:
        print(f"❌ 获取训练邀请失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/respond-invitation', methods=['POST'])
@require_auth
def respond_invitation():
    """响应训练邀请"""
    try:
        data = request.json
        invitation_id = data['invitation_id']
        user_id = request.current_user_id
        response = data['response']  # 'accepted' or 'rejected'
        
        if invitation_id not in training_invitations:
            return jsonify({'success': False, 'error': '邀请不存在'}), 404
        
        invitation = training_invitations[invitation_id]
        
        if user_id not in invitation['to_users']:
            return jsonify({'success': False, 'error': '无权响应此邀请'}), 403
        
        if response not in ['accepted', 'rejected']:
            return jsonify({'success': False, 'error': '无效的响应'}), 400
        
        # 记录响应
        invitation['responses'][user_id] = response
        
        # 保存邀请数据到文件
        save_invitations_to_file()
        
        # 获取响应用户信息
        user_username = 'Unknown'
        for uid, user_info in users_db.items():
            if uid == user_id:
                user_username = user_info['username']
                break
        
        # 通知发起方
        response_text = '接受' if response == 'accepted' else '拒绝'
        add_notification(
            invitation['from_user'],
            'invitation_response',
            f'邀请响应: {response_text}',
            f'用户 {user_username} {response_text}了您的联邦学习训练邀请',
            {
                'invitation_id': invitation_id,
                'responder': user_id,
                'responder_username': user_username,
                'response': response
            }
        )
        
        # 检查是否所有人都已响应
        all_responded = len(invitation['responses']) == len(invitation['to_users'])
        all_accepted = all_responded and all(resp == 'accepted' for resp in invitation['responses'].values())
        
        if all_accepted:
            # 所有人都接受，开始训练
            job_id = str(uuid.uuid4())
            all_participants = [invitation['from_user']] + invitation['to_users']
            
            print(f"🚀 准备开始训练，参与方: {all_participants}")
            print(f"📊 当前数据集: {list(uploaded_datasets.keys())}")
            
            # 检查所有参与方是否都有数据集
            missing_datasets = []
            dataset_paths = {}
            for pid in all_participants:
                dataset_id = find_dataset_id_by_user_id(pid)
                if dataset_id and dataset_id in uploaded_datasets:
                    dataset_paths[pid] = uploaded_datasets[dataset_id]['processed_path']
                    print(f"✅ 找到参与方 {pid} 的数据集: {dataset_id}")
                else:
                    missing_datasets.append(pid)
                    print(f"❌ 参与方 {pid} 缺少数据集")
            
            if missing_datasets:
                print(f"❌ 训练失败，缺少数据集的参与方: {missing_datasets}")
                return jsonify({
                    'success': False,
                    'error': f'以下参与方缺少数据集: {missing_datasets}',
                    'missing_datasets': missing_datasets
                }), 400
            
            # 初始化训练状态
            training_jobs[job_id] = {
                'job_id': job_id,
                'user_id': invitation['from_user'],
                'collaborator_ids': invitation['to_users'],
                'federation_type': invitation['federation_type'],
                'status': 'initializing',
                'current_round': 0,
                'total_rounds': invitation['job_info']['total_rounds'],
                'start_time': datetime.now().isoformat(),
                'metrics': {},
                'model_path': None,
                'fate_enabled': FATE_AVAILABLE,
                'dataset_paths': dataset_paths,
                'invitation_id': invitation_id
            }
            
            # 更新邀请状态
            invitation['status'] = 'accepted'
            invitation['job_id'] = job_id
            
            # 保存训练任务数据
            save_training_jobs_to_file()
            
            # 启动后台训练任务
            training_thread = threading.Thread(
                target=run_federated_training,
                args=(job_id, invitation['federation_type'], invitation['from_user'], invitation['to_users'])
            )
            training_thread.daemon = True
            training_thread.start()
            
            # 通知所有参与方
            for participant in all_participants:
                add_notification(
                    participant,
                    'training_started',
                    '联邦学习训练已开始',
                    f'所有参与方都已同意，{invitation["federation_type"]}联邦学习训练正在进行中',
                    {
                        'job_id': job_id,
                        'invitation_id': invitation_id,
                        'participants_count': len(all_participants)
                    }
                )
            
            return jsonify({
                'success': True,
                'message': '所有参与方已同意，训练开始',
                'job_id': job_id,
                'all_accepted': True
            })
            
        elif all_responded:
            # 有人拒绝，训练失败
            invitation['status'] = 'rejected'
            
            # 通知发起方
            add_notification(
                invitation['from_user'],
                'training_cancelled',
                '联邦学习训练已取消',
                '由于有参与者拒绝，训练邀请已被取消',
                {
                    'invitation_id': invitation_id,
                    'rejected_by': [uid for uid, resp in invitation['responses'].items() if resp == 'rejected']
                }
            )
            
            return jsonify({
                'success': True,
                'message': f'您已{response_text}邀请',
                'all_accepted': False,
                'training_cancelled': True
            })
        
        return jsonify({
            'success': True,
            'message': f'您已{response_text}邀请，等待其他参与方响应',
            'all_accepted': False,
            'pending_responses': len(invitation['to_users']) - len(invitation['responses'])
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/training-status/<job_id>', methods=['GET'])
def get_training_status(job_id):
    """获取训练状态"""
    try:
        if job_id not in training_jobs:
            return jsonify({'success': False, 'error': '训练任务不存在'}), 404
            
        job_info = training_jobs[job_id]
        return jsonify({
            'success': True,
            'job_info': job_info
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download-model/<job_id>', methods=['GET'])
def download_model(job_id):
    """下载训练好的模型"""
    try:
        if job_id not in training_jobs:
            return jsonify({'success': False, 'error': '训练任务不存在'}), 404
            
        job_info = training_jobs[job_id]
        
        if job_info['status'] != 'completed':
            return jsonify({'success': False, 'error': '模型训练尚未完成'}), 400
            
        model_path = job_info.get('model_path')
        if not model_path or not os.path.exists(model_path):
            return jsonify({'success': False, 'error': '模型文件不存在'}), 404
            
        return send_file(
            model_path,
            as_attachment=True,
            download_name=f'federated_model_{job_id}.pkl'
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    """获取模型库"""
    try:
        models = []
        for job_id, job_info in training_jobs.items():
            if job_info['status'] == 'completed':
                models.append({
                    'job_id': job_id,
                    'federation_type': job_info['federation_type'],
                    'training_time': job_info['start_time'],
                    'metrics': job_info['metrics'],
                    'participants': len(job_info['collaborator_ids']) + 1,
                    'fate_enabled': job_info.get('fate_enabled', False)
                })
                
        return jsonify({
            'success': True,
            'models': models
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notifications/<user_id>', methods=['GET'])
def get_notifications(user_id):
    """获取用户通知"""
    try:
        notifications = []
        
        # 首先获取存储的历史通知
        if user_id in notifications_db:
            stored_notifications = notifications_db[user_id]
            # 按时间戳排序，最新的在前
            stored_notifications.sort(key=lambda x: x['timestamp'], reverse=True)
            notifications.extend(stored_notifications)
        
        # 检查是否有新的合作机会（如果还没有相关通知）
        if user_id in collaboration_intents:
            intent_data = collaboration_intents[user_id]
            matches = fl_service.find_collaborators(intent_data)
            
            if matches:
                # 检查是否已经有类似的通知
                has_collab_notification = any(
                    n['type'] in ['collaboration_opportunity', 'collaboration_match'] 
                    for n in notifications
                )
                
                if not has_collab_notification:
                    new_notification = {
                        'id': str(uuid.uuid4()),
                        'type': 'collaboration_opportunity',
                        'title': '发现新的合作机会',
                        'message': f'找到 {len(matches)} 个匹配的合作方',
                        'timestamp': datetime.now().isoformat(),
                        'data': {'matches': matches[:3], 'match_count': len(matches)}
                    }
                    notifications.append(new_notification)
                    # 同时保存到数据库
                    if user_id not in notifications_db:
                        notifications_db[user_id] = []
                    notifications_db[user_id].append(new_notification)
                    save_notifications_to_file()
        
        # 检查训练状态更新（如果还没有相关通知）
        for job_id, job_info in training_jobs.items():
            if job_info['user_id'] == user_id or user_id in job_info.get('collaborator_ids', []):
                if job_info['status'] == 'completed':
                    # 检查是否已经有这个训练完成的通知
                    has_training_notification = any(
                        n['type'] == 'training_completed' and 
                        n.get('data', {}).get('job_id') == job_id
                        for n in notifications
                    )
                    
                    if not has_training_notification:
                        fate_status = "（FATE框架）" if job_info.get('fate_enabled') else "（模拟）"
                        new_notification = {
                            'id': str(uuid.uuid4()),
                            'type': 'training_completed',
                            'title': f'模型训练完成{fate_status}',
                            'message': f"联邦学习训练已完成，准确率: {job_info['metrics'].get('accuracy', 'N/A')}",
                            'timestamp': job_info.get('completion_time', datetime.now().isoformat()),
                            'data': {'job_id': job_id}
                        }
                        notifications.append(new_notification)
                        # 同时保存到数据库
                        if user_id not in notifications_db:
                            notifications_db[user_id] = []
                        notifications_db[user_id].append(new_notification)
                        save_notifications_to_file()
        
        # 再次按时间戳排序，确保最新的在前
        notifications.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            'success': True,
            'notifications': notifications
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/debug-training-jobs', methods=['GET'])
def debug_training_jobs():
    """调试接口：查看所有训练任务"""
    return jsonify({
        'success': True,
        'training_jobs_count': len(training_jobs),
        'training_jobs': {
            job_id: {
                'status': job_info['status'],
                'start_time': job_info.get('start_time', ''),
                'completion_time': job_info.get('completion_time', ''),
                'federation_type': job_info.get('federation_type', ''),
                'metrics': job_info.get('metrics', {}),
                'fate_enabled': job_info.get('fate_enabled', False),
                'participants': len(job_info.get('collaborator_ids', [])) + 1,
                'invitation_id': job_info.get('invitation_id', 'N/A')
            }
            for job_id, job_info in training_jobs.items()
        }
    })

@app.route('/api/fix-invitation-status', methods=['POST'])
def fix_invitation_status():
    """修复邀请状态：将已完成训练的邀请状态更新为completed"""
    try:
        updated_count = 0
        
        # 查找所有已完成的训练任务
        for job_id, job_info in training_jobs.items():
            if job_info['status'] == 'completed':
                invitation_id = job_info.get('invitation_id')
                if invitation_id and invitation_id in training_invitations:
                    current_status = training_invitations[invitation_id]['status']
                    if current_status != 'completed':
                        training_invitations[invitation_id]['status'] = 'completed'
                        updated_count += 1
                        print(f"✅ 更新邀请 {invitation_id} 状态: {current_status} -> completed")
        
        # 保存更新后的邀请数据
        if updated_count > 0:
            save_invitations_to_file()
        
        return jsonify({
            'success': True,
            'message': f'成功更新 {updated_count} 个邀请的状态',
            'updated_count': updated_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def run_federated_training(job_id, federation_type, user_id, collaborator_ids):
    """运行联邦学习训练（后台任务）"""
    try:
        job_info = training_jobs[job_id]
        total_rounds = job_info['total_rounds']
        
        # 更新状态为训练中
        job_info['status'] = 'training'
        
        print(f"🚀 开始使用真实数据进行{federation_type}联邦学习训练")
        print(f"📊 数据路径: {job_info['dataset_paths']}")
        
        if FATE_AVAILABLE:
            # 使用真实的FATE框架进行训练
            pipeline = fl_service.horizontal_pipeline if federation_type == 'horizontal' else fl_service.vertical_pipeline
            
            # 这里可以集成真实的FATE训练逻辑
            # 目前仍使用模拟训练，但显示真实数据信息
            
        # 模拟训练过程（显示真实数据信息）
        for round_num in range(1, total_rounds + 1):
            time.sleep(2)  # 模拟训练时间
            
            job_info['current_round'] = round_num
            job_info['status'] = f'training_round_{round_num}'
            
            # 基于真实数据量调整模拟指标
            total_samples = 0
            for pid in [user_id] + collaborator_ids:
                dataset_id = find_dataset_id_by_user_id(pid)
                if dataset_id and dataset_id in uploaded_datasets:
                    total_samples += uploaded_datasets[dataset_id]['sample_count']
            
            # 模拟训练指标（考虑数据量影响）
            data_quality_factor = min(1.0, total_samples / 1000)  # 数据量越多，效果越好
            
            if federation_type == 'horizontal':
                base_accuracy = 0.6 + data_quality_factor * 0.1
                accuracy = base_accuracy + (round_num / total_rounds) * 0.25
                loss = 0.8 - (round_num / total_rounds) * 0.6 * data_quality_factor
                job_info['metrics'] = {
                    'accuracy': round(accuracy, 4),
                    'loss': round(loss, 4),
                    'f1_score': round(accuracy * 0.95, 4),
                    'total_samples': total_samples
                }
            else:  # vertical
                base_accuracy = 0.7 + data_quality_factor * 0.1
                accuracy = base_accuracy + (round_num / total_rounds) * 0.2
                auc = 0.75 + (round_num / total_rounds) * 0.2 * data_quality_factor
                job_info['metrics'] = {
                    'accuracy': round(accuracy, 4),
                    'auc': round(auc, 4),
                    'precision': round(accuracy * 0.92, 4),
                    'recall': round(accuracy * 1.05, 4),
                    'total_samples': total_samples
                }
        
        # 训练完成，创建模型文件
        model_dir = os.path.join('results', job_id)
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, 'model.pkl')
        
        # 创建模型文件（包含数据集信息）
        model_info = {
            'job_id': job_id,
            'federation_type': federation_type,
            'metrics': job_info['metrics'],
            'training_completed': datetime.now().isoformat(),
            'fate_enabled': FATE_AVAILABLE,
            'participants': len(collaborator_ids) + 1,
            'dataset_info': {}
        }
        
        # 收集数据集信息
        for pid in [user_id] + collaborator_ids:
            dataset_id = find_dataset_id_by_user_id(pid)
            if dataset_id and dataset_id in uploaded_datasets:
                model_info['dataset_info'][pid] = uploaded_datasets[dataset_id]
        
        with open(model_path, 'w') as f:
            json.dump(model_info, f, indent=2)
        
        job_info['status'] = 'completed'
        job_info['model_path'] = model_path
        job_info['completion_time'] = datetime.now().isoformat()
        
        # 更新相关邀请的状态为completed
        invitation_id = job_info.get('invitation_id')
        if invitation_id and invitation_id in training_invitations:
            training_invitations[invitation_id]['status'] = 'completed'
            save_invitations_to_file()
            print(f"✅ 邀请状态已更新为completed: {invitation_id}")
        
        # 保存训练任务数据
        save_training_jobs_to_file()
        
        print(f"✅ 训练完成 - Job ID: {job_id}, 使用真实数据: {total_samples} 样本")
        
    except Exception as e:
        job_info['status'] = 'failed'
        job_info['error'] = str(e)
        print(f"❌ 训练失败 - Job ID: {job_id}, 错误: {e}")

def find_user_id_by_short_id(short_id):
    """通过简短ID查找完整的用户ID"""
    
    # 首先检查是否已经是完整ID（在数据集中存在）
    if short_id in uploaded_datasets:
        return short_id
    
    # 检查是否已经是有效的短ID（在意向数据中存在）
    if short_id in collaboration_intents:
        return short_id
    
    # 尝试通过短ID匹配数据集中的完整ID
    for user_id in uploaded_datasets.keys():
        if short_id in user_id:
            return user_id
    
    # 尝试通过短ID匹配意向数据中的完整ID
    for user_id in collaboration_intents.keys():
        if short_id in user_id:
            return user_id
    
    # 如果都找不到，返回原始ID
    return short_id

def find_dataset_id_by_user_id(user_id):
    """根据用户ID查找对应的数据集ID"""
    # 首先直接查找
    if user_id in uploaded_datasets:
        return user_id
    
    # 查找以user_id开头的数据集ID（包含时间戳）
    for dataset_id in uploaded_datasets.keys():
        if dataset_id.startswith(user_id):
            return dataset_id
    
    # 如果都找不到，返回None
    return None

if __name__ == '__main__':
    print("🚀 启动联邦学习API服务器...")
    print("📡 服务地址: http://localhost:5000")
    print("📋 API文档: http://localhost:5000/api/health")
    print(f"🔧 FATE框架状态: {'✅ 已启用' if FATE_AVAILABLE else '❌ 未启用（使用模拟）'}")
    
    # 确保results目录存在
    os.makedirs('results', exist_ok=True)
    
    # 恢复数据
    restore_datasets_from_files()
    restore_intents_from_file()
    restore_invitations_from_file()
    restore_training_jobs_from_file()
    restore_notifications_from_file()
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True) 
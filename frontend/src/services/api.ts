// API服务层 - 与后端进行通信
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

export interface FeatureData {
  name: string;
  format: string;
  range: string;
}

export interface IntentData {
  user_id?: string;
  federation_type: 'horizontal' | 'vertical';
  features: FeatureData[];
  data_amount: number;
  start_time: string;
  end_time: string;
}

export interface CollaboratorMatch {
  user_id: string;
  similarity?: number;
  complementarity?: number;
  data_amount: number;
  features: string[];
  dataset_info?: {
    original_filename: string;
    sample_count: number;
    feature_count: number;
    features: any[];
  };
}

export interface TrainingJob {
  job_id: string;
  user_id: string;
  collaborator_ids: string[];
  federation_type: 'horizontal' | 'vertical';
  status: string;
  current_round: number;
  total_rounds: number;
  start_time: string;
  metrics: Record<string, number>;
  model_path?: string;
  completion_time?: string;
  error?: string;
}

export interface ModelInfo {
  job_id: string;
  federation_type: 'horizontal' | 'vertical';
  training_time: string;
  metrics: Record<string, number>;
  participants: number;
}

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  timestamp: string;
  data: any;
}

// 用户认证相关接口
export interface User {
  user_id: string;
  username: string;
  email: string;
  profile: {
    display_name: string;
    created_at: string;
    avatar: string;
  };
}

export interface AuthResponse {
  success: boolean;
  message: string;
  user: User;
  token: string;
}

export interface TrainingInvitation {
  invitation_id: string;
  from_user: string;
  from_username?: string;
  to_users: string[];
  federation_type: 'horizontal' | 'vertical';
  status: 'pending' | 'accepted' | 'rejected' | 'completed';
  created_at: string;
  responses: Record<string, 'accepted' | 'rejected'>;
  user_response?: 'accepted' | 'rejected';
  pending_count?: number;
  accepted_count?: number;
  rejected_count?: number;
  job_info: {
    total_rounds: number;
    dataset_info: Record<string, any>;
  };
}

class ApiService {
  private token: string | null = null;

  constructor() {
    // 从localStorage获取token
    this.token = localStorage.getItem('authToken');
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('authToken', token);
  }

  removeToken() {
    this.token = null;
    localStorage.removeItem('authToken');
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { 'Authorization': `Bearer ${this.token}` }),
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (!data.success) {
        throw new Error(data.error || 'API request failed');
      }
      
      return data;
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // 健康检查
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.request('/health');
  }

  // 上传参与意愿
  async uploadIntent(intentData: IntentData): Promise<{
    user_id: string;
    matches: CollaboratorMatch[];
    message: string;
  }> {
    return this.request('/upload-intent', {
      method: 'POST',
      body: JSON.stringify(intentData),
    });
  }

  // 获取合作机会
  async getCollaborations(userId: string): Promise<{
    matches: CollaboratorMatch[];
    total_count: number;
  }> {
    return this.request(`/collaborations/${userId}`);
  }

  // 开始训练
  async startTraining(data: {
    user_id: string;
    collaborator_ids: string[];
    federation_type: 'horizontal' | 'vertical';
    total_rounds?: number;
  }): Promise<{
    job_id: string;
    message: string;
  }> {
    return this.request('/start-training', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // 获取训练状态
  async getTrainingStatus(jobId: string): Promise<{
    job_info: TrainingJob;
  }> {
    return this.request(`/training-status/${jobId}`);
  }

  // 下载模型
  async downloadModel(jobId: string): Promise<Blob> {
    const url = `${API_BASE_URL}/download-model/${jobId}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`);
    }
    
    return response.blob();
  }

  // 获取模型库
  async getModels(): Promise<{
    models: ModelInfo[];
  }> {
    return this.request('/models');
  }

  // 获取通知
  async getNotifications(userId: string): Promise<{
    notifications: Notification[];
  }> {
    return this.request(`/notifications/${userId}`);
  }

  // 用户认证相关方法
  async register(username: string, password: string, email: string): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, email }),
    });
    
    if (response.token) {
      this.setToken(response.token);
    }
    
    return response;
  }

  async login(username: string, password: string): Promise<AuthResponse> {
    const response = await this.request<AuthResponse>('/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    
    if (response.token) {
      this.setToken(response.token);
    }
    
    return response;
  }

  async getProfile(): Promise<{ user: User }> {
    return this.request('/profile');
  }

  // 训练邀请相关方法
  async getTrainingInvitations(userId: string): Promise<{
    received_invitations: TrainingInvitation[];
    sent_invitations: TrainingInvitation[];
  }> {
    return this.request(`/training-invitations/${userId}`);
  }

  async respondInvitation(invitationId: string, response: 'accepted' | 'rejected'): Promise<{
    message: string;
    all_accepted: boolean;
    job_id?: string;
    training_cancelled?: boolean;
    pending_responses?: number;
  }> {
    return this.request('/respond-invitation', {
      method: 'POST',
      body: JSON.stringify({ 
        invitation_id: invitationId, 
        response 
      }),
    });
  }
}

export const apiService = new ApiService(); 
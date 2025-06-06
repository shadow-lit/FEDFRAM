import React, { useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  Tab,
  Tabs,
  Alert,
  CircularProgress,
  Avatar,
  Card,
  CardContent,
} from '@mui/material';
import { Person, PersonAdd, Login as LoginIcon } from '@mui/icons-material';
import { apiService } from '../services/api';

interface LoginProps {
  onLogin: (user: any, token: string) => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  
  // 登录表单
  const [loginData, setLoginData] = useState({
    username: '',
    password: ''
  });
  
  // 注册表单
  const [registerData, setRegisterData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
    email: ''
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
    setAlert(null);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAlert(null);

    try {
      const response = await apiService.login(loginData.username, loginData.password);
      setAlert({ type: 'success', message: response.message });
      
      // 延迟调用onLogin以显示成功消息
      setTimeout(() => {
        onLogin(response.user, response.token);
      }, 1000);
      
    } catch (error: any) {
      setAlert({ type: 'error', message: error.message || '登录失败' });
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAlert(null);

    // 验证密码确认
    if (registerData.password !== registerData.confirmPassword) {
      setAlert({ type: 'error', message: '密码确认不匹配' });
      setLoading(false);
      return;
    }

    try {
      const response = await apiService.register(
        registerData.username,
        registerData.password,
        registerData.email
      );
      setAlert({ type: 'success', message: response.message });
      
      // 延迟调用onLogin以显示成功消息
      setTimeout(() => {
        onLogin(response.user, response.token);
      }, 1000);
      
    } catch (error: any) {
      setAlert({ type: 'error', message: error.message || '注册失败' });
    } finally {
      setLoading(false);
    }
  };

  // 快速登录演示账户
  const demoAccounts = [
    { username: 'hospital_a', password: 'demo123', name: '医院A' },
    { username: 'hospital_b', password: 'demo123', name: '医院B' },
    { username: 'hospital_c', password: 'demo123', name: '医院C' }
  ];

  const handleDemoLogin = async (username: string, password: string) => {
    setLoading(true);
    setAlert(null);

    try {
      // 先尝试注册（如果用户不存在）
      try {
        await apiService.register(username, password, `${username}@demo.com`);
      } catch (error) {
        // 如果注册失败（用户已存在），继续登录
      }
      
      // 登录
      const response = await apiService.login(username, password);
      setAlert({ type: 'success', message: `欢迎 ${response.user.username}！` });
      
      setTimeout(() => {
        onLogin(response.user, response.token);
      }, 1000);
      
    } catch (error: any) {
      setAlert({ type: 'error', message: error.message || '演示登录失败' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="md" sx={{ mt: 8, mb: 4 }}>
      <Box display="flex" justifyContent="center" mb={4}>
        <Avatar sx={{ width: 80, height: 80, bgcolor: 'primary.main' }}>
          <Person sx={{ fontSize: 40 }} />
        </Avatar>
      </Box>
      
      <Typography variant="h3" component="h1" align="center" gutterBottom>
        联邦学习平台
      </Typography>
      
      <Typography variant="h6" component="h2" align="center" color="text.secondary" sx={{ mb: 4 }}>
        多机构协作的隐私保护机器学习
      </Typography>

      {/* 演示账户快速登录 */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          🚀 快速开始 - 演示账户
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          选择一个演示账户快速体验联邦学习流程
        </Typography>
        
        <Box display="flex" gap={2} flexWrap="wrap">
          {demoAccounts.map((account) => (
            <Card key={account.username} sx={{ minWidth: 200 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {account.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  用户名: {account.username}
          </Typography>
                <Button
                  variant="contained"
                  size="small"
                  onClick={() => handleDemoLogin(account.username, account.password)}
                  disabled={loading}
                  startIcon={<LoginIcon />}
                >
                  快速登录
                </Button>
              </CardContent>
            </Card>
          ))}
        </Box>
      </Paper>

      <Paper sx={{ p: 4 }}>
        <Tabs value={activeTab} onChange={handleTabChange} centered sx={{ mb: 3 }}>
          <Tab 
            label="登录" 
            icon={<LoginIcon />} 
            iconPosition="start"
          />
          <Tab 
            label="注册" 
            icon={<PersonAdd />} 
            iconPosition="start"
          />
        </Tabs>

        {alert && (
          <Alert 
            severity={alert.type} 
            sx={{ mb: 3 }}
            onClose={() => setAlert(null)}
          >
            {alert.message}
          </Alert>
        )}

        {activeTab === 0 ? (
          // 登录表单
          <Box component="form" onSubmit={handleLogin}>
            <TextField
              fullWidth
              label="用户名"
              value={loginData.username}
              onChange={(e) => setLoginData({ ...loginData, username: e.target.value })}
              margin="normal"
              required
              disabled={loading}
            />
            <TextField
              fullWidth
              label="密码"
              type="password"
              value={loginData.password}
              onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
              margin="normal"
              required
              disabled={loading}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={loading}
              sx={{ mt: 3 }}
            >
              {loading ? <CircularProgress size={24} /> : '登录'}
            </Button>
          </Box>
        ) : (
          // 注册表单
          <Box component="form" onSubmit={handleRegister}>
            <TextField
              fullWidth
              label="用户名"
              value={registerData.username}
              onChange={(e) => setRegisterData({ ...registerData, username: e.target.value })}
              margin="normal"
              required
              disabled={loading}
              helperText="至少3个字符"
            />
            <TextField
              fullWidth
              label="邮箱"
              type="email"
              value={registerData.email}
              onChange={(e) => setRegisterData({ ...registerData, email: e.target.value })}
              margin="normal"
              required
              disabled={loading}
            />
            <TextField
              fullWidth
              label="密码"
              type="password"
              value={registerData.password}
              onChange={(e) => setRegisterData({ ...registerData, password: e.target.value })}
              margin="normal"
              required
              disabled={loading}
              helperText="至少6个字符"
            />
            <TextField
              fullWidth
              label="确认密码"
              type="password"
              value={registerData.confirmPassword}
              onChange={(e) => setRegisterData({ ...registerData, confirmPassword: e.target.value })}
              margin="normal"
              required
              disabled={loading}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              size="large"
              disabled={loading}
              sx={{ mt: 3 }}
            >
              {loading ? <CircularProgress size={24} /> : '注册'}
            </Button>
          </Box>
        )}
        </Paper>
    </Container>
  );
};

export default Login; 
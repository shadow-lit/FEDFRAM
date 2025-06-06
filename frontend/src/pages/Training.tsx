import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  LinearProgress,
  Box,
  Button,
  Grid,
  Card,
  CardContent,
  Chip,
  Alert,
  CircularProgress,
  Snackbar,
} from '@mui/material';
import { 
  Download, 
  PlayArrow, 
  Pause, 
  CheckCircle,
  TrendingUp,
  Groups,
  Timer,
  Assessment,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { apiService, type User } from '../services/api';
import type { TrainingJob } from '../services/api';
import AppNavBar from '../components/AppNavBar';

interface TrainingProps {
  user: User | null;
  onLogout: () => void;
}

const Training: React.FC<TrainingProps> = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [jobInfo, setJobInfo] = useState<TrainingJob | null>(null);
  const [loading, setLoading] = useState(false);
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });
  
  // 从localStorage获取当前训练任务ID
  const currentJobId = localStorage.getItem('currentJobId');

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  // 获取训练状态
  const fetchTrainingStatus = async () => {
    if (!currentJobId) {
      return;
    }

    try {
      const response = await apiService.getTrainingStatus(currentJobId);
      setJobInfo(response.job_info);
    } catch (error) {
      console.error('获取训练状态失败:', error);
      showSnackbar('获取训练状态失败', 'error');
    }
  };

  // 定期更新训练状态
  useEffect(() => {
    if (currentJobId) {
      fetchTrainingStatus();
      
      // 如果训练未完成，每2秒更新一次状态
      const interval = setInterval(() => {
        fetchTrainingStatus();
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [currentJobId]);

  // 下载模型
  const handleDownload = async () => {
    if (!currentJobId) {
      showSnackbar('没有可下载的模型', 'error');
      return;
    }

    setDownloadLoading(true);
    try {
      const blob = await apiService.downloadModel(currentJobId);
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `federated_model_${currentJobId}.pkl`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      showSnackbar('模型下载成功！', 'success');
    } catch (error) {
      console.error('下载失败:', error);
      showSnackbar('模型下载失败，请稍后重试', 'error');
    } finally {
      setDownloadLoading(false);
    }
  };

  // 计算进度百分比
  const getProgress = () => {
    if (!jobInfo) return 0;
    return (jobInfo.current_round / jobInfo.total_rounds) * 100;
  };

  // 获取状态描述
  const getStatusDescription = () => {
    if (!jobInfo) return '等待训练任务...';
    
    switch (jobInfo.status) {
      case 'initializing':
        return '正在初始化训练环境...';
      case 'training':
        return '联邦学习训练进行中...';
      case 'completed':
        return '训练完成！';
      case 'failed':
        return '训练失败';
      default:
        if (jobInfo.status.startsWith('training_round')) {
          return `第 ${jobInfo.current_round} 轮训练中...`;
        }
        return jobInfo.status;
    }
  };

  // 获取联邦类型描述
  const getFederationTypeDescription = (type: string) => {
    return type === 'horizontal' ? '横向联邦学习' : '纵向联邦学习';
  };

  // 渲染指标卡片
  const renderMetricsCards = () => {
    if (!jobInfo || !jobInfo.metrics || Object.keys(jobInfo.metrics).length === 0) {
      return null;
    }

    return (
      <Grid container spacing={2} sx={{ mt: 2 }}>
        {Object.entries(jobInfo.metrics).map(([key, value]) => (
          <Grid item xs={6} sm={3} key={key}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 2 }}>
                <Typography variant="h6" color="primary">
                  {typeof value === 'number' ? value.toFixed(4) : value}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {key === 'accuracy' ? '准确率' :
                   key === 'loss' ? '损失值' :
                   key === 'f1_score' ? 'F1分数' :
                   key === 'auc' ? 'AUC值' :
                   key === 'precision' ? '精确率' :
                   key === 'recall' ? '召回率' : key}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    );
  };

  if (!currentJobId) {
    return (
      <Box>
        <AppNavBar user={user} onLogout={onLogout} title="训练过程" />
        <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h4" gutterBottom>
              训练过程
            </Typography>
            <Alert severity="info" sx={{ mt: 3 }}>
              <Typography variant="h6">
                没有正在进行的训练任务
              </Typography>
              <Typography variant="body2">
                请先上传参与意愿并选择合作方来开始训练
              </Typography>
            </Alert>
            <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button
                variant="outlined"
                onClick={() => navigate('/home')}
              >
                返回主页
              </Button>
              <Button
                variant="contained"
                onClick={() => navigate('/intent-upload')}
              >
                开始新的训练
              </Button>
            </Box>
          </Paper>
        </Container>
      </Box>
    );
  }

  return (
    <Box>
      <AppNavBar user={user} onLogout={onLogout} title="训练过程" />
      <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom>
          联邦学习训练过程
        </Typography>

        {jobInfo && (
          <>
            <Grid container spacing={3} sx={{ mb: 4 }}>
              <Grid item xs={12} sm={6}>
                <Box display="flex" alignItems="center" mb={1}>
                  <Assessment sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">
                    {getFederationTypeDescription(jobInfo.federation_type)}
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Box display="flex" alignItems="center" mb={1}>
                  <Groups sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">
                    参与方: {jobInfo.collaborator_ids.length + 1} 个
                  </Typography>
                </Box>
              </Grid>
            </Grid>

            <Box sx={{ mb: 4 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  训练进度
                </Typography>
                <Chip 
                  label={getStatusDescription()}
                  color={jobInfo.status === 'completed' ? 'success' : 
                         jobInfo.status === 'failed' ? 'error' : 'primary'}
                  icon={jobInfo.status === 'completed' ? <CheckCircle /> : 
                        jobInfo.status.includes('training') ? <PlayArrow /> : <Timer />}
                />
              </Box>
              
              <Box display="flex" justifyContent="space-between" mb={1}>
                <Typography variant="body1">
                  第 {jobInfo.current_round} 轮 / 共 {jobInfo.total_rounds} 轮
                </Typography>
                <Typography variant="body1">
                  {Math.round(getProgress())}%
                </Typography>
              </Box>
              
              <LinearProgress
                variant="determinate"
                value={getProgress()}
                sx={{ height: 10, borderRadius: 5 }}
              />
            </Box>

            {/* 训练指标 */}
            {renderMetricsCards()}

            {/* 训练完成后的操作 */}
            {jobInfo.status === 'completed' && (
              <Box sx={{ mt: 4, textAlign: 'center' }}>
                <Alert severity="success" sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    🎉 联邦学习训练完成！
                  </Typography>
                  <Typography variant="body2">
                    模型已成功训练完成，您可以下载模型文件进行部署使用
                  </Typography>
                </Alert>
                
                <Button
                  variant="contained"
                  startIcon={downloadLoading ? <CircularProgress size={20} /> : <Download />}
                  onClick={handleDownload}
                  disabled={downloadLoading}
                  size="large"
                >
                  {downloadLoading ? '下载中...' : '下载模型'}
                </Button>
              </Box>
            )}

            {/* 训练失败 */}
            {jobInfo.status === 'failed' && (
              <Box sx={{ mt: 4, textAlign: 'center' }}>
                <Alert severity="error" sx={{ mb: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    ❌ 训练失败
                  </Typography>
                  <Typography variant="body2">
                    {jobInfo.error || '训练过程中发生了错误，请检查配置并重试'}
                  </Typography>
                </Alert>
                
                <Button
                  variant="contained"
                  onClick={() => window.location.href = '/intent-upload'}
                >
                  重新开始训练
                </Button>
              </Box>
            )}

            {/* 训练中状态 */}
            {jobInfo.status.includes('training') && (
              <Box sx={{ mt: 4, textAlign: 'center' }}>
                <Alert severity="info">
                  <Typography variant="body1">
                    训练正在进行中，请耐心等待...
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    页面会自动更新训练进度，请勿关闭浏览器
                  </Typography>
                </Alert>
              </Box>
            )}
          </>
        )}

        {/* 加载状态 */}
        {!jobInfo && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <CircularProgress size={40} />
            <Typography variant="body1" sx={{ mt: 2 }}>
              正在获取训练状态...
            </Typography>
          </Box>
        )}
      </Paper>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
    </Box>
  );
};

export default Training; 
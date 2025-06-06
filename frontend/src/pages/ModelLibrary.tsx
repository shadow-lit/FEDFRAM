import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Box,
  Chip,
  Alert,
  CircularProgress,
  Snackbar,
} from '@mui/material';
import {
  Download,
  Assessment,
  Group,
  Schedule,
  TrendingUp,
  Refresh,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { apiService, type User } from '../services/api';
import type { ModelInfo } from '../services/api';
import AppNavBar from '../components/AppNavBar';

interface ModelLibraryProps {
  user: User | null;
  onLogout: () => void;
}

const ModelLibrary: React.FC<ModelLibraryProps> = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [downloadLoading, setDownloadLoading] = useState<string | null>(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  // 获取模型列表
  const fetchModels = async () => {
    setLoading(true);
    try {
      const response = await apiService.getModels();
      setModels(response.models);
    } catch (error) {
      console.error('获取模型列表失败:', error);
      showSnackbar('获取模型列表失败，请稍后重试', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  // 下载模型
  const handleDownload = async (jobId: string) => {
    setDownloadLoading(jobId);
    try {
      const blob = await apiService.downloadModel(jobId);
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `federated_model_${jobId}.pkl`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      showSnackbar('模型下载成功！', 'success');
    } catch (error) {
      console.error('下载失败:', error);
      showSnackbar('模型下载失败，请稍后重试', 'error');
    } finally {
      setDownloadLoading(null);
    }
  };

  // 格式化时间
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // 获取联邦类型描述
  const getFederationTypeDescription = (type: string) => {
    return type === 'horizontal' ? '横向联邦学习' : '纵向联邦学习';
  };

  // 获取联邦类型颜色
  const getFederationTypeColor = (type: string) => {
    return type === 'horizontal' ? 'primary' : 'secondary';
  };

  // 渲染指标
  const renderMetrics = (metrics: Record<string, number>) => {
    return Object.entries(metrics).map(([key, value]) => (
      <Box key={key} display="flex" justifyContent="space-between" mb={1}>
        <Typography variant="body2" color="text.secondary">
          {key === 'accuracy' ? '准确率' :
           key === 'loss' ? '损失值' :
           key === 'f1_score' ? 'F1分数' :
           key === 'auc' ? 'AUC值' :
           key === 'precision' ? '精确率' :
           key === 'recall' ? '召回率' : key}:
        </Typography>
        <Typography variant="body2" fontWeight="medium">
          {typeof value === 'number' ? value.toFixed(4) : value}
        </Typography>
      </Box>
    ));
  };

  return (
    <Box>
      <AppNavBar user={user} onLogout={onLogout} title="模型库" />
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Paper sx={{ p: 4 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
            <Typography variant="h4">
              模型库
            </Typography>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={fetchModels}
              disabled={loading}
            >
              刷新
            </Button>
          </Box>

        <Typography variant="body1" color="text.secondary" paragraph>
          这里展示了所有已完成训练的联邦学习模型，您可以下载这些模型用于部署和预测。
        </Typography>

        {loading && (
          <Box display="flex" justifyContent="center" py={8}>
            <CircularProgress size={40} />
          </Box>
        )}

        {!loading && models.length === 0 && (
          <Alert severity="info" sx={{ textAlign: 'center' }}>
            <Typography variant="h6" gutterBottom>
              暂无可用模型
            </Typography>
            <Typography variant="body2">
              完成联邦学习训练后，模型将出现在这里
            </Typography>
            <Button
              variant="contained"
              sx={{ mt: 2 }}
              onClick={() => window.location.href = '/intent-upload'}
            >
              开始新的训练
            </Button>
          </Alert>
        )}

        {!loading && models.length > 0 && (
          <>
            <Typography variant="h6" gutterBottom>
              共 {models.length} 个模型
            </Typography>
            
            <Grid container spacing={3} sx={{ mt: 2 }}>
              {models.map((model) => (
                <Grid item xs={12} md={6} lg={4} key={model.job_id}>
                  <Card 
                    sx={{ 
                      height: '100%',
                      display: 'flex',
                      flexDirection: 'column',
                      '&:hover': { 
                        boxShadow: 4,
                        transform: 'translateY(-2px)',
                        transition: 'all 0.2s ease-in-out'
                      }
                    }}
                  >
                    <CardContent sx={{ flexGrow: 1 }}>
                      {/* 模型类型标签 */}
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                        <Chip
                          label={getFederationTypeDescription(model.federation_type)}
                          color={getFederationTypeColor(model.federation_type) as any}
                          size="small"
                        />
                        <Typography variant="caption" color="text.secondary">
                          ID: {model.job_id.substring(0, 8)}...
                        </Typography>
                      </Box>

                      {/* 基本信息 */}
                      <Box display="flex" alignItems="center" mb={1}>
                        <Schedule sx={{ mr: 1, fontSize: 16, color: 'text.secondary' }} />
                        <Typography variant="body2" color="text.secondary">
                          训练时间: {formatTime(model.training_time)}
                        </Typography>
                      </Box>

                      <Box display="flex" alignItems="center" mb={2}>
                        <Group sx={{ mr: 1, fontSize: 16, color: 'text.secondary' }} />
                        <Typography variant="body2" color="text.secondary">
                          参与方: {model.participants} 个
                        </Typography>
                      </Box>

                      {/* 性能指标 */}
                      <Typography variant="subtitle2" gutterBottom>
                        性能指标
                      </Typography>
                      <Box sx={{ pl: 1 }}>
                        {renderMetrics(model.metrics)}
                      </Box>
                    </CardContent>

                    <CardActions sx={{ p: 2, pt: 0 }}>
                      <Button
                        fullWidth
                        variant="contained"
                        startIcon={
                          downloadLoading === model.job_id ? 
                          <CircularProgress size={16} /> : 
                          <Download />
                        }
                        onClick={() => handleDownload(model.job_id)}
                        disabled={downloadLoading === model.job_id}
                      >
                        {downloadLoading === model.job_id ? '下载中...' : '下载模型'}
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>

            {/* 统计信息 */}
            <Box mt={4} p={3} bgcolor="background.default" borderRadius={2}>
              <Typography variant="h6" gutterBottom>
                统计信息
              </Typography>
              <Grid container spacing={3}>
                <Grid item xs={6} sm={3}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="primary">
                      {models.length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      总模型数
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="primary">
                      {models.filter(m => m.federation_type === 'horizontal').length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      横向联邦
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="secondary">
                      {models.filter(m => m.federation_type === 'vertical').length}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      纵向联邦
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6} sm={3}>
                  <Box textAlign="center">
                    <Typography variant="h4" color="success.main">
                      {Math.round(models.reduce((acc, m) => acc + m.participants, 0) / models.length) || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      平均参与方
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Box>
          </>
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

export default ModelLibrary; 
import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  ToggleButton,
  ToggleButtonGroup,
  Grid,
  Alert,
  Snackbar,
  CircularProgress,
  Card,
  CardContent,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
} from '@mui/material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs';
import { 
  CheckCircle, 
  Groups, 
  TrendingUp, 
  Storage,
  PlayArrow,
  CloudUpload,
  FilePresent,
  Delete,
  Person,
  PersonAdd,
  Search
} from '@mui/icons-material';
import dayjs, { Dayjs } from 'dayjs';
import { apiService, type User } from '../services/api';
import type { FeatureData, CollaboratorMatch } from '../services/api';
import AppNavBar from '../components/AppNavBar';

interface IntentUploadProps {
  user: User | null;
  onLogout: () => void;
}

const IntentUpload: React.FC<IntentUploadProps> = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [activeStep, setActiveStep] = useState(0);
  const [federationType, setFederationType] = useState<'horizontal' | 'vertical'>('horizontal');
  const [features, setFeatures] = useState<FeatureData[]>([{ name: '', format: '', range: '' }]);
  const [dataAmount, setDataAmount] = useState('');
  const [startTime, setStartTime] = useState<Dayjs | null>(dayjs('2025-01-10T22:00'));
  const [endTime, setEndTime] = useState<Dayjs | null>(dayjs('2025-01-18T05:00'));
  
  // 多用户模拟相关状态
  const [currentRole, setCurrentRole] = useState<'guest' | 'host1' | 'host2'>('guest');
  const [uploadedDatasets, setUploadedDatasets] = useState<{[key: string]: any}>({});
  const [submittedIntents, setSubmittedIntents] = useState<{[key: string]: boolean}>({});
  
  // 文件上传相关状态
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(false);
  const [datasetInfo, setDatasetInfo] = useState<any>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  
  // 状态管理
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [userId, setUserId] = useState<string>('');
  const [matches, setMatches] = useState<CollaboratorMatch[]>([]);
  const [selectedCollaborators, setSelectedCollaborators] = useState<string[]>([]);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' | 'info' });
  const [intentSubmitted, setIntentSubmitted] = useState(false);
  const [previousCollaborators, setPreviousCollaborators] = useState<string[]>([]);
  const [showPreviousInvites, setShowPreviousInvites] = useState(false);

  // 使用真实用户信息
  useEffect(() => {
    if (user) {
      setUserId(user.user_id);
    }
  }, [user]);

  // 处理从通知页面跳转的查看合作方请求
  useEffect(() => {
    const action = searchParams.get('action');
    if (action === 'view-collaborators' && user) {
      loadExistingCollaborators();
    }
    
    // 加载历史合作方
    if (user) {
      loadPreviousCollaborators();
    }
  }, [searchParams, user]);

  const loadExistingCollaborators = async () => {
    try {
      setLoading(true);
      
      if (!user?.user_id) {
        showSnackbar('用户身份验证失败，请重新登录', 'error');
        return;
      }

      console.log('从通知页面加载合作方数据, 用户ID:', user.user_id);
      
      try {
        // 直接使用当前用户的ID获取合作方数据
        const response = await apiService.getCollaborations(user.user_id);
        console.log('获取到的合作方数据:', response);
        
        if (response.matches && response.matches.length > 0) {
          // 找到了合作方数据
          setUserId(user.user_id);
          setMatches(response.matches);
          setSubmitted(true);
          // 根据合作方数据推测联邦类型，默认为vertical
          setFederationType('vertical');
          showSnackbar(`找到 ${response.matches.length} 个潜在合作方`, 'success');
          return;
        }
      } catch (error) {
        console.error(`获取用户 ${user.user_id} 的合作方失败:`, error);
      }

      // 如果没有找到合作方数据，也尝试从localStorage获取之前保存的用户ID
      const savedUserId = localStorage.getItem(`userId_${user.user_id}`);
      if (savedUserId && savedUserId !== user.user_id) {
        console.log('尝试使用保存的用户ID:', savedUserId);
        try {
          const response = await apiService.getCollaborations(savedUserId);
          if (response.matches && response.matches.length > 0) {
            setUserId(savedUserId);
            setMatches(response.matches);
            setSubmitted(true);
            setFederationType('vertical');
            showSnackbar(`找到 ${response.matches.length} 个潜在合作方`, 'success');
            return;
          }
        } catch (error) {
          console.warn(`获取保存的用户 ${savedUserId} 的合作方失败:`, error);
        }
      }

      showSnackbar('未找到匹配的合作方，请先上传数据并提交意向', 'info');
    } catch (error) {
      console.error('加载合作方数据失败:', error);
      showSnackbar('加载失败，请稍后重试', 'error');
    } finally {
      setLoading(false);
    }
  };

  // 角色配置
  const roleConfig = {
    guest: { 
      name: 'Guest (医院A)', 
      description: '作为Guest方参与联邦学习',
      color: 'primary',
      suffix: '_guest'
    },
    host1: { 
      name: 'Host1 (医院B)', 
      description: '作为Host方参与联邦学习',
      color: 'secondary',
      suffix: '_host1'
    },
    host2: { 
      name: 'Host2 (医院C)', 
      description: '作为第二个Host方参与联邦学习',
      color: 'info',
      suffix: '_host2'
    }
  };

  // 直接使用真实用户ID，不需要角色选择
  useEffect(() => {
    if (user) {
      // 检查是否有已保存的用户ID
      const savedUserId = localStorage.getItem(`userId_${user.user_id}`);
      if (savedUserId) {
        setUserId(savedUserId);
      } else {
        setUserId('');
      }
    }
    
    // 检查用户是否已有数据
    if (user && datasetInfo) {
      setActiveStep(1);
    } else {
      setDatasetInfo(null);
      setActiveStep(0);
    }
    
    // 重置提交状态
    setSubmitted(false);
    setMatches([]);
  }, [user]);

  const handleRoleChange = (newRole: 'guest' | 'host1' | 'host2') => {
    setCurrentRole(newRole);
    setUploadedFile(null);
    setFeatures([{ name: '', format: '', range: '' }]);
    setDataAmount('');
  };

  const handleFederationTypeChange = (
    event: React.MouseEvent<HTMLElement>,
    newType: 'horizontal' | 'vertical',
  ) => {
    if (newType !== null) {
      // 如果已经有上传的数据，询问用户是否重新上传
      if (datasetInfo && newType !== federationType) {
        if (window.confirm('更改联邦学习类型需要重新上传数据文件，是否继续？')) {
          setFederationType(newType);
          // 清除现有数据
          setDatasetInfo(null);
          setUploadedFile(null);
          setFeatures([{ name: '', format: '', range: '' }]);
          setDataAmount('');
          setActiveStep(0);
          showSnackbar('联邦学习类型已更改，请重新上传数据文件', 'info');
        }
      } else {
      setFederationType(newType);
    }
    }
  };

  // 处理文件上传（点击或拖拽）
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    await processFile(file);
  };

  // 处理拖拽上传
  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragEnter = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = async (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragOver(false);
    
    const files = event.dataTransfer.files;
    if (files && files.length > 0) {
      const file = files[0];
      await processFile(file);
    }
  };

  // 统一的文件处理函数
  const processFile = async (file: File) => {
    // 检查文件类型
    const allowedTypes = ['text/csv', 'application/json', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
    if (!allowedTypes.includes(file.type) && !file.name.endsWith('.csv')) {
      showSnackbar('请选择CSV、JSON或Excel文件', 'error');
      return;
    }

    // 检查文件大小 (16MB)
    if (file.size > 16 * 1024 * 1024) {
      showSnackbar('文件大小不能超过16MB', 'error');
      return;
    }

    setUploadedFile(file);
    setUploadProgress(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      
      // 使用真实用户的ID，与后端注册时生成的ID保持一致
      const uniqueUserId = user?.user_id;
      if (!uniqueUserId) {
        showSnackbar('用户身份验证失败，请重新登录', 'error');
        setUploadProgress(false);
        return;
      }
      formData.append('user_id', uniqueUserId);
      formData.append('federation_type', federationType);

      const response = await fetch('http://localhost:5000/api/upload-dataset', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (result.success) {
        setUserId(result.user_id);
        // 使用真实用户ID作为localStorage键
        if (user) {
          localStorage.setItem(`userId_${user.user_id}`, result.user_id);
        }
        
        // 保存当前角色的数据集信息
        const newDatasetInfo = result.dataset_info;
        setDatasetInfo(newDatasetInfo);
        setUploadedDatasets(prev => ({
          ...prev,
          [currentRole]: newDatasetInfo
        }));
        
        // 自动填充特征信息
        setFeatures(newDatasetInfo.features.map((f: any) => ({
          name: f.name,
          format: f.type,
          range: f.range
        })));
        
        setDataAmount(newDatasetInfo.sample_count.toString());
        showSnackbar(`${roleConfig[currentRole].name} 数据上传成功！${result.message}`, 'success');
        setActiveStep(1); // 前进到下一步
      } else {
        throw new Error(result.error);
      }
    } catch (error) {
      console.error('文件上传失败:', error);
      showSnackbar('文件上传失败，请稍后重试', 'error');
      setUploadedFile(null);
    } finally {
      setUploadProgress(false);
    }
  };

  const handleRemoveFile = () => {
    setUploadedFile(null);
    setDatasetInfo(null);
    setUploadedDatasets(prev => {
      const newDatasets = { ...prev };
      delete newDatasets[currentRole];
      return newDatasets;
    });
    setFeatures([{ name: '', format: '', range: '' }]);
    setDataAmount('');
    setActiveStep(0);
  };

  const handleFeatureChange = (index: number, field: keyof FeatureData, value: string) => {
    const newFeatures = [...features];
    newFeatures[index] = { ...newFeatures[index], [field]: value };
    setFeatures(newFeatures);
  };

  const addFeature = () => {
    setFeatures([...features, { name: '', format: '', range: '' }]);
  };

  const removeFeature = (index: number) => {
    setFeatures(features.filter((_, i) => i !== index));
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (!user?.user_id) {
        showSnackbar('用户身份验证失败，请重新登录', 'error');
        setLoading(false);
        return;
      }

      const intentData = {
        user_id: user.user_id, // 使用真实用户ID，与注册时一致
        federation_type: federationType,
      features,
        data_amount: parseInt(dataAmount),
        start_time: startTime?.toISOString() || '',
        end_time: endTime?.toISOString() || '',
      };

      const response = await apiService.uploadIntent(intentData);
      
      setMatches(response.matches);
      setIntentSubmitted(true);
      showSnackbar('意向上传成功！系统将自动为您匹配合作方', 'success');
      
    } catch (error) {
      console.error('提交失败:', error);
      showSnackbar('提交失败，请稍后重试', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleFindCollaborators = () => {
    setSubmitted(true);
  };

  const handleCollaboratorToggle = (collaboratorId: string) => {
    setSelectedCollaborators(prev => 
      prev.includes(collaboratorId)
        ? prev.filter(id => id !== collaboratorId)
        : [...prev, collaboratorId]
    );
  };

  const handleStartTraining = async () => {
    if (selectedCollaborators.length === 0) {
      showSnackbar('请至少选择一个合作方', 'error');
      return;
    }

    setLoading(true);
    try {
      if (!user?.user_id) {
        showSnackbar('用户身份验证失败，请重新登录', 'error');
        setLoading(false);
        return;
      }

      console.log('发送训练邀请:', {
        from_user_id: user.user_id,
        from_username: user.username,
        collaborator_ids: selectedCollaborators,
        federation_type: federationType,
        total_rounds: 10
      });

      const response = await apiService.startTraining({
        user_id: user.user_id, // 使用真实用户ID，与注册时一致
        collaborator_ids: selectedCollaborators,
        federation_type: federationType,
        total_rounds: 10,
      });

      console.log('邀请发送响应:', response);
      showSnackbar(`训练邀请已发送给 ${selectedCollaborators.length} 个合作方，请在通知中心查看响应`, 'success');
      
      // 延迟跳转到通知页面
      setTimeout(() => {
        navigate('/notifications');
      }, 2000);

    } catch (error: any) {
      console.error('发送邀请失败:', error);
      const errorMessage = error.message || '发送邀请失败，请稍后重试';
      showSnackbar(errorMessage, 'error');
    } finally {
      setLoading(false);
    }
  };

  // 加载之前的合作方历史
  const loadPreviousCollaborators = async () => {
    try {
      if (!user?.user_id) return;
      
      console.log('加载历史合作方, 用户ID:', user.user_id);
      const response = await apiService.getTrainingInvitations(user.user_id);
      console.log('邀请数据:', response);
      
      const previousCollabs = new Set<string>();
      
      // 从发送的邀请中提取之前的合作方
      response.sent_invitations.forEach(invitation => {
        console.log('检查发送的邀请:', invitation);
        if (invitation.status === 'accepted') {
          invitation.to_users.forEach(userId => {
            console.log('添加合作方(发送):', userId);
            previousCollabs.add(userId);
          });
        }
      });
      
      // 从收到的邀请中提取之前的合作方
      response.received_invitations.forEach(invitation => {
        console.log('检查收到的邀请:', invitation);
        if (invitation.user_response === 'accepted') {
          console.log('添加合作方(接收):', invitation.from_user);
          previousCollabs.add(invitation.from_user);
        }
      });
      
      const collaboratorList = Array.from(previousCollabs);
      console.log('最终合作方列表:', collaboratorList);
      setPreviousCollaborators(collaboratorList);
    } catch (error) {
      console.error('加载历史合作方失败:', error);
    }
  };

  // 重新邀请之前的合作方
  const handleReinvitePreviousCollaborators = async () => {
    if (previousCollaborators.length === 0) {
      showSnackbar('没有找到之前的合作方', 'info');
      return;
    }

    setLoading(true);
    try {
      if (!user?.user_id) {
        showSnackbar('用户身份验证失败，请重新登录', 'error');
        return;
      }

      console.log('重新邀请参数:', {
        from_user_id: user.user_id,
        from_username: user.username,
        collaborator_ids: previousCollaborators,
        federation_type: federationType,
        total_rounds: 10
      });

      const response = await apiService.startTraining({
        user_id: user.user_id,
        collaborator_ids: previousCollaborators,
        federation_type: federationType,
        total_rounds: 10,
      });

      console.log('重新邀请响应:', response);
      showSnackbar(`重新邀请已发送给 ${previousCollaborators.length} 个之前的合作方`, 'success');
      
      // 延迟跳转到通知页面
      setTimeout(() => {
        navigate('/notifications');
      }, 2000);

    } catch (error: any) {
      console.error('重新发送邀请失败:', error);
      const errorMessage = error.message || '重新发送邀请失败，请稍后重试';
      showSnackbar(errorMessage, 'error');
    } finally {
      setLoading(false);
    }
  };

  // 数据上传步骤
  const renderDataUploadStep = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        📂 上传您的数据集
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        支持CSV、JSON、Excel格式，文件大小不超过16MB
      </Typography>

      {/* 先选择联邦类型 */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="subtitle1" gutterBottom>
          1. 选择联邦学习类型
          </Typography>
            <ToggleButtonGroup
              value={federationType}
              exclusive
              onChange={handleFederationTypeChange}
          aria-label="federation type"
          fullWidth
          sx={{ mb: 2 }}
            >
          <ToggleButton value="horizontal" aria-label="horizontal">
            <Box display="flex" alignItems="center" flexDirection="column" p={2}>
              <Groups sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h6">横向联邦学习</Typography>
              <Typography variant="body2" color="text.secondary">
                相同特征，不同样本
              </Typography>
            </Box>
          </ToggleButton>
          <ToggleButton value="vertical" aria-label="vertical">
            <Box display="flex" alignItems="center" flexDirection="column" p={2}>
              <TrendingUp sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h6">纵向联邦学习</Typography>
              <Typography variant="body2" color="text.secondary">
                不同特征，相同样本
              </Typography>
            </Box>
          </ToggleButton>
            </ToggleButtonGroup>
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>当前选择：</strong>{federationType === 'horizontal' ? '横向联邦学习' : '纵向联邦学习'}
          </Typography>
        </Alert>
      </Box>

      {/* 然后上传数据 */}
      <Typography variant="subtitle1" gutterBottom>
        2. 上传数据文件
      </Typography>

      {!datasetInfo ? (
        <Box
          sx={{
            border: isDragOver ? '2px dashed #1976d2' : '2px dashed #ccc',
            borderRadius: 2,
            p: 4,
            textAlign: 'center',
            cursor: 'pointer',
            backgroundColor: isDragOver ? 'primary.light' : 'transparent',
            transition: 'all 0.2s ease-in-out',
            '&:hover': { 
              borderColor: 'primary.main',
              backgroundColor: 'action.hover'
            }
          }}
          component="label"
          onDragOver={handleDragOver}
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
        >
          <input
            type="file"
            hidden
            accept=".csv,.json,.xlsx,.xls"
            onChange={handleFileUpload}
            disabled={uploadProgress}
          />
          {uploadProgress ? (
            <Box>
              <CircularProgress sx={{ mb: 2 }} />
              <Typography>正在上传和处理数据...</Typography>
            </Box>
          ) : (
            <Box>
              <CloudUpload sx={{ 
                fontSize: 48, 
                color: isDragOver ? 'white' : 'primary.main', 
                mb: 2,
                transition: 'color 0.2s ease-in-out'
              }} />
              <Typography 
                variant="h6" 
                gutterBottom
                sx={{ color: isDragOver ? 'white' : 'inherit' }}
              >
                {isDragOver ? '松开鼠标以上传文件' : '点击选择文件或拖拽到此处'}
              </Typography>
              <Typography 
                variant="body2" 
                sx={{ color: isDragOver ? 'rgba(255,255,255,0.8)' : 'text.secondary' }}
              >
                支持 CSV, JSON, Excel 格式
              </Typography>
            </Box>
          )}
        </Box>
      ) : (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between">
              <Box display="flex" alignItems="center">
                <FilePresent color="success" sx={{ mr: 2 }} />
                <Box>
                  <Typography variant="h6">
                    {datasetInfo.original_filename}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {datasetInfo.sample_count} 样本, {datasetInfo.feature_count} 特征
                  </Typography>
                </Box>
              </Box>
              <IconButton onClick={handleRemoveFile} color="error">
                <Delete />
              </IconButton>
            </Box>
            
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                检测到的特征:
              </Typography>
              <Box display="flex" flexWrap="wrap" gap={1}>
                {datasetInfo.features.map((feature: any, index: number) => (
                  <Chip
                    key={index}
                    label={`${feature.name} (${feature.type})`}
                    size="small"
                    variant="outlined"
                  />
                ))}
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {datasetInfo && (
        <Button
          variant="contained"
          onClick={() => setActiveStep(1)}
          sx={{ mt: 2 }}
        >
          下一步: 配置参与意愿
        </Button>
      )}
    </Box>
  );

  // 配置意愿步骤
  const renderIntentConfigStep = () => (
    <Box component="form" onSubmit={handleSubmit}>
      <Typography variant="h6" gutterBottom>
        ⚙️ 配置联邦学习参与意愿
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Alert severity="success" sx={{ mb: 2 }}>
            <Typography variant="subtitle2">
              📊 选中的联邦学习类型
            </Typography>
            <Typography variant="h6">
              {federationType === 'horizontal' ? '🔗 横向联邦学习' : '📈 纵向联邦学习'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {federationType === 'horizontal' ? '相同特征，不同样本' : '不同特征，相同样本'}
            </Typography>
          </Alert>
        </Grid>

        {datasetInfo && (
          <Grid item xs={12}>
            <Alert severity="info" sx={{ mb: 2 }}>
              <Typography variant="subtitle2">
                📊 数据集信息
              </Typography>
              <Typography variant="body2">
                文件: {datasetInfo.original_filename} | 
                样本数: {datasetInfo.sample_count} | 
                特征数: {datasetInfo.feature_count}
              </Typography>
            </Alert>
                </Grid>
        )}

        <Grid item xs={12} md={6}>
          <DateTimePicker
            label="训练开始时间"
            value={startTime}
            onChange={setStartTime}
            slots={{
              textField: TextField
            }}
            slotProps={{
              textField: { fullWidth: true }
            }}
                  />
                </Grid>

        <Grid item xs={12} md={6}>
          <DateTimePicker
            label="训练结束时间"
            value={endTime}
            onChange={setEndTime}
            slots={{
              textField: TextField
            }}
            slotProps={{
              textField: { fullWidth: true }
            }}
                  />
                </Grid>

        <Grid item xs={12}>
          <Box display="flex" gap={2}>
            <Button
              variant="outlined"
              onClick={() => setActiveStep(0)}
            >
              返回上传数据
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={loading || !datasetInfo}
            >
              {loading ? <CircularProgress size={24} /> : '寻找合作方'}
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );

  // 意向提交成功页面
  if (intentSubmitted && !submitted) {
    return (
      <LocalizationProvider dateAdapter={AdapterDayjs}>
        <AppNavBar user={user} onLogout={onLogout} title="联邦学习参与意向" />
        <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
          <Paper sx={{ p: 4 }}>
            <Box textAlign="center" sx={{ mb: 4 }}>
              <CheckCircle sx={{ fontSize: 80, color: 'success.main', mb: 2 }} />
              <Typography variant="h4" gutterBottom>
                意向上传成功！
              </Typography>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
                您的联邦学习参与意向已成功上传！
                <br />
                {matches.length > 0 ? (
                  <strong style={{ color: '#2e7d32' }}>
                    🎉 系统已为您找到 {matches.length} 个潜在合作方！
                  </strong>
                ) : (
                  "系统将自动为您匹配合适的合作方，匹配成功后会通过通知中心提醒您。"
                )}
              </Typography>
            </Box>

            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                📋 您的信息摘要
              </Typography>
              <Typography variant="body2">
                <strong>联邦学习类型：</strong>{federationType === 'horizontal' ? '横向联邦学习' : '纵向联邦学习'}
              </Typography>
              <Typography variant="body2">
                <strong>数据量：</strong>{dataAmount} 样本
              </Typography>
              <Typography variant="body2">
                <strong>特征数：</strong>{features.length} 个
              </Typography>
              <Typography variant="body2">
                <strong>训练时间：</strong>{startTime?.format('YYYY-MM-DD HH:mm')} 至 {endTime?.format('YYYY-MM-DD HH:mm')}
              </Typography>
            </Alert>

            <Grid container spacing={2} justifyContent="center">
              <Grid item>
                <Button
                  variant="contained"
                  onClick={handleFindCollaborators}
                  startIcon={matches.length > 0 ? <Groups /> : <Search />}
                  size="large"
                  color={matches.length > 0 ? "success" : "primary"}
                >
                  {matches.length > 0 ? `查看 ${matches.length} 个合作方` : "立即寻找合作方"}
                </Button>
              </Grid>
              {previousCollaborators.length > 0 && (
                <Grid item>
                  <Button
                    variant="contained"
                    onClick={handleReinvitePreviousCollaborators}
                    startIcon={<PlayArrow />}
                    size="large"
                    color="secondary"
                    disabled={loading}
                  >
                    {loading ? <CircularProgress size={24} /> : `重新邀请 ${previousCollaborators.length} 个合作方`}
                  </Button>
                </Grid>
              )}
              <Grid item>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/home')}
                  size="large"
                >
                  返回主页
                </Button>
              </Grid>
              <Grid item>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/notifications')}
                  size="large"
                >
                  查看通知
                </Button>
              </Grid>
            </Grid>

            <Typography variant="body2" color="text.secondary" textAlign="center" sx={{ mt: 3 }}>
              💡 提示：您也可以稍后在"通知中心"查看匹配结果，或在"主页"重新发起训练
            </Typography>
          </Paper>
        </Container>
      </LocalizationProvider>
    );
  }

  if (submitted && matches.length > 0) {
    return (
      <LocalizationProvider dateAdapter={AdapterDayjs}>
        <AppNavBar user={user} onLogout={onLogout} title="选择合作方" />
        <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
          <Paper sx={{ p: 4 }}>
            <Typography variant="h4" gutterBottom>
              找到合作方
            </Typography>
            
            <Alert severity="success" sx={{ mb: 3 }}>
              <Typography variant="h6">
                🎉 成功找到 {matches.length} 个合作方！
              </Typography>
              <Typography variant="body2">
                选择合作方并发送训练邀请，等待所有参与方同意后开始联邦学习
              </Typography>
            </Alert>

            <Grid container spacing={3}>
              {matches.map((match, index) => (
                <Grid item xs={12} md={6} key={match.user_id}>
                  <Card 
                    sx={{ 
                      cursor: 'pointer',
                      border: selectedCollaborators.includes(match.user_id) ? 2 : 1,
                      borderColor: selectedCollaborators.includes(match.user_id) ? 'primary.main' : 'divider',
                      '&:hover': { boxShadow: 2 }
                    }}
                    onClick={() => handleCollaboratorToggle(match.user_id)}
                  >
                    <CardContent>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                        <Typography variant="h6">
                          合作方 {index + 1}
                        </Typography>
                        {selectedCollaborators.includes(match.user_id) && (
                          <CheckCircle color="primary" />
                        )}
                      </Box>
                      
                      <Box mb={2}>
                        <Typography variant="body2" color="text.secondary">
                          匹配度: {(((match.similarity || match.complementarity) || 0) * 100).toFixed(1)}%
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          数据量: {match.data_amount} 样本
                        </Typography>
                        {match.dataset_info && (
                          <Typography variant="body2" color="text.secondary">
                            数据集: {match.dataset_info.original_filename}
                          </Typography>
                        )}
                      </Box>

                      <Box display="flex" flexWrap="wrap" gap={0.5}>
                        {match.features.slice(0, 3).map((feature, idx) => (
                          <Chip
                            key={idx}
                            label={feature}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                        {match.features.length > 3 && (
                          <Chip
                            label={`+${match.features.length - 3} 更多`}
                            size="small"
                            variant="outlined"
                          />
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>

            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
              <Box>
                <Button
                  variant="outlined"
                  onClick={() => {setSubmitted(false); setActiveStep(1);}}
                  sx={{ mr: 1 }}
                >
                  重新配置
                </Button>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/home')}
                  sx={{ mr: 1 }}
                >
                  返回主页
                </Button>
              </Box>
              <Button
                variant="contained"
                startIcon={<PlayArrow />}
                onClick={handleStartTraining}
                disabled={selectedCollaborators.length === 0 || loading}
                size="large"
              >
                {loading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  `发送邀请 (${selectedCollaborators.length}个合作方)`
                )}
              </Button>
            </Box>
          </Paper>
        </Container>
      </LocalizationProvider>
    );
  }

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs}>
      <AppNavBar user={user} onLogout={onLogout} title="联邦学习参与意向上传" />
      <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
        <Paper sx={{ p: 4 }}>
          <Typography variant="h4" gutterBottom>
            联邦学习参与意愿上传
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            上传您的数据集并配置联邦学习参与意愿，系统将为您匹配合适的合作方
          </Typography>

          <Stepper activeStep={activeStep} orientation="vertical">
            <Step>
              <StepLabel>上传数据集</StepLabel>
              <StepContent>
                {renderDataUploadStep()}
              </StepContent>
            </Step>
            
            <Step>
              <StepLabel>配置参与意愿</StepLabel>
              <StepContent>
                {renderIntentConfigStep()}
              </StepContent>
            </Step>
          </Stepper>

          <Snackbar
            open={snackbar.open}
            autoHideDuration={6000}
            onClose={() => setSnackbar({ ...snackbar, open: false })}
          >
            <Alert severity={snackbar.severity} onClose={() => setSnackbar({ ...snackbar, open: false })}>
              {snackbar.message}
            </Alert>
          </Snackbar>
        </Paper>
      </Container>
    </LocalizationProvider>
  );
};

export default IntentUpload; 
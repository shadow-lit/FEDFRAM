import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  Alert,
  Chip,
  Grid,
  CircularProgress,
  Tab,
  Tabs,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Badge,
  Divider,
} from '@mui/material';
import {
  CheckCircle,
  Cancel,
  Schedule,
  Notifications as NotificationsIcon,
  Groups,
  TrendingUp,
  Person,
  Refresh,
  PlayArrow,
} from '@mui/icons-material';
import { apiService, type User, type TrainingInvitation, type Notification } from '../services/api';
import AppNavBar from '../components/AppNavBar';

interface NotificationsProps {
  user: User | null;
  onLogout: () => void;
}

const Notifications: React.FC<NotificationsProps> = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(0);
  const [invitations, setInvitations] = useState<{
    received: TrainingInvitation[];
    sent: TrainingInvitation[];
  }>({ received: [], sent: [] });
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const [responseLoading, setResponseLoading] = useState<string | null>(null);
  const [alert, setAlert] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [reinviteLoading, setReinviteLoading] = useState(false);

  useEffect(() => {
    if (user) {
      loadInvitations();
      loadNotifications();
      
      // 定时刷新
      const interval = setInterval(() => {
        loadInvitations();
        loadNotifications();
      }, 5000);
      
      return () => clearInterval(interval);
    }
  }, [user]);

  const loadInvitations = async () => {
    if (!user) return;
    
    try {
      console.log('查询邀请使用的用户ID:', user.user_id);
      
      // 直接使用真实用户ID查询邀请
      const response = await apiService.getTrainingInvitations(user.user_id);
      setInvitations({
        received: response.received_invitations,
        sent: response.sent_invitations
      });
      
      console.log('邀请查询结果:', response);
    } catch (error) {
      console.error('加载邀请失败:', error);
    }
  };

  const loadNotifications = async () => {
    if (!user) return;
    
    try {
      console.log('查询通知使用的用户ID:', user.user_id);
      
      // 直接使用真实用户ID查询通知
      const response = await apiService.getNotifications(user.user_id);
      
      // 按时间戳排序，最新的在前
      const sortedNotifications = response.notifications.sort((a, b) => 
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
      );
      
      setNotifications(sortedNotifications);
      console.log('通知查询结果:', response);
    } catch (error) {
      console.error('加载通知失败:', error);
    }
  };

  const handleRespondInvitation = async (invitationId: string, response: 'accepted' | 'rejected') => {
    setResponseLoading(invitationId);
    
    try {
      const result = await apiService.respondInvitation(invitationId, response);
      setAlert({ 
        type: 'success', 
        message: result.message 
      });
      
      if (result.all_accepted && result.job_id) {
        // 保存训练任务ID到localStorage
        localStorage.setItem('currentJobId', result.job_id);
        
        setAlert({ 
          type: 'success', 
          message: `所有参与方已同意！训练已开始，正在跳转到训练页面...` 
        });
        
        // 2秒后跳转到训练页面
        setTimeout(() => {
          navigate('/training');
        }, 2000);
      }
      
      // 刷新邀请列表
      await loadInvitations();
      await loadNotifications();
      
    } catch (error: any) {
      setAlert({ 
        type: 'error', 
        message: error.message || '响应邀请失败' 
      });
    } finally {
      setResponseLoading(null);
    }
  };

  const handleRefresh = async () => {
    setLoading(true);
    await Promise.all([loadInvitations(), loadNotifications()]);
    setLoading(false);
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN');
  };

  const getDisplayName = (username?: string, userId?: string) => {
    if (username && username !== 'Unknown' && username.trim() !== '') {
      return username;
    }
    if (userId) {
      // 尝试从常见的用户名模式推断
      if (userId.includes('hospital')) {
        const match = userId.match(/hospital[_-]?([a-zA-Z])/i);
        if (match) {
          return `医院${match[1].toUpperCase()}`;
        }
      }
      // 显示用户ID的后8位
      return `用户${userId.slice(-8)}`;
    }
    return '未知用户';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'warning';
      case 'accepted': return 'success';
      case 'completed': return 'success';
      case 'rejected': return 'error';
      default: return 'default';
    }
  };

  const getInvitationStatusLabel = (invitation: TrainingInvitation) => {
    // 如果用户已经响应，显示用户的响应状态
    if (invitation.user_response) {
      if (invitation.user_response === 'accepted') {
        // 如果用户接受了，进一步检查邀请状态
        if (invitation.status === 'completed') {
          return '训练已完成';
        } else if (invitation.status === 'accepted') {
          return '训练已开始';
        } else if (invitation.status === 'pending') {
          return '已接受，等待其他参与方';
        } else {
          return '已接受';
        }
      } else {
        return '已拒绝';
      }
    }
    
    // 如果用户还没有响应
    if (invitation.status === 'completed') {
      return '训练已完成';
    } else if (invitation.status === 'accepted') {
      return '训练已开始';
    } else if (invitation.status === 'rejected') {
      return '已被拒绝';
    } else {
      return '等待响应';
    }
  };

  const getInvitationStatusColor = (invitation: TrainingInvitation) => {
    if (invitation.user_response) {
      if (invitation.user_response === 'accepted') {
        if (invitation.status === 'completed') {
          return 'success'; // 训练已完成
        } else if (invitation.status === 'accepted') {
          return 'success'; // 训练已开始
        } else {
          return 'info'; // 已接受，等待其他参与方
        }
      } else {
        return 'error'; // 已拒绝
      }
    }
    
    if (invitation.status === 'completed') {
      return 'success'; // 训练已完成
    } else if (invitation.status === 'accepted') {
      return 'success';
    } else if (invitation.status === 'rejected') {
      return 'error';
    } else {
      return 'warning';
    }
  };

  const renderReceivedInvitations = () => (
    <Box>
      <Box display="flex" justifyContent="between" alignItems="center" mb={2}>
        <Typography variant="h6" gutterBottom>
          收到的训练邀请 ({invitations.received.length})
      </Typography>
        <Button
          startIcon={<Refresh />}
          onClick={handleRefresh}
          disabled={loading}
        >
          刷新
        </Button>
      </Box>

      {invitations.received.length === 0 ? (
        <Alert severity="info">暂无收到的训练邀请</Alert>
      ) : (
        <Grid container spacing={2}>
          {invitations.received.map((invitation) => (
            <Grid item xs={12} key={invitation.invitation_id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                    <Box>
                      <Typography variant="h6">
                        来自 {getDisplayName(invitation.from_username, invitation.from_user)} 的邀请
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {formatDateTime(invitation.created_at)}
                      </Typography>
                    </Box>
                    <Chip
                      label={getInvitationStatusLabel(invitation)}
                      color={getInvitationStatusColor(invitation) as any}
                      size="small"
                    />
                  </Box>

                  <Box mb={2}>
                    <Box display="flex" alignItems="center" gap={1} mb={1}>
                      {invitation.federation_type === 'horizontal' ? (
                        <Groups color="primary" />
                      ) : (
                        <TrendingUp color="primary" />
                      )}
                      <Typography variant="body1">
                        {invitation.federation_type === 'horizontal' ? '横向联邦学习' : '纵向联邦学习'}
                      </Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">
                      参与方数量: {invitation.to_users.length + 1}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      训练轮次: {invitation.job_info.total_rounds}
                    </Typography>
                  </Box>

                  {invitation.status === 'pending' && !invitation.user_response && (
                    <Box display="flex" gap={2}>
                    <Button
                      variant="contained"
                        color="success"
                        startIcon={<CheckCircle />}
                        onClick={() => handleRespondInvitation(invitation.invitation_id, 'accepted')}
                        disabled={responseLoading === invitation.invitation_id}
                    >
                        {responseLoading === invitation.invitation_id ? (
                          <CircularProgress size={20} />
                        ) : (
                          '接受'
                        )}
                    </Button>
                    <Button
                        variant="contained"
                      color="error"
                        startIcon={<Cancel />}
                        onClick={() => handleRespondInvitation(invitation.invitation_id, 'rejected')}
                        disabled={responseLoading === invitation.invitation_id}
                      >
                        拒绝
                      </Button>
                    </Box>
                  )}

                  {invitation.user_response && (
                    <>
                      <Alert 
                        severity={invitation.user_response === 'accepted' ? 'success' : 'error'}
                        sx={{ mt: 1 }}
                      >
                        您已{invitation.user_response === 'accepted' ? '接受' : '拒绝'}此邀请
                        {invitation.user_response === 'accepted' && (invitation.status === 'accepted' || invitation.status === 'completed') && 
                          ` - 训练已${invitation.status === 'completed' ? '完成' : '开始'}`}
                      </Alert>
                      
                      {/* 如果训练已完成，显示重新邀请按钮 */}
                      {invitation.user_response === 'accepted' && (invitation.status === 'accepted' || invitation.status === 'completed') && (
                        <Box display="flex" gap={2} mt={2}>
                          <Button
                            variant="outlined"
                            color="primary"
                            startIcon={<PlayArrow />}
                            onClick={() => handleReinviteForInvitation(invitation)}
                            disabled={reinviteLoading}
                            size="small"
                          >
                            {reinviteLoading ? '发送中...' : '重新邀请此合作方'}
                          </Button>
                          <Button
                            variant="contained"
                            color="primary"
                            onClick={() => navigate('/training')}
                            size="small"
                          >
                            查看训练结果
                          </Button>
                        </Box>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );

  const renderSentInvitations = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        发送的训练邀请 ({invitations.sent.length})
      </Typography>

      {invitations.sent.length === 0 ? (
        <Alert severity="info">暂无发送的训练邀请</Alert>
      ) : (
        <Grid container spacing={2}>
          {invitations.sent.map((invitation) => (
            <Grid item xs={12} key={invitation.invitation_id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                    <Box>
                      <Typography variant="h6">
                        {invitation.federation_type === 'horizontal' ? '横向' : '纵向'}联邦学习邀请
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {formatDateTime(invitation.created_at)}
                      </Typography>
                    </Box>
                    <Chip
                      label={invitation.status === 'pending' ? '等待响应' : 
                             invitation.status === 'accepted' ? '训练已开始' : 
                             invitation.status === 'completed' ? '训练已完成' : 
                             '已被拒绝'}
                      color={getStatusColor(invitation.status) as any}
                      size="small"
                    />
                  </Box>

                  <Typography variant="body2" sx={{ mb: 2 }}>
                    邀请了 {invitation.to_users.length} 个合作方参与训练
                  </Typography>

                  <Box display="flex" gap={2} mb={2}>
                    <Chip
                      label={`已接受: ${invitation.accepted_count || 0}`}
                      color="success"
                      size="small"
                    />
                    <Chip
                      label={`已拒绝: ${invitation.rejected_count || 0}`}
                      color="error"
                      size="small"
                    />
                    <Chip
                      label={`待响应: ${invitation.pending_count || 0}`}
                      color="warning"
                      size="small"
                    />
                  </Box>

                  {(invitation.status === 'accepted' || invitation.status === 'completed') && (
                    <>
                      <Alert severity="success">
                        所有参与方已同意，训练已{invitation.status === 'completed' ? '完成' : '开始'}！
                      </Alert>
                      <Box display="flex" gap={2} mt={2}>
                        <Button
                          variant="outlined"
                          color="primary"
                          startIcon={<PlayArrow />}
                          onClick={() => handleReinviteForInvitation(invitation)}
                          disabled={reinviteLoading}
                          size="small"
                        >
                          {reinviteLoading ? '发送中...' : '重新邀请相同合作方'}
                        </Button>
                        <Button
                          variant="contained"
                          color="primary"
                          onClick={() => navigate('/training')}
                          size="small"
                        >
                          查看训练结果
                        </Button>
                      </Box>
                    </>
                  )}

                  {invitation.status === 'rejected' && (
                    <>
                      <Alert severity="error">
                        有参与方拒绝，训练已取消
                      </Alert>
                      <Box display="flex" gap={2} mt={2}>
                        <Button
                          variant="outlined"
                          color="primary"
                          startIcon={<PlayArrow />}
                          onClick={() => handleReinviteForInvitation(invitation)}
                          disabled={reinviteLoading}
                          size="small"
                        >
                          {reinviteLoading ? '发送中...' : '重新发送邀请'}
                        </Button>
                      </Box>
                    </>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );

  const renderNotifications = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        系统通知 ({notifications.length})
      </Typography>

      {notifications.length === 0 ? (
        <Alert severity="info">暂无系统通知</Alert>
      ) : (
        <Grid container spacing={2}>
          {notifications.map((notification, index) => (
            <Grid item xs={12} key={notification.id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                    <Box>
                      <Typography variant="h6">
                        {notification.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {notification.message}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {formatDateTime(notification.timestamp)}
                      </Typography>
                    </Box>
                    <Chip
                      label={notification.type}
                      size="small"
                      variant="outlined"
                    />
                  </Box>

                                    {/* 根据通知类型显示操作按钮 */}
                  {notification.type === 'collaboration_match' && (
                    <Box display="flex" gap={2} mt={2}>
                      <Button
                        variant="contained"
                        color="primary"
                        startIcon={<Groups />}
                        onClick={() => navigate('/intent-upload?action=view-collaborators')}
                        size="small"
                      >
                        查看合作方
                      </Button>
                      <Button
                        variant="outlined"
                        color="secondary"
                        startIcon={<PlayArrow />}
                        onClick={handleReinvitePreviousCollaborators}
                        disabled={reinviteLoading}
                        size="small"
                      >
                        {reinviteLoading ? <CircularProgress size={16} /> : '重新发送邀请'}
                      </Button>
                      {notification.data?.match_count && (
                        <Chip
                          label={`${notification.data.match_count} 个潜在合作方`}
                          color="success"
                          size="small"
                        />
                      )}
                    </Box>
                  )}

                  {notification.type === 'collaboration_opportunity' && (
                    <Box display="flex" gap={2} mt={2}>
                      <Button
                        variant="contained"
                        color="primary"
                        startIcon={<Groups />}
                        onClick={() => navigate('/intent-upload?action=view-collaborators')}
                        size="small"
                      >
                        查看合作方
                      </Button>
                      <Button
                        variant="outlined"
                        color="secondary"
                        startIcon={<PlayArrow />}
                        onClick={handleReinvitePreviousCollaborators}
                        disabled={reinviteLoading}
                        size="small"
                      >
                        {reinviteLoading ? <CircularProgress size={16} /> : '重新发送邀请'}
                      </Button>
                      {notification.data?.matches && notification.data.matches.length > 0 && (
                        <Chip
                          label={`${notification.data.matches.length} 个合作方`}
                          color="success"
                          size="small"
                        />
                      )}
                  </Box>
                )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );

  // 重新邀请特定邀请的合作方
  const handleReinviteForInvitation = async (invitation: TrainingInvitation) => {
    if (!user?.user_id) return;
    
    setReinviteLoading(true);
    try {
      let collaboratorIds: string[] = [];
      
      // 如果是收到的邀请，重新邀请发送方
      if (invitation.from_user !== user.user_id) {
        collaboratorIds = [invitation.from_user];
      } else {
        // 如果是发送的邀请，重新邀请之前的接收方
        collaboratorIds = invitation.to_users;
      }
      
      if (collaboratorIds.length === 0) {
        setAlert({ type: 'error', message: '没有找到可以重新邀请的合作方' });
        return;
      }

      // 发送重新邀请
      const result = await apiService.startTraining({
        user_id: user.user_id,
        collaborator_ids: collaboratorIds,
        federation_type: invitation.federation_type,
        total_rounds: invitation.job_info.total_rounds || 10,
      });

      setAlert({ 
        type: 'success', 
        message: `重新邀请已发送给 ${collaboratorIds.length} 个合作方` 
      });
      
      // 刷新邀请列表
      await loadInvitations();
      await loadNotifications();

    } catch (error: any) {
      console.error('重新发送邀请失败:', error);
      setAlert({ 
        type: 'error', 
        message: error.message || '重新发送邀请失败，请稍后重试' 
      });
    } finally {
      setReinviteLoading(false);
    }
  };

  // 重新邀请之前的合作方（通用版本，用于系统通知）
  const handleReinvitePreviousCollaborators = async () => {
    if (!user?.user_id) return;
    
    setReinviteLoading(true);
    try {
      // 获取之前的合作方列表
      const response = await apiService.getTrainingInvitations(user.user_id);
      const previousCollaborators = new Set<string>();
      
      // 从发送的邀请中提取
      response.sent_invitations.forEach(invitation => {
        if (invitation.status === 'accepted') {
          invitation.to_users.forEach(userId => previousCollaborators.add(userId));
        }
      });
      
      // 从收到的邀请中提取
      response.received_invitations.forEach(invitation => {
        if (invitation.user_response === 'accepted') {
          previousCollaborators.add(invitation.from_user);
        }
      });
      
      const collaboratorIds = Array.from(previousCollaborators);
      
      if (collaboratorIds.length === 0) {
        setAlert({ type: 'error', message: '没有找到之前的合作方' });
        return;
      }

      // 发送重新邀请
      const result = await apiService.startTraining({
        user_id: user.user_id,
        collaborator_ids: collaboratorIds,
        federation_type: 'vertical', // 默认使用vertical
        total_rounds: 10,
      });

      setAlert({ 
        type: 'success', 
        message: `重新邀请已发送给 ${collaboratorIds.length} 个之前的合作方` 
      });
      
      // 刷新邀请列表
      await loadInvitations();
      await loadNotifications();

    } catch (error: any) {
      console.error('重新发送邀请失败:', error);
      setAlert({ 
        type: 'error', 
        message: error.message || '重新发送邀请失败，请稍后重试' 
      });
    } finally {
      setReinviteLoading(false);
    }
  };

  if (!user) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="error">请先登录</Alert>
      </Container>
    );
  }

  const totalPendingInvitations = invitations.received.filter(inv => 
    inv.status === 'pending' && !inv.user_response
  ).length;

  return (
    <Box>
      <AppNavBar user={user} onLogout={onLogout} title="通知中心" />
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Paper sx={{ p: 4 }}>
        <Box display="flex" alignItems="center" mb={3}>
          <NotificationsIcon sx={{ mr: 2, fontSize: 32 }} />
          <Typography variant="h4" component="h1">
            通知中心
          </Typography>
          {totalPendingInvitations > 0 && (
            <Badge badgeContent={totalPendingInvitations} color="error" sx={{ ml: 2 }}>
              <Person />
            </Badge>
          )}
        </Box>

        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          管理您的训练邀请和系统通知
        </Typography>

        {alert && (
          <Alert 
            severity={alert.type} 
            sx={{ mb: 3 }}
            onClose={() => setAlert(null)}
          >
            {alert.message}
          </Alert>
        )}

        <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
          <Tab 
            label={
              <Box display="flex" alignItems="center" gap={1}>
                收到的邀请
                {totalPendingInvitations > 0 && (
                  <Badge badgeContent={totalPendingInvitations} color="error" />
                )}
              </Box>
            } 
          />
          <Tab label="发送的邀请" />
          <Tab label="系统通知" />
        </Tabs>

        {activeTab === 0 && renderReceivedInvitations()}
        {activeTab === 1 && renderSentInvitations()}
        {activeTab === 2 && renderNotifications()}
      </Paper>
    </Container>
    </Box>
  );
};

export default Notifications; 
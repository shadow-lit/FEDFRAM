import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  AppBar,
  Toolbar,
  Avatar,
  Button,
  IconButton,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  CloudUpload,
  Notifications,
  PlayArrow,
  Storage,
  Logout,
  AccountCircle,
} from '@mui/icons-material';
import { User } from '../services/api';

interface HomeProps {
  user: User | null;
  onLogout: () => void;
}

const Home: React.FC<HomeProps> = ({ user, onLogout }) => {
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleUserMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleCloseUserMenu = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    onLogout();
    navigate('/login');
  };

  const menuItems = [
    {
      title: '参与意愿上传',
      description: '上传您的参与意愿和数据信息',
      icon: <CloudUpload />,
      path: '/intent-upload',
    },
    {
      title: '消息通知',
      description: '查看联邦学习邀请和通知',
      icon: <Notifications />,
      path: '/notifications',
    },
    {
      title: '训练过程',
      description: '查看当前训练进度',
      icon: <PlayArrow />,
      path: '/training',
    },
    {
      title: '模型库',
      description: '浏览和下载训练完成的模型',
      icon: <Storage />,
      path: '/model-library',
    },
  ];

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            联邦学习平台
          </Typography>
          
          {user && (
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Typography variant="body2" sx={{ mr: 2 }}>
                欢迎，{user.username}！
              </Typography>
              <IconButton
                size="large"
                onClick={handleUserMenu}
                color="inherit"
              >
                <Avatar 
                  src={user.profile.avatar} 
                  alt={user.username}
                  sx={{ width: 32, height: 32 }}
                >
                  <AccountCircle />
                </Avatar>
              </IconButton>
              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleCloseUserMenu}
              >
                <MenuItem onClick={handleCloseUserMenu}>
                  <Typography variant="body2" color="text.secondary">
                    {user.email}
                  </Typography>
                </MenuItem>
                <MenuItem onClick={handleLogout}>
                  <Logout sx={{ mr: 1 }} />
                  登出
                </MenuItem>
              </Menu>
            </Box>
          )}
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" gutterBottom component="h1">
          欢迎使用联邦学习系统
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          选择下面的功能开始您的联邦学习之旅
        </Typography>
        
        <Grid container spacing={3}>
          {menuItems.map((item) => (
            <Grid item xs={12} sm={6} md={3} key={item.path}>
              <Paper
                sx={{
                  p: 3,
                  display: 'flex',
                  flexDirection: 'column',
                  height: 200,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  '&:hover': {
                    backgroundColor: 'rgba(0, 0, 0, 0.04)',
                    transform: 'translateY(-4px)',
                    boxShadow: 4,
                  },
                }}
                onClick={() => navigate(item.path)}
              >
                <Box
                  sx={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    flex: 1,
                  }}
                >
                  {React.cloneElement(item.icon, { 
                    sx: { fontSize: 48, mb: 2, color: 'primary.main' } 
                  })}
                  <Typography variant="h6" gutterBottom align="center">
                    {item.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" align="center">
                    {item.description}
                  </Typography>
                </Box>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
};

export default Home; 
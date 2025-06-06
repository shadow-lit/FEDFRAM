import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  IconButton,
  Avatar,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  AccountCircle,
  Logout,
  Home as HomeIcon,
} from '@mui/icons-material';
import { User } from '../services/api';

interface AppNavBarProps {
  user: User | null;
  onLogout: () => void;
  title?: string;
}

const AppNavBar: React.FC<AppNavBarProps> = ({ user, onLogout, title = '联邦学习平台' }) => {
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
    handleCloseUserMenu();
    navigate('/login');
  };

  const handleGoHome = () => {
    navigate('/home');
    handleCloseUserMenu();
  };

  return (
    <AppBar position="static">
      <Toolbar>
        <IconButton
          color="inherit"
          onClick={handleGoHome}
          sx={{ mr: 2 }}
        >
          <HomeIcon />
        </IconButton>
        
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          {title}
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
                src={user.profile?.avatar} 
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
              <MenuItem onClick={handleGoHome}>
                <HomeIcon sx={{ mr: 1 }} />
                返回主页
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
  );
};

export default AppNavBar; 
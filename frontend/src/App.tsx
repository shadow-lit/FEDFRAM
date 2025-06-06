import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material';
import CssBaseline from '@mui/material/CssBaseline';
import Login from './pages/Login';
import Home from './pages/Home';
import IntentUpload from './pages/IntentUpload';
import Notifications from './pages/Notifications';
import Training from './pages/Training';
import ModelLibrary from './pages/ModelLibrary';
import { apiService, type User } from './services/api';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

// 路由守卫组件
const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = localStorage.getItem('authToken');
  return token ? <>{children}</> : <Navigate to="/login" />;
};

const App: React.FC = () => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 检查是否有有效的认证token
    const checkAuth = async () => {
      const token = localStorage.getItem('authToken');
      if (token) {
        try {
          const response = await apiService.getProfile();
          setUser(response.user);
        } catch (error) {
          // Token无效，清除本地存储
          localStorage.removeItem('authToken');
          apiService.removeToken();
        }
      }
      setLoading(false);
    };

    checkAuth();
  }, []);

  const handleLogin = (userData: User, token: string) => {
    setUser(userData);
    apiService.setToken(token);
  };

  const handleLogout = () => {
    setUser(null);
    apiService.removeToken();
  };

  if (loading) {
    return <div>加载中...</div>;
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route 
            path="/login" 
            element={
              user ? <Navigate to="/home" /> : <Login onLogin={handleLogin} />
            } 
          />
          <Route 
            path="/home" 
            element={
              <PrivateRoute>
                <Home user={user} onLogout={handleLogout} />
              </PrivateRoute>
            } 
          />
          <Route 
            path="/intent-upload" 
            element={
              <PrivateRoute>
                <IntentUpload user={user} onLogout={handleLogout} />
              </PrivateRoute>
            } 
          />
          <Route 
            path="/notifications" 
            element={
              <PrivateRoute>
                <Notifications user={user} onLogout={handleLogout} />
              </PrivateRoute>
            } 
          />
          <Route 
            path="/training" 
            element={
              <PrivateRoute>
                <Training user={user} onLogout={handleLogout} />
              </PrivateRoute>
            } 
          />
          <Route 
            path="/model-library" 
            element={
              <PrivateRoute>
                <ModelLibrary user={user} onLogout={handleLogout} />
              </PrivateRoute>
            } 
          />
          <Route
            path="/"
            element={
              user ? <Navigate to="/home" /> : <Navigate to="/login" />
            }
          />
        </Routes>
      </Router>
    </ThemeProvider>
  );
};

export default App;

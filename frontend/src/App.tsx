import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Typography } from '@mui/material';
import Login from './pages/Login';
import Conversations from './pages/Conversations';
import Contacts from './pages/Contacts';
import Campaigns from './pages/Campaigns';
import Quotations from './pages/Quotations';
import QuotationForm from './pages/QuotationForm';
import QuotationView from './pages/QuotationView';
import Layout from './components/Layout';
import authService from './services/auth.service';

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

const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuth = authService.isAuthenticated();
  return isAuth ? <>{children}</> : <Navigate to="/login" />;
};

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <PrivateRoute>
                <Layout>
                  <Conversations />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/contacts"
            element={
              <PrivateRoute>
                <Layout>
                  <Contacts />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/campaigns"
            element={
              <PrivateRoute>
                <Layout>
                  <Campaigns />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/quotations"
            element={
              <PrivateRoute>
                <Layout>
                  <Quotations />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/quotations/new"
            element={
              <PrivateRoute>
                <Layout>
                  <QuotationForm />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/quotations/:id"
            element={
              <PrivateRoute>
                <Layout>
                  <QuotationView />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/quotations/:id/edit"
            element={
              <PrivateRoute>
                <Layout>
                  <QuotationForm />
                </Layout>
              </PrivateRoute>
            }
          />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
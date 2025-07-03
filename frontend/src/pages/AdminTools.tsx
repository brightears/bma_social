import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import {
  Sync as SyncIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import api from '../services/api';

interface TableInfo {
  schema: string;
  table: string;
  size: string;
  row_count: number;
}

const AdminTools: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [syncResult, setSyncResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [tables, setTables] = useState<TableInfo[]>([]);
  const [loadingInfo, setLoadingInfo] = useState(false);

  const syncDatabase = async () => {
    try {
      setLoading(true);
      setError(null);
      setSyncResult(null);
      
      const response = await api.post('/admin/sync-database');
      setSyncResult(response.data);
      
      // Refresh table info after sync
      await loadDatabaseInfo();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to sync database');
    } finally {
      setLoading(false);
    }
  };

  const loadDatabaseInfo = async () => {
    try {
      setLoadingInfo(true);
      setError(null);
      
      const response = await api.get('/admin/database-info');
      setTables(response.data.tables);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load database info');
    } finally {
      setLoadingInfo(false);
    }
  };

  React.useEffect(() => {
    loadDatabaseInfo();
  }, []);

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>Admin Tools</Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {syncResult && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSyncResult(null)}>
          <Typography variant="subtitle2">{syncResult.message}</Typography>
          <Typography variant="body2">
            Tables: {syncResult.tables.join(', ')}
          </Typography>
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Database Sync</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          This will create any missing database tables. Use this after deploying new features that require database changes.
        </Typography>
        <Button
          variant="contained"
          startIcon={loading ? <CircularProgress size={20} /> : <SyncIcon />}
          onClick={syncDatabase}
          disabled={loading}
        >
          {loading ? 'Syncing...' : 'Sync Database'}
        </Button>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Database Tables</Typography>
          <Button
            startIcon={<InfoIcon />}
            onClick={loadDatabaseInfo}
            disabled={loadingInfo}
          >
            Refresh
          </Button>
        </Box>
        
        {loadingInfo ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Table Name</TableCell>
                  <TableCell align="right">Rows</TableCell>
                  <TableCell align="right">Size</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {tables.map((table) => (
                  <TableRow key={table.table}>
                    <TableCell>{table.table}</TableCell>
                    <TableCell align="right">{table.row_count.toLocaleString()}</TableCell>
                    <TableCell align="right">{table.size}</TableCell>
                  </TableRow>
                ))}
                {tables.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={3} align="center">
                      <Typography color="text.secondary" sx={{ py: 2 }}>
                        No tables found
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
    </Box>
  );
};

export default AdminTools;
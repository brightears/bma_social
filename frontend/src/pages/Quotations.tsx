import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  CircularProgress,
  Alert,
  Tooltip,
  Menu,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Send as SendIcon,
  Download as DownloadIcon,
  MoreVert as MoreVertIcon,
  Visibility as ViewIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import quotationService, { Quotation } from '../services/quotation.service';

const Quotations: React.FC = () => {
  const navigate = useNavigate();
  const [quotations, setQuotations] = useState<Quotation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedQuotation, setSelectedQuotation] = useState<Quotation | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [sendDialogOpen, setSendDialogOpen] = useState(false);
  const [sendChannel, setSendChannel] = useState<'whatsapp' | 'line' | 'email'>('whatsapp');
  const [sendMessage, setSendMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  useEffect(() => {
    loadQuotations();
  }, []);

  const loadQuotations = async () => {
    try {
      setLoading(true);
      const data = await quotationService.getQuotations();
      setQuotations(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load quotations');
    } finally {
      setLoading(false);
    }
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, quotation: Quotation) => {
    setAnchorEl(event.currentTarget);
    setSelectedQuotation(quotation);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleDownloadPDF = async () => {
    if (!selectedQuotation) return;
    
    try {
      const blob = await quotationService.downloadPDF(selectedQuotation.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `quotation_${selectedQuotation.quote_number}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || 'Failed to download PDF');
    }
    handleMenuClose();
  };

  const handleSendQuotation = async () => {
    if (!selectedQuotation) return;
    
    try {
      setSending(true);
      await quotationService.sendQuotation(selectedQuotation.id, {
        channel: sendChannel,
        message: sendMessage || undefined,
      });
      await loadQuotations(); // Reload to get updated status
      setSendDialogOpen(false);
      setSendMessage('');
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to send quotation');
    } finally {
      setSending(false);
    }
  };

  const handleDeleteQuotation = async () => {
    if (!selectedQuotation) return;
    
    try {
      await quotationService.deleteQuotation(selectedQuotation.id);
      await loadQuotations();
      setDeleteDialogOpen(false);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to delete quotation');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft':
        return 'default';
      case 'sent':
        return 'primary';
      case 'viewed':
        return 'info';
      case 'accepted':
        return 'success';
      case 'rejected':
        return 'error';
      case 'expired':
        return 'warning';
      default:
        return 'default';
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('th-TH', {
      style: 'currency',
      currency: 'THB',
    }).format(amount);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Quotations</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/quotations/new')}
        >
          New Quotation
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Quote #</TableCell>
                <TableCell>Customer</TableCell>
                <TableCell>Title</TableCell>
                <TableCell align="right">Amount</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {quotations.map((quotation) => (
                <TableRow key={quotation.id}>
                  <TableCell>{quotation.quote_number}</TableCell>
                  <TableCell>
                    <Box>
                      <Typography variant="body2">{quotation.customer_name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {quotation.customer_phone}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>{quotation.title}</TableCell>
                  <TableCell align="right">{formatCurrency(quotation.total_amount)}</TableCell>
                  <TableCell>
                    <Chip
                      label={quotation.status.toUpperCase()}
                      color={getStatusColor(quotation.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{format(new Date(quotation.created_at), 'MMM d, yyyy')}</TableCell>
                  <TableCell align="center">
                    <IconButton onClick={(e) => handleMenuClick(e, quotation)}>
                      <MoreVertIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
              {quotations.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography color="text.secondary" sx={{ py: 3 }}>
                      No quotations found. Create your first quotation!
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        )}
      </TableContainer>

      {/* Actions Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => {
          navigate(`/quotations/${selectedQuotation?.id}`);
          handleMenuClose();
        }}>
          <ViewIcon sx={{ mr: 1 }} /> View
        </MenuItem>
        {selectedQuotation?.status === 'draft' && (
          <MenuItem onClick={() => {
            navigate(`/quotations/${selectedQuotation?.id}/edit`);
            handleMenuClose();
          }}>
            <EditIcon sx={{ mr: 1 }} /> Edit
          </MenuItem>
        )}
        <MenuItem onClick={handleDownloadPDF}>
          <DownloadIcon sx={{ mr: 1 }} /> Download PDF
        </MenuItem>
        <MenuItem onClick={() => {
          setSendDialogOpen(true);
          handleMenuClose();
        }}>
          <SendIcon sx={{ mr: 1 }} /> Send
        </MenuItem>
        {selectedQuotation?.status === 'draft' && (
          <MenuItem onClick={() => {
            setDeleteDialogOpen(true);
            handleMenuClose();
          }}>
            <DeleteIcon sx={{ mr: 1 }} /> Delete
          </MenuItem>
        )}
      </Menu>

      {/* Send Dialog */}
      <Dialog open={sendDialogOpen} onClose={() => setSendDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Send Quotation</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              select
              fullWidth
              label="Channel"
              value={sendChannel}
              onChange={(e) => setSendChannel(e.target.value as 'whatsapp' | 'line' | 'email')}
              sx={{ mb: 2 }}
            >
              <MenuItem value="whatsapp">WhatsApp</MenuItem>
              <MenuItem value="line" disabled>LINE (Coming Soon)</MenuItem>
              <MenuItem value="email" disabled>Email (Coming Soon)</MenuItem>
            </TextField>
            <TextField
              fullWidth
              multiline
              rows={4}
              label="Custom Message (Optional)"
              value={sendMessage}
              onChange={(e) => setSendMessage(e.target.value)}
              placeholder="Leave empty to use default message"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSendDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSendQuotation}
            variant="contained"
            disabled={sending}
            startIcon={sending ? <CircularProgress size={20} /> : <SendIcon />}
          >
            Send
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Quotation</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete quotation {selectedQuotation?.quote_number}?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDeleteQuotation} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Quotations;
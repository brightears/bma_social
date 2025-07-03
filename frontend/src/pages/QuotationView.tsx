import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
  Divider,
} from '@mui/material';
import {
  Download as DownloadIcon,
  Send as SendIcon,
  Edit as EditIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { format } from 'date-fns';
import quotationService, { Quotation } from '../services/quotation.service';

const QuotationView: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const [quotation, setQuotation] = useState<Quotation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadQuotation(id);
    }
  }, [id]);

  const loadQuotation = async (quotationId: string) => {
    try {
      setLoading(true);
      const data = await quotationService.getQuotation(quotationId);
      setQuotation(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load quotation');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async () => {
    if (!quotation) return;
    
    try {
      const blob = await quotationService.downloadPDF(quotation.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `quotation_${quotation.quote_number}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setError(err.message || 'Failed to download PDF');
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

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!quotation) {
    return (
      <Box>
        <Alert severity="error">Quotation not found</Alert>
        <Button onClick={() => navigate('/quotations')} sx={{ mt: 2 }}>
          Back to Quotations
        </Button>
      </Box>
    );
  }

  const validUntil = new Date(quotation.created_at);
  validUntil.setDate(validUntil.getDate() + quotation.validity_days);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/quotations')}
          >
            Back
          </Button>
          <Typography variant="h4">Quotation {quotation.quote_number}</Typography>
          <Chip
            label={quotation.status.toUpperCase()}
            color={getStatusColor(quotation.status)}
          />
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {quotation.status === 'draft' && (
            <Button
              variant="outlined"
              startIcon={<EditIcon />}
              onClick={() => navigate(`/quotations/${quotation.id}/edit`)}
            >
              Edit
            </Button>
          )}
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleDownloadPDF}
          >
            Download PDF
          </Button>
          <Button
            variant="contained"
            startIcon={<SendIcon />}
            onClick={() => navigate(`/quotations/${quotation.id}/send`)}
          >
            Send
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Quotation Info */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Quotation Information</Typography>
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell component="th">Quote Number</TableCell>
                  <TableCell>{quotation.quote_number}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell component="th">Date</TableCell>
                  <TableCell>{format(new Date(quotation.created_at), 'MMM d, yyyy')}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell component="th">Valid Until</TableCell>
                  <TableCell>{format(validUntil, 'MMM d, yyyy')}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell component="th">Created By</TableCell>
                  <TableCell>{quotation.created_by_name}</TableCell>
                </TableRow>
                {quotation.sent_at && (
                  <TableRow>
                    <TableCell component="th">Sent At</TableCell>
                    <TableCell>{format(new Date(quotation.sent_at), 'MMM d, yyyy HH:mm')}</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Paper>
        </Grid>

        {/* Customer Info */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" sx={{ mb: 2 }}>Customer Information</Typography>
            <Table size="small">
              <TableBody>
                <TableRow>
                  <TableCell component="th">Name</TableCell>
                  <TableCell>{quotation.customer_name}</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell component="th">Phone</TableCell>
                  <TableCell>{quotation.customer_phone}</TableCell>
                </TableRow>
                {quotation.customer_email && (
                  <TableRow>
                    <TableCell component="th">Email</TableCell>
                    <TableCell>{quotation.customer_email}</TableCell>
                  </TableRow>
                )}
                {quotation.company_name && (
                  <TableRow>
                    <TableCell component="th">Company</TableCell>
                    <TableCell>{quotation.company_name}</TableCell>
                  </TableRow>
                )}
                {quotation.company_tax_id && (
                  <TableRow>
                    <TableCell component="th">Tax ID</TableCell>
                    <TableCell>{quotation.company_tax_id}</TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Paper>
        </Grid>

        {/* Items */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 2 }}>{quotation.title}</Typography>
            {quotation.description && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {quotation.description}
              </Typography>
            )}
            
            <TableContainer>
              <Table>
                <TableBody>
                  {quotation.items.map((item, index) => (
                    <TableRow key={index}>
                      <TableCell>{item.description}</TableCell>
                      <TableCell align="right" sx={{ width: 100 }}>{item.quantity}</TableCell>
                      <TableCell align="right" sx={{ width: 150 }}>{formatCurrency(item.unit_price)}</TableCell>
                      <TableCell align="right" sx={{ width: 150 }}>{formatCurrency(item.total)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <Box sx={{ mt: 3 }}>
              <Grid container>
                <Grid item xs={12} md={6}>
                  {quotation.notes && (
                    <Box>
                      <Typography variant="subtitle2">Notes:</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {quotation.notes}
                      </Typography>
                    </Box>
                  )}
                </Grid>
                <Grid item xs={12} md={6}>
                  <Box sx={{ textAlign: 'right' }}>
                    <Typography variant="body2">Subtotal: {formatCurrency(quotation.subtotal)}</Typography>
                    {quotation.discount_amount > 0 && (
                      <Typography variant="body2" color="error">
                        Discount ({quotation.discount_percent}%): -{formatCurrency(quotation.discount_amount)}
                      </Typography>
                    )}
                    <Typography variant="body2">
                      Tax ({quotation.tax_percent}%): {formatCurrency(quotation.tax_amount)}
                    </Typography>
                    <Divider sx={{ my: 1 }} />
                    <Typography variant="h5">Total: {formatCurrency(quotation.total_amount)}</Typography>
                  </Box>
                </Grid>
              </Grid>
            </Box>

            <Box sx={{ mt: 3, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
              <Typography variant="subtitle2">Payment Terms:</Typography>
              <Typography variant="body2">{quotation.payment_terms}</Typography>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default QuotationView;
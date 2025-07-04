import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Autocomplete,
  Alert,
  CircularProgress,
  Divider,
  MenuItem,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import quotationService, { QuotationCreate, QuotationItem, Quotation } from '../services/quotation.service';
import contactService, { Contact } from '../services/contact.service';

const QuotationForm: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);
  
  const [formData, setFormData] = useState({
    customer_id: '',
    company_name: '',
    company_address: '',
    company_tax_id: '',
    title: '',
    description: '',
    items: [] as QuotationItem[],
    currency: 'THB',
    discount_percent: 0,
    tax_percent: 7,
    payment_terms: '50% deposit, 50% on completion',
    validity_days: 30,
    notes: '',
  });

  const [newItem, setNewItem] = useState({
    description: '',
    quantity: 1,
    unit_price: 0,
  });

  useEffect(() => {
    loadContacts();
    if (isEdit && id) {
      loadQuotation(id);
    }
  }, [id, isEdit]);

  const loadContacts = async () => {
    try {
      const data = await contactService.getContacts();
      setContacts(data);
    } catch (err: any) {
      setError('Failed to load contacts');
    }
  };

  const loadQuotation = async (quotationId: string) => {
    try {
      setLoading(true);
      const quotation = await quotationService.getQuotation(quotationId);
      
      if (quotation.status !== 'draft') {
        setError('Can only edit draft quotations');
        return;
      }

      const contact = contacts.find(c => c.id === quotation.customer_id);
      setSelectedContact(contact || null);
      
      setFormData({
        customer_id: quotation.customer_id,
        company_name: quotation.company_name || '',
        company_address: quotation.company_address || '',
        company_tax_id: quotation.company_tax_id || '',
        title: quotation.title,
        description: quotation.description || '',
        items: quotation.items,
        currency: quotation.currency || 'THB',
        discount_percent: quotation.discount_percent,
        tax_percent: quotation.tax_percent,
        payment_terms: quotation.payment_terms,
        validity_days: quotation.validity_days,
        notes: quotation.notes || '',
      });
    } catch (err: any) {
      setError(err.message || 'Failed to load quotation');
    } finally {
      setLoading(false);
    }
  };

  const handleContactChange = (contact: Contact | null) => {
    setSelectedContact(contact);
    if (contact) {
      setFormData(prev => ({
        ...prev,
        customer_id: contact.id,
      }));
    }
  };

  const handleAddItem = () => {
    if (newItem.description && newItem.unit_price > 0) {
      const total = newItem.quantity * newItem.unit_price;
      setFormData(prev => ({
        ...prev,
        items: [...prev.items, { ...newItem, total }],
      }));
      setNewItem({ description: '', quantity: 1, unit_price: 0 });
    }
  };

  const handleRemoveItem = (index: number) => {
    setFormData(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index),
    }));
  };

  const calculateTotals = () => {
    const subtotal = formData.items.reduce((sum, item) => sum + item.total, 0);
    const discountAmount = subtotal * (formData.discount_percent / 100);
    const afterDiscount = subtotal - discountAmount;
    const taxAmount = afterDiscount * (formData.tax_percent / 100);
    const total = afterDiscount + taxAmount;
    
    return { subtotal, discountAmount, taxAmount, total };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedContact) {
      setError('Please select a customer');
      return;
    }
    
    if (formData.items.length === 0) {
      setError('Please add at least one item');
      return;
    }

    try {
      setSaving(true);
      setError(null);

      const data: QuotationCreate = {
        ...formData,
        customer_id: selectedContact.id,
      };

      if (isEdit && id) {
        await quotationService.updateQuotation(id, data);
      } else {
        await quotationService.createQuotation(data);
      }

      navigate('/quotations');
    } catch (err: any) {
      setError(err.message || 'Failed to save quotation');
    } finally {
      setSaving(false);
    }
  };

  const totals = calculateTotals();

  const formatCurrency = (amount: number) => {
    const currency = formData.currency || 'THB';
    return new Intl.NumberFormat(currency === 'THB' ? 'th-TH' : 'en-US', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3 }}>
        {isEdit ? 'Edit Quotation' : 'New Quotation'}
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <Grid container spacing={3}>
          {/* Customer Information */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>Customer Information</Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Autocomplete
                    options={contacts}
                    getOptionLabel={(option) => `${option.name} - ${option.phone}`}
                    value={selectedContact}
                    onChange={(_, value) => handleContactChange(value)}
                    renderInput={(params) => (
                      <TextField {...params} label="Select Customer" required />
                    )}
                    disabled={isEdit}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Company Name"
                    value={formData.company_name}
                    onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Company Address"
                    multiline
                    rows={2}
                    value={formData.company_address}
                    onChange={(e) => setFormData({ ...formData, company_address: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Company Tax ID"
                    value={formData.company_tax_id}
                    onChange={(e) => setFormData({ ...formData, company_tax_id: e.target.value })}
                  />
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          {/* Quotation Details */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>Quotation Details</Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={8}>
                  <TextField
                    fullWidth
                    label="Title"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    required
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    select
                    fullWidth
                    label="Currency"
                    value={formData.currency}
                    onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                  >
                    <MenuItem value="THB">THB (฿)</MenuItem>
                    <MenuItem value="USD">USD ($)</MenuItem>
                  </TextField>
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Description"
                    multiline
                    rows={2}
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          {/* Items */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>Items</Typography>
              
              <Box sx={{ mb: 2 }}>
                <Grid container spacing={2} alignItems="flex-end">
                  <Grid item xs={12} md={6}>
                    <TextField
                      fullWidth
                      label="Description"
                      value={newItem.description}
                      onChange={(e) => setNewItem({ ...newItem, description: e.target.value })}
                    />
                  </Grid>
                  <Grid item xs={6} md={2}>
                    <TextField
                      fullWidth
                      label="Quantity"
                      type="number"
                      value={newItem.quantity}
                      onChange={(e) => setNewItem({ ...newItem, quantity: parseInt(e.target.value) || 1 })}
                      inputProps={{ min: 1 }}
                    />
                  </Grid>
                  <Grid item xs={6} md={2}>
                    <TextField
                      fullWidth
                      label="Unit Price"
                      type="number"
                      value={newItem.unit_price}
                      onChange={(e) => setNewItem({ ...newItem, unit_price: parseFloat(e.target.value) || 0 })}
                      inputProps={{ min: 0, step: 0.01 }}
                    />
                  </Grid>
                  <Grid item xs={12} md={2}>
                    <Button
                      fullWidth
                      variant="contained"
                      startIcon={<AddIcon />}
                      onClick={handleAddItem}
                    >
                      Add Item
                    </Button>
                  </Grid>
                </Grid>
              </Box>

              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Description</TableCell>
                      <TableCell align="right">Quantity</TableCell>
                      <TableCell align="right">Unit Price</TableCell>
                      <TableCell align="right">Total</TableCell>
                      <TableCell align="center">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {formData.items.map((item, index) => (
                      <TableRow key={index}>
                        <TableCell>{item.description}</TableCell>
                        <TableCell align="right">{item.quantity}</TableCell>
                        <TableCell align="right">{formatCurrency(item.unit_price)}</TableCell>
                        <TableCell align="right">{formatCurrency(item.total)}</TableCell>
                        <TableCell align="center">
                          <IconButton
                            size="small"
                            onClick={() => handleRemoveItem(index)}
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                    {formData.items.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} align="center">
                          <Typography color="text.secondary" sx={{ py: 2 }}>
                            No items added yet
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>

              {/* Totals */}
              <Box sx={{ mt: 3 }}>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <TextField
                          fullWidth
                          label="Discount %"
                          type="number"
                          value={formData.discount_percent}
                          onChange={(e) => setFormData({ ...formData, discount_percent: parseFloat(e.target.value) || 0 })}
                          inputProps={{ min: 0, max: 100, step: 0.01 }}
                        />
                      </Grid>
                      <Grid item xs={6}>
                        <TextField
                          fullWidth
                          label="Tax %"
                          type="number"
                          value={formData.tax_percent}
                          onChange={(e) => setFormData({ ...formData, tax_percent: parseFloat(e.target.value) || 0 })}
                          inputProps={{ min: 0, max: 100, step: 0.01 }}
                        />
                      </Grid>
                    </Grid>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Box sx={{ textAlign: 'right' }}>
                      <Typography variant="body2">Subtotal: {formatCurrency(totals.subtotal)}</Typography>
                      {totals.discountAmount > 0 && (
                        <Typography variant="body2" color="error">
                          Discount: -{formatCurrency(totals.discountAmount)}
                        </Typography>
                      )}
                      <Typography variant="body2">Tax: {formatCurrency(totals.taxAmount)}</Typography>
                      <Divider sx={{ my: 1 }} />
                      <Typography variant="h6">Total: {formatCurrency(totals.total)}</Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Box>
            </Paper>
          </Grid>

          {/* Additional Information */}
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" sx={{ mb: 2 }}>Additional Information</Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Payment Terms"
                    value={formData.payment_terms}
                    onChange={(e) => setFormData({ ...formData, payment_terms: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Validity (Days)"
                    type="number"
                    value={formData.validity_days}
                    onChange={(e) => setFormData({ ...formData, validity_days: parseInt(e.target.value) || 30 })}
                    inputProps={{ min: 1 }}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Notes"
                    multiline
                    rows={3}
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  />
                </Grid>
              </Grid>
            </Paper>
          </Grid>

          {/* Actions */}
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              <Button
                variant="outlined"
                startIcon={<CancelIcon />}
                onClick={() => navigate('/quotations')}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                startIcon={<SaveIcon />}
                disabled={saving}
              >
                {saving ? 'Saving...' : (isEdit ? 'Update' : 'Create')} Quotation
              </Button>
            </Box>
          </Grid>
        </Grid>
      </form>
    </Box>
  );
};

export default QuotationForm;
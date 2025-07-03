import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Stack,
  Typography,
  InputAdornment,
  Menu,
  MenuItem,
  Checkbox,
  FormControlLabel,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Search as SearchIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  FilterList as FilterIcon,
  WhatsApp as WhatsAppIcon,
  Email as EmailIcon,
  LocalOffer as TagIcon,
} from '@mui/icons-material';
import contactService, { Contact, ContactCreate, ContactUpdate } from '../services/contact.service';

const Contacts: React.FC = () => {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTag, setSelectedTag] = useState<string | null>(null);
  const [allTags, setAllTags] = useState<string[]>([]);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingContact, setEditingContact] = useState<Contact | null>(null);
  const [formData, setFormData] = useState<ContactCreate>({
    name: '',
    phone: '',
    email: '',
    whatsapp_id: '',
    line_id: '',
    tags: [],
    notes: '',
  });
  const [selectedContacts, setSelectedContacts] = useState<string[]>([]);
  const [filterAnchorEl, setFilterAnchorEl] = useState<null | HTMLElement>(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  useEffect(() => {
    loadContacts();
  }, [searchTerm, selectedTag]);

  const loadContacts = async () => {
    try {
      const data = await contactService.getContacts({ search: searchTerm, tag: selectedTag });
      setContacts(data);
      
      // Extract all unique tags
      const tags = new Set<string>();
      data.forEach(contact => {
        contact.tags.forEach(tag => tags.add(tag));
      });
      setAllTags(Array.from(tags).sort());
      
      setLoading(false);
    } catch (error) {
      console.error('Failed to load contacts:', error);
      setLoading(false);
      showSnackbar('Failed to load contacts', 'error');
    }
  };

  const handleOpenDialog = (contact?: Contact) => {
    if (contact) {
      setEditingContact(contact);
      setFormData({
        name: contact.name,
        phone: contact.phone,
        email: contact.email || '',
        whatsapp_id: contact.whatsapp_id || '',
        line_id: contact.line_id || '',
        tags: contact.tags,
        notes: contact.notes || '',
      });
    } else {
      setEditingContact(null);
      setFormData({
        name: '',
        phone: '',
        email: '',
        whatsapp_id: '',
        line_id: '',
        tags: [],
        notes: '',
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingContact(null);
  };

  const handleSaveContact = async () => {
    try {
      // Clean up form data
      const contactData = {
        ...formData,
        email: formData.email?.trim() || undefined,
        whatsapp_id: formData.whatsapp_id?.trim() || undefined,
        line_id: formData.line_id?.trim() || undefined,
        notes: formData.notes?.trim() || undefined,
      };

      if (editingContact) {
        await contactService.updateContact(editingContact.id, contactData as ContactUpdate);
        showSnackbar('Contact updated successfully', 'success');
      } else {
        await contactService.createContact(contactData);
        showSnackbar('Contact created successfully', 'success');
      }
      handleCloseDialog();
      loadContacts();
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to save contact', 'error');
    }
  };

  const handleDeleteContact = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this contact?')) {
      try {
        await contactService.deleteContact(id);
        showSnackbar('Contact deleted successfully', 'success');
        loadContacts();
      } catch (error) {
        showSnackbar('Failed to delete contact', 'error');
      }
    }
  };

  const handleSelectAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      setSelectedContacts(contacts.map(c => c.id));
    } else {
      setSelectedContacts([]);
    }
  };

  const handleSelectContact = (id: string) => {
    setSelectedContacts(prev =>
      prev.includes(id) ? prev.filter(cId => cId !== id) : [...prev, id]
    );
  };

  const handleExport = async () => {
    try {
      const data = await contactService.exportContacts(selectedTag);
      // Create a blob and download
      const blob = new Blob([data.content], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = data.filename;
      a.click();
      window.URL.revokeObjectURL(url);
      showSnackbar('Contacts exported successfully', 'success');
    } catch (error) {
      showSnackbar('Failed to export contacts', 'error');
    }
  };

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const result = await contactService.importContacts(file);
      showSnackbar(`Imported ${result.imported} contacts, skipped ${result.skipped}`, 'success');
      loadContacts();
    } catch (error) {
      showSnackbar('Failed to import contacts', 'error');
    }
  };

  const handleTagInput = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault();
      const input = event.currentTarget;
      const value = input.value.trim();
      if (value && !formData.tags.includes(value)) {
        setFormData({ ...formData, tags: [...formData.tags, value] });
        input.value = '';
      }
    }
  };

  const removeTag = (tagToRemove: string) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter(tag => tag !== tagToRemove),
    });
  };

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Contacts</Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<UploadIcon />}
            component="label"
          >
            Import CSV
            <input
              type="file"
              hidden
              accept=".csv"
              onChange={handleImport}
            />
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleExport}
          >
            Export CSV
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Add Contact
          </Button>
        </Stack>
      </Box>

      <Paper sx={{ mb: 2, p: 2 }}>
        <Stack direction="row" spacing={2} alignItems="center">
          <TextField
            placeholder="Search contacts..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ flexGrow: 1 }}
          />
          <IconButton onClick={(e) => setFilterAnchorEl(e.currentTarget)}>
            <FilterIcon />
          </IconButton>
        </Stack>

        {selectedTag && (
          <Chip
            label={`Tag: ${selectedTag}`}
            onDelete={() => setSelectedTag(null)}
            sx={{ mt: 2 }}
          />
        )}
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  checked={selectedContacts.length === contacts.length && contacts.length > 0}
                  indeterminate={selectedContacts.length > 0 && selectedContacts.length < contacts.length}
                  onChange={handleSelectAll}
                />
              </TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Phone</TableCell>
              <TableCell>Channels</TableCell>
              <TableCell>Tags</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {contacts.map((contact) => (
              <TableRow key={contact.id}>
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selectedContacts.includes(contact.id)}
                    onChange={() => handleSelectContact(contact.id)}
                  />
                </TableCell>
                <TableCell>{contact.name}</TableCell>
                <TableCell>{contact.phone}</TableCell>
                <TableCell>
                  <Stack direction="row" spacing={1}>
                    {contact.whatsapp_id && <WhatsAppIcon color="success" fontSize="small" />}
                    {contact.email && <EmailIcon color="primary" fontSize="small" />}
                  </Stack>
                </TableCell>
                <TableCell>
                  <Stack direction="row" spacing={0.5}>
                    {contact.tags.map((tag) => (
                      <Chip
                        key={tag}
                        label={tag}
                        size="small"
                        onClick={() => setSelectedTag(tag)}
                      />
                    ))}
                  </Stack>
                </TableCell>
                <TableCell>
                  <IconButton onClick={() => handleOpenDialog(contact)} size="small">
                    <EditIcon />
                  </IconButton>
                  <IconButton onClick={() => handleDeleteContact(contact.id)} size="small">
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Filter Menu */}
      <Menu
        anchorEl={filterAnchorEl}
        open={Boolean(filterAnchorEl)}
        onClose={() => setFilterAnchorEl(null)}
      >
        <MenuItem disabled>
          <Typography variant="subtitle2">Filter by Tag</Typography>
        </MenuItem>
        {allTags.map((tag) => (
          <MenuItem
            key={tag}
            onClick={() => {
              setSelectedTag(tag);
              setFilterAnchorEl(null);
            }}
          >
            <TagIcon fontSize="small" sx={{ mr: 1 }} />
            {tag}
          </MenuItem>
        ))}
        {allTags.length === 0 && (
          <MenuItem disabled>
            <Typography variant="body2" color="text.secondary">
              No tags available
            </Typography>
          </MenuItem>
        )}
      </Menu>

      {/* Add/Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{editingContact ? 'Edit Contact' : 'Add New Contact'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 2 }}>
            <TextField
              label="Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              fullWidth
            />
            <TextField
              label="Phone"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              required
              fullWidth
              placeholder="+1234567890"
            />
            <TextField
              label="Email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              fullWidth
            />
            <TextField
              label="WhatsApp ID"
              value={formData.whatsapp_id}
              onChange={(e) => setFormData({ ...formData, whatsapp_id: e.target.value })}
              fullWidth
              placeholder="Leave empty to use phone number"
            />
            <TextField
              label="LINE ID"
              value={formData.line_id}
              onChange={(e) => setFormData({ ...formData, line_id: e.target.value })}
              fullWidth
            />
            <Box>
              <TextField
                label="Tags (press Enter to add)"
                onKeyDown={handleTagInput}
                fullWidth
                placeholder="marketing, vip, newsletter..."
              />
              <Stack direction="row" spacing={1} sx={{ mt: 1 }} flexWrap="wrap">
                {formData.tags.map((tag) => (
                  <Chip
                    key={tag}
                    label={tag}
                    onDelete={() => removeTag(tag)}
                    size="small"
                  />
                ))}
              </Stack>
            </Box>
            <TextField
              label="Notes"
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              multiline
              rows={3}
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button
            onClick={handleSaveContact}
            variant="contained"
            disabled={!formData.name || !formData.phone}
          >
            {editingContact ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Contacts;
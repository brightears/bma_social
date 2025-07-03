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
  Card,
  CardContent,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Autocomplete,
  LinearProgress,
  Tooltip,
  Alert,
  Snackbar,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Send as SendIcon,
  Pause as PauseIcon,
  PlayArrow as PlayIcon,
  People as PeopleIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import campaignService, { Campaign, CampaignCreate, CampaignStatus } from '../services/campaign.service';
import contactService from '../services/contact.service';

const Campaigns: React.FC = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [openPreview, setOpenPreview] = useState(false);
  const [editingCampaign, setEditingCampaign] = useState<Campaign | null>(null);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [formData, setFormData] = useState<CampaignCreate>({
    name: '',
    description: '',
    channel: 'whatsapp',
    message_content: '',
    segment_filters: { tags: [] },
    scheduled_at: null,
  });
  const [recipientCount, setRecipientCount] = useState(0);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  useEffect(() => {
    loadCampaigns();
    loadTags();
  }, []);

  useEffect(() => {
    // Calculate recipients when filters change
    if (formData.segment_filters.tags?.length > 0) {
      calculateRecipients();
    } else {
      setRecipientCount(0);
    }
  }, [formData.segment_filters]);

  const loadCampaigns = async () => {
    try {
      const data = await campaignService.getCampaigns();
      setCampaigns(data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to load campaigns:', error);
      setLoading(false);
      showSnackbar('Failed to load campaigns', 'error');
    }
  };

  const loadTags = async () => {
    try {
      const groups = await contactService.getContactGroups();
      setAvailableTags(groups.map(g => g.name));
    } catch (error) {
      console.error('Failed to load tags:', error);
    }
  };

  const calculateRecipients = async () => {
    try {
      const contacts = await contactService.getContacts({ tag: null });
      const filtered = contacts.filter(contact => {
        if (formData.segment_filters.tags?.length === 0) return true;
        return formData.segment_filters.tags?.some(tag => contact.tags.includes(tag));
      });
      setRecipientCount(filtered.length);
    } catch (error) {
      console.error('Failed to calculate recipients:', error);
    }
  };

  const handleOpenDialog = (campaign?: Campaign) => {
    if (campaign) {
      setEditingCampaign(campaign);
      setFormData({
        name: campaign.name,
        description: campaign.description || '',
        channel: campaign.channel,
        message_content: campaign.message_content || '',
        segment_filters: campaign.segment_filters,
        scheduled_at: campaign.scheduled_at ? new Date(campaign.scheduled_at) : null,
      });
    } else {
      setEditingCampaign(null);
      setFormData({
        name: '',
        description: '',
        channel: 'whatsapp',
        message_content: '',
        segment_filters: { tags: [] },
        scheduled_at: null,
      });
      setRecipientCount(0);
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingCampaign(null);
  };

  const handleSaveCampaign = async () => {
    try {
      if (editingCampaign) {
        await campaignService.updateCampaign(editingCampaign.id, {
          name: formData.name,
          description: formData.description,
          message_content: formData.message_content,
          segment_filters: formData.segment_filters,
          scheduled_at: formData.scheduled_at,
        });
        showSnackbar('Campaign updated successfully', 'success');
      } else {
        await campaignService.createCampaign(formData);
        showSnackbar('Campaign created successfully', 'success');
      }
      handleCloseDialog();
      loadCampaigns();
    } catch (error: any) {
      showSnackbar(error.response?.data?.detail || 'Failed to save campaign', 'error');
    }
  };

  const handleSendCampaign = async (campaignId: string) => {
    if (window.confirm('Are you sure you want to send this campaign now?')) {
      try {
        await campaignService.sendCampaign(campaignId);
        showSnackbar('Campaign started successfully', 'success');
        loadCampaigns();
      } catch (error) {
        showSnackbar('Failed to send campaign', 'error');
      }
    }
  };

  const handlePauseCampaign = async (campaignId: string) => {
    try {
      await campaignService.pauseCampaign(campaignId);
      showSnackbar('Campaign paused', 'success');
      loadCampaigns();
    } catch (error) {
      showSnackbar('Failed to pause campaign', 'error');
    }
  };

  const handleResumeCampaign = async (campaignId: string) => {
    try {
      await campaignService.resumeCampaign(campaignId);
      showSnackbar('Campaign resumed', 'success');
      loadCampaigns();
    } catch (error) {
      showSnackbar('Failed to resume campaign', 'error');
    }
  };

  const handleDeleteCampaign = async (campaignId: string) => {
    if (window.confirm('Are you sure you want to delete this campaign?')) {
      try {
        await campaignService.deleteCampaign(campaignId);
        showSnackbar('Campaign deleted successfully', 'success');
        loadCampaigns();
      } catch (error) {
        showSnackbar('Failed to delete campaign', 'error');
      }
    }
  };

  const handlePreviewCampaign = (campaign: Campaign) => {
    setSelectedCampaign(campaign);
    setOpenPreview(true);
  };

  const getStatusColor = (status: CampaignStatus) => {
    switch (status) {
      case 'draft': return 'default';
      case 'scheduled': return 'info';
      case 'running': return 'warning';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'paused': return 'secondary';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: CampaignStatus) => {
    switch (status) {
      case 'draft': return <EditIcon fontSize="small" />;
      case 'scheduled': return <ScheduleIcon fontSize="small" />;
      case 'running': return <PlayIcon fontSize="small" />;
      case 'completed': return <CheckCircleIcon fontSize="small" />;
      case 'failed': return <ErrorIcon fontSize="small" />;
      case 'paused': return <PauseIcon fontSize="small" />;
      default: return <InfoIcon fontSize="small" />;
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error') => {
    setSnackbar({ open: true, message, severity });
  };

  return (
    <LocalizationProvider dateAdapter={AdapterDateFns}>
      <Box sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
          <Typography variant="h4">Campaigns</Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => handleOpenDialog()}
          >
            Create Campaign
          </Button>
        </Box>

        {/* Campaign Stats */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total Campaigns
                </Typography>
                <Typography variant="h4">
                  {campaigns.length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Active
                </Typography>
                <Typography variant="h4">
                  {campaigns.filter(c => c.status === 'running').length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Scheduled
                </Typography>
                <Typography variant="h4">
                  {campaigns.filter(c => c.status === 'scheduled').length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Completed
                </Typography>
                <Typography variant="h4">
                  {campaigns.filter(c => c.status === 'completed').length}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Campaigns Table */}
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Campaign</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Recipients</TableCell>
                <TableCell>Sent</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {campaigns.map((campaign) => (
                <TableRow key={campaign.id}>
                  <TableCell>
                    <Typography variant="subtitle2">{campaign.name}</Typography>
                    <Typography variant="body2" color="textSecondary">
                      {campaign.description}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      icon={getStatusIcon(campaign.status)}
                      label={campaign.status.toUpperCase()}
                      color={getStatusColor(campaign.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{campaign.recipient_count}</TableCell>
                  <TableCell>
                    <Box>
                      <Typography variant="body2">
                        {campaign.sent_count} sent
                      </Typography>
                      {campaign.failed_count > 0 && (
                        <Typography variant="caption" color="error">
                          {campaign.failed_count} failed
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    {new Date(campaign.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={1}>
                      <Tooltip title="Preview">
                        <IconButton
                          size="small"
                          onClick={() => handlePreviewCampaign(campaign)}
                        >
                          <InfoIcon />
                        </IconButton>
                      </Tooltip>
                      
                      {campaign.status === 'draft' && (
                        <>
                          <Tooltip title="Edit">
                            <IconButton
                              size="small"
                              onClick={() => handleOpenDialog(campaign)}
                            >
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Send">
                            <IconButton
                              size="small"
                              color="primary"
                              onClick={() => handleSendCampaign(campaign.id)}
                            >
                              <SendIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleDeleteCampaign(campaign.id)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </>
                      )}
                      
                      {campaign.status === 'running' && (
                        <Tooltip title="Pause">
                          <IconButton
                            size="small"
                            color="warning"
                            onClick={() => handlePauseCampaign(campaign.id)}
                          >
                            <PauseIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                      
                      {campaign.status === 'paused' && (
                        <Tooltip title="Resume">
                          <IconButton
                            size="small"
                            color="success"
                            onClick={() => handleResumeCampaign(campaign.id)}
                          >
                            <PlayIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Create/Edit Dialog */}
        <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
          <DialogTitle>{editingCampaign ? 'Edit Campaign' : 'Create New Campaign'}</DialogTitle>
          <DialogContent>
            <Stack spacing={3} sx={{ mt: 2 }}>
              <TextField
                label="Campaign Name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                required
                fullWidth
              />
              
              <TextField
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                multiline
                rows={2}
                fullWidth
              />
              
              <FormControl fullWidth>
                <InputLabel>Channel</InputLabel>
                <Select
                  value={formData.channel}
                  onChange={(e) => setFormData({ ...formData, channel: e.target.value as any })}
                  label="Channel"
                >
                  <MenuItem value="whatsapp">WhatsApp</MenuItem>
                  <MenuItem value="line" disabled>LINE (Coming Soon)</MenuItem>
                  <MenuItem value="email" disabled>Email (Coming Soon)</MenuItem>
                </Select>
              </FormControl>
              
              <Autocomplete
                multiple
                options={availableTags}
                value={formData.segment_filters.tags || []}
                onChange={(_, value) => setFormData({
                  ...formData,
                  segment_filters: { ...formData.segment_filters, tags: value }
                })}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Target Audience (Tags)"
                    placeholder="Select tags"
                    helperText={`${recipientCount} recipients will receive this campaign`}
                  />
                )}
                renderTags={(value, getTagProps) =>
                  value.map((option, index) => (
                    <Chip
                      variant="outlined"
                      label={option}
                      {...getTagProps({ index })}
                    />
                  ))
                }
              />
              
              <TextField
                label="Message"
                value={formData.message_content}
                onChange={(e) => setFormData({ ...formData, message_content: e.target.value })}
                multiline
                rows={4}
                fullWidth
                required
                helperText="This message will be sent to all recipients"
              />
              
              <DateTimePicker
                label="Schedule for later (optional)"
                value={formData.scheduled_at}
                onChange={(value) => setFormData({ ...formData, scheduled_at: value })}
                minDateTime={new Date()}
                slotProps={{
                  textField: {
                    fullWidth: true
                  }
                }}
              />
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog}>Cancel</Button>
            <Button
              onClick={handleSaveCampaign}
              variant="contained"
              disabled={!formData.name || !formData.message_content || recipientCount === 0}
            >
              {editingCampaign ? 'Update' : 'Create'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Preview Dialog */}
        <Dialog open={openPreview} onClose={() => setOpenPreview(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Campaign Details</DialogTitle>
          <DialogContent>
            {selectedCampaign && (
              <Stack spacing={2} sx={{ mt: 2 }}>
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">Name</Typography>
                  <Typography>{selectedCampaign.name}</Typography>
                </Box>
                
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">Status</Typography>
                  <Chip
                    icon={getStatusIcon(selectedCampaign.status)}
                    label={selectedCampaign.status.toUpperCase()}
                    color={getStatusColor(selectedCampaign.status)}
                    size="small"
                  />
                </Box>
                
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">Message</Typography>
                  <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
                    <Typography style={{ whiteSpace: 'pre-wrap' }}>
                      {selectedCampaign.message_content}
                    </Typography>
                  </Paper>
                </Box>
                
                <Box>
                  <Typography variant="subtitle2" color="textSecondary">Performance</Typography>
                  <Stack spacing={1}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Recipients</Typography>
                      <Typography variant="body2">{selectedCampaign.recipient_count}</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Sent</Typography>
                      <Typography variant="body2">{selectedCampaign.sent_count}</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Failed</Typography>
                      <Typography variant="body2" color="error">
                        {selectedCampaign.failed_count}
                      </Typography>
                    </Box>
                  </Stack>
                  
                  {selectedCampaign.status === 'running' && (
                    <Box sx={{ mt: 2 }}>
                      <LinearProgress
                        variant="determinate"
                        value={(selectedCampaign.sent_count / selectedCampaign.recipient_count) * 100}
                      />
                    </Box>
                  )}
                </Box>
              </Stack>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenPreview(false)}>Close</Button>
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
    </LocalizationProvider>
  );
};

export default Campaigns;
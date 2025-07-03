import api from './api';

export type CampaignStatus = 'draft' | 'scheduled' | 'running' | 'paused' | 'completed' | 'failed';
export type CampaignChannel = 'whatsapp' | 'line' | 'email' | 'all';

export interface Campaign {
  id: string;
  name: string;
  description?: string;
  channel: CampaignChannel;
  template_id?: string;
  message_content?: string;
  status: CampaignStatus;
  scheduled_at?: string;
  started_at?: string;
  completed_at?: string;
  segment_filters: {
    tags?: string[];
    has_whatsapp?: boolean;
  };
  recipient_count: number;
  sent_count: number;
  delivered_count: number;
  read_count: number;
  clicked_count: number;
  failed_count: number;
  created_at: string;
  created_by_id: string;
  created_by_name: string;
}

export interface CampaignCreate {
  name: string;
  description?: string;
  channel: CampaignChannel;
  message_content: string;
  template_id?: string;
  segment_filters: {
    tags?: string[];
    has_whatsapp?: boolean;
  };
  scheduled_at?: Date | null;
}

export interface CampaignUpdate {
  name?: string;
  description?: string;
  message_content?: string;
  segment_filters?: {
    tags?: string[];
    has_whatsapp?: boolean;
  };
  scheduled_at?: Date | null;
}

export interface CampaignRecipient {
  id: string;
  name: string;
  phone: string;
  whatsapp_id?: string;
  tags: string[];
}

class CampaignService {
  async getCampaigns(status?: CampaignStatus): Promise<Campaign[]> {
    const params = new URLSearchParams();
    if (status) {
      params.append('status', status);
    }
    
    const response = await api.get<Campaign[]>(`/campaigns/?${params.toString()}`);
    return response.data;
  }

  async getCampaign(id: string): Promise<Campaign> {
    const response = await api.get<Campaign>(`/campaigns/${id}`);
    return response.data;
  }

  async createCampaign(campaign: CampaignCreate): Promise<Campaign> {
    const response = await api.post<Campaign>('/campaigns/', campaign);
    return response.data;
  }

  async updateCampaign(id: string, campaign: CampaignUpdate): Promise<Campaign> {
    const response = await api.put<Campaign>(`/campaigns/${id}`, campaign);
    return response.data;
  }

  async deleteCampaign(id: string): Promise<void> {
    await api.delete(`/campaigns/${id}`);
  }

  async getCampaignRecipients(id: string): Promise<CampaignRecipient[]> {
    const response = await api.get<CampaignRecipient[]>(`/campaigns/${id}/recipients`);
    return response.data;
  }

  async sendCampaign(id: string): Promise<{ status: string; campaign_id: string }> {
    const response = await api.post<{ status: string; campaign_id: string }>(`/campaigns/${id}/send`);
    return response.data;
  }

  async pauseCampaign(id: string): Promise<{ status: string }> {
    const response = await api.post<{ status: string }>(`/campaigns/${id}/pause`);
    return response.data;
  }

  async resumeCampaign(id: string): Promise<{ status: string }> {
    const response = await api.post<{ status: string }>(`/campaigns/${id}/resume`);
    return response.data;
  }
}

export default new CampaignService();
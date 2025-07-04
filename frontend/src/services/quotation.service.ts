import api from './api';

export interface QuotationItem {
  description: string;
  quantity: number;
  unit_price: number;
  total: number;
}

export interface QuotationCreate {
  customer_id: string;
  company_name?: string;
  company_address?: string;
  company_tax_id?: string;
  title: string;
  description?: string;
  items: QuotationItem[];
  discount_percent?: number;
  tax_percent?: number;
  payment_terms?: string;
  validity_days?: number;
  notes?: string;
}

export interface QuotationUpdate {
  company_name?: string;
  company_address?: string;
  company_tax_id?: string;
  title?: string;
  description?: string;
  items?: QuotationItem[];
  discount_percent?: number;
  tax_percent?: number;
  payment_terms?: string;
  validity_days?: number;
  notes?: string;
}

export interface Quotation {
  id: string;
  quote_number: string;
  customer_id: string;
  customer_name: string;
  customer_phone: string;
  customer_email?: string;
  company_name?: string;
  company_address?: string;
  company_tax_id?: string;
  title: string;
  description?: string;
  items: QuotationItem[];
  subtotal: number;
  discount_percent: number;
  discount_amount: number;
  tax_percent: number;
  tax_amount: number;
  total_amount: number;
  payment_terms: string;
  validity_days: number;
  notes?: string;
  status: 'draft' | 'sent' | 'viewed' | 'accepted' | 'rejected' | 'expired';
  sent_at?: string;
  viewed_at?: string;
  responded_at?: string;
  pdf_url?: string;
  created_at: string;
  created_by_name: string;
}

export interface SendQuotationRequest {
  channel: 'whatsapp' | 'line' | 'email';
  message?: string;
}

class QuotationService {
  private baseUrl = '/quotations';

  async getQuotations(params?: {
    skip?: number;
    limit?: number;
    status?: string;
    customer_id?: string;
  }): Promise<Quotation[]> {
    const response = await api.get<Quotation[]>(`${this.baseUrl}/`, { params });
    return response.data;
  }

  async getQuotation(id: string): Promise<Quotation> {
    const response = await api.get<Quotation>(`${this.baseUrl}/${id}`);
    return response.data;
  }

  async createQuotation(data: QuotationCreate): Promise<Quotation> {
    try {
      const response = await api.post<Quotation>(`${this.baseUrl}/`, data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to create quotation');
    }
  }

  async updateQuotation(id: string, data: QuotationUpdate): Promise<Quotation> {
    try {
      const response = await api.put<Quotation>(`${this.baseUrl}/${id}`, data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to update quotation');
    }
  }

  async deleteQuotation(id: string): Promise<void> {
    try {
      await api.delete(`${this.baseUrl}/${id}`);
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to delete quotation');
    }
  }

  async downloadPDF(id: string): Promise<Blob> {
    const response = await api.get(`${this.baseUrl}/${id}/pdf`, {
      responseType: 'blob',
    });
    return response.data;
  }

  async sendQuotation(id: string, data: SendQuotationRequest): Promise<{ status: string; channel: string }> {
    try {
      const response = await api.post<{ status: string; channel: string }>(`${this.baseUrl}/${id}/send`, data);
      return response.data;
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Failed to send quotation');
    }
  }
}

export default new QuotationService();
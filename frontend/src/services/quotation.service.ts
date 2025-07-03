import { authService } from './auth.service';

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
  private baseUrl = `${import.meta.env.VITE_API_URL}/api/v1/quotations`;

  async getQuotations(params?: {
    skip?: number;
    limit?: number;
    status?: string;
    customer_id?: string;
  }): Promise<Quotation[]> {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.append('skip', params.skip.toString());
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.status) queryParams.append('status', params.status);
    if (params?.customer_id) queryParams.append('customer_id', params.customer_id);

    const response = await fetch(`${this.baseUrl}?${queryParams}`, {
      headers: authService.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch quotations');
    }

    return response.json();
  }

  async getQuotation(id: string): Promise<Quotation> {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      headers: authService.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch quotation');
    }

    return response.json();
  }

  async createQuotation(data: QuotationCreate): Promise<Quotation> {
    const response = await fetch(this.baseUrl, {
      method: 'POST',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create quotation');
    }

    return response.json();
  }

  async updateQuotation(id: string, data: QuotationUpdate): Promise<Quotation> {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      method: 'PUT',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update quotation');
    }

    return response.json();
  }

  async deleteQuotation(id: string): Promise<void> {
    const response = await fetch(`${this.baseUrl}/${id}`, {
      method: 'DELETE',
      headers: authService.getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete quotation');
    }
  }

  async downloadPDF(id: string): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/${id}/pdf`, {
      headers: authService.getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to download PDF');
    }

    return response.blob();
  }

  async sendQuotation(id: string, data: SendQuotationRequest): Promise<{ status: string; channel: string }> {
    const response = await fetch(`${this.baseUrl}/${id}/send`, {
      method: 'POST',
      headers: authService.getAuthHeaders(),
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to send quotation');
    }

    return response.json();
  }
}

export default new QuotationService();
import api from './api';

export interface Contact {
  id: string;
  name: string;
  phone: string;
  email?: string;
  whatsapp_id?: string;
  line_id?: string;
  tags: string[];
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface ContactCreate {
  name: string;
  phone: string;
  email?: string;
  whatsapp_id?: string;
  line_id?: string;
  tags: string[];
  notes?: string;
}

export interface ContactUpdate {
  name?: string;
  phone?: string;
  email?: string;
  whatsapp_id?: string;
  line_id?: string;
  tags?: string[];
  notes?: string;
}

export interface ContactGroup {
  name: string;
  description?: string;
  color: string;
  contact_count: number;
}

export interface ImportResult {
  imported: number;
  skipped: number;
  errors: string[];
}

export interface ExportResult {
  content: string;
  filename: string;
}

class ContactService {
  async getContacts(params?: { search?: string; tag?: string | null }): Promise<Contact[]> {
    const queryParams = new URLSearchParams();
    if (params?.search) {
      queryParams.append('search', params.search);
    }
    if (params?.tag) {
      queryParams.append('tag', params.tag);
    }
    
    const response = await api.get<Contact[]>(`/contacts/?${queryParams.toString()}`);
    return response.data;
  }

  async getContact(id: string): Promise<Contact> {
    const response = await api.get<Contact>(`/contacts/${id}`);
    return response.data;
  }

  async createContact(contact: ContactCreate): Promise<Contact> {
    const response = await api.post<Contact>('/contacts/', contact);
    return response.data;
  }

  async updateContact(id: string, contact: ContactUpdate): Promise<Contact> {
    const response = await api.put<Contact>(`/contacts/${id}`, contact);
    return response.data;
  }

  async deleteContact(id: string): Promise<void> {
    await api.delete(`/contacts/${id}`);
  }

  async getContactGroups(): Promise<ContactGroup[]> {
    const response = await api.get<ContactGroup[]>('/contacts/groups/');
    return response.data;
  }

  async importContacts(file: File): Promise<ImportResult> {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post<ImportResult>('/contacts/import/csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async exportContacts(tag?: string | null): Promise<ExportResult> {
    const queryParams = new URLSearchParams();
    if (tag) {
      queryParams.append('tag', tag);
    }
    
    const response = await api.get<ExportResult>(`/contacts/export/csv?${queryParams.toString()}`);
    return response.data;
  }
}

export default new ContactService();
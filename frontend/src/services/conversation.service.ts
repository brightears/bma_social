import api from './api';

export interface Customer {
  id: string;
  name: string;
  phone: string;
  email?: string;
  whatsapp_id?: string;
  line_id?: string;
}

export interface Conversation {
  id: string;
  customer_id: string;
  customer_name: string;
  customer_phone: string;
  channel: 'whatsapp' | 'line' | 'email';
  status: 'open' | 'closed' | 'pending';
  unread_count: number;
  last_message_at: string;
  last_message_preview: string;
  assigned_to_id?: string;
  assigned_to_name?: string;
  created_at: string;
  tags: string[];
}

export interface Message {
  id: string;
  conversation_id: string;
  type: 'text' | 'image' | 'video' | 'audio' | 'document' | 'template';
  content: string;
  media_url?: string;
  direction: 'inbound' | 'outbound';
  status: 'pending' | 'sent' | 'delivered' | 'read' | 'failed';
  created_at: string;
  sender_name?: string;
}

export interface SendMessageRequest {
  conversation_id: string;
  content: string;
  type?: 'text' | 'image' | 'video' | 'audio' | 'document' | 'template';
  media_url?: string;
  template_name?: string;
  template_params?: any;
}

class ConversationService {
  async getConversations(): Promise<Conversation[]> {
    const response = await api.get<Conversation[]>('/conversations/');
    return response.data;
  }

  async getConversation(id: string): Promise<Conversation> {
    const response = await api.get<Conversation>(`/conversations/${id}`);
    return response.data;
  }

  async getMessages(conversationId: string): Promise<Message[]> {
    const response = await api.get<Message[]>(`/messages/conversation/${conversationId}`);
    return response.data;
  }

  async sendMessage(message: SendMessageRequest): Promise<Message> {
    const response = await api.post<Message>('/messages/send', message);
    return response.data;
  }

  async markAsRead(messageId: string): Promise<void> {
    await api.post(`/messages/${messageId}/read`);
  }
}

export default new ConversationService();
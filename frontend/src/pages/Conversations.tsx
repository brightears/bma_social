import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  List,
  ListItemButton,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Badge,
  Divider,
  TextField,
  Paper,
  Button,
  CircularProgress,
  Alert,
  Typography,
} from '@mui/material';
import {
  Send as SendIcon,
  WhatsApp as WhatsAppIcon,
  Email as EmailIcon,
} from '@mui/icons-material';
import { format } from 'date-fns';
import conversationService, { Conversation, Message } from '../services/conversation.service';

const Conversations: React.FC = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [messageError, setMessageError] = useState<string | null>(null);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [isFirstLoad, setIsFirstLoad] = useState(true);

  useEffect(() => {
    loadConversations();
    // Re-enable auto-refresh
    const interval = setInterval(() => {
      loadConversations();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedConversation) {
      setIsFirstLoad(true);
      loadMessages(selectedConversation.id);
      // Re-enable auto-refresh with smart loading
      const interval = setInterval(() => {
        loadMessagesSmartly(selectedConversation.id);
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [selectedConversation]);

  useEffect(() => {
    // Auto-scroll to bottom when new messages arrive (only on first load)
    if (messages.length > 0 && isFirstLoad) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      setIsFirstLoad(false);
    }
  }, [messages, isFirstLoad]);

  const loadConversations = async () => {
    try {
      const data = await conversationService.getConversations();
      // Only update if there are actual changes
      if (JSON.stringify(data) !== JSON.stringify(conversations)) {
        setConversations(data);
      }
      setLoading(false);
    } catch (error) {
      console.error('Failed to load conversations:', error);
      setLoading(false);
    }
  };

  const loadMessages = async (conversationId: string) => {
    setLoadingMessages(true);
    setMessageError(null);
    try {
      const data = await conversationService.getMessages(conversationId);
      setMessages(data);
    } catch (error: any) {
      console.error('Failed to load messages:', error);
      setMessageError(error.response?.data?.detail || 'Failed to load messages');
      setMessages([]);
    } finally {
      setLoadingMessages(false);
    }
  };

  const loadMessagesSmartly = async (conversationId: string) => {
    // Save current scroll position
    const container = messagesContainerRef.current;
    const scrollPosition = container ? container.scrollHeight - container.scrollTop : 0;
    
    try {
      const data = await conversationService.getMessages(conversationId);
      
      // Only update if there are new messages
      if (data.length !== messages.length || 
          (data.length > 0 && messages.length > 0 && 
           data[data.length - 1].id !== messages[messages.length - 1].id)) {
        setMessages(data);
        
        // Restore scroll position after DOM update
        setTimeout(() => {
          if (container && scrollPosition > 0) {
            container.scrollTop = container.scrollHeight - scrollPosition;
          }
        }, 0);
      }
    } catch (error) {
      // Silently fail on refresh errors to avoid spam
      console.error('Failed to refresh messages:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim() || !selectedConversation) return;

    setSending(true);
    try {
      await conversationService.sendMessage({
        conversation_id: selectedConversation.id,
        content: newMessage,
        type: 'text',
      });
      setNewMessage('');
      // Reload messages
      await loadMessages(selectedConversation.id);
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setSending(false);
    }
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'whatsapp':
        return <WhatsAppIcon color="success" />;
      case 'email':
        return <EmailIcon color="primary" />;
      default:
        return <Avatar>{channel[0].toUpperCase()}</Avatar>;
    }
  };

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 112px)' }}>
      {/* Conversations List */}
      <Paper sx={{ width: 350, overflow: 'auto', borderRadius: 0 }}>
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Typography variant="h6">Conversations</Typography>
        </Box>
        {loading ? (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        ) : (
          <List>
            {conversations.map((conversation) => (
              <ListItemButton
                key={conversation.id}
                selected={selectedConversation?.id === conversation.id}
                onClick={() => setSelectedConversation(conversation)}
              >
                <ListItemAvatar>
                  {getChannelIcon(conversation.channel)}
                </ListItemAvatar>
                <ListItemText
                  primary={conversation.customer_name}
                  secondary={
                    <>
                      <Typography component="span" variant="body2" color="text.primary">
                        {conversation.last_message_preview}
                      </Typography>
                      <br />
                      {format(new Date(conversation.last_message_at), 'MMM d, h:mm a')}
                    </>
                  }
                />
                {conversation.unread_count > 0 && (
                  <Badge badgeContent={conversation.unread_count} color="primary" />
                )}
              </ListItemButton>
            ))}
          </List>
        )}
      </Paper>

      {/* Messages Area */}
      <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        {selectedConversation ? (
          <>
            <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
              <Typography variant="h6">{selectedConversation.customer_name}</Typography>
              <Typography variant="caption" color="text.secondary">
                {selectedConversation.channel} • {selectedConversation.customer_phone}
              </Typography>
            </Box>

            <Box 
              ref={messagesContainerRef}
              sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}
            >
              {messageError && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {messageError}
                </Alert>
              )}
              {loadingMessages ? (
                <Box display="flex" justifyContent="center" p={3}>
                  <CircularProgress />
                </Box>
              ) : messages.length === 0 ? (
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '100%',
                    color: 'text.secondary'
                  }}
                >
                  <Typography>No messages yet. Start a conversation!</Typography>
                </Box>
              ) : (
                messages.map((message) => (
                  <Box
                    key={message.id}
                    sx={{
                      display: 'flex',
                      justifyContent: message.direction === 'outbound' ? 'flex-end' : 'flex-start',
                      mb: 2,
                    }}
                  >
                    <Paper
                      sx={{
                        p: 2,
                        maxWidth: '70%',
                        bgcolor: message.direction === 'outbound' ? 'primary.main' : 'grey.100',
                        color: message.direction === 'outbound' ? 'white' : 'text.primary',
                      }}
                    >
                      <Typography variant="body1">{message.content}</Typography>
                      <Typography
                        variant="caption"
                        sx={{
                          display: 'block',
                          mt: 1,
                          opacity: 0.8,
                        }}
                      >
                        {format(new Date(message.created_at), 'h:mm a')}
                      </Typography>
                    </Paper>
                  </Box>
                ))
              )}
              <div ref={messagesEndRef} />
            </Box>
            
            <Paper sx={{ p: 2, display: 'flex', gap: 1 }}>
              <TextField
                fullWidth
                variant="outlined"
                placeholder="Type a message..."
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                disabled={sending}
              />
              <Button
                variant="contained"
                endIcon={<SendIcon />}
                onClick={handleSendMessage}
                disabled={sending || !newMessage.trim()}
              >
                Send
              </Button>
            </Paper>
          </>
        ) : (
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
            }}
          >
            <Typography variant="h5" color="text.secondary">
              Select a conversation to start messaging
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default Conversations;
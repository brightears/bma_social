# BMA Social

A unified multi-channel communication platform for Bright Ears Music Asia, enabling seamless customer engagement across WhatsApp, Line, and Email.

## 🎯 Overview

BMA Social is a tailored marketing and customer communication platform that centralizes all customer interactions. It enables marketing, sales, and admin teams to:

- Manage conversations across multiple channels from a single interface
- Create and schedule marketing campaigns
- Provide technical support with full context
- Track customer engagement and analytics
- Automate routine communications while maintaining personal touch

## 🚀 Key Features

### Multi-Channel Support
- **WhatsApp Business API** - Fully integrated with real-time messaging
- **Line Business** - Connect with Thai customers on their preferred platform (planned)
- **Email** - Traditional email support for formal communications (planned)

### Conversation Management
- Unified inbox for WhatsApp conversations
- Real-time message delivery and status tracking
- Conversation assignment and routing
- Full conversation history with search capabilities
- Contact management with custom fields

### Campaign Management
- Campaign creation and scheduling
- Message templates with dynamic variables
- Bulk messaging with contact segmentation
- Campaign analytics and performance tracking
- Template library for reusable content

### Quotation System
- Professional quotation generation with PDF export
- Multi-currency support (THB and USD)
- Customizable quotation templates
- Item-based pricing with automatic calculations
- Tax and discount management
- Status tracking (draft, sent, viewed, accepted, rejected)
- Direct sharing via WhatsApp

### Contact Management
- Comprehensive contact database
- Custom fields and tags
- Import/export functionality
- Contact grouping and segmentation
- Activity history tracking
- Integration with conversations and campaigns

### Admin Tools
- User management with role-based access
- System configuration
- Audit logs and activity tracking
- Database management tools
- Performance monitoring

### Team Collaboration
- Role-based access control (Admin, Manager, Agent)
- Team member management
- Performance metrics per user
- Activity logs for compliance

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **PostgreSQL** - Primary database with asyncpg
- **Redis** - Caching and message queue
- **Celery** - Background task processing
- **SQLAlchemy** - ORM with async support

### Frontend
- **React** with TypeScript
- **Material-UI** for components
- **React Query** for data fetching and caching
- **React Router** for navigation
- **Axios** for API communication
- **React Hook Form** for form management
- **Date-fns** for date handling

### Infrastructure
- **Render** - Web service deployment
- **PostgreSQL on Render** - Managed database
- **Redis on Render** - Managed Redis instance
- **GitHub Actions** - CI/CD pipeline

## 📁 Project Structure

```
bma_social/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       └── dependencies/
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── models/
│   │   ├── services/
│   │   └── utils/
│   ├── tests/
│   ├── migrations/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── utils/
│   └── package.json
├── docs/
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── ARCHITECTURE.md
└── deployment/
    ├── render.yaml
    └── docker-compose.yml
```

## 🚦 Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for frontend)

### Backend Setup

1. Clone the repository
```bash
git clone https://github.com/brightears/bma_social.git
cd bma_social
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run database migrations
```bash
alembic upgrade head
```

6. Start the development server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup (Coming Soon)

```bash
cd frontend
npm install
npm start
```

## 🔗 Integration with BMA CRM

BMA Social integrates seamlessly with the existing BMA CRM system:

- **Customer Data Sync** - Pull customer information and zone data
- **Single Sign-On** - Shared authentication between platforms
- **Event-Driven Updates** - Contract renewals, zone status changes
- **Unified Analytics** - Combined reporting across platforms

Configure integration in `.env`:
```env
CRM_API_URL=https://bmasia-crm.onrender.com/api
CRM_API_KEY=your-api-key
```

## 📊 API Documentation

Once running, access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧪 Testing

Run the test suite:
```bash
pytest
pytest --cov=app  # With coverage
```

## 📦 Deployment

### Render Deployment

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure environment variables
4. Deploy using `render.yaml` configuration

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

## 🔒 Security

- JWT-based authentication
- Role-based access control
- API rate limiting
- Input validation and sanitization
- Audit logging for compliance
- Encrypted message storage

## 🚀 Current Status (January 4, 2025)

### ✅ Completed Features
- **Backend API**: Fully deployed on Render at https://bma-social-api.onrender.com
- **Frontend Application**: React TypeScript app deployed at https://bma-social-frontend.onrender.com
- **WhatsApp Integration**: 
  - Real-time message sending and receiving
  - Media support (images, documents)
  - Webhook processing with message status updates
  - Integration with Meta Business API
- **Conversation Management**:
  - Real-time conversation view with message history
  - Contact association and management
  - Message status tracking (sent, delivered, read)
  - Search and filtering capabilities
- **Contact Management**:
  - Full CRUD operations for contacts
  - Custom fields and tags
  - Bulk import/export
  - Activity tracking
- **Campaign System**:
  - Campaign creation and scheduling
  - Template management
  - Contact selection and segmentation
  - Basic analytics
- **Quotation System**:
  - Professional quotation generation
  - Multi-currency support (THB/USD)
  - PDF generation and export
  - Template library
  - WhatsApp sharing integration
  - Status tracking and analytics
- **Admin Tools**:
  - User management
  - System configuration
  - Activity logs
  - Database utilities
- **Authentication & Security**:
  - JWT-based authentication
  - Role-based access control
  - Secure session management

### 🚧 Known Issues
- Some CORS configuration fine-tuning may be needed for specific domains
- Background job processing for scheduled campaigns needs optimization
- Real-time updates via WebSocket pending implementation

### 📝 Access Information
- **Admin Login**: Contact system administrator for credentials
- **API Base URL**: https://bma-social-api.onrender.com/api/v1
- **Frontend URL**: https://bma-social-frontend.onrender.com
- **API Documentation**: https://bma-social-api.onrender.com/docs

## 📈 Roadmap

### Phase 1: Core Messaging ✅ (Completed)
- [x] Project structure setup
- [x] WhatsApp integration with real-time messaging
- [x] Conversation management system
- [x] Contact management
- [x] User authentication and authorization

### Phase 2: Campaign Management ✅ (Completed)
- [x] Template builder and management
- [x] Campaign creation and scheduling
- [x] Contact selection and segmentation
- [x] Basic campaign analytics

### Phase 3: Business Tools ✅ (Completed)
- [x] Quotation system with multi-currency
- [x] PDF generation and export
- [x] Template library
- [x] Admin tools and utilities

### Phase 4: Multi-channel (Next)
- [ ] Line Business integration
- [ ] Email channel integration
- [ ] Unified inbox for all channels
- [ ] Channel preference management

### Phase 5: Intelligence Layer (Future)
- [ ] Advanced analytics dashboard
- [ ] AI-powered auto-tagging
- [ ] Smart conversation routing
- [ ] Predictive insights
- [ ] Performance optimization

### Phase 6: Advanced Features (Future)
- [ ] WebSocket for real-time updates
- [ ] Advanced automation workflows
- [ ] CRM deep integration
- [ ] Mobile app development

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is proprietary to Bright Ears Music Asia.

## 👥 Team

- Development: Bright Ears Tech Team
- Product: BMA Marketing & Sales Teams
- DevOps: Render deployment and monitoring

## 📞 Support

For issues and questions:
- Create an issue in this repository
- Contact the development team
- Check the [documentation](docs/)
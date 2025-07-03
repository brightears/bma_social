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
- **WhatsApp Business API** - Leverage existing integration for customer communications
- **Line Business** - Connect with Thai customers on their preferred platform  
- **Email** - Traditional email support for formal communications

### Conversation Management
- Unified inbox for all channels
- Team collaboration with internal notes
- Conversation assignment and routing
- Full conversation history and context

### Campaign Management
- Visual campaign builder
- Message templates with dynamic variables
- Bulk messaging with segmentation
- Scheduled campaigns and automated reminders

### Customer Intelligence
- Integration with BMA CRM for customer data
- Automatic customer segmentation
- Engagement tracking and analytics
- Zone status integration for contextual messaging

### Team Collaboration
- Role-based access control
- @mentions and internal notes
- Performance metrics per team member
- Audit logs for compliance

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern async Python web framework
- **PostgreSQL** - Primary database with asyncpg
- **Redis** - Caching and message queue
- **Celery** - Background task processing
- **SQLAlchemy** - ORM with async support

### Frontend (Planned)
- **React** with TypeScript
- **Material-UI** or **Ant Design** for components
- **Redux Toolkit** for state management
- **Socket.io** for real-time updates

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

## 🚀 Current Status (July 3, 2025)

### ✅ Completed Features
- **Backend API**: Fully deployed on Render at https://bma-social-api.onrender.com
- **WhatsApp Integration**: Successfully receiving and sending messages
- **Database**: PostgreSQL on Render with all tables created
- **Authentication**: JWT-based auth implemented with admin user
- **Webhook Router**: Deployed separately to forward WhatsApp to both Zone Monitor and BMA Social
- **Frontend**: React TypeScript app deployed at https://bma-social-frontend.onrender.com
- **Message Management**: Send/receive WhatsApp messages, conversation tracking

### 🚧 Current Issues
- **CORS Configuration**: Frontend login failing due to CORS headers
  - BACKEND_CORS_ORIGINS set but not properly returned in headers
  - Temporary workaround: Add wildcard to origins

### 📝 Access Information
- **Admin Login**: username: `admin`, password: `changeme123`
- **API Base URL**: https://bma-social-api.onrender.com/api/v1
- **Frontend URL**: https://bma-social-frontend.onrender.com

## 📈 Roadmap

### Phase 1: Core Messaging (Current)
- [x] Project structure setup
- [x] WhatsApp integration
- [x] Basic conversation view
- [x] Team user management (admin created)

### Phase 2: Campaign Management
- [ ] Template builder
- [ ] Bulk messaging
- [ ] Scheduling system
- [ ] Customer import from CRM

### Phase 3: Multi-channel
- [ ] Line Business integration
- [ ] Email channel
- [ ] Unified inbox
- [ ] Channel preferences

### Phase 4: Intelligence Layer
- [ ] Analytics dashboard
- [ ] Auto-tagging
- [ ] Smart routing
- [ ] Performance metrics

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
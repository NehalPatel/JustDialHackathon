# JustDial Hackathon - Project 1 (Python Backend)

This project has been migrated to a Python FastAPI backend. The previous Node.js backend has been removed.

## 🚀 Project Overview

This project implements a comprehensive solution with the following features:
- User authentication and authorization
- Project and task management
- Real-time updates
- Responsive design
- RESTful API architecture

## 🛠 Technology Stack

### Backend
- **Python** 3.10+
- **FastAPI** for API framework
- **MongoDB** with **PyMongo** driver
- **JWT** with **PyJWT**
- **bcrypt** for password hashing

### Development Tools
- **Uvicorn** for development server
- **python-dotenv** for environment management

## 📋 Prerequisites

- Python >= 3.10
- MongoDB >= 6.0 (local or MongoDB Atlas)
- Git >= 2.30.0

## 🚀 Quick Start

### 1. Clone and Install
```bash
git clone <repository-url>
cd justdial-hackathon-project1
npm install
```

### 2. Environment Setup
```bash
# Copy environment template
cp env.example .env

# Edit .env with your configuration
# Set your MongoDB URI, JWT secrets, etc.
```

### 3. Database Setup
```bash
# Start MongoDB (if running locally)
mongod --dbpath /path/to/your/db

# Or use MongoDB Atlas connection string in .env
```

### 4. Development
```bash
# Install Python dependencies
python -m pip install -r pyapp/requirements.txt

# Start FastAPI dev server (port 3001)
python -m uvicorn pyapp.main:app --reload --port 3001
```

### 5. Production Build
```bash
npm run build
npm start
```

## 📁 Project Structure

```
project/
├── pyapp/                 # Python FastAPI backend
│   ├── main.py            # FastAPI app entry
│   ├── config.py          # Environment settings
│   ├── db.py              # MongoDB connection
│   ├── auth.py            # Auth routes and JWT
│   ├── moderation.py      # Moderation routes and analysis
│   └── requirements.txt   # Python dependencies
├── uploads/               # Uploaded files
├── README.md
└── .env
```

## 🔧 Running Commands

- `python -m pip install -r pyapp/requirements.txt` - Install dependencies
- `python -m uvicorn pyapp.main:app --reload --port 3001` - Start dev server

## 🌐 API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login

### Moderation
- `POST /api/v1/moderation/analyze`
- `GET /api/v1/moderation/{id}`
- `GET /api/v1/moderation?decision=approved`
- `POST /api/v1/moderation/settings`

## 🔒 Security Features

- Password hashing with bcrypt
- JWT token authentication
- Input validation and sanitization
- CORS configuration
- Rate limiting
- Helmet security headers

## 📊 Performance

- Page load time < 3 seconds
- API response time < 200ms
- Support for 100+ concurrent users
- Bundle size < 500KB (frontend)

## 🧪 Testing

```bash
npm test                 # Run all tests
npm run test:watch       # Run tests in watch mode
npm run test:coverage    # Run tests with coverage
```

## 🚀 Deployment

### Backend (Railway/Heroku)
1. Set environment variables
2. Deploy with Uvicorn/Gunicorn

### Frontend (Vercel/Netlify)
1. Build with `npm run build:frontend`
2. Deploy dist folder

## 📝 Development Timeline

- **Days 1-3**: Project setup and authentication
- **Days 4-7**: Core API development
- **Days 8-10**: Frontend development
- **Days 11-14**: Integration and testing
- **Days 15-16**: Final polish and deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support, please contact the development team or create an issue in the repository.

---

**Built with ❤️ using FastAPI for JustDial Hackathon**

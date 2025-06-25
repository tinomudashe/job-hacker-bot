# 🚀 AI Job Application Assistant

A comprehensive AI-powered job application assistant built with Next.js frontend and FastAPI backend. Features advanced CV processing, glassmorphism UI, Safari compatibility, and intelligent job application automation.

## ✨ Key Features

### 🎯 **Core Functionality**
- **Intelligent Chat Interface** - AI-powered conversation with context awareness
- **CV RAG System** - Automatic profile updates from uploaded CVs
- **PDF Generation** - Multiple styles (Modern, Classic, Minimal) for resumes and cover letters
- **Text-to-Speech** - Real-time audio generation with progress tracking
- **Job Search Integration** - Automated job searching and application assistance

### 🎨 **UI/UX Excellence**
- **Glassmorphism Design** - Modern glass effects with enhanced borders and corners
- **Safari Compatibility** - Fully optimized for all browsers including Safari
- **Mobile Responsive** - Touch-friendly interface with optimized layouts
- **Theme Support** - Dark/Light mode with system preference detection
- **Enhanced Conversations** - Polished chat bubbles with interactive features

### 🔧 **Technical Features**
- **FastAPI Backend** - High-performance API with async processing
- **Next.js 15 Frontend** - Latest React 19 with advanced optimizations
- **Vector Search** - FAISS integration for document similarity search
- **Authentication** - Clerk integration for secure user management
- **Database** - PostgreSQL with Alembic migrations

## 🏗️ Architecture

```
job-application/
├── Frontend/           # Next.js 15 + React 19 Frontend
│   ├── app/           # App Router pages
│   ├── components/    # Reusable React components
│   └── lib/          # Utilities and configurations
├── backend/           # FastAPI Backend
│   ├── app/          # API routes and business logic
│   ├── alembic/      # Database migrations
│   └── uploads/      # File storage and vector databases
└── README.md         # Project documentation
```

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18+ and npm
- **Python** 3.9+
- **PostgreSQL** 14+
- **Git**

### 1. Clone Repository
```bash
git clone https://github.com/tinomudashe/agent-apply.git
cd agent-apply
```

### 2. Frontend Setup
```bash
cd Frontend
npm install
npm run dev
```
*Runs on http://localhost:3003*

### 3. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
*Runs on http://localhost:8000*

### 4. Environment Configuration
Create `.env` files in both directories with:

**Frontend/.env.local:**
```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_clerk_key
CLERK_SECRET_KEY=your_clerk_secret
NEXT_PUBLIC_GOOGLE_TTS_API_KEY=your_google_tts_key
```

**backend/.env:**
```env
DATABASE_URL=postgresql://user:password@localhost/dbname
GOOGLE_API_KEY=your_google_api_key
CLERK_SECRET_KEY=your_clerk_secret
```

## 💫 Safari Compatibility Features

### ✅ **Compatibility Fixes Applied**
- **Optional Chaining Removed** - Replaced `?.` with explicit null checks
- **Array Methods Enhanced** - Safari-compatible loops instead of modern array methods
- **Audio API Optimized** - Enhanced error handling for Safari's strict audio policies
- **Clipboard API** - Fallback for older Safari versions
- **Memory Management** - Improved blob URL and resource cleanup

### 🔧 **Next.js Optimizations**
- **Webpack Configuration** - Safari-specific JavaScript optimizations
- **Bundle Splitting** - Optimized chunk loading for Safari's engine
- **Headers Configuration** - WebKit-specific security headers
- **Polyfills** - Separate chunk for enhanced compatibility

## 🎨 UI Components

### **Enhanced Chat Interface**
- **Message Bubbles** - Multi-layer gradients with enhanced shadows
- **Action Buttons** - Floating panels with backdrop blur effects
- **PDF Generation** - Dropdown with style previews and visual feedback
- **Audio Player** - Real-time progress with state indicators

### **Glassmorphism Dialog**
- **Conversation Management** - Clean, scrollable interface
- **Glass Effects** - Authentic transparency with edge lighting
- **Perfect Corners** - Refined border treatments and corner radius
- **Interactive States** - Smooth transitions and hover effects

## 📱 Mobile Optimization

- **Responsive Typography** - Adaptive font scaling
- **Touch Targets** - Optimized button sizes and spacing
- **Gesture Support** - Enhanced interaction patterns
- **Layout Adaptation** - Single-column layouts for mobile
- **Performance** - GPU-accelerated animations

## 🔒 Security & Performance

- **Authentication** - Clerk-based secure user management
- **API Security** - JWT token validation and CORS configuration
- **Data Protection** - Secure file upload and processing
- **Performance** - Code splitting and lazy loading
- **Monitoring** - Error tracking and logging

## 🛠️ Development

### **Testing Safari Compatibility**
```bash
# Enable Safari Developer Menu
Safari > Preferences > Advanced > Show Develop menu

# Open Web Inspector
Develop > Show Web Inspector > Console

# Test specific features
- Audio playback (requires user interaction)
- Clipboard functionality (may require HTTPS)
- File uploads and processing
```

### **Build for Production**
```bash
# Frontend
cd Frontend
npm run build

# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📊 Technology Stack

### **Frontend**
- **Next.js 15** - React framework with App Router
- **React 19** - Latest React with concurrent features
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Radix UI** - Accessible component primitives
- **Lucide Icons** - Beautiful icon library

### **Backend**
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **Alembic** - Database migration tool
- **FAISS** - Vector similarity search
- **Clerk** - Authentication service
- **PostgreSQL** - Primary database

## 🚀 Deployment

### **Frontend (Vercel)**
```bash
npm run build
vercel deploy
```

### **Backend (Google Cloud)**
```bash
docker build -t job-app-backend .
gcloud run deploy --image gcr.io/project/job-app-backend
```

## 📈 Future Enhancements

- **Real-time Collaboration** - Multi-user chat rooms
- **Advanced Analytics** - Application success tracking
- **Integration Expansion** - More job boards and platforms
- **AI Improvements** - Enhanced conversation context
- **Mobile App** - React Native implementation

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Clerk** - Authentication infrastructure
- **Vercel** - Frontend hosting platform
- **Google Cloud** - Backend infrastructure
- **OpenAI** - AI model integration
- **Radix UI** - Component library

---

**Built with ❤️ by [Tinomudashe Marecha](https://github.com/tinomudashe)**

🔗 **Repository**: https://github.com/tinomudashe/agent-apply
📧 **Contact**: [Your Email]
🌐 **Live Demo**: [Your Live URL] 
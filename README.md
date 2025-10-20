# 🏙️ Local Life Assistant

An AI-powered local life assistant that helps users discover events and restaurants in their area using advanced RAG (Retrieval-Augmented Generation) technology with multiple LLM providers.

## 🌟 Features

- **Intelligent Chat Interface**: Natural language conversations to find local events and restaurants
- **Multi-LLM Support**: Switch between OpenAI, Anthropic Claude, and Ollama (local models)
- **RAG-Powered Recommendations**: Vector similarity search with ChromaDB for relevant suggestions
- **Dual Interface**: Both web UI and command-line interface
- **Real-time Chat**: Conversational context maintained across interactions
- **Rich Recommendations**: Detailed cards with ratings, prices, locations, and explanations

## 🏗️ Architecture

```
┌──────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │  FastAPI Backend│    │    ChromaDB     │
│                  │    │                 │    │                 │
│ • Chat Interface │◄──►│ • RAG Engine    │◄──►│ • Vector Store  │
│ • Recommendations│    │ • Multi-LLM     │    │ • Embeddings    │
│ • Settings       │    │ • API Endpoints │    │ • Collections   │
└──────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   CLI Interface │    │   Mock Data     │
│                 │    │                 │
│ • Rich Display  │    │ • Events        │
│ • Commands      │    │ • Restaurants   │
│ • Interactive   │    │ • Realistic     │
└─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### 1. Clone and Setup

```bash
git clone <repository-url>
cd LocalLifeAssistant
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp ../.env.example .env
# Edit .env with your OpenAI API key
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install
```

### 4. Environment Configuration

Create a `.env` file in the project root directory (copy from `.env.example`):

```env
# Required: OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Optional: Eventbrite API Configuration
EVENTBRITE_API_KEY=your_eventbrite_api_key_here

# Optional: Server Configuration
PORT=8000
HOST=0.0.0.0
```

**Important**: You must set your OpenAI API key for the application to work!

## 🎯 Usage

### Option 1: Web Interface

1. **Start the Backend**:
   ```bash
   # Option 1: Use the startup script (recommended)
   python start_backend.py
   
   # Option 2: Manual start
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Start the Frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open your browser** to `http://localhost:3000`

### Option 2: Command Line Interface

```bash
cd cli
python assistant_cli.py
```

## 💬 Example Queries

Try these natural language queries:

- "Find me a jazz concert this weekend"
- "What restaurants are good for a date night?"
- "Show me free events in Brooklyn"
- "I want to try some new cuisine"
- "What networking events are happening?"
- "Find me a romantic Italian restaurant"
- "Show me tech meetups this week"

## 🔧 API Endpoints

### Chat Endpoints

- `POST /api/chat` - Main conversational endpoint
- `POST /api/chat/simple` - Simplified chat endpoint

### Recommendation Endpoints

- `GET /api/recommendations` - Get recommendations with filters
- `GET /api/events` - Search events only
- `GET /api/restaurants` - Search restaurants only
- `GET /api/search` - Search both events and restaurants

### Utility Endpoints

- `GET /health` - Health check
- `GET /stats` - Database statistics

## 🛠️ CLI Commands

When using the CLI interface:

- `/help` - Show available commands
- `/clear` - Clear conversation history
- `/llm <provider>` - Switch LLM provider
- `/stats` - Show database statistics
- `/exit` - Exit the application

## 🧠 LLM Providers

### OpenAI (Default)
- Models: GPT-3.5-turbo, GPT-4
- Requires: OpenAI API key

### Anthropic Claude
- Models: Claude-3-sonnet, Claude-3-haiku
- Requires: Anthropic API key

### Ollama (Local)
- Models: llama2, codellama, mistral
- Requires: Ollama running locally on port 11434

## 📊 Data Schema

### Events
```json
{
  "event_id": "string",
  "title": "string",
  "description": "string",
  "start_datetime": "ISO datetime",
  "end_datetime": "ISO datetime",
  "venue_name": "string",
  "venue_city": "string",
  "categories": ["array"],
  "is_free": boolean,
  "ticket_min_price": "string",
  "image_url": "string",
  "event_url": "string"
}
```

### Restaurants
```json
{
  "restaurant_id": "string",
  "name": "string",
  "description": "string",
  "cuisine_type": "string",
  "price_range": "string",
  "rating": number,
  "venue_city": "string",
  "categories": ["array"],
  "is_open_now": boolean
}
```

## 🔍 How It Works

1. **Intent Parsing**: Natural language queries are analyzed to extract:
   - Type (event vs restaurant)
   - Location preferences
   - Price range
   - Categories/interest
   - Time preferences

2. **Vector Search**: ChromaDB performs semantic similarity search using embeddings

3. **Context Formatting**: Relevant results are formatted for the LLM

4. **Response Generation**: LLM generates personalized recommendations with explanations

5. **Result Presentation**: Rich cards display recommendations with all relevant details

## 🧪 Testing

### Backend Testing
```bash
cd backend
python -m pytest tests/
```

### API Testing
```bash
# Test health endpoint
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Find me a jazz concert", "conversation_history": []}'
```

## 🚀 Development & Deployment Guide

### 🔧 **Development Workflow**

#### **Making Product Logic Changes**

1. **Backend Changes** (`backend/app/main.py`):
   ```bash
   # Edit the main application logic
   nano backend/app/main.py
   
   # Test locally
   python start_backend.py
   ```

2. **Frontend Changes** (`frontend/src/`):
   ```bash
   # Edit React components
   nano frontend/src/components/YourComponent.tsx
   
   # Test locally
   cd frontend
   npm run dev
   ```

3. **API Changes**:
   ```bash
   # Add new endpoints in backend/app/main.py
   # Update frontend API client in frontend/src/api/client.ts
   ```

#### **Testing Changes Locally**

```bash
# Start backend
python start_backend.py

# Start frontend (in another terminal)
cd frontend
npm run dev

# Test at http://localhost:3000
```

### 🐳 **Docker Deployment (Production)**

#### **Prerequisites**
- DigitalOcean Droplet (or any VPS)
- Domain name with Cloudflare DNS
- SSH access to your server

#### **Initial Server Setup**

1. **Connect to your server**:
   ```bash
   ssh root@138.197.222.160
   ```

2. **Run the setup script**:
   ```bash
   wget https://raw.githubusercontent.com/YOUR_USERNAME/LocalLifeAssistant/feature/llm-city-extraction/deploy/docker-setup.sh
   chmod +x docker-setup.sh
   ./docker-setup.sh
   ```

#### **Deploying Changes**

1. **Push your changes to GitHub**:
   ```bash
   git add .
   git commit -m "Your changes description"
   git push origin feature/llm-city-extraction
   ```

2. **Deploy to production**:
   ```bash
   # SSH into your server
   ssh root@138.197.222.160
   
   # Navigate to the project
   cd /opt/locallifeassistant
   
   # Pull latest changes
   git pull origin feature/llm-city-extraction
   
   # Rebuild and deploy
   cd deploy
   docker-compose build --no-cache
   docker-compose up -d
   ```

#### **Environment Configuration**

1. **Update environment variables**:
   ```bash
   # On your server
   cd /opt/locallifeassistant/deploy
   nano .env
   ```

2. **Required environment variables**:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

#### **Monitoring Deployment**

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs nginx

# Restart services if needed
docker-compose restart backend
```

### 🌐 **Domain & SSL Setup**

#### **Cloudflare Configuration**

1. **Add DNS Records**:
   - `A` record: `locomoco.lijietu.com` → `YOUR_DROPLET_IP`
   - `A` record: `www.locomoco.lijietu.com` → `YOUR_DROPLET_IP`
   - Enable **Proxy** (orange cloud) ✅

2. **SSL Settings**:
   - SSL/TLS encryption mode: **Full (strict)**
   - Always Use HTTPS: **On**

#### **Nginx Configuration**

The application uses Nginx as a reverse proxy:
- **Frontend**: `https://locomoco.lijietu.com/` → React app
- **API**: `https://locomoco.lijietu.com/api/` → FastAPI backend

### 🔄 **Common Deployment Scenarios**

#### **Scenario 1: Adding New Features**

```bash
# 1. Develop locally
# Edit your code...

# 2. Test locally
python start_backend.py
cd frontend && npm run dev

# 3. Commit and push
git add .
git commit -m "Add new feature: description"
git push origin feature/llm-city-extraction

# 4. Deploy to production
ssh root@138.197.222.160
cd /opt/locallifeassistant
git pull origin feature/llm-city-extraction
cd deploy
docker-compose build --no-cache
docker-compose up -d
```

#### **Scenario 2: Updating Dependencies**

```bash
# 1. Update requirements.txt or package.json
# Edit backend/requirements.txt or frontend/package.json

# 2. Deploy with rebuild
cd deploy
docker-compose build --no-cache
docker-compose up -d
```

#### **Scenario 3: Environment Variable Changes**

```bash
# 1. Update .env file on server
cd /opt/locallifeassistant/deploy
nano .env

# 2. Restart services
docker-compose restart backend
```

#### **Scenario 4: Database/Cache Reset**

```bash
# Clear ChromaDB cache
docker-compose down
docker volume rm deploy_chroma_data
docker-compose up -d
```

### 🛠️ **Troubleshooting Deployment**

#### **Common Issues**

1. **"Disconnected" Error**:
   ```bash
   # Check if API is accessible
   curl https://locomoco.lijietu.com/api/health
   
   # Check Nginx logs
   docker-compose logs nginx
   ```

2. **Build Failures**:
   ```bash
   # Check build logs
   docker-compose build --no-cache
   
   # Check for syntax errors
   docker-compose config
   ```

3. **Container Not Starting**:
   ```bash
   # Check container status
   docker-compose ps
   
   # Check logs
   docker-compose logs backend
   ```

#### **Useful Commands**

```bash
# View all containers
docker ps -a

# Restart specific service
docker-compose restart backend

# View real-time logs
docker-compose logs -f backend

# Access container shell
docker exec -it locallifeassistant-backend bash

# Check disk usage
df -h

# Check memory usage
free -h
```

### 📊 **Production Monitoring**

#### **Health Checks**

```bash
# Backend health
curl https://locomoco.lijietu.com/api/health

# Frontend accessibility
curl https://locomoco.lijietu.com/

# Direct backend (bypassing Nginx)
curl http://138.197.222.160:8000/health
```

#### **Performance Monitoring**

```bash
# Check container resource usage
docker stats

# Check system resources
htop
```

### 🔐 **Security Considerations**

- **API Keys**: Store in environment variables, never in code
- **CORS**: Configured for your domain only
- **SSL**: Enabled via Cloudflare
- **Firewall**: Only ports 80, 443, and 22 open
- **Updates**: Regularly update Docker images and system packages

### 📝 **Deployment Checklist**

Before deploying to production:

- [ ] Code tested locally
- [ ] Environment variables configured
- [ ] Domain DNS pointing to server
- [ ] SSL certificate active
- [ ] CORS origins updated
- [ ] API keys valid and not expired
- [ ] Database/cache cleared if needed
- [ ] Backup created (if applicable)

### 🚨 **Emergency Procedures**

#### **Rollback Deployment**

```bash
# Revert to previous commit
git log --oneline
git reset --hard PREVIOUS_COMMIT_HASH
git push origin feature/llm-city-extraction --force

# Redeploy
cd deploy
docker-compose build --no-cache
docker-compose up -d
```

#### **Service Recovery**

```bash
# Restart all services
docker-compose restart

# If containers won't start
docker-compose down
docker-compose up -d

# If still failing, check logs
docker-compose logs
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **ChromaDB Connection Issues**
   - Ensure ChromaDB is properly installed
   - Check the persist directory permissions

2. **LLM Provider Errors**
   - Verify API keys are correctly set
   - Check network connectivity
   - Ensure sufficient API credits

3. **Frontend Connection Issues**
   - Verify backend is running on port 8000
   - Check CORS settings
   - Ensure proxy configuration is correct

### Getting Help

- Check the logs for detailed error messages
- Verify all dependencies are installed
- Ensure environment variables are set correctly
- Test individual components separately

## 🔮 Future Enhancements

- [ ] Real-time data integration (Eventbrite, Yelp APIs)
- [ ] User preferences and history
- [ ] Location-based filtering
- [ ] Calendar integration
- [ ] Social features (sharing, reviews)
- [ ] Mobile app
- [ ] Voice interface
- [ ] Multi-language support

## 📞 Support

For questions or issues:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting section

---

Built with ❤️ using FastAPI, React, ChromaDB, and modern AI technologies.

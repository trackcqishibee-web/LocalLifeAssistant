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
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │   FastAPI Backend│    │   ChromaDB      │
│                 │    │                 │    │                 │
│ • Chat Interface│◄──►│ • RAG Engine    │◄──►│ • Vector Store  │
│ • Recommendations│    │ • Multi-LLM     │    │ • Embeddings    │
│ • Settings      │    │ • API Endpoints │    │ • Collections   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
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
# Edit .env with your API keys
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install
```

### 4. Environment Configuration

Create a `.env` file in the backend directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
DEFAULT_LLM_PROVIDER=openai
CHROMA_PERSIST_DIRECTORY=./chroma_db
```

## 🎯 Usage

### Option 1: Web Interface

1. **Start the Backend**:
   ```bash
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

## 🚀 Deployment

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build
```

### Production Considerations
- Set up proper CORS origins
- Use environment-specific configurations
- Implement rate limiting
- Add authentication if needed
- Set up monitoring and logging

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

#!/bin/bash

# Startup script for the Local Life Assistant frontend

echo "🎨 Starting Local Life Assistant Frontend..."
echo "🌐 Frontend will be available at: http://localhost:3000"
echo "🛑 Press Ctrl+C to stop the server"
echo "----------------------------------------"

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Start the development server
npm run dev

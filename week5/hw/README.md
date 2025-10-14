# Vue Social Media Website

A modern social media website built with Vue 3, Firebase Authentication, and Firestore. Users can create, read, update, and delete messages, like posts, and comment on messages in real-time.

## Features

- 🔐 **User Authentication**: Sign up, sign in, and sign out using Firebase Auth
- 📝 **Message Management**: Create, edit, and delete messages (only for authenticated users)
- 👀 **Public Browsing**: Anyone can view all messages without authentication
- ❤️ **Like System**: Like and unlike messages with real-time updates
- 💬 **Comments**: Add comments to messages with real-time updates
- 📱 **Responsive Design**: Beautiful, mobile-friendly interface with Tailwind CSS
- ⚡ **Real-time Updates**: All changes sync instantly across all users

## Tech Stack

- **Frontend**: Vue 3 (Composition API)
- **Styling**: Tailwind CSS
- **Backend**: Firebase Authentication + Firestore
- **Build Tool**: Vite

## Project Structure

```
src/
├── main.js                 # App entry point
├── App.vue                 # Main app component
├── firebase.js             # Firebase configuration
├── style.css               # Global styles with Tailwind
├── components/
│   ├── Navbar.vue          # Navigation with auth buttons
│   ├── AuthModal.vue       # Login/Register modal
│   ├── MessageForm.vue     # Create/Edit message form
│   ├── MessageCard.vue     # Display message with actions
│   └── CommentSection.vue  # Comments for each message
└── composables/
    ├── useAuth.js          # Authentication logic
    └── useMessages.js      # Firestore CRUD operations
```

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
npm install
```

### 2. Firebase Project Setup

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project" or "Add project"
3. Enter project name (e.g., "vue-social-media")
4. Enable Google Analytics (optional)
5. Click "Create project"

### 3. Enable Authentication

1. In your Firebase project, go to "Authentication" in the left sidebar
2. Click "Get started"
3. Go to "Sign-in method" tab
4. Enable "Email/Password" provider
5. Click "Save"

### 4. Create Firestore Database

1. Go to "Firestore Database" in the left sidebar
2. Click "Create database"
3. Choose "Start in test mode" (we'll update rules later)
4. Select a location for your database
5. Click "Done"

### 5. Get Firebase Configuration

1. Go to Project Settings (gear icon)
2. Scroll down to "Your apps" section
3. Click the web icon (`</>`) to add a web app
4. Enter app nickname (e.g., "vue-social-media-web")
5. Click "Register app"
6. Copy the Firebase configuration object

### 6. Configure Environment Variables

1. Copy `env.template` to `.env.local`:
   ```bash
   cp env.template .env.local
   ```

2. Replace the placeholder values in `.env.local` with your Firebase config:
   ```env
   VITE_FIREBASE_API_KEY=your_actual_api_key
   VITE_FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
   VITE_FIREBASE_PROJECT_ID=your-project-id
   VITE_FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
   VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
   VITE_FIREBASE_APP_ID=your_app_id
   ```

### 7. Set Up Firestore Security Rules

1. Go to Firestore Database → Rules
2. Replace the default rules with:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /messages/{messageId} {
      allow read: if true; // Everyone can read messages
      allow create: if request.auth != null; // Only authenticated users can create
      allow update, delete: if request.auth != null && request.auth.uid == resource.data.authorId; // Only author can edit/delete
      
      match /comments/{commentId} {
        allow read: if true; // Everyone can read comments
        allow create: if request.auth != null; // Only authenticated users can create
        allow delete: if request.auth != null && request.auth.uid == resource.data.authorId; // Only author can delete
      }
    }
  }
}
```

3. Click "Publish"

### 8. Run the Application

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Data Structure

### Messages Collection (`messages`)
```javascript
{
  id: string,                    // Auto-generated document ID
  title: string,                 // Message title
  content: string,                // Message content
  authorId: string,               // User ID of the author
  authorName: string,             // Display name of the author
  timestamp: Firestore Timestamp, // When the message was created
  likes: number,                  // Number of likes
  likedBy: array                  // Array of user IDs who liked this message
}
```

### Comments Subcollection (`messages/{messageId}/comments`)
```javascript
{
  id: string,                    // Auto-generated document ID
  content: string,                // Comment content
  authorId: string,               // User ID of the commenter
  authorName: string,             // Display name of the commenter
  timestamp: Firestore Timestamp  // When the comment was created
}
```

## Features in Detail

### Authentication
- Users can sign up with email/password and display name
- Users can sign in with email/password
- Users can sign out
- Authentication state is persistent across browser sessions

### Message Management
- **Create**: Logged-in users can create new messages with title and content
- **Read**: All users (logged in or not) can view all messages
- **Update**: Only the message author can edit their own messages
- **Delete**: Only the message author can delete their own messages
- Messages are sorted by creation time (newest first)

### Like System
- Logged-in users can like/unlike messages
- Like count is displayed in real-time
- Users can see if they've liked a message (heart icon changes color)

### Comment System
- Logged-in users can add comments to any message
- Comments are displayed in real-time
- Only the comment author can delete their own comments
- Comment count is displayed on each message

### Real-time Updates
- All data changes are synchronized in real-time across all users
- No need to refresh the page to see new messages, likes, or comments
- Uses Firestore's `onSnapshot` listeners for real-time updates

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build

### Project Structure

The project follows Vue 3 Composition API patterns with:
- **Composables**: Reusable logic for authentication and data management
- **Components**: UI components for different parts of the application
- **Real-time listeners**: Automatic updates when data changes
- **Error handling**: User-friendly error messages and loading states

## Troubleshooting

### Common Issues

1. **Firebase connection errors**: Check that your environment variables are correctly set in `.env.local`

2. **Authentication not working**: Ensure Authentication is enabled in Firebase Console and Email/Password provider is configured

3. **Permission denied errors**: Check that your Firestore security rules are correctly set up

4. **Real-time updates not working**: Verify that your Firestore database is in the correct mode and rules allow the operations

### Getting Help

If you encounter issues:
1. Check the browser console for error messages
2. Verify your Firebase configuration
3. Ensure all environment variables are set correctly
4. Check that Firestore security rules match the provided rules

## License

This project is open source and available under the MIT License.

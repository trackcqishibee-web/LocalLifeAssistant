<template>
  <div id="app" class="min-h-screen bg-gray-50">
    <!-- Navigation -->
    <Navbar @show-auth-modal="handleShowAuthModal" />
    
    <!-- Main Content -->
    <main class="max-w-4xl mx-auto px-4 py-8">
      <!-- Loading State -->
      <div v-if="messagesLoading" class="flex justify-center items-center py-12">
        <div class="text-gray-600">Loading messages...</div>
      </div>
      
      <!-- Error State -->
      <div v-else-if="messagesError" class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
        Error loading messages: {{ messagesError }}
      </div>
      
      <!-- Main Content -->
      <div v-else>
        <!-- Message Form (only for logged in users) -->
        <MessageForm
          v-if="currentUser"
          :editing-message="editingMessage"
          @message-saved="handleMessageSaved"
          @edit-cancelled="handleEditCancelled"
        />
        
        <!-- Messages List -->
        <div v-if="messages.length === 0" class="text-center py-12">
          <div class="text-gray-500 text-lg">No messages yet.</div>
          <div v-if="!currentUser" class="text-gray-400 text-sm mt-2">
            Sign in to create the first message!
          </div>
        </div>
        
        <div v-else class="space-y-6">
          <MessageCard
            v-for="message in messages"
            :key="message.id"
            :message="message"
            @edit-message="handleEditMessage"
            @delete-message="handleDeleteMessage"
          />
        </div>
      </div>
    </main>
    
    <!-- Auth Modal -->
    <AuthModal
      :show="showAuthModal"
      :is-login="authModalIsLogin"
      @close="showAuthModal = false"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useAuth } from './composables/useAuth'
import { useMessages } from './composables/useMessages'
import Navbar from './components/Navbar.vue'
import AuthModal from './components/AuthModal.vue'
import MessageForm from './components/MessageForm.vue'
import MessageCard from './components/MessageCard.vue'

const { currentUser } = useAuth()
const { messages, loading: messagesLoading, error: messagesError, deleteMessage } = useMessages()

const showAuthModal = ref(false)
const authModalIsLogin = ref(true)
const editingMessage = ref(null)

const handleShowAuthModal = (data) => {
  if (typeof data === 'object' && data !== null) {
    showAuthModal.value = data.show
    authModalIsLogin.value = data.isLogin
  } else {
    // Fallback for old event format
    showAuthModal.value = true
    authModalIsLogin.value = true
  }
}

const handleMessageSaved = () => {
  editingMessage.value = null
}

const handleEditCancelled = () => {
  editingMessage.value = null
}

const handleEditMessage = (message) => {
  editingMessage.value = message
  // Scroll to top to show the form
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

const handleDeleteMessage = async (messageId) => {
  try {
    await deleteMessage(messageId)
  } catch (error) {
    console.error('Error deleting message:', error)
  }
}
</script>

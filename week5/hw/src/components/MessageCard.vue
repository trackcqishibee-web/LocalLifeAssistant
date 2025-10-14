<template>
  <div class="bg-white rounded-lg shadow-md p-6 mb-4 hover:shadow-lg transition-shadow">
    <div class="flex justify-between items-start mb-3">
      <div class="flex-1">
        <h3 class="text-xl font-semibold text-gray-900 mb-2">{{ message.title }}</h3>
        <div class="flex items-center text-sm text-gray-600 mb-3">
          <span class="font-medium">{{ message.authorName }}</span>
          <span class="mx-2">•</span>
          <span>{{ formatDate(message.timestamp) }}</span>
        </div>
      </div>
      
      <div v-if="isAuthor" class="flex space-x-2">
        <button
          @click="handleEdit"
          class="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
          Edit
        </button>
        <button
          @click="handleDelete"
          class="text-red-600 hover:text-red-800 text-sm font-medium"
        >
          Delete
        </button>
      </div>
    </div>

    <div class="text-gray-700 mb-4 whitespace-pre-wrap">{{ message.content }}</div>

    <div class="flex items-center justify-between border-t pt-4">
      <div class="flex items-center space-x-4">
        <button
          @click="handleLike"
          :disabled="!currentUser"
          class="flex items-center space-x-1 text-gray-600 hover:text-red-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg 
            class="w-5 h-5" 
            :class="{ 'text-red-600 fill-current': isLiked, 'text-gray-400': !isLiked }"
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
          <span class="text-sm">{{ message.likes || 0 }}</span>
        </button>
        
        <button
          @click="toggleComments"
          class="flex items-center space-x-1 text-gray-600 hover:text-blue-600"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <span class="text-sm">{{ commentCount }}</span>
        </button>
      </div>
    </div>

    <!-- Comments Section -->
    <div v-if="showComments" class="mt-4 border-t pt-4">
      <CommentSection :message-id="message.id" @comment-count="updateCommentCount" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAuth } from '../composables/useAuth'
import { useMessages } from '../composables/useMessages'
import CommentSection from './CommentSection.vue'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['edit-message', 'delete-message'])

const { currentUser } = useAuth()
const { toggleLike } = useMessages()

const showComments = ref(false)
const commentCount = ref(0)

const isAuthor = computed(() => {
  return currentUser.value && currentUser.value.uid === props.message.authorId
})

const isLiked = computed(() => {
  const liked = currentUser.value && props.message.likedBy?.includes(currentUser.value.uid)
  console.log('isLiked computed:', liked, 'user:', currentUser.value?.uid, 'likedBy:', props.message.likedBy)
  return liked
})

const formatDate = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString()
}

const handleLike = async () => {
  console.log('Like button clicked')
  console.log('Current user:', currentUser.value)
  console.log('Message:', props.message)
  
  if (!currentUser.value) {
    console.error('No user logged in')
    alert('Please sign in to like messages')
    return
  }
  
  try {
    console.log('Attempting to toggle like for message:', props.message.id, 'user:', currentUser.value.uid)
    await toggleLike(props.message.id, currentUser.value.uid)
    console.log('Like toggled successfully')
  } catch (error) {
    console.error('Error toggling like:', error)
    alert('Error liking message: ' + error.message)
  }
}

const handleEdit = () => {
  emit('edit-message', props.message)
}

const handleDelete = () => {
  if (confirm('Are you sure you want to delete this message?')) {
    emit('delete-message', props.message.id)
  }
}

const toggleComments = () => {
  showComments.value = !showComments.value
}

const updateCommentCount = (count) => {
  commentCount.value = count
}
</script>

<template>
  <div class="space-y-4">
    <!-- Add Comment Form -->
    <div v-if="currentUser" class="bg-gray-50 rounded-lg p-4">
      <form @submit.prevent="handleSubmit" class="space-y-3">
        <textarea
          v-model="newComment"
          placeholder="Write a comment..."
          rows="3"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required
        ></textarea>
        <div class="flex justify-end">
          <button
            type="submit"
            :disabled="loading"
            class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {{ loading ? 'Posting...' : 'Post Comment' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Comments List -->
    <div v-if="comments.length > 0" class="space-y-3">
      <div
        v-for="comment in comments"
        :key="comment.id"
        class="bg-gray-50 rounded-lg p-4"
      >
        <div class="flex justify-between items-start mb-2">
          <div class="flex items-center space-x-2">
            <span class="font-medium text-gray-900">{{ comment.authorName }}</span>
            <span class="text-sm text-gray-500">{{ formatDate(comment.timestamp) }}</span>
          </div>
          <button
            v-if="currentUser && currentUser.uid === comment.authorId"
            @click="handleDeleteComment(comment.id)"
            class="text-red-600 hover:text-red-800 text-sm"
          >
            Delete
          </button>
        </div>
        <div class="text-gray-700 whitespace-pre-wrap">{{ comment.content }}</div>
      </div>
    </div>

    <div v-else class="text-gray-500 text-center py-4">
      No comments yet. Be the first to comment!
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { 
  collection, 
  addDoc, 
  deleteDoc, 
  doc, 
  onSnapshot, 
  query, 
  orderBy,
  serverTimestamp 
} from 'firebase/firestore'
import { db } from '../firebase.js'
import { useAuth } from '../composables/useAuth'

const props = defineProps({
  messageId: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['comment-count'])

const { currentUser } = useAuth()

const comments = ref([])
const newComment = ref('')
const loading = ref(false)
const unsubscribe = ref(null)

const handleSubmit = async () => {
  console.log('Comment submit clicked')
  console.log('Current user:', currentUser.value)
  console.log('New comment:', newComment.value)
  
  if (!currentUser.value) {
    console.error('No user logged in')
    alert('Please sign in to leave a comment')
    return
  }
  
  if (!newComment.value.trim()) {
    console.error('No comment content')
    return
  }
  
  loading.value = true
  
  try {
    console.log('Attempting to add comment to message:', props.messageId)
    const docRef = await addDoc(collection(db, 'messages', props.messageId, 'comments'), {
      content: newComment.value.trim(),
      authorId: currentUser.value.uid,
      authorName: currentUser.value.displayName || currentUser.value.email,
      timestamp: serverTimestamp()
    })
    
    console.log('Comment added successfully:', docRef.id)
    newComment.value = ''
  } catch (error) {
    console.error('Error adding comment:', error)
    alert('Error adding comment: ' + error.message)
  } finally {
    loading.value = false
  }
}

const handleDeleteComment = async (commentId) => {
  if (!confirm('Are you sure you want to delete this comment?')) return
  
  try {
    await deleteDoc(doc(db, 'messages', props.messageId, 'comments', commentId))
  } catch (error) {
    console.error('Error deleting comment:', error)
  }
}

const formatDate = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString()
}

// Set up real-time listener for comments
onMounted(() => {
  console.log('CommentSection mounted for message:', props.messageId)
  const q = query(
    collection(db, 'messages', props.messageId, 'comments'),
    orderBy('timestamp', 'asc')
  )
  
  unsubscribe.value = onSnapshot(q, (snapshot) => {
    console.log('Comments snapshot received:', snapshot.docs.length, 'comments')
    comments.value = snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data(),
      timestamp: doc.data().timestamp?.toDate() || new Date()
    }))
    
    // Emit comment count to parent
    emit('comment-count', comments.value.length)
  }, (error) => {
    console.error('Error listening to comments:', error)
  })
})

onUnmounted(() => {
  if (unsubscribe.value) {
    unsubscribe.value()
  }
})
</script>

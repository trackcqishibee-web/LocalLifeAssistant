import { ref, onMounted } from 'vue'
import { 
  collection, 
  addDoc, 
  updateDoc, 
  deleteDoc, 
  doc, 
  onSnapshot, 
  query, 
  orderBy, 
  serverTimestamp,
  arrayUnion,
  arrayRemove
} from 'firebase/firestore'
import { db } from '../firebase.js'

const messages = ref([])
const loading = ref(true)
const error = ref(null)

export function useMessages() {
  // Initialize real-time listener for messages
  onMounted(() => {
    const q = query(collection(db, 'messages'), orderBy('timestamp', 'desc'))
    
    const unsubscribe = onSnapshot(q, (snapshot) => {
      messages.value = snapshot.docs.map(doc => ({
        id: doc.id,
        ...doc.data(),
        timestamp: doc.data().timestamp?.toDate() || new Date()
      }))
      loading.value = false
    }, (err) => {
      error.value = err.message
      loading.value = false
    })
    
    // Cleanup listener on unmount
    return () => unsubscribe()
  })

  const createMessage = async (title, content, authorName) => {
    try {
      error.value = null
      const docRef = await addDoc(collection(db, 'messages'), {
        title,
        content,
        authorName,
        timestamp: serverTimestamp(),
        likes: 0,
        likedBy: []
      })
      return docRef.id
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  const updateMessage = async (id, title, content) => {
    try {
      error.value = null
      const messageRef = doc(db, 'messages', id)
      await updateDoc(messageRef, {
        title,
        content,
        timestamp: serverTimestamp()
      })
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  const deleteMessage = async (id) => {
    try {
      error.value = null
      await deleteDoc(doc(db, 'messages', id))
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  const toggleLike = async (messageId, userId) => {
    try {
      console.log('toggleLike called with:', { messageId, userId })
      error.value = null
      const messageRef = doc(db, 'messages', messageId)
      const message = messages.value.find(m => m.id === messageId)
      
      console.log('Found message:', message)
      
      if (!message) {
        console.error('Message not found')
        return
      }
      
      const isLiked = message.likedBy?.includes(userId) || false
      console.log('Current like status:', isLiked)
      console.log('Current likes count:', message.likes)
      console.log('Current likedBy array:', message.likedBy)
      
      if (isLiked) {
        // Unlike
        console.log('Removing like...')
        await updateDoc(messageRef, {
          likes: message.likes - 1,
          likedBy: arrayRemove(userId)
        })
        console.log('Like removed successfully')
      } else {
        // Like
        console.log('Adding like...')
        await updateDoc(messageRef, {
          likes: message.likes + 1,
          likedBy: arrayUnion(userId)
        })
        console.log('Like added successfully')
      }
    } catch (err) {
      console.error('Error in toggleLike:', err)
      error.value = err.message
      throw err
    }
  }

  const clearError = () => {
    error.value = null
  }

  return {
    messages,
    loading,
    error,
    createMessage,
    updateMessage,
    deleteMessage,
    toggleLike,
    clearError
  }
}

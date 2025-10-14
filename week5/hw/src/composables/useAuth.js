import { ref, onMounted } from 'vue'
import { 
  createUserWithEmailAndPassword, 
  signInWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged,
  updateProfile
} from 'firebase/auth'
import { auth } from '../firebase.js'

const currentUser = ref(null)
const loading = ref(true)
const error = ref(null)

export function useAuth() {
  // Initialize auth state listener
  onMounted(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      currentUser.value = user
      loading.value = false
    })
    
    // Cleanup listener on unmount
    return () => unsubscribe()
  })

  const signUp = async (email, password, displayName) => {
    try {
      error.value = null
      const userCredential = await createUserWithEmailAndPassword(auth, email, password)
      
      // Update the user's display name
      await updateProfile(userCredential.user, {
        displayName: displayName
      })
      
      return userCredential.user
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  const signIn = async (email, password) => {
    try {
      error.value = null
      const userCredential = await signInWithEmailAndPassword(auth, email, password)
      return userCredential.user
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  const signOutUser = async () => {
    try {
      error.value = null
      await signOut(auth)
    } catch (err) {
      error.value = err.message
      throw err
    }
  }

  const clearError = () => {
    error.value = null
  }

  return {
    currentUser,
    loading,
    error,
    signUp,
    signIn,
    signOut: signOutUser,
    clearError
  }
}

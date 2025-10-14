<template>
  <nav class="bg-blue-600 text-white shadow-lg">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <div class="flex items-center">
          <h1 class="text-xl font-bold">Vue Social Media</h1>
        </div>
        
        <div class="flex items-center space-x-4">
          <div v-if="loading" class="text-sm">
            Loading...
          </div>
          
          <div v-else-if="currentUser" class="flex items-center space-x-4">
            <span class="text-sm">Welcome, {{ currentUser.displayName || currentUser.email }}</span>
            <button
              @click="handleSignOut"
              class="bg-red-500 hover:bg-red-600 px-4 py-2 rounded-md text-sm font-medium transition-colors"
            >
              Sign Out
            </button>
          </div>
          
          <div v-else class="flex items-center space-x-2">
            <button
              @click="showModal(true)"
              class="bg-green-500 hover:bg-green-600 px-4 py-2 rounded-md text-sm font-medium transition-colors"
            >
              Sign In
            </button>
            <button
              @click="showModal(false)"
              class="bg-blue-500 hover:bg-blue-600 px-4 py-2 rounded-md text-sm font-medium transition-colors"
            >
              Sign Up
            </button>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue'
import { useAuth } from '../composables/useAuth'

const { currentUser, loading, signOut } = useAuth()

const showAuthModal = ref(false)
const isLogin = ref(true)

const emit = defineEmits(['show-auth-modal'])

const handleSignOut = async () => {
  try {
    await signOut()
  } catch (error) {
    console.error('Error signing out:', error)
  }
}

// Emit event to parent to show auth modal with mode
const showModal = (login = true) => {
  isLogin.value = login
  emit('show-auth-modal', { show: true, isLogin: login })
}

// Expose methods for parent component
defineExpose({
  showModal
})
</script>

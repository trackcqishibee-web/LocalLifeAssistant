<template>
  <div v-if="show" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 w-full max-w-md mx-4">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-2xl font-bold text-gray-900">
          {{ isLogin ? 'Sign In' : 'Sign Up' }}
        </h2>
        <button
          @click="$emit('close')"
          class="text-gray-500 hover:text-gray-700 text-2xl"
        >
          ×
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div v-if="!isLogin">
          <label for="displayName" class="block text-sm font-medium text-gray-700 mb-1">
            Display Name
          </label>
          <input
            id="displayName"
            v-model="displayName"
            type="text"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter your display name"
          />
        </div>

        <div>
          <label for="email" class="block text-sm font-medium text-gray-700 mb-1">
            Email
          </label>
          <input
            id="email"
            v-model="email"
            type="email"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter your email"
          />
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700 mb-1">
            Password
          </label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter your password"
          />
        </div>

        <div v-if="error" class="text-red-600 text-sm">
          {{ error }}
        </div>

        <div class="flex space-x-3">
          <button
            type="submit"
            :disabled="loading"
            class="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {{ loading ? 'Loading...' : (isLogin ? 'Sign In' : 'Sign Up') }}
          </button>
        </div>

        <div class="text-center">
          <button
            type="button"
            @click="toggleMode"
            class="text-blue-600 hover:text-blue-800 text-sm"
          >
            {{ isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in" }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useAuth } from '../composables/useAuth'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  isLogin: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['close'])

const { signIn, signUp, error, clearError } = useAuth()

const isLogin = ref(props.isLogin)
const email = ref('')
const password = ref('')
const displayName = ref('')
const loading = ref(false)

const toggleMode = () => {
  isLogin.value = !isLogin.value
  clearError()
}

const handleSubmit = async () => {
  loading.value = true
  clearError()
  
  try {
    if (isLogin.value) {
      await signIn(email.value, password.value)
    } else {
      await signUp(email.value, password.value, displayName.value)
    }
    
    // Close modal on success
    emit('close')
    
    // Reset form
    email.value = ''
    password.value = ''
    displayName.value = ''
  } catch (err) {
    console.error('Auth error:', err)
  } finally {
    loading.value = false
  }
}

// Update isLogin when prop changes
watch(() => props.isLogin, (newValue) => {
  isLogin.value = newValue
})

// Clear form when modal closes
watch(() => props.show, (newValue) => {
  if (!newValue) {
    email.value = ''
    password.value = ''
    displayName.value = ''
    clearError()
  }
})
</script>

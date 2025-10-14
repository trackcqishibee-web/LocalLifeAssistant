<template>
  <div class="bg-white rounded-lg shadow-md p-6 mb-6">
    <h3 class="text-lg font-semibold text-gray-900 mb-4">Create New Message</h3>
    
    <form @submit.prevent="handleSubmit" class="space-y-4">
      <div>
        <label for="title" class="block text-sm font-medium text-gray-700 mb-1">
          Title
        </label>
        <input
          id="title"
          v-model="title"
          type="text"
          required
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Enter message title"
        />
      </div>

      <div>
        <label for="content" class="block text-sm font-medium text-gray-700 mb-1">
          Content
        </label>
        <textarea
          id="content"
          v-model="content"
          required
          rows="4"
          class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Enter your message content"
        ></textarea>
      </div>

      <div v-if="error" class="text-red-600 text-sm">
        {{ error }}
      </div>

      <div class="flex justify-end space-x-3">
        <button
          v-if="isEditing"
          type="button"
          @click="cancelEdit"
          class="px-4 py-2 text-gray-600 hover:text-gray-800"
        >
          Cancel
        </button>
        <button
          type="submit"
          :disabled="loading"
          class="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {{ loading ? 'Saving...' : (isEditing ? 'Update Message' : 'Post Message') }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useMessages } from '../composables/useMessages'
import { useAuth } from '../composables/useAuth'

const props = defineProps({
  editingMessage: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['message-saved', 'edit-cancelled'])

const { createMessage, updateMessage, error, clearError } = useMessages()
const { currentUser } = useAuth()

const title = ref('')
const content = ref('')
const loading = ref(false)
const isEditing = ref(false)

const handleSubmit = async () => {
  if (!currentUser.value) return
  
  loading.value = true
  clearError()
  
  try {
    if (isEditing.value && props.editingMessage) {
      await updateMessage(props.editingMessage.id, title.value, content.value)
    } else {
      await createMessage(title.value, content.value, currentUser.value.displayName || currentUser.value.email)
    }
    
    // Reset form
    title.value = ''
    content.value = ''
    isEditing.value = false
    
    emit('message-saved')
  } catch (err) {
    console.error('Error saving message:', err)
  } finally {
    loading.value = false
  }
}

const cancelEdit = () => {
  title.value = ''
  content.value = ''
  isEditing.value = false
  emit('edit-cancelled')
}

// Watch for editing message changes
watch(() => props.editingMessage, (newMessage) => {
  if (newMessage) {
    title.value = newMessage.title
    content.value = newMessage.content
    isEditing.value = true
  } else {
    title.value = ''
    content.value = ''
    isEditing.value = false
  }
}, { immediate: true })
</script>

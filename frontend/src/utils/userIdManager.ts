/**
 * Anonymous user ID management utilities
 */

const USER_ID_KEY = 'anonymous_user_id';

export function getOrCreateUserId(): string {
  // Check if user ID exists in localStorage
  let userId = localStorage.getItem(USER_ID_KEY);
  
  if (!userId) {
    // Generate new anonymous user ID
    const timestamp = Date.now();
    const randomString = Math.random().toString(36).substr(2, 9);
    userId = `user_${timestamp}_${randomString}`;
    
    // Save to localStorage
    localStorage.setItem(USER_ID_KEY, userId);
    console.log('Created new anonymous user ID:', userId);
  } else {
    console.log('Using existing user ID:', userId);
  }
  
  return userId;
}

export function getUserId(): string | null {
  return localStorage.getItem(USER_ID_KEY);
}

export function clearUserId(): void {
  localStorage.removeItem(USER_ID_KEY);
}

export function setUserId(userId: string): void {
  localStorage.setItem(USER_ID_KEY, userId);
}

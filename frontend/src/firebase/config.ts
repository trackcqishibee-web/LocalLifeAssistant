import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider } from 'firebase/auth';

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyBuyz1n59jmzVPKSgd-rCszyShpvBmRsq8",
  authDomain: "locomoco-53d3e.firebaseapp.com",
  projectId: "locomoco-53d3e",
  storageBucket: "locomoco-53d3e.firebasestorage.app",
  messagingSenderId: "1091029977613",
  appId: "1:1091029977613:web:288ee80f568dd97de1a344",
  measurementId: "G-3D8RHWZ9GP"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Authentication and get a reference to the service
export const auth = getAuth(app);

// Initialize Google Auth Provider
export const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({
  prompt: 'select_account'
});

export default app;

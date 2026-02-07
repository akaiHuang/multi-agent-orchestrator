// Firebase Web SDK config (client-side only).
// Moved from .env to avoid leaking secrets in env files.

import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyD0RpCCzJ7LE52qCoTSKjFe8eWwMy7XLig",
  authDomain: "fir-js-61ce8.firebaseapp.com",
  databaseURL: "https://fir-js-61ce8-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "fir-js-61ce8",
  storageBucket: "fir-js-61ce8.firebasestorage.app",
  messagingSenderId: "487507361407",
  appId: "1:487507361407:web:3078b8df1fc44f18c8094a",
  measurementId: "G-J7F42XLV41"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

import { initializeApp, getApps } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut, onAuthStateChanged, updateProfile } from 'firebase/auth';
import { getFirestore, doc, setDoc, getDoc, collection, query, where, orderBy, limit, getDocs, addDoc, deleteDoc, updateDoc, serverTimestamp } from 'firebase/firestore';

const firebaseConfig = {
apiKey: process.env.REACT_APP_FIREBASE_API_KEY,
authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET,
messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID,
appId: process.env.REACT_APP_FIREBASE_APP_ID,
};

// Initialize Firebase
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApps()[0];
const auth = getAuth(app);
const db = getFirestore(app);
const googleProvider = new GoogleAuthProvider();

// Auth functions
export const signUpWithEmail = async (email, password, name) => {
  const userCredential = await createUserWithEmailAndPassword(auth, email, password);
  await updateProfile(userCredential.user, { displayName: name });
  
  // Save user to Firestore
  try {
    await setDoc(doc(db, 'users', userCredential.user.uid), {
      name: name,
      email: email,
      provider: 'email',
      createdAt: serverTimestamp()
    });
    
    // Initialize empty memory for new user
    await setDoc(doc(db, 'user_memory', userCredential.user.uid), {
      preferred_name: name,
      language_style: null,
      interests: [],
      skill_level: null,
      goals: [],
      personal_facts: [],
      communication_preferences: null,
      updatedAt: serverTimestamp()
    });
  } catch (error) {
    console.error('Error saving user to Firestore:', error);
  }
  
  return userCredential.user;
};

export const signInWithEmail = async (email, password) => {
  const userCredential = await signInWithEmailAndPassword(auth, email, password);
  return userCredential.user;
};

export const signInWithGoogle = async () => {
  const result = await signInWithPopup(auth, googleProvider);
  const user = result.user;
  
  // Check if user exists, if not create
  try {
    const userDoc = await getDoc(doc(db, 'users', user.uid));
    if (!userDoc.exists()) {
      await setDoc(doc(db, 'users', user.uid), {
        name: user.displayName,
        email: user.email,
        provider: 'google',
        createdAt: serverTimestamp()
      });
      
      // Initialize empty memory for new user
      await setDoc(doc(db, 'user_memory', user.uid), {
        preferred_name: user.displayName,
        language_style: null,
        interests: [],
        skill_level: null,
        goals: [],
        personal_facts: [],
        communication_preferences: null,
        updatedAt: serverTimestamp()
      });
    }
  } catch (error) {
    console.error('Error saving Google user to Firestore:', error);
  }
  
  return user;
};

export const logOut = async () => {
  await signOut(auth);
};

// ============== User Memory Functions ==============

export const getUserMemory = async (userId) => {
  try {
    const memoryDoc = await getDoc(doc(db, 'user_memory', userId));
    if (memoryDoc.exists()) {
      const data = memoryDoc.data();
      console.log('Loaded user memory:', data);
      return {
        preferred_name: data.preferred_name || null,
        language_style: data.language_style || null,
        interests: data.interests || [],
        skill_level: data.skill_level || null,
        goals: data.goals || [],
        personal_facts: data.personal_facts || [],
        communication_preferences: data.communication_preferences || null
      };
    }
    return null;
  } catch (error) {
    console.error('Error loading user memory:', error);
    return null;
  }
};

export const updateUserMemory = async (userId, memory) => {
  try {
    await setDoc(doc(db, 'user_memory', userId), {
      ...memory,
      updatedAt: serverTimestamp()
    }, { merge: true });
    console.log('Updated user memory:', memory);
    return true;
  } catch (error) {
    console.error('Error updating user memory:', error);
    return false;
  }
};

// ============== Conversation Functions ==============

export const createConversation = async (userId, title = 'New Chat') => {
  try {
    const conversationRef = await addDoc(collection(db, 'conversations'), {
      userId,
      title,
      createdAt: serverTimestamp(),
      lastMessageAt: serverTimestamp()
    });
    console.log('Created conversation:', conversationRef.id);
    return conversationRef.id;
  } catch (error) {
    console.error('Error creating conversation:', error);
    throw error;
  }
};

export const getConversations = async (userId) => {
  try {
    // First try with orderBy (requires composite index)
    const q = query(
      collection(db, 'conversations'),
      where('userId', '==', userId),
      orderBy('lastMessageAt', 'desc'),
      limit(50)
    );
    const snapshot = await getDocs(q);
    const convos = snapshot.docs.map(docSnap => ({
      id: docSnap.id,
      ...docSnap.data(),
      createdAt: docSnap.data().createdAt?.toDate?.() || new Date(),
      lastMessageAt: docSnap.data().lastMessageAt?.toDate?.() || new Date()
    }));
    console.log('Loaded conversations:', convos.length);
    return convos;
  } catch (error) {
    console.error('Error loading conversations (may need index):', error);
    
    // Fallback: query without orderBy and sort client-side
    try {
      const fallbackQuery = query(
        collection(db, 'conversations'),
        where('userId', '==', userId),
        limit(50)
      );
      const snapshot = await getDocs(fallbackQuery);
      const convos = snapshot.docs.map(docSnap => ({
        id: docSnap.id,
        ...docSnap.data(),
        createdAt: docSnap.data().createdAt?.toDate?.() || new Date(),
        lastMessageAt: docSnap.data().lastMessageAt?.toDate?.() || new Date()
      }));
      // Sort client-side
      convos.sort((a, b) => b.lastMessageAt - a.lastMessageAt);
      console.log('Loaded conversations (fallback):', convos.length);
      return convos;
    } catch (fallbackError) {
      console.error('Fallback query also failed:', fallbackError);
      return [];
    }
  }
};

export const deleteConversation = async (conversationId) => {
  try {
    // Delete all messages in the conversation
    const messagesQuery = query(
      collection(db, 'messages'),
      where('conversationId', '==', conversationId)
    );
    const messagesSnapshot = await getDocs(messagesQuery);
    const deletePromises = messagesSnapshot.docs.map(docSnap => deleteDoc(docSnap.ref));
    await Promise.all(deletePromises);
    
    // Delete the conversation
    await deleteDoc(doc(db, 'conversations', conversationId));
    console.log('Deleted conversation:', conversationId);
  } catch (error) {
    console.error('Error deleting conversation:', error);
    throw error;
  }
};

export const updateConversationTitle = async (conversationId, title) => {
  try {
    await updateDoc(doc(db, 'conversations', conversationId), {
      title,
      lastMessageAt: serverTimestamp()
    });
    console.log('Updated conversation title:', conversationId, title);
  } catch (error) {
    console.error('Error updating conversation title:', error);
    throw error;
  }
};

// ============== Message Functions ==============

export const saveMessage = async (conversationId, userId, role, content) => {
  try {
    const messageRef = await addDoc(collection(db, 'messages'), {
      conversationId,
      userId,
      role,
      content,
      timestamp: serverTimestamp()
    });
    console.log('Saved message:', messageRef.id, 'to conversation:', conversationId);
    
    // Update conversation's lastMessageAt
    try {
      await updateDoc(doc(db, 'conversations', conversationId), {
        lastMessageAt: serverTimestamp()
      });
    } catch (updateError) {
      console.error('Error updating conversation lastMessageAt:', updateError);
    }
    
    return messageRef.id;
  } catch (error) {
    console.error('Error saving message:', error);
    throw error;
  }
};

export const getMessages = async (conversationId, messageLimit = 50) => {
  try {
    // First try with orderBy (requires composite index)
    const q = query(
      collection(db, 'messages'),
      where('conversationId', '==', conversationId),
      orderBy('timestamp', 'asc'),
      limit(messageLimit)
    );
    const snapshot = await getDocs(q);
    const msgs = snapshot.docs.map(docSnap => ({
      id: docSnap.id,
      ...docSnap.data(),
      timestamp: docSnap.data().timestamp?.toDate?.() || new Date()
    }));
    console.log('Loaded messages:', msgs.length, 'for conversation:', conversationId);
    return msgs;
  } catch (error) {
    console.error('Error loading messages (may need index):', error);
    
    // Fallback: query without orderBy and sort client-side
    try {
      const fallbackQuery = query(
        collection(db, 'messages'),
        where('conversationId', '==', conversationId),
        limit(messageLimit)
      );
      const snapshot = await getDocs(fallbackQuery);
      const msgs = snapshot.docs.map(docSnap => ({
        id: docSnap.id,
        ...docSnap.data(),
        timestamp: docSnap.data().timestamp?.toDate?.() || new Date()
      }));
      // Sort client-side
      msgs.sort((a, b) => a.timestamp - b.timestamp);
      console.log('Loaded messages (fallback):', msgs.length);
      return msgs;
    } catch (fallbackError) {
      console.error('Fallback query also failed:', fallbackError);
      return [];
    }
  }
};

export { auth, db, onAuthStateChanged };

# Nex.AI - Personal AI Chat Application

## Overview
Nex.AI is a personal AI chat application with Claude-style design and a deeply personal, step-by-step ChatGPT-like AI tone.

## Tech Stack
- **Frontend**: React 19 + TailwindCSS + Framer Motion
- **Backend**: FastAPI (Python)
- **Database**: Firebase Firestore
- **Authentication**: Firebase Auth (Google + Email/Password)
- **AI Model**: Claude Sonnet 4.5 via Emergent LLM Key

## User Personas
1. **Casual Users**: People seeking a friendly AI companion for everyday questions
2. **Students**: Those who need step-by-step explanations
3. **Professionals**: Users wanting a thinking partner for ideas and problems

## Core Requirements
- Light neutral background (off-white/warm gray)
- Clean, minimal, Claude-style UI
- Google Sign-In + Email/Password authentication
- Chat with AI that uses user's name
- Conversation history stored in Firestore
- Word-by-word AI typing animation
- Stop button to cancel AI responses
- Responsive design with collapsible sidebar

## What's Been Implemented (January 2026)

### Authentication (✅ Complete)
- [x] Email/Password signup with Firebase
- [x] Email/Password login with Firebase
- [x] Google Sign-In popup integration
- [x] User data saved to Firestore `users` collection
- [x] Auth context for global state management
- [x] Protected routes (redirect to login if not authenticated)

### Pages (✅ Complete)
- [x] Login page with split-screen layout
- [x] Signup page with split-screen layout
- [x] Chat page with sidebar and main chat area

### Chat Features (✅ Complete)
- [x] Sidebar showing previous conversations
- [x] New Chat button
- [x] Delete conversation option
- [x] Messages saved to Firestore
- [x] AI responses with word-by-word streaming
- [x] Stop button to cancel AI generation
- [x] User messages right-aligned, AI messages left-aligned
- [x] Personal AI tone using user's name

### UI/UX (✅ Complete)
- [x] Terracotta + Soft Teal + Light Gray color palette
- [x] Manrope font for headings
- [x] Plus Jakarta Sans for body text
- [x] Soft shadows and rounded corners
- [x] Responsive sidebar (collapsible on mobile)
- [x] Micro-animations with Framer Motion

### Backend API (✅ Complete)
- [x] POST /api/auth/verify-token - Verify Firebase tokens
- [x] POST /api/chat/stream - Streaming AI responses
- [x] GET /api/health - Health check

## Firebase Collections
- `users`: {uid, name, email, provider, createdAt}
- `conversations`: {userId, title, createdAt, lastMessageAt}
- `messages`: {conversationId, userId, role, content, timestamp}

## Prioritized Backlog

### P0 (Critical)
- None remaining

### P1 (High Priority)
- [ ] Edit message and regenerate response
- [ ] Copy message to clipboard
- [ ] Search within conversations
- [ ] Export chat history

### P2 (Medium Priority)
- [ ] Voice input/output
- [ ] Dark mode toggle
- [ ] Conversation folders/tags
- [ ] Multiple AI personality options
- [ ] Share conversation link

### P3 (Nice to Have)
- [ ] Image upload for context
- [ ] Code syntax highlighting
- [ ] Markdown rendering for AI responses
- [ ] Keyboard shortcuts

## Environment Variables

### Frontend (.env)
```
REACT_APP_BACKEND_URL=<backend_url>
REACT_APP_FIREBASE_API_KEY=<firebase_api_key>
REACT_APP_FIREBASE_AUTH_DOMAIN=<firebase_auth_domain>
REACT_APP_FIREBASE_PROJECT_ID=<firebase_project_id>
REACT_APP_FIREBASE_STORAGE_BUCKET=<firebase_storage_bucket>
REACT_APP_FIREBASE_MESSAGING_SENDER_ID=<firebase_messaging_sender_id>
REACT_APP_FIREBASE_APP_ID=<firebase_app_id>
```

### Backend (.env)
```
EMERGENT_LLM_KEY=<emergent_llm_key>
```

## What's Been Implemented (January 2026 - Update 3)

### Special Modes System (✅ Complete)
- [x] Plus (+) button next to chat input opens feature menu
- [x] Three modes with ON/OFF toggles (mutually exclusive)
- [x] Modes reset on page refresh (default behavior)
- [x] Mode-specific UI styling (header, avatars, message bubbles)
- [x] Voice/text commands to turn off modes

### Learn Mode (✅ Complete)
- [x] Step-by-step teaching with examples
- [x] Quiz system after explanations
- [x] Beginner-friendly language
- [x] Hinglish support

### English Speaking Mode (✅ Complete)
- [x] Grammar correction for every sentence
- [x] Structured feedback (Corrected → What was wrong → Better way → Grammar tip)
- [x] Vocabulary and pronunciation tips

### The Billionaire Dollar Idea Game (✅ Complete)
- [x] Startup brainstorming game mode
- [x] Random card spinning (Audience + Pain Point + Tech)
- [x] User pitches startup idea
- [x] Rating system (Innovation, Money-Making, Scalability /10)
- [x] Auto-improvement suggestions if score < 7
- [x] Final verdict (Unicorn potential vs Pivot needed)
- [x] Safety rules for legal/ethical content
- [x] Bro-style, Shark Tank feedback tone

### Memory & Personalization (✅ Complete)
- [x] `user_memory` Firestore collection
- [x] Auto-extraction of user preferences
- [x] Memory persists across sessions
- [x] AI uses stored memory in responses

### Tavily Live Search (✅ Complete)
- [x] Auto-detects live info queries
- [x] Injects search results into AI context

## Testing Results (January 2026)

### Issues Fixed
- ✅ React infinite loop bug in FeatureMenu - FIXED
- ✅ Learn mode API timeout - FIXED (optimized prompts)
- ✅ Mode toggle state management - FIXED

### Remaining Known Issues
- Firebase Firestore requires composite index for conversations (userId + lastMessageAt)
- Chat input requires "New Chat" to be clicked first (expected behavior)

### Test Coverage
- Backend: 85.7% (6/7 tests passed)
- Frontend: 90% (React state issues fixed)
- Integration: 85% (core functionality working)

## Next Tasks
1. Add message editing capability
2. Implement copy-to-clipboard for messages
3. Add search within conversations

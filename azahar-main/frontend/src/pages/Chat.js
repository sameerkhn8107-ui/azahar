import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { ChatSidebar } from '../components/ChatSidebar';
import { ChatMessage } from '../components/ChatMessage';
import { ChatInput } from '../components/ChatInput';
import { Menu, X, Sparkles, GraduationCap, Languages, Lightbulb } from 'lucide-react';
import { 
  getConversations, 
  createConversation, 
  deleteConversation,
  getMessages, 
  saveMessage,
  updateConversationTitle,
  getUserMemory,
  updateUserMemory
} from '../lib/firebase';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Keywords to detect mode turn-off requests
const TURN_OFF_KEYWORDS = [
  'turn off', 'stop mode', 'remove mode', 'disable mode', 'exit mode',
  'normal mode', 'regular chat', 'band karo', 'mode hatao', 'mode band',
  'turn this mode off', 'disable the billionaire', 'go back to normal',
  'stop the game', 'stop game mode'
];

export default function Chat() {
  const navigate = useNavigate();
  const { user, loading: authLoading, logout, isAuthenticated } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [loadingConversations, setLoadingConversations] = useState(true);
  const [userMemory, setUserMemory] = useState(null);
  const [memoryLoaded, setMemoryLoaded] = useState(false);
  const [activeMode, setActiveMode] = useState(null); // 'learn' | 'english' | null
  const [pendingModeOff, setPendingModeOff] = useState(false);
  const messagesEndRef = useRef(null);
  const abortControllerRef = useRef(null);

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/login');
    }
  }, [authLoading, isAuthenticated, navigate]);

  // Load user memory
  useEffect(() => {
    const loadUserMemory = async () => {
      if (!user) return;
      try {
        const memory = await getUserMemory(user.uid);
        if (memory) {
          setUserMemory(memory);
        }
      } catch (error) {
        console.error('Error loading user memory:', error);
      } finally {
        setMemoryLoaded(true);
      }
    };

    if (user) {
      loadUserMemory();
    }
  }, [user]);

  // Load conversations
  useEffect(() => {
    const loadConversations = async () => {
      if (!user) return;
      try {
        const convos = await getConversations(user.uid);
        setConversations(convos);
        if (convos.length > 0) {
          setCurrentConversationId(convos[0].id);
        }
      } catch (error) {
        console.error('Error loading conversations:', error);
        toast.error('Failed to load conversations');
      } finally {
        setLoadingConversations(false);
      }
    };

    if (user) {
      loadConversations();
    }
  }, [user]);

  // Load messages when conversation changes
  useEffect(() => {
    const loadMessages = async () => {
      if (!currentConversationId) {
        setMessages([]);
        return;
      }
      try {
        const msgs = await getMessages(currentConversationId);
        setMessages(msgs);
      } catch (error) {
        console.error('Error loading messages:', error);
      }
    };
    loadMessages();
  }, [currentConversationId]);

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  // Check if message is asking to turn off mode
  const checkForModeOffRequest = (content) => {
    const lowerContent = content.toLowerCase();
    return TURN_OFF_KEYWORDS.some(keyword => lowerContent.includes(keyword));
  };

  // Extract memory from conversation
  const extractMemoryFromConversation = useCallback(async (conversationMessages) => {
    if (!user || conversationMessages.length < 2) return;

    try {
      const response = await fetch(`${BACKEND_URL}/api/memory/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: conversationMessages.slice(-10).map(m => ({ role: m.role, content: m.content })),
          current_memory: userMemory
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.extracted_facts && data.extracted_facts.length > 0) {
          setUserMemory(data.updated_memory);
          await updateUserMemory(user.uid, data.updated_memory);
          
          if (data.updated_memory.preferred_name && data.updated_memory.preferred_name !== userMemory?.preferred_name) {
            toast.success(`I'll remember to call you ${data.updated_memory.preferred_name}!`, {
              icon: <Sparkles className="w-4 h-4 text-[#81B29A]" />
            });
          }
        }
      }
    } catch (error) {
      console.error('Error extracting memory:', error);
    }
  }, [user, userMemory]);

  const handleNewChat = async () => {
    if (!user) return;
    try {
      const newConvoId = await createConversation(user.uid, 'New Chat');
      const newConvo = {
        id: newConvoId,
        userId: user.uid,
        title: 'New Chat',
        createdAt: new Date(),
        lastMessageAt: new Date()
      };
      setConversations(prev => [newConvo, ...prev]);
      setCurrentConversationId(newConvoId);
      setMessages([]);
      setMobileMenuOpen(false);
    } catch (error) {
      console.error('Error creating conversation:', error);
      toast.error('Failed to create new chat');
    }
  };

  const handleDeleteConversation = async (convoId) => {
    try {
      await deleteConversation(convoId);
      setConversations(prev => prev.filter(c => c.id !== convoId));
      if (currentConversationId === convoId) {
        const remaining = conversations.filter(c => c.id !== convoId);
        setCurrentConversationId(remaining.length > 0 ? remaining[0].id : null);
      }
      toast.success('Chat deleted');
    } catch (error) {
      console.error('Error deleting conversation:', error);
      toast.error('Failed to delete chat');
    }
  };

  const handleSelectConversation = (convoId) => {
    setCurrentConversationId(convoId);
    setMobileMenuOpen(false);
  };

  const handleStopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsTyping(false);
    }
  }, []);

  const handleModeChange = (mode) => {
    setActiveMode(mode);
    setPendingModeOff(false);
    
    if (mode) {
      const modeNames = {
        'learn': 'Learn Mode',
        'english': 'English Speaking Mode',
        'startup': 'The Billionaire Dollar Idea'
      };
      const icons = {
        'learn': <GraduationCap className="w-4 h-4 text-[#81B29A]" />,
        'english': <Languages className="w-4 h-4 text-[#E07A5F]" />,
        'startup': <Lightbulb className="w-4 h-4 text-[#F2CC8F]" />
      };
      toast.success(`${modeNames[mode]} activated!`, { icon: icons[mode] });
      
      // Auto-start the startup game with intro
      if (mode === 'startup' && messages.length === 0) {
        // The intro will be triggered on first message or auto-shown
      }
    } else {
      toast.info('Mode deactivated - back to normal chat');
    }
  };

  const handleSendMessage = async (content) => {
    if (!content.trim() || !user) return;

    // Check if user is confirming mode turn off
    if (pendingModeOff) {
      const lowerContent = content.toLowerCase();
      if (lowerContent.includes('yes') || lowerContent.includes('haan') || lowerContent.includes('ok')) {
        setActiveMode(null);
        setPendingModeOff(false);
        toast.info('Mode deactivated - back to normal chat');
        
        // Add confirmation message
        const confirmMsg = {
          id: Date.now().toString(),
          role: 'assistant',
          content: "Done! I've turned off the mode. We're back to our regular chat now. What would you like to talk about?",
          timestamp: new Date()
        };
        setMessages(prev => [...prev, confirmMsg]);
        return;
      } else if (lowerContent.includes('no') || lowerContent.includes('nahi') || lowerContent.includes('cancel')) {
        setPendingModeOff(false);
        const keepMsg = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `Alright, I'll keep the ${activeMode === 'learn' ? 'Learn Mode' : 'English Speaking Mode'} active. Let's continue!`,
          timestamp: new Date()
        };
        setMessages(prev => [...prev, keepMsg]);
        return;
      }
      setPendingModeOff(false);
    }

    // Check if user wants to turn off mode
    if (activeMode && checkForModeOffRequest(content)) {
      setPendingModeOff(true);
      const askMsg = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Do you want me to turn off ${activeMode === 'learn' ? 'Learn Mode' : 'English Speaking Mode'}? Just say "Yes" to confirm or "No" to keep it active.`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, { id: (Date.now() - 1).toString(), role: 'user', content, timestamp: new Date() }, askMsg]);
      return;
    }

    let conversationId = currentConversationId;

    // Create new conversation if none exists
    if (!conversationId) {
      try {
        conversationId = await createConversation(user.uid, content.slice(0, 30) + '...');
        const newConvo = {
          id: conversationId,
          userId: user.uid,
          title: content.slice(0, 30) + '...',
          createdAt: new Date(),
          lastMessageAt: new Date()
        };
        setConversations(prev => [newConvo, ...prev]);
        setCurrentConversationId(conversationId);
      } catch (error) {
        console.error('Error creating conversation:', error);
        toast.error('Failed to start conversation');
        return;
      }
    }

    // Add user message
    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);

    // Save user message
    try {
      await saveMessage(conversationId, user.uid, 'user', content);
      if (messages.length === 0) {
        await updateConversationTitle(conversationId, content.slice(0, 30) + (content.length > 30 ? '...' : ''));
        setConversations(prev => prev.map(c => 
          c.id === conversationId 
            ? { ...c, title: content.slice(0, 30) + (content.length > 30 ? '...' : '') }
            : c
        ));
      }
    } catch (error) {
      console.error('Error saving message:', error);
    }

    // Start AI response
    setIsTyping(true);
    abortControllerRef.current = new AbortController();

    try {
      const displayName = userMemory?.preferred_name || user.name || 'friend';
      
      const response = await fetch(`${BACKEND_URL}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, userMessage].map(m => ({ role: m.role, content: m.content })),
          user_name: displayName,
          conversation_id: conversationId,
          user_memory: userMemory,
          active_mode: activeMode // Pass active mode to backend
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) throw new Error('Failed to get AI response');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let aiContent = '';
      
      const aiMessageId = (Date.now() + 1).toString();
      setMessages(prev => [...prev, {
        id: aiMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isTyping: true
      }]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.word) {
                aiContent += data.word;
                setMessages(prev => prev.map(m => 
                  m.id === aiMessageId ? { ...m, content: aiContent } : m
                ));
              }
              
              if (data.done) {
                setMessages(prev => prev.map(m => 
                  m.id === aiMessageId ? { ...m, isTyping: false } : m
                ));
                
                if (aiContent) {
                  try {
                    await saveMessage(conversationId, user.uid, 'assistant', aiContent);
                    const updatedMessages = [...messages, userMessage, { role: 'assistant', content: aiContent }];
                    extractMemoryFromConversation(updatedMessages);
                  } catch (saveError) {
                    console.error('Failed to save AI message:', saveError);
                  }
                }
              }
              
              if (data.error) throw new Error(data.error);
            } catch (parseError) {
              // Skip invalid JSON
            }
          }
        }
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        setMessages(prev => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg?.role === 'assistant' && lastMsg?.isTyping) {
            if (lastMsg.content) {
              saveMessage(conversationId, user.uid, 'assistant', lastMsg.content + ' [stopped]');
              return prev.map(m => 
                m.id === lastMsg.id ? { ...m, isTyping: false, content: m.content + ' [stopped]' } : m
              );
            }
            return prev.slice(0, -1);
          }
          return prev;
        });
      } else {
        console.error('Chat error:', error);
        toast.error('Failed to get AI response');
        setMessages(prev => prev.filter(m => !m.isTyping));
      }
    } finally {
      setIsTyping(false);
      abortControllerRef.current = null;
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-[#FDFCF8] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[#E07A5F] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const displayName = userMemory?.preferred_name || user?.name;

  return (
    <div className="h-screen bg-[#FDFCF8] flex overflow-hidden" data-testid="chat-page">
      {/* Mobile Menu Button */}
      <button
        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-xl bg-white shadow-lg border border-[#EAE7DC]"
        data-testid="mobile-menu-btn"
      >
        {mobileMenuOpen ? <X className="w-5 h-5 text-[#3D405B]" /> : <Menu className="w-5 h-5 text-[#3D405B]" />}
      </button>

      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="lg:hidden fixed inset-0 bg-black/30 z-40"
            onClick={() => setMobileMenuOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar */}
      <AnimatePresence>
        {(sidebarOpen || mobileMenuOpen) && (
          <motion.div
            initial={{ x: -320, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -320, opacity: 0 }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className={`fixed lg:relative z-40 lg:z-0 w-80 h-full ${mobileMenuOpen ? 'block' : 'hidden lg:block'}`}
          >
            <ChatSidebar
              conversations={conversations}
              currentConversationId={currentConversationId}
              onSelectConversation={handleSelectConversation}
              onNewChat={handleNewChat}
              onDeleteConversation={handleDeleteConversation}
              onLogout={logout}
              user={user}
              userMemory={userMemory}
              loading={loadingConversations}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Chat Header */}
        <div className="h-16 border-b border-[#EAE7DC] bg-white/80 backdrop-blur-md flex items-center justify-between px-6 lg:px-8">
          <div className="flex items-center gap-3 ml-12 lg:ml-0">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
              activeMode === 'learn' ? 'bg-[#81B29A]/20' :
              activeMode === 'english' ? 'bg-[#E07A5F]/20' :
              activeMode === 'startup' ? 'bg-[#F2CC8F]/20' :
              'bg-[#81B29A]/20'
            }`}>
              {activeMode === 'learn' ? (
                <GraduationCap className="w-4 h-4 text-[#81B29A]" />
              ) : activeMode === 'english' ? (
                <Languages className="w-4 h-4 text-[#E07A5F]" />
              ) : activeMode === 'startup' ? (
                <Lightbulb className="w-4 h-4 text-[#D4A84B]" />
              ) : (
                <span className="text-[#81B29A] font-semibold text-sm">N</span>
              )}
            </div>
            <div>
              <h2 className="font-semibold text-[#3D405B] font-['Manrope']">
                {activeMode === 'learn' ? 'Nex Teacher' :
                 activeMode === 'english' ? 'Nex English Coach' : 
                 activeMode === 'startup' ? 'Nex Startup Game' : 'Nex'}
              </h2>
              <p className="text-xs text-[#9CA3AF]">
                {activeMode === 'learn' ? 'Teaching mode active' :
                 activeMode === 'english' ? 'English coach active' : 
                 activeMode === 'startup' ? 'Billionaire Ideas Game' : 'Your AI companion'}
              </p>
            </div>
          </div>
          
          {/* Status indicators */}
          <div className="flex items-center gap-2">
            {activeMode && (
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs ${
                activeMode === 'learn' 
                  ? 'bg-[#81B29A]/10 text-[#81B29A]' 
                  : activeMode === 'english'
                  ? 'bg-[#E07A5F]/10 text-[#E07A5F]'
                  : 'bg-[#F2CC8F]/10 text-[#D4A84B]'
              }`}>
                {activeMode === 'learn' ? <GraduationCap className="w-3 h-3" /> : 
                 activeMode === 'english' ? <Languages className="w-3 h-3" /> :
                 <Lightbulb className="w-3 h-3" />}
                <span>{activeMode === 'learn' ? 'Learn' : activeMode === 'english' ? 'English' : 'Startup Game'}</span>
              </div>
            )}
            {userMemory && (userMemory.interests?.length > 0 || userMemory.personal_facts?.length > 0) && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#81B29A]/10 text-[#81B29A] text-xs">
                <Sparkles className="w-3 h-3" />
                <span>Memory</span>
              </div>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 lg:p-8">
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.length === 0 && !isTyping && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="text-center py-20"
              >
                <div className={`w-20 h-20 rounded-3xl flex items-center justify-center mx-auto mb-6 ${
                  activeMode === 'learn' ? 'bg-[#81B29A]/10' :
                  activeMode === 'english' ? 'bg-[#E07A5F]/10' :
                  activeMode === 'startup' ? 'bg-[#F2CC8F]/10' :
                  'bg-gradient-to-br from-[#E07A5F]/10 to-[#81B29A]/10'
                }`}>
                  <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${
                    activeMode === 'learn' ? 'bg-[#81B29A]' :
                    activeMode === 'english' ? 'bg-[#E07A5F]' :
                    activeMode === 'startup' ? 'bg-[#F2CC8F]' :
                    'bg-gradient-to-br from-[#E07A5F] to-[#81B29A]'
                  }`}>
                    {activeMode === 'learn' ? (
                      <GraduationCap className="w-6 h-6 text-white" />
                    ) : activeMode === 'english' ? (
                      <Languages className="w-6 h-6 text-white" />
                    ) : activeMode === 'startup' ? (
                      <Lightbulb className="w-6 h-6 text-white" />
                    ) : (
                      <span className="text-white font-bold text-xl">N</span>
                    )}
                  </div>
                </div>
                <h3 className="text-2xl font-semibold text-[#3D405B] font-['Manrope'] mb-2">
                  {activeMode === 'learn' 
                    ? `Ready to learn, ${displayName || 'friend'}?`
                    : activeMode === 'english'
                    ? `Let's improve your English, ${displayName || 'friend'}!`
                    : activeMode === 'startup'
                    ? `Hey ${displayName || 'Bro'}! Ready to build a billion-dollar idea? 🚀`
                    : `Hey${displayName ? `, ${displayName}` : ''}!`
                  }
                </h3>
                <p className="text-[#6D6F7C] font-['Plus_Jakarta_Sans'] max-w-md mx-auto">
                  {activeMode === 'learn' 
                    ? "I'm in teaching mode. Ask me anything and I'll explain it step-by-step with examples and quizzes!"
                    : activeMode === 'english'
                    ? "Write any sentence and I'll correct it, explain the grammar, and help you sound more natural."
                    : activeMode === 'startup'
                    ? "Type 'spin' or 'start' to spin 3 random cards and build your startup idea. Let's make it happen! 💡"
                    : userMemory?.interests?.length > 0 
                    ? `Ready to chat about ${userMemory.interests[0]} or anything else?`
                    : "I'm Nex, your AI companion. Use the + button to activate special modes!"
                  }
                </p>
              </motion.div>
            )}

            {messages.map((message, index) => (
              <ChatMessage
                key={message.id}
                message={message}
                isLast={index === messages.length - 1}
                userName={displayName}
                activeMode={activeMode}
              />
            ))}

            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input */}
        <div className="p-4 lg:p-6 border-t border-[#EAE7DC] bg-white/80 backdrop-blur-md">
          <div className="max-w-3xl mx-auto">
            <ChatInput
              onSendMessage={handleSendMessage}
              onStopGeneration={handleStopGeneration}
              isTyping={isTyping}
              disabled={isTyping}
              activeMode={activeMode}
              onModeChange={handleModeChange}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

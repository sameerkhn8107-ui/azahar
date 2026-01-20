import { motion } from 'framer-motion';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { 
  Plus, 
  MessageSquare, 
  Trash2, 
  LogOut,
  MoreHorizontal,
  Sparkles,
  User
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from './ui/tooltip';

export const ChatSidebar = ({ 
  conversations, 
  currentConversationId, 
  onSelectConversation, 
  onNewChat, 
  onDeleteConversation,
  onLogout,
  user,
  userMemory,
  loading
}) => {
  const formatDate = (date) => {
    if (!date) return '';
    const now = new Date();
    const messageDate = new Date(date);
    const diffDays = Math.floor((now - messageDate) / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    return messageDate.toLocaleDateString();
  };

  // Get display name from memory or user
  const displayName = userMemory?.preferred_name || user?.name || 'User';

  return (
    <div className="h-full bg-[#F4F1DE]/80 backdrop-blur-md border-r border-[#EAE7DC] flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-[#EAE7DC]">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[#E07A5F] to-[#81B29A] flex items-center justify-center">
            <span className="text-white font-bold text-lg">N</span>
          </div>
          <span className="text-xl font-semibold text-[#3D405B] font-['Manrope']">Nex.AI</span>
        </div>
        
        <Button
          onClick={onNewChat}
          className="w-full h-12 rounded-2xl bg-white hover:bg-[#FDFCF8] text-[#3D405B] border border-[#EAE7DC] font-medium transition-transform active:scale-[0.98] shadow-sm"
          data-testid="new-chat-btn"
        >
          <Plus className="w-5 h-5 mr-2" />
          New Chat
        </Button>
      </div>

      {/* Conversations List */}
      <ScrollArea className="flex-1 px-2 py-2">
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="w-6 h-6 border-2 border-[#E07A5F] border-t-transparent rounded-full animate-spin" />
          </div>
        ) : conversations.length === 0 ? (
          <div className="text-center py-8 px-4">
            <MessageSquare className="w-8 h-8 text-[#9CA3AF] mx-auto mb-2" />
            <p className="text-sm text-[#9CA3AF]">No conversations yet</p>
            <p className="text-xs text-[#9CA3AF] mt-1">Start a new chat!</p>
          </div>
        ) : (
          <div className="space-y-1">
            {conversations.map((convo, index) => (
              <motion.div
                key={convo.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <div
                  className={`
                    group flex items-center gap-3 p-3 rounded-xl cursor-pointer
                    transition-colors
                    ${currentConversationId === convo.id 
                      ? 'bg-white shadow-sm border border-[#EAE7DC]' 
                      : 'hover:bg-white/50'
                    }
                  `}
                  onClick={() => onSelectConversation(convo.id)}
                  data-testid={`conversation-${convo.id}`}
                >
                  <MessageSquare className={`w-4 h-4 flex-shrink-0 ${
                    currentConversationId === convo.id ? 'text-[#E07A5F]' : 'text-[#9CA3AF]'
                  }`} />
                  
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm truncate font-medium ${
                      currentConversationId === convo.id ? 'text-[#3D405B]' : 'text-[#6D6F7C]'
                    }`}>
                      {convo.title || 'New Chat'}
                    </p>
                    <p className="text-xs text-[#9CA3AF] truncate">
                      {formatDate(convo.lastMessageAt)}
                    </p>
                  </div>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <button
                        className="opacity-0 group-hover:opacity-100 p-1 rounded-lg hover:bg-[#EAE7DC] transition-opacity"
                        onClick={(e) => e.stopPropagation()}
                        data-testid={`conversation-menu-${convo.id}`}
                      >
                        <MoreHorizontal className="w-4 h-4 text-[#6D6F7C]" />
                      </button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-40">
                      <DropdownMenuItem
                        className="text-red-500 focus:text-red-500 cursor-pointer"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteConversation(convo.id);
                        }}
                        data-testid={`delete-conversation-${convo.id}`}
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </ScrollArea>

      {/* Memory Section - Show if user has stored preferences */}
      {userMemory && (userMemory.interests?.length > 0 || userMemory.personal_facts?.length > 0 || userMemory.goals?.length > 0) && (
        <div className="px-4 py-3 border-t border-[#EAE7DC]">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-[#81B29A]/10 cursor-help">
                  <Sparkles className="w-4 h-4 text-[#81B29A]" />
                  <span className="text-xs text-[#81B29A] font-medium">Memory Active</span>
                </div>
              </TooltipTrigger>
              <TooltipContent side="top" className="max-w-xs">
                <div className="text-xs space-y-1">
                  <p className="font-medium">I remember:</p>
                  {userMemory.interests?.length > 0 && (
                    <p>• Interests: {userMemory.interests.slice(0, 3).join(', ')}</p>
                  )}
                  {userMemory.goals?.length > 0 && (
                    <p>• Goals: {userMemory.goals.slice(0, 2).join(', ')}</p>
                  )}
                  {userMemory.personal_facts?.length > 0 && (
                    <p>• {userMemory.personal_facts.length} personal facts</p>
                  )}
                </div>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      )}

      {/* User Section */}
      <div className="p-4 border-t border-[#EAE7DC]">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-[#E07A5F]/10 flex items-center justify-center">
            {user?.photoURL ? (
              <img 
                src={user.photoURL} 
                alt={displayName} 
                className="w-10 h-10 rounded-full object-cover"
              />
            ) : (
              <span className="text-[#E07A5F] font-semibold">
                {displayName?.charAt(0)?.toUpperCase() || <User className="w-4 h-4" />}
              </span>
            )}
          </div>
          
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-[#3D405B] truncate">
              {displayName}
            </p>
            <p className="text-xs text-[#9CA3AF] truncate">
              {user?.email}
            </p>
          </div>

          <Button
            variant="ghost"
            size="icon"
            onClick={onLogout}
            className="text-[#9CA3AF] hover:text-[#E07A5F] hover:bg-[#E07A5F]/10"
            data-testid="logout-btn"
          >
            <LogOut className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

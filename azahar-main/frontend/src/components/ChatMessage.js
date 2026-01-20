import { motion } from 'framer-motion';
import { User, GraduationCap, Languages, Lightbulb } from 'lucide-react';

export const ChatMessage = ({ message, isLast, userName, activeMode }) => {
  const isUser = message.role === 'user';
  const isTyping = message.isTyping;

  const getAIBubbleStyle = () => {
    if (activeMode === 'learn') {
      return 'bg-[#81B29A]/10 text-[#3D405B] border border-[#81B29A]/20';
    }
    if (activeMode === 'english') {
      return 'bg-[#E07A5F]/10 text-[#3D405B] border border-[#E07A5F]/20';
    }
    if (activeMode === 'startup') {
      return 'bg-[#F2CC8F]/10 text-[#3D405B] border border-[#F2CC8F]/30';
    }
    return 'bg-[#F4F1DE] text-[#3D405B] shadow-sm';
  };

  const getAIAvatar = () => {
    if (activeMode === 'learn') {
      return (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#81B29A]/20 flex items-center justify-center">
          <GraduationCap className="w-4 h-4 text-[#81B29A]" />
        </div>
      );
    }
    if (activeMode === 'english') {
      return (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#E07A5F]/20 flex items-center justify-center">
          <Languages className="w-4 h-4 text-[#E07A5F]" />
        </div>
      );
    }
    if (activeMode === 'startup') {
      return (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#F2CC8F]/20 flex items-center justify-center">
          <Lightbulb className="w-4 h-4 text-[#D4A84B]" />
        </div>
      );
    }
    return (
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#81B29A]/20 flex items-center justify-center">
        <span className="text-[#81B29A] font-semibold text-sm">N</span>
      </div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex gap-4 ${isUser ? 'justify-end' : 'justify-start'}`}
      data-testid={`chat-message-${message.id}`}
    >
      {!isUser && getAIAvatar()}

      <div
        className={`
          relative max-w-[80%] px-5 py-3.5 rounded-2xl
          ${isUser 
            ? 'bg-[#E07A5F] text-white rounded-tr-sm' 
            : `${getAIBubbleStyle()} rounded-tl-sm`
          }
        `}
      >
        <div className="font-['Plus_Jakarta_Sans'] text-[15px] leading-relaxed whitespace-pre-wrap break-words">
          {message.content}
          {isTyping && (
            <span className="inline-flex ml-1">
              <span className="w-1.5 h-1.5 bg-current rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-1.5 h-1.5 bg-current rounded-full animate-bounce mx-0.5" style={{ animationDelay: '150ms' }} />
              <span className="w-1.5 h-1.5 bg-current rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </span>
          )}
        </div>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#E07A5F]/20 flex items-center justify-center">
          <span className="text-[#E07A5F] font-semibold text-sm">
            {userName?.charAt(0)?.toUpperCase() || <User className="w-4 h-4" />}
          </span>
        </div>
      )}
    </motion.div>
  );
};

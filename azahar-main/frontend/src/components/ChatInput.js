import { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Button } from './ui/button';
import { Send, Square, GraduationCap, Languages, Lightbulb } from 'lucide-react';
import { FeatureMenu } from './FeatureMenu';

export const ChatInput = ({ 
  onSendMessage, 
  onStopGeneration, 
  isTyping, 
  disabled,
  activeMode,
  onModeChange
}) => {
  const [message, setMessage] = useState('');
  const [menuOpen, setMenuOpen] = useState(false);
  const textareaRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }
  }, [message]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !isTyping && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleMenuOpen = () => setMenuOpen(true);
  const handleMenuClose = () => setMenuOpen(false);

  const getModeInfo = () => {
    switch (activeMode) {
      case 'learn':
        return { icon: <GraduationCap className="w-4 h-4" />, name: 'Learn Mode', color: 'bg-[#81B29A]' };
      case 'english':
        return { icon: <Languages className="w-4 h-4" />, name: 'English Speaking Mode', color: 'bg-[#E07A5F]' };
      case 'startup':
        return { icon: <Lightbulb className="w-4 h-4" />, name: 'The Billionaire Dollar Idea', color: 'bg-[#D4A84B]' };
      default:
        return null;
    }
  };

  const modeInfo = getModeInfo();

  const getPlaceholder = () => {
    if (disabled) return "Start a new chat to begin...";
    switch (activeMode) {
      case 'learn': return "Ask me to teach you anything...";
      case 'english': return "Write a sentence and I'll help improve it...";
      case 'startup': return "Type 'spin' to start or share your startup idea...";
      default: return "Message Nex...";
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      {/* Active Mode Indicator */}
      {modeInfo && (
        <motion.div
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-2 mb-3"
        >
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-white text-xs font-medium ${modeInfo.color}`}>
            {modeInfo.icon}
            <span>{modeInfo.name}</span>
          </div>
          <span className="text-xs text-[#9CA3AF]">
            Say "turn off mode" to deactivate
          </span>
        </motion.div>
      )}

      <div className="relative flex items-end gap-2">
        {/* Plus Button / Feature Menu */}
        <FeatureMenu
          activeMode={activeMode}
          onModeChange={onModeChange}
          isOpen={menuOpen}
          onClose={handleMenuClose}
          onOpen={handleMenuOpen}
        />

        {/* Input Field */}
        <div className="flex-1 relative bg-white rounded-3xl shadow-[0_10px_40px_-10px_rgba(61,64,91,0.1)] border border-[#EAE7DC]">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={getPlaceholder()}
            disabled={disabled || isTyping}
            rows={1}
            className="
              w-full resize-none bg-transparent
              px-6 py-4 pr-14
              text-[#3D405B] text-base
              placeholder:text-[#9CA3AF]
              focus:outline-none
              font-['Plus_Jakarta_Sans']
              disabled:opacity-50 disabled:cursor-not-allowed
              rounded-3xl
            "
            style={{ maxHeight: '200px' }}
            data-testid="chat-input"
          />

          {/* Send/Stop Button */}
          <div className="absolute right-3 bottom-3">
            {isTyping ? (
              <Button
                type="button"
                onClick={onStopGeneration}
                className="w-10 h-10 rounded-full bg-[#EF4444] hover:bg-[#DC2626] text-white p-0"
                data-testid="stop-generation-btn"
              >
                <Square className="w-4 h-4 fill-current" />
              </Button>
            ) : (
              <Button
                type="submit"
                disabled={!message.trim() || disabled}
                className={`
                  w-10 h-10 rounded-full p-0
                  ${message.trim() && !disabled
                    ? `${modeInfo?.color || 'bg-[#E07A5F]'} hover:opacity-90 text-white`
                    : 'bg-[#EAE7DC] text-[#9CA3AF] cursor-not-allowed'
                  }
                `}
                data-testid="send-message-btn"
              >
                <Send className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
      </div>

      <p className="text-center text-xs text-[#9CA3AF] mt-3">
        {activeMode 
          ? "Mode resets on page refresh • Press Enter to send"
          : "Press Enter to send, Shift+Enter for new line"
        }
      </p>
    </form>
  );
};

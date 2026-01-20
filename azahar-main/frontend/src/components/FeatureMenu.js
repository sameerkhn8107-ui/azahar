import { useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, X, GraduationCap, Languages, Lightbulb } from 'lucide-react';

export const FeatureMenu = ({ activeMode, onModeChange, isOpen, onClose, onOpen }) => {
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, onClose]);

  const handleModeClick = (modeId) => {
    // Simple toggle: if same mode, turn off; otherwise turn on new mode
    const newMode = activeMode === modeId ? null : modeId;
    onModeChange(newMode);
  };

  const modes = [
    {
      id: 'learn',
      name: 'Learn Mode',
      description: 'Step-by-step teaching',
      icon: GraduationCap,
      color: '#81B29A',
      info: "I'll teach you step-by-step with examples and quizzes."
    },
    {
      id: 'english',
      name: 'English Speaking',
      description: 'Grammar & correction',
      icon: Languages,
      color: '#E07A5F',
      info: "I'll correct your sentences and explain grammar."
    },
    {
      id: 'startup',
      name: 'The Billionaire Dollar Idea',
      description: 'Startup brainstorming game',
      icon: Lightbulb,
      color: '#D4A84B',
      info: "Let's spin cards and build startup ideas together! 🚀"
    }
  ];

  return (
    <div className="relative" ref={menuRef}>
      {/* Plus Button */}
      <button
        type="button"
        onClick={() => isOpen ? onClose() : onOpen()}
        className={`
          w-10 h-10 rounded-full flex items-center justify-center
          transition-all duration-200
          ${isOpen 
            ? 'bg-[#E07A5F] text-white' 
            : 'bg-[#F4F1DE] text-[#3D405B] hover:bg-[#EAE7DC]'
          }
          ${activeMode ? 'ring-2 ring-[#81B29A] ring-offset-2' : ''}
        `}
        data-testid="feature-menu-btn"
      >
        <motion.div
          animate={{ rotate: isOpen ? 45 : 0 }}
          transition={{ duration: 0.2 }}
        >
          {isOpen ? <X className="w-5 h-5" /> : <Plus className="w-5 h-5" />}
        </motion.div>
      </button>

      {/* Feature Menu Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            className="absolute bottom-14 left-0 w-80 bg-white rounded-2xl shadow-xl border border-[#EAE7DC] overflow-hidden z-50"
          >
            {/* Header */}
            <div className="px-4 py-3 bg-[#F4F1DE]/50 border-b border-[#EAE7DC]">
              <h3 className="font-semibold text-[#3D405B] text-sm">Special Modes</h3>
              <p className="text-xs text-[#9CA3AF] mt-0.5">Only one mode active at a time</p>
            </div>

            {/* Options */}
            <div className="p-2 space-y-1">
              {modes.map((mode) => {
                const Icon = mode.icon;
                const isActive = activeMode === mode.id;
                
                return (
                  <button
                    key={mode.id}
                    type="button"
                    onClick={() => handleModeClick(mode.id)}
                    className={`
                      w-full flex items-center justify-between p-3 rounded-xl
                      transition-all duration-200 text-left
                      ${isActive 
                        ? 'bg-opacity-10 border' 
                        : 'hover:bg-[#F4F1DE]/50 border border-transparent'
                      }
                    `}
                    style={{
                      backgroundColor: isActive ? `${mode.color}15` : undefined,
                      borderColor: isActive ? `${mode.color}40` : 'transparent'
                    }}
                    data-testid={`${mode.id}-mode-toggle`}
                  >
                    <div className="flex items-center gap-3">
                      <div 
                        className="w-10 h-10 rounded-xl flex items-center justify-center"
                        style={{ 
                          backgroundColor: isActive ? mode.color : '#F4F1DE',
                          color: isActive ? 'white' : '#6D6F7C'
                        }}
                      >
                        <Icon className="w-5 h-5" />
                      </div>
                      <div>
                        <p className={`font-medium text-sm ${isActive ? 'text-[#3D405B]' : 'text-[#6D6F7C]'}`}>
                          {mode.name}
                        </p>
                        <p className="text-xs text-[#9CA3AF]">{mode.description}</p>
                      </div>
                    </div>
                    
                    {/* Custom Toggle Switch */}
                    <div 
                      className={`
                        w-11 h-6 rounded-full relative transition-colors duration-200
                        ${isActive ? '' : 'bg-[#EAE7DC]'}
                      `}
                      style={{ backgroundColor: isActive ? mode.color : undefined }}
                    >
                      <div 
                        className={`
                          absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-sm
                          transition-transform duration-200
                          ${isActive ? 'translate-x-[22px]' : 'translate-x-0.5'}
                        `}
                      />
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Active Mode Info */}
            {activeMode && (
              <div className="px-4 py-3 bg-[#F4F1DE]/30 border-t border-[#EAE7DC]">
                <p className="text-xs text-[#6D6F7C]">
                  {modes.find(m => m.id === activeMode)?.info}
                </p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

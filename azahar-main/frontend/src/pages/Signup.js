import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { signUpWithEmail, signInWithGoogle } from '../lib/firebase';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Mail, Lock, User, Eye, EyeOff, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

export default function Signup() {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  const handleEmailSignup = async (e) => {
    e.preventDefault();
    if (!name || !email || !password) {
      toast.error('Please fill in all fields');
      return;
    }
    
    if (password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    
    setLoading(true);
    try {
      await signUpWithEmail(email, password, name);
      toast.success(`Welcome to Nex.AI, ${name}!`);
      navigate('/chat');
    } catch (error) {
      console.error('Signup error:', error);
      if (error.code === 'auth/email-already-in-use') {
        toast.error('An account with this email already exists');
      } else if (error.code === 'auth/weak-password') {
        toast.error('Password is too weak');
      } else {
        toast.error('Signup failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignup = async () => {
    setGoogleLoading(true);
    try {
      await signInWithGoogle();
      toast.success('Welcome to Nex.AI!');
      navigate('/chat');
    } catch (error) {
      console.error('Google signup error:', error);
      if (error.code !== 'auth/popup-closed-by-user') {
        toast.error('Google sign-up failed. Please try again.');
      }
    } finally {
      setGoogleLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FDFCF8] flex">
      {/* Left Side - Form */}
      <motion.div 
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full lg:w-1/2 flex items-center justify-center p-8 lg:p-16"
      >
        <div className="w-full max-w-md space-y-8">
          {/* Logo & Title */}
          <div className="text-left space-y-2">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="flex items-center gap-3 mb-8"
            >
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[#E07A5F] to-[#81B29A] flex items-center justify-center">
                <span className="text-white font-bold text-lg">N</span>
              </div>
              <span className="text-2xl font-semibold text-[#3D405B] font-['Manrope']">Nex.AI</span>
            </motion.div>
            
            <h1 className="text-4xl font-semibold text-[#3D405B] font-['Manrope'] tracking-tight">
              Create account
            </h1>
            <p className="text-[#6D6F7C] text-lg font-['Plus_Jakarta_Sans']">
              Start your journey with a personal AI companion
            </p>
          </div>

          {/* Google Sign Up */}
          <Button
            type="button"
            variant="outline"
            className="w-full h-14 rounded-2xl border-[#EAE7DC] bg-white hover:bg-[#F4F1DE] text-[#3D405B] font-medium text-base transition-transform active:scale-[0.98]"
            onClick={handleGoogleSignup}
            disabled={googleLoading}
            data-testid="google-signup-btn"
          >
            {googleLoading ? (
              <Loader2 className="w-5 h-5 animate-spin mr-2" />
            ) : (
              <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
            )}
            Continue with Google
          </Button>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-[#EAE7DC]" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-4 bg-[#FDFCF8] text-[#9CA3AF]">or sign up with email</span>
            </div>
          </div>

          {/* Email Form */}
          <form onSubmit={handleEmailSignup} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="name" className="text-[#3D405B] font-medium">Name</Label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9CA3AF]" />
                <Input
                  id="name"
                  type="text"
                  placeholder="What should I call you?"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="h-14 pl-12 rounded-2xl border-[#EAE7DC] bg-white focus:border-[#81B29A] focus:ring-2 focus:ring-[#81B29A]/20 placeholder:text-[#9CA3AF] text-[#3D405B]"
                  data-testid="signup-name-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-[#3D405B] font-medium">Email</Label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9CA3AF]" />
                <Input
                  id="email"
                  type="email"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="h-14 pl-12 rounded-2xl border-[#EAE7DC] bg-white focus:border-[#81B29A] focus:ring-2 focus:ring-[#81B29A]/20 placeholder:text-[#9CA3AF] text-[#3D405B]"
                  data-testid="signup-email-input"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-[#3D405B] font-medium">Password</Label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9CA3AF]" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Create a password (min. 6 characters)"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-14 pl-12 pr-12 rounded-2xl border-[#EAE7DC] bg-white focus:border-[#81B29A] focus:ring-2 focus:ring-[#81B29A]/20 placeholder:text-[#9CA3AF] text-[#3D405B]"
                  data-testid="signup-password-input"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-[#9CA3AF] hover:text-[#6D6F7C] transition-colors"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full h-14 rounded-full bg-[#E07A5F] hover:bg-[#D06950] text-white font-medium text-lg transition-transform active:scale-[0.98] shadow-[0_4px_20px_-4px_rgba(224,122,95,0.4)]"
              disabled={loading}
              data-testid="signup-submit-btn"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Create Account'}
            </Button>
          </form>

          <p className="text-center text-[#6D6F7C] font-['Plus_Jakarta_Sans']">
            Already have an account?{' '}
            <Link to="/login" className="text-[#E07A5F] hover:text-[#D06950] font-medium transition-colors" data-testid="login-link">
              Sign in
            </Link>
          </p>
        </div>
      </motion.div>

      {/* Right Side - Image */}
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, delay: 0.2 }}
        className="hidden lg:block w-1/2 relative overflow-hidden"
      >
        <div className="absolute inset-0 bg-gradient-to-br from-[#81B29A]/20 to-[#E07A5F]/20" />
        <img
          src="https://images.unsplash.com/photo-1642957096727-b85727004b48?crop=entropy&cs=srgb&fm=jpg&q=85"
          alt="Soft fabric abstract"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-[#3D405B]/30 to-transparent" />
        <div className="absolute bottom-12 left-12 right-12">
          <motion.p 
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="text-white text-2xl font-['Manrope'] font-medium leading-relaxed"
          >
            "Meet Nex — your AI that understands<br />you, step by step."
          </motion.p>
        </div>
      </motion.div>
    </div>
  );
}

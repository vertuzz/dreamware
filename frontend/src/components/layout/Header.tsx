import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '~/contexts/AuthContext';
import FeedbackModal from '~/components/common/FeedbackModal';
import { feedbackService } from '~/lib/services/feedback-service';
import type { FeedbackType } from '~/lib/types';

interface HeaderProps {
  onSearch?: (query: string) => void;
}

export default function Header({ onSearch }: HeaderProps) {
  const { user } = useAuth();
  const isLoggedIn = !!user;
  const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);

  const handleSubmitFeedback = async (type: FeedbackType, message: string) => {
    await feedbackService.submitFeedback({ type, message });
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-[var(--border)] bg-white/80 dark:bg-[var(--background)]/90 backdrop-blur-md">
      <div className="px-6 md:px-10 py-3 flex items-center justify-between gap-4">
        {/* Logo & Search Group */}
        <div className="flex items-center gap-8 flex-1">
          {/* Logo */}
          <Link
            to="/"
            className="flex items-center gap-3 hover:opacity-80 transition-opacity"
          >
            <div className="size-9 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
              <span className="material-symbols-outlined filled" style={{ fontVariationSettings: "'FILL' 1" }}>
                auto_awesome
              </span>
            </div>
            <h2 className="text-xl font-bold tracking-tight text-[#0d111b] dark:text-white">
              Dreamware
            </h2>
          </Link>

          {/* Search Bar (Hidden on Mobile) */}
          <label className="hidden md:flex flex-col w-full max-w-md h-11">
            <div className="flex w-full flex-1 items-center rounded-xl bg-[#f0f2f5] dark:bg-gray-800 border-2 border-transparent focus-within:border-primary/20 focus-within:bg-white dark:focus-within:bg-gray-800 transition-all overflow-hidden px-4">
              <span className="material-symbols-outlined text-gray-500">search</span>
              <input
                type="text"
                className="w-full bg-transparent border-none focus:ring-0 text-sm font-medium text-[#0d111b] dark:text-white placeholder:text-gray-500 ml-2 h-full outline-none"
                placeholder="Search dreams, agents..."
                onChange={(e) => onSearch?.(e.target.value)}
              />
            </div>
          </label>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-6">
          {/* Nav Links (Desktop) */}
          <nav className="hidden lg:flex items-center gap-6">
            <Link
              to="/"
              className="text-sm font-semibold text-[#0d111b] dark:text-white hover:text-primary transition-colors"
            >
              Explore
            </Link>
            <Link
              to="/agent-instructions"
              className="text-sm font-semibold text-[#0d111b] dark:text-white hover:text-primary transition-colors flex items-center gap-1.5"
            >
              <span className="material-symbols-outlined text-[18px]">smart_toy</span>
              AI Agent
            </Link>
            {user?.is_admin && (
              <Link
                to="/admin"
                className="text-sm font-semibold text-primary hover:text-primary-dark transition-colors flex items-center gap-1.5"
              >
                <span className="material-symbols-outlined text-[18px]">admin_panel_settings</span>
                Admin
              </Link>
            )}
            {isLoggedIn && (
              <button
                onClick={() => setIsFeedbackOpen(true)}
                className="text-sm font-semibold text-[#0d111b] dark:text-white hover:text-primary transition-colors flex items-center gap-1.5"
              >
                <span className="material-symbols-outlined text-[18px]">feedback</span>
                Feedback
              </button>
            )}
          </nav>

          {/* CTA Button */}
          <Link
            to={isLoggedIn ? "/dreams/create" : "/login"}
            className="hidden sm:flex items-center justify-center gap-2 h-10 px-5 bg-primary hover:bg-primary-dark text-white text-sm font-bold rounded-xl transition-all shadow-md hover:shadow-lg hover:-translate-y-0.5"
          >
            <span className="material-symbols-outlined text-[20px]">add</span>
            <span>Submit a Dream</span>
          </Link>

          {/* User Profile */}
          <Link
            to={isLoggedIn ? "/profile" : "/login"}
            className="size-10 rounded-full bg-gray-200 cursor-pointer overflow-hidden border-2 border-white dark:border-gray-700 shadow-sm hover:ring-2 hover:ring-primary hover:ring-offset-2 transition-all flex items-center justify-center"
          >
            {user?.avatar ? (
              <img src={user.avatar} alt={user.username} className="w-full h-full object-cover" />
            ) : (
              <span className="material-symbols-outlined text-gray-500">person</span>
            )}
          </Link>
        </div>
      </div>

      {/* Feedback Modal */}
      <FeedbackModal
        isOpen={isFeedbackOpen}
        onClose={() => setIsFeedbackOpen(false)}
        onSubmit={handleSubmitFeedback}
      />
    </header>
  );
}

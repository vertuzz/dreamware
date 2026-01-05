import { Link, useNavigate } from 'react-router-dom';
import type { App } from '~/lib/types';

interface AppCardProps {
  app: App;
  aspectRatio?: 'square' | 'video' | 'portrait' | 'landscape';
  onLike?: (app: App) => void;
}

// Aspect ratio classes for masonry variety
const aspectRatioClasses = {
  square: 'aspect-square',
  video: 'aspect-video',
  portrait: 'aspect-[3/4]',
  landscape: 'aspect-[4/3]',
};

// Status badge component
function StatusBadge({ status, isDead }: { status: App['status']; isDead?: boolean }) {
  if (isDead) {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-700 border border-red-200 shadow-sm backdrop-blur-md">
        <span className="material-symbols-outlined text-[12px] mr-1">link_off</span>
        DEAD
      </span>
    );
  }

  if (status === 'Live') {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-green-100 text-green-700 border border-green-200 shadow-sm backdrop-blur-md">
        <span className="w-1.5 h-1.5 rounded-full bg-green-500 mr-1.5 animate-pulse"></span>
        LIVE
      </span>
    );
  }

  if (status === 'WIP') {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-yellow-100 text-yellow-700 border border-yellow-200 shadow-sm backdrop-blur-md">
        WIP
      </span>
    );
  }

  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-gray-100/90 text-gray-700 border border-white/20 shadow-sm backdrop-blur-md">
      CONCEPT
    </span>
  );
}

// Format number for display (1200 -> 1.2k)
function formatCount(count: number | undefined): string {
  if (!count) return '0';
  if (count >= 1000) {
    return (count / 1000).toFixed(1).replace(/\.0$/, '') + 'k';
  }
  return count.toString();
}

// Default placeholder image for apps without media
const placeholderImage = '/placeholder-app.png';

export default function AppCard({ app, aspectRatio = 'landscape', onLike }: AppCardProps) {
  const navigate = useNavigate();
  
  // Get the first media image or use a placeholder
  const imageUrl = app.media?.[0]?.media_url || placeholderImage;

  const creatorName = app.creator?.username || `user_${app.creator_id}`;
  const creatorAvatar = app.creator?.avatar;

  const handleCardClick = () => {
    navigate(`/apps/${app.slug || app.id}`);
  };

  return (
    <div className="break-inside-avoid mb-6 group cursor-pointer">
      <div 
        onClick={handleCardClick}
        className="bg-white dark:bg-gray-800 rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border border-gray-100 dark:border-gray-700"
      >
          {/* Image Section */}
          <div className={`relative ${aspectRatioClasses[aspectRatio]} w-full overflow-hidden`}>
            <img
              src={imageUrl}
              alt={app.title || 'App'}
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
            <div className="absolute top-3 right-3">
              <StatusBadge status={app.status} isDead={app.is_dead} />
            </div>
          </div>

          {/* Content Section */}
          <div className="p-4">
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-bold text-lg text-gray-900 dark:text-white leading-tight group-hover:text-primary transition-colors">
                {app.title || 'Untitled App'}
              </h3>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 mb-4">
              {app.prompt_text || 'No description available'}
            </p>

            {/* Footer */}
            <div className="flex items-center justify-between border-t border-gray-100 dark:border-gray-700 pt-3 mt-2">
              {/* Creator Info */}
              <Link 
                to={`/users/${creatorName}`} 
                className="flex items-center gap-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-full pr-2 transition-colors" 
                onClick={(e) => e.stopPropagation()}
              >
                {creatorAvatar ? (
                  <img
                    src={creatorAvatar}
                    alt={creatorName}
                    className="w-6 h-6 rounded-full object-cover"
                  />
                ) : (
                  <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center text-white text-xs font-bold">
                    {creatorName.charAt(0).toUpperCase()}
                  </div>
                )}
                <span className="text-xs font-medium text-gray-600 dark:text-gray-300 hover:text-primary transition-colors">
                  @{creatorName}
                </span>
              </Link>

              {/* Stats */}
              <div className="flex items-center gap-3 text-gray-400">
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    onLike?.(app);
                  }}
                  className={`flex items-center gap-1 transition-colors ${app.is_liked
                    ? 'text-rose-500 hover:text-rose-600'
                    : 'hover:text-red-500'
                    }`}
                >
                  <span className={`material-symbols-outlined text-[16px] ${app.is_liked ? 'filled' : ''}`}>favorite</span>
                  <span className="text-xs font-medium">{formatCount(app.likes_count)}</span>
                </button>
                <div className="flex items-center gap-1 hover:text-primary transition-colors">
                  <span className="material-symbols-outlined text-[16px]">chat_bubble</span>
                  <span className="text-xs font-medium">{formatCount(app.comments_count)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
    </div>
  );
}

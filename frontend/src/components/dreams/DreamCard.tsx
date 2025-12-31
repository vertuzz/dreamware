import { Link } from 'react-router-dom';
import type { Dream } from '~/lib/types';

interface DreamCardProps {
  dream: Dream;
  aspectRatio?: 'square' | 'video' | 'portrait' | 'landscape';
}

// Aspect ratio classes for masonry variety
const aspectRatioClasses = {
  square: 'aspect-square',
  video: 'aspect-video',
  portrait: 'aspect-[3/4]',
  landscape: 'aspect-[4/3]',
};

// Status badge component
function StatusBadge({ status, isAgentSubmitted }: { status: Dream['status']; isAgentSubmitted: boolean }) {
  if (isAgentSubmitted) {
    return (
      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-purple-100 text-purple-700 border border-purple-200 shadow-sm backdrop-blur-md">
        <span className="material-symbols-outlined text-[14px] mr-1">bolt</span>
        AUTO-AGENT
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

// Default placeholder images for dreams without media
const placeholderImages = [
  'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=400&h=300&fit=crop',
  'https://images.unsplash.com/photo-1677442136019-21780ecad995?w=400&h=300&fit=crop',
  'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=400&h=300&fit=crop',
  'https://images.unsplash.com/photo-1535378917042-10a22c95931a?w=400&h=300&fit=crop',
];

export default function DreamCard({ dream, aspectRatio = 'landscape' }: DreamCardProps) {
  // Get the first media image or use a placeholder
  const imageUrl = dream.media?.[0]?.media_url ||
    placeholderImages[dream.id % placeholderImages.length];

  const creatorName = dream.creator?.username || `user_${dream.creator_id}`;
  const creatorAvatar = dream.creator?.avatar;

  return (
    <div className="break-inside-avoid mb-6 group cursor-pointer">
      <Link to={`/dreams/${dream.slug || dream.id}`}>
        <div className="bg-white dark:bg-gray-800 rounded-2xl overflow-hidden shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border border-gray-100 dark:border-gray-700">
          {/* Image Section */}
          <div className={`relative ${aspectRatioClasses[aspectRatio]} w-full overflow-hidden`}>
            <img
              src={imageUrl}
              alt={dream.title || 'Dream'}
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
            <div className="absolute top-3 right-3">
              <StatusBadge status={dream.status} isAgentSubmitted={dream.is_agent_submitted} />
            </div>
          </div>

          {/* Content Section */}
          <div className="p-4">
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-bold text-lg text-gray-900 dark:text-white leading-tight group-hover:text-primary transition-colors">
                {dream.title || 'Untitled Dream'}
              </h3>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 mb-4">
              {dream.prompt_text || 'No description available'}
            </p>

            {/* Footer */}
            <div className="flex items-center justify-between border-t border-gray-100 dark:border-gray-700 pt-3 mt-2">
              {/* Creator Info */}
              <Link to={`/users/${creatorName}`} className="flex items-center gap-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-full pr-2 transition-colors" onClick={(e) => e.stopPropagation()}>
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
                <div className="flex items-center gap-1 hover:text-red-500 transition-colors">
                  <span className="material-symbols-outlined text-[16px]">favorite</span>
                  <span className="text-xs font-medium">{formatCount(dream.likes_count)}</span>
                </div>
                <div className="flex items-center gap-1 hover:text-primary transition-colors">
                  <span className="material-symbols-outlined text-[16px]">chat_bubble</span>
                  <span className="text-xs font-medium">{formatCount(dream.comments_count)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Link>
    </div>
  );
}

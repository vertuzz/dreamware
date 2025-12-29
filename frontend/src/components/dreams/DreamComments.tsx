import { useState } from 'react';
import type { Comment } from '~/lib/types';

interface DreamCommentsProps {
    comments: Comment[];
    onSubmitComment: (content: string) => Promise<void>;
}

// Helper to format relative time
function formatRelativeTime(dateString: string): string {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export default function DreamComments({ comments, onSubmitComment }: DreamCommentsProps) {
    const [newComment, setNewComment] = useState('');
    const [submitting, setSubmitting] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newComment.trim()) return;

        setSubmitting(true);
        try {
            await onSubmitComment(newComment.trim());
            setNewComment('');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <section className="border-t border-[var(--border)] pt-10">
            <h3 className="text-2xl font-bold text-[var(--foreground)] mb-6">
                Discussion ({comments.length})
            </h3>

            {/* Comment Input */}
            <form onSubmit={handleSubmit} className="flex gap-4 mb-8">
                <div className="size-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold shrink-0">
                    <span className="material-symbols-outlined">person</span>
                </div>
                <div className="flex-1">
                    <textarea
                        value={newComment}
                        onChange={(e) => setNewComment(e.target.value)}
                        className="w-full bg-white dark:bg-[var(--card)] border border-[var(--border)] rounded-xl p-3 focus:ring-2 focus:ring-primary focus:border-transparent text-sm min-h-[100px] resize-none"
                        placeholder="What do you think about this dream?"
                    />
                    <div className="flex justify-end mt-2">
                        <button
                            type="submit"
                            disabled={submitting || !newComment.trim()}
                            className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-bold hover:bg-primary-dark transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {submitting ? 'Posting...' : 'Post Comment'}
                        </button>
                    </div>
                </div>
            </form>

            {/* Comment List */}
            <div className="space-y-6">
                {comments.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">No comments yet. Be the first to share your thoughts!</p>
                ) : (
                    comments.map((comment) => (
                        <CommentItem key={comment.id} comment={comment} />
                    ))
                )}
            </div>
        </section>
    );
}

interface CommentItemProps {
    comment: Comment;
}

function CommentItem({ comment }: CommentItemProps) {
    return (
        <div className="flex gap-4">
            <div className="size-10 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-gray-500 font-bold shrink-0">
                {comment.user?.avatar ? (
                    <img src={comment.user.avatar} alt={comment.user.username} className="w-full h-full rounded-full object-cover" />
                ) : (
                    <span className="text-sm">{comment.user?.username?.charAt(0).toUpperCase() || 'U'}</span>
                )}
            </div>
            <div className="flex-1">
                <div className="bg-white dark:bg-[var(--card)] p-4 rounded-xl border border-[var(--border)] shadow-sm">
                    <div className="flex justify-between items-center mb-2">
                        <span className="font-bold text-sm text-[var(--foreground)]">
                            {comment.user?.username || 'Anonymous'}
                        </span>
                        <span className="text-xs text-gray-500">
                            {formatRelativeTime(comment.created_at)}
                        </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-300">{comment.content}</p>
                </div>
                <div className="flex items-center gap-4 mt-2 ml-2">
                    <button className="text-xs font-medium text-gray-500 hover:text-primary flex items-center gap-1">
                        <span className="material-symbols-outlined text-sm">thumb_up</span>
                        {comment.likes_count || 0}
                    </button>
                    <button className="text-xs font-medium text-gray-500 hover:text-primary">Reply</button>
                </div>
            </div>
        </div>
    );
}

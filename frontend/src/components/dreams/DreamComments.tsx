import { useState, useMemo } from 'react';
import type { Comment } from '~/lib/types';
import { useAuth } from '~/contexts/AuthContext';
import api from '~/lib/api';

interface DreamCommentsProps {
    dreamId: number;
    comments: Comment[];
    onRefresh: () => Promise<void>;
}

// Tree Node structure for recursive rendering
interface CommentNode extends Comment {
    children: CommentNode[];
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

export default function DreamComments({ dreamId, comments, onRefresh }: DreamCommentsProps) {
    const { user, isAuthenticated } = useAuth();
    const [newComment, setNewComment] = useState('');
    const [submitting, setSubmitting] = useState(false);

    // Build comment tree
    const commentTree = useMemo(() => {
        const nodes: Record<number, CommentNode> = {};
        const roots: CommentNode[] = [];

        // First pass: create nodes
        comments.forEach(c => {
            nodes[c.id] = { ...c, children: [] };
        });

        // Second pass: link parents
        comments.forEach(c => {
            const node = nodes[c.id];
            if (c.parent_id && nodes[c.parent_id]) {
                nodes[c.parent_id].children.push(node);
            } else {
                roots.push(node);
            }
        });

        // Sort roots by date (newest first)
        // Children typically sorted oldest first (chronological conversation) or newest? 
        // Reddit uses "Best", but chronological for replies is common. Let's do newest first for top level, old to new for replies?
        // Let's stick to newest first for everything for now, consistent with queries.
        // Actually, for threaded conversations, reading top-down (oldest first) is often better for replies. 
        // But backend sends desc created_at. Let's keep desc for now.
        return roots;
    }, [comments]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newComment.trim()) return;

        setSubmitting(true);
        try {
            await api.post(`/dreams/${dreamId}/comments`, { content: newComment.trim() });
            setNewComment('');
            await onRefresh();
        } catch (error) {
            console.error("Failed to post comment", error);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <section className="border-t border-[var(--border)] pt-10">
            <h3 className="text-2xl font-bold text-[var(--foreground)] mb-6">
                Discussion ({comments.length})
            </h3>

            {/* Main Comment Input */}
            {isAuthenticated ? (
                <form onSubmit={handleSubmit} className="flex gap-4 mb-8">
                    <div className="size-10 rounded-full bg-primary/20 flex items-center justify-center text-primary font-bold shrink-0 overflow-hidden">
                        {user?.avatar ? (
                            <img src={user.avatar} alt={user.username} className="w-full h-full object-cover" />
                        ) : (
                            <span>{user?.username?.charAt(0).toUpperCase()}</span>
                        )}
                    </div>
                    <div className="flex-1">
                        <textarea
                            value={newComment}
                            onChange={(e) => setNewComment(e.target.value)}
                            className="w-full bg-white dark:bg-[var(--card)] border border-[var(--border)] rounded-xl p-3 focus:ring-2 focus:ring-primary focus:border-transparent text-sm min-h-[80px] resize-none"
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
            ) : (
                <div className="mb-8 p-4 bg-gray-50 dark:bg-gray-800 rounded-xl text-center">
                    <p className="text-gray-600 dark:text-gray-300 mb-2">Log in to join the discussion</p>
                    {/* Add login button or link if needed, but header has it */}
                </div>
            )}

            {/* Comment Tree */}
            <div className="space-y-6">
                {commentTree.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">No comments yet. Be the first to share your thoughts!</p>
                ) : (
                    commentTree.map((node) => (
                        <CommentThread
                            key={node.id}
                            comment={node}
                            dreamId={dreamId}
                            onRefresh={onRefresh}
                            depth={0}
                        />
                    ))
                )}
            </div>
        </section>
    );
}

interface CommentThreadProps {
    comment: CommentNode;
    dreamId: number;
    onRefresh: () => Promise<void>;
    depth: number;
}

function CommentThread({ comment, dreamId, onRefresh, depth }: CommentThreadProps) {
    const { isAuthenticated, user } = useAuth();
    const [replying, setReplying] = useState(false);
    const [replyContent, setReplyContent] = useState('');
    const [submittingReply, setSubmittingReply] = useState(false);
    const [collapsed, setCollapsed] = useState(false);

    // State for editing
    const [editing, setEditing] = useState(false);
    const [editContent, setEditContent] = useState(comment.content);
    const [submittingEdit, setSubmittingEdit] = useState(false);

    // State for optimistic UI on voting
    const [voteState, setVoteState] = useState({
        userVote: comment.user_vote || 0,
        score: comment.score || 0
    });

    const isOwner = isAuthenticated && user?.id === comment.user_id;

    const handleEditSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!editContent.trim()) return;

        setSubmittingEdit(true);
        try {
            await api.patch(`/comments/${comment.id}`, { content: editContent.trim() });
            setEditing(false);
            await onRefresh();
        } catch (error) {
            console.error("Failed to edit comment", error);
        } finally {
            setSubmittingEdit(false);
        }
    };

    const handleDelete = async () => {
        if (!window.confirm("Are you sure you want to delete this comment?")) return;

        try {
            await api.delete(`/comments/${comment.id}`);
            await onRefresh();
        } catch (error) {
            console.error("Failed to delete comment", error);
        }
    };

    const handleVote = async (value: number) => {
        if (!isAuthenticated) return;

        // Optimistic update
        const previousVote = voteState.userVote;
        let scoreDelta = 0;

        if (value === previousVote) {
            // Toggle off if clicking same vote? Typical reddit behavior is yes. 
            // But my backend expects "0" to remove. 
            // But frontend click on active upvote usually means "remove upvote".
            // Let's implement toggle.
            value = 0;
            scoreDelta = -previousVote;
        } else {
            if (previousVote !== 0) {
                // Change from up to down or vice versa
                scoreDelta = value - previousVote;
            } else {
                // New vote
                scoreDelta = value;
            }
        }

        const newState = {
            userVote: value,
            score: voteState.score + scoreDelta
        };
        setVoteState(newState);

        try {
            await api.post(`/comments/${comment.id}/vote?value=${value}`, {});
            // No need to refresh whole list for just a vote, optimistic is enough
        } catch (error) {
            console.error("Failed to vote", error);
            // Revert
            setVoteState({ userVote: comment.user_vote || 0, score: comment.score || 0 });
        }
    };

    const handleReplySubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!replyContent.trim()) return;

        setSubmittingReply(true);
        try {
            await api.post(`/dreams/${dreamId}/comments`, {
                content: replyContent.trim(),
                parent_id: comment.id
            });
            setReplyContent('');
            setReplying(false);
            await onRefresh();
            // Automatically expand if collapsed (though we are replying to it so it must be expanded)
        } catch (error) {
            console.error("Failed to reply", error);
        } finally {
            setSubmittingReply(false);
        }
    };

    // Max depth to stop indentation to prevent squishing
    const maxIndentationDepth = 5;
    const isTooDeep = depth > maxIndentationDepth;

    if (collapsed) {
        return (
            <div className={`py-2 ${depth > 0 ? 'ml-0 border-l-2 border-transparent' : ''}`}>
                <button
                    onClick={() => setCollapsed(false)}
                    className="text-xs font-semibold text-gray-500 hover:text-primary flex items-center gap-2"
                >
                    <span className="material-symbols-outlined text-sm rotate-0 transition-transform">unfold_more</span>
                    <span className="font-bold">{comment.user?.username || 'Anonymous'}</span>
                    <span className="text-gray-400">{formatRelativeTime(comment.created_at)}</span>
                    <span className="text-gray-400">({comment.children.length} children)</span>
                </button>
            </div>
        );
    }

    return (
        <div className={`group relative ${depth > 0 ? 'mt-4' : ''}`}>

            {/* Thread Line */}
            {depth > 0 && (
                <div className="absolute -left-[19px] top-0 bottom-0 w-[2px] bg-[var(--border)] group-hover:bg-gray-300 dark:group-hover:bg-gray-600 transition-colors" />
            )}

            <div className="flex gap-3">
                {/* Avatar / Vote Column */}
                <div className="flex flex-col items-center gap-1 shrink-0">
                    <div className="size-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-gray-500 font-bold overflow-hidden">
                        {comment.user?.avatar ? (
                            <img src={comment.user.avatar} alt={comment.user?.username} className="w-full h-full object-cover" />
                        ) : (
                            <span className="text-xs">{comment.user?.username?.charAt(0).toUpperCase() || 'U'}</span>
                        )}
                    </div>
                    {/* Collapsing Line Trigger (for visual users) */}
                    <div
                        className="flex-1 w-6 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 rounded flex justify-center py-2"
                        onClick={() => setCollapsed(true)}
                        title="Collapse thread"
                    />
                </div>

                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                        <span className="font-bold text-sm text-[var(--foreground)]">
                            {comment.user?.username || 'Anonymous'}
                        </span>
                        <span className="text-xs text-gray-500">
                            {formatRelativeTime(comment.created_at)}
                        </span>
                        {/* Collapse Button */}
                        <button
                            onClick={() => setCollapsed(true)}
                            className="text-gray-400 hover:text-gray-600 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                            <span className="material-symbols-outlined text-[16px]">remove_circle_outline</span>
                        </button>
                    </div>

                    {/* Comment Content or Edit Form */}
                    {editing ? (
                        <form onSubmit={handleEditSubmit} className="mb-2">
                            <textarea
                                value={editContent}
                                onChange={(e) => setEditContent(e.target.value)}
                                autoFocus
                                className="w-full bg-white dark:bg-[var(--card)] border border-[var(--border)] rounded-lg p-3 focus:ring-2 focus:ring-primary focus:border-transparent text-sm min-h-[80px] resize-none"
                            />
                            <div className="flex justify-end gap-2 mt-2">
                                <button
                                    type="button"
                                    onClick={() => { setEditing(false); setEditContent(comment.content); }}
                                    className="px-3 py-1.5 text-gray-500 text-sm font-medium hover:text-gray-700 dark:hover:text-gray-300"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={submittingEdit || !editContent.trim()}
                                    className="px-3 py-1.5 bg-primary text-white rounded-lg text-sm font-bold hover:bg-primary-dark transition-colors disabled:opacity-50"
                                >
                                    {submittingEdit ? 'Saving...' : 'Save'}
                                </button>
                            </div>
                        </form>
                    ) : (
                        <div className="text-sm text-gray-600 dark:text-gray-300 mb-2 whitespace-pre-wrap break-words">
                            {comment.content}
                        </div>
                    )}

                    {/* Actions Row */}
                    <div className="flex items-center gap-4 select-none">
                        {/* Voting */}
                        <div className="flex items-center gap-1 bg-gray-100 dark:bg-gray-800 rounded-lg p-0.5">
                            <button
                                onClick={() => handleVote(1)}
                                className={`p-1 rounded hover:bg-white dark:hover:bg-gray-700 transition-colors ${voteState.userVote === 1 ? 'text-orange-500' : 'text-gray-500'}`}
                            >
                                <span className={`material-symbols-outlined text-[18px] ${voteState.userVote === 1 ? 'fill-current' : ''}`}>arrow_upward</span>
                            </button>
                            <span className={`text-xs font-bold min-w-[16px] text-center ${voteState.userVote === 1 ? 'text-orange-500' : voteState.userVote === -1 ? 'text-blue-500' : 'text-gray-500'}`}>
                                {voteState.score}
                            </span>
                            <button
                                onClick={() => handleVote(-1)}
                                className={`p-1 rounded hover:bg-white dark:hover:bg-gray-700 transition-colors ${voteState.userVote === -1 ? 'text-blue-500' : 'text-gray-500'}`}
                            >
                                <span className={`material-symbols-outlined text-[18px] ${voteState.userVote === -1 ? 'fill-current' : ''}`}>arrow_downward</span>
                            </button>
                        </div>

                        {isAuthenticated && (
                            <button
                                onClick={() => setReplying(!replying)}
                                className="text-xs font-bold text-gray-500 hover:text-primary flex items-center gap-1"
                            >
                                <span className="material-symbols-outlined text-[16px]">chat_bubble</span>
                                Reply
                            </button>
                        )}

                        {isOwner && !editing && (
                            <>
                                <button
                                    onClick={() => setEditing(true)}
                                    className="text-xs font-bold text-gray-500 hover:text-primary flex items-center gap-1"
                                >
                                    <span className="material-symbols-outlined text-[16px]">edit</span>
                                    Edit
                                </button>
                                <button
                                    onClick={handleDelete}
                                    className="text-xs font-bold text-gray-500 hover:text-red-500 flex items-center gap-1"
                                >
                                    <span className="material-symbols-outlined text-[16px]">delete</span>
                                    Delete
                                </button>
                            </>
                        )}
                    </div>

                    {/* Reply Form */}
                    {replying && (
                        <div className="mt-4">
                            <form onSubmit={handleReplySubmit}>
                                <textarea
                                    value={replyContent}
                                    onChange={(e) => setReplyContent(e.target.value)}
                                    autoFocus
                                    className="w-full bg-white dark:bg-[var(--card)] border border-[var(--border)] rounded-lg p-3 focus:ring-2 focus:ring-primary focus:border-transparent text-sm min-h-[80px] resize-none"
                                    placeholder={`Reply to ${comment.user?.username}...`}
                                />
                                <div className="flex justify-end gap-2 mt-2">
                                    <button
                                        type="button"
                                        onClick={() => setReplying(false)}
                                        className="px-3 py-1.5 text-gray-500 text-sm font-medium hover:text-gray-700 dark:hover:text-gray-300"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={submittingReply || !replyContent.trim()}
                                        className="px-3 py-1.5 bg-primary text-white rounded-lg text-sm font-bold hover:bg-primary-dark transition-colors disabled:opacity-50"
                                    >
                                        {submittingReply ? 'Sending...' : 'Reply'}
                                    </button>
                                </div>
                            </form>
                        </div>
                    )}

                    {/* Nested Comments (Recursion) */}
                    {comment.children.length > 0 && (
                        <div className={`mt-4 ${isTooDeep ? '' : 'pl-4 lg:pl-6'}`}>
                            {comment.children.map(child => (
                                <CommentThread
                                    key={child.id}
                                    comment={child}
                                    dreamId={dreamId}
                                    onRefresh={onRefresh}
                                    depth={depth + 1}
                                />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

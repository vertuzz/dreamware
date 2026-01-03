import { useState } from 'react';
import type { FeedbackType } from '~/lib/types';

interface FeedbackModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (type: FeedbackType, message: string) => Promise<void>;
}

export default function FeedbackModal({ isOpen, onClose, onSubmit }: FeedbackModalProps) {
    const [type, setType] = useState<FeedbackType>('feature');
    const [message, setMessage] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!message.trim()) {
            setError('Please enter a message');
            return;
        }
        
        setIsSubmitting(true);
        setError(null);
        try {
            await onSubmit(type, message.trim());
            setMessage('');
            setType('feature');
            onClose();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to submit feedback');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleClose = () => {
        if (!isSubmitting) {
            setMessage('');
            setType('feature');
            setError(null);
            onClose();
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div 
                className="absolute inset-0 bg-black/60 backdrop-blur-sm" 
                onClick={handleClose} 
            />
            
            {/* Modal */}
            <div className="relative w-full max-w-md bg-white dark:bg-[var(--card)] rounded-2xl shadow-2xl border border-[var(--border)]">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-[var(--border)]">
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                        <span className="material-symbols-outlined text-primary">feedback</span>
                        Send Feedback
                    </h2>
                    <button
                        onClick={handleClose}
                        disabled={isSubmitting}
                        className="size-8 flex items-center justify-center rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-slate-500"
                    >
                        <span className="material-symbols-outlined text-[20px]">close</span>
                    </button>
                </div>

                {/* Body */}
                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    {/* Type Selection */}
                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                            Type
                        </label>
                        <div className="flex gap-2">
                            {(['feature', 'bug', 'other'] as FeedbackType[]).map((t) => (
                                <button
                                    key={t}
                                    type="button"
                                    onClick={() => setType(t)}
                                    className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-all border ${
                                        type === t
                                            ? 'bg-primary text-white border-primary'
                                            : 'bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-primary/50'
                                    }`}
                                >
                                    {t === 'feature' && '✨ Feature'}
                                    {t === 'bug' && '🐛 Bug'}
                                    {t === 'other' && '💬 Other'}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Message */}
                    <div className="space-y-2">
                        <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                            Message
                        </label>
                        <textarea
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            placeholder="Tell us what's on your mind..."
                            rows={4}
                            className="w-full px-4 py-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-none"
                            disabled={isSubmitting}
                        />
                    </div>

                    {/* Error */}
                    {error && (
                        <p className="text-sm text-red-500 font-medium">{error}</p>
                    )}

                    {/* Actions */}
                    <div className="flex gap-3 pt-2">
                        <button
                            type="button"
                            onClick={handleClose}
                            disabled={isSubmitting}
                            className="flex-1 py-2.5 px-4 rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 font-semibold hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={isSubmitting || !message.trim()}
                            className="flex-1 py-2.5 px-4 rounded-xl bg-primary hover:bg-primary-dark text-white font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                            {isSubmitting ? (
                                <>
                                    <div className="size-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                    Sending...
                                </>
                            ) : (
                                <>
                                    <span className="material-symbols-outlined text-[18px]">send</span>
                                    Send Feedback
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

import { useEffect, useCallback } from 'react';

interface MediaFullscreenModalProps {
    isOpen: boolean;
    onClose: () => void;
    appUrl: string;
    title: string;
}

export default function MediaFullscreenModal({
    isOpen,
    onClose,
    appUrl,
    title,
}: MediaFullscreenModalProps) {
    const handleKeyDown = useCallback(
        (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                onClose();
            }
        },
        [onClose]
    );

    useEffect(() => {
        if (isOpen) {
            document.addEventListener('keydown', handleKeyDown);
            document.body.style.overflow = 'hidden';
        }
        return () => {
            document.removeEventListener('keydown', handleKeyDown);
            document.body.style.overflow = '';
        };
    }, [isOpen, handleKeyDown]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex flex-col">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/90 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Header */}
            <div className="relative z-10 flex items-center justify-between px-4 py-3 bg-black/50">
                <h3 className="text-white font-semibold truncate pr-4">
                    {title} - Live Preview
                </h3>
                <button
                    onClick={onClose}
                    className="flex items-center justify-center w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
                    aria-label="Close fullscreen"
                >
                    <span className="material-symbols-outlined">close</span>
                </button>
            </div>

            {/* Iframe Container */}
            <div className="relative z-10 flex-1 p-4">
                <div className="w-full h-full rounded-xl overflow-hidden bg-white shadow-2xl">
                    <iframe
                        src={appUrl}
                        title={`${title} - Live Preview`}
                        className="w-full h-full border-0"
                        sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox"
                        loading="lazy"
                    />
                </div>
            </div>
        </div>
    );
}

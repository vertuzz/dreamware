import { useState, useEffect } from 'react';
import type { AppMedia } from '~/lib/types';
import MediaFullscreenModal from './MediaFullscreenModal';

interface AppMediaGalleryProps {
    media?: AppMedia[];
    youtubeUrl?: string;
    appUrl?: string;
    title: string;
}

// Helper to extract YouTube video ID
function getYouTubeVideoId(url: string): string | null {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return match && match[2].length === 11 ? match[2] : null;
}

// Media index constants
const MEDIA_INDEX_APP_PREVIEW = -2;
const MEDIA_INDEX_YOUTUBE = -1;

export default function AppMediaGallery({ media, youtubeUrl, appUrl, title }: AppMediaGalleryProps) {
    const [selectedMediaIndex, setSelectedMediaIndex] = useState(0);
    const [isFullscreen, setIsFullscreen] = useState(false);
    const [isMobile, setIsMobile] = useState(false);

    const hasYouTube = youtubeUrl && getYouTubeVideoId(youtubeUrl);
    const hasAppUrl = !!appUrl;
    const heroMedia = media && media.length > 0 ? media[selectedMediaIndex]?.media_url : null;
    const youtubeId = youtubeUrl ? getYouTubeVideoId(youtubeUrl) : null;

    // Detect mobile viewport
    useEffect(() => {
        const checkMobile = () => setIsMobile(window.innerWidth < 1024);
        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    // Set initial selected media based on device
    // Desktop: show app preview first if available
    // Mobile: show first image (app preview is last in carousel)
    useEffect(() => {
        if (hasAppUrl && !isMobile) {
            setSelectedMediaIndex(MEDIA_INDEX_APP_PREVIEW);
        } else if (media && media.length > 0) {
            setSelectedMediaIndex(0);
        } else if (hasYouTube) {
            setSelectedMediaIndex(MEDIA_INDEX_YOUTUBE);
        } else if (hasAppUrl && isMobile) {
            setSelectedMediaIndex(MEDIA_INDEX_APP_PREVIEW);
        }
    }, [hasAppUrl, hasYouTube, media, isMobile]);

    return (
        <section className="flex flex-col gap-4">
            {/* Main Preview (Hero) */}
            <div className="relative w-full aspect-[3/2] rounded-2xl overflow-hidden bg-gray-900 shadow-sm group">
                {/* App Preview iframe */}
                {hasAppUrl && selectedMediaIndex === MEDIA_INDEX_APP_PREVIEW ? (
                    <>
                        <iframe
                            src={appUrl}
                            title={`${title} - Live Preview`}
                            className="absolute inset-0 w-full h-full bg-white"
                            sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox"
                            loading="lazy"
                        />
                        {/* Expand button */}
                        <button
                            onClick={() => setIsFullscreen(true)}
                            className="absolute top-3 right-3 z-20 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-black/60 hover:bg-black/80 text-white text-sm font-medium transition-colors backdrop-blur-sm"
                            aria-label="Expand to fullscreen"
                        >
                            <span className="material-symbols-outlined text-lg">fullscreen</span>
                            <span className="hidden sm:inline">Expand</span>
                        </button>
                    </>
                ) : hasYouTube && selectedMediaIndex === MEDIA_INDEX_YOUTUBE ? (
                    <iframe
                        className="absolute inset-0 w-full h-full"
                        src={`https://www.youtube.com/embed/${youtubeId}`}
                        title={title}
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowFullScreen
                    />
                ) : heroMedia ? (
                    <>
                        {/* Blurred background for premium feel and to fill gaps */}
                        <div
                            className="absolute inset-0 bg-cover bg-center blur-2xl opacity-50 scale-110 pointer-events-none"
                            style={{ backgroundImage: `url('${heroMedia}')` }}
                        />
                        <div className="absolute inset-0 bg-black/10" />

                        {/* Main image - contain to avoid cropping */}
                        <img
                            src={heroMedia}
                            alt={title}
                            className="relative z-10 w-full h-full object-contain transition-transform duration-700 group-hover:scale-[1.02]"
                        />
                    </>
                ) : hasYouTube ? (
                    <>
                        <div
                            className="absolute inset-0 bg-cover bg-center transition-transform duration-700 group-hover:scale-105"
                            style={{ backgroundImage: `url('https://img.youtube.com/vi/${youtubeId}/maxresdefault.jpg')` }}
                        />
                        <div className="absolute inset-0 bg-black/40 group-hover:bg-black/30 transition-colors" />
                        <button
                            onClick={() => setSelectedMediaIndex(MEDIA_INDEX_YOUTUBE)}
                            className="absolute inset-0 m-auto size-20 flex items-center justify-center rounded-full bg-white/20 backdrop-blur-sm text-white hover:bg-white/30 hover:scale-110 transition-all duration-300 z-20"
                        >
                            <span className="material-symbols-outlined text-5xl filled">play_arrow</span>
                        </button>
                    </>
                ) : hasAppUrl ? (
                    <>
                        <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
                            <span className="material-symbols-outlined text-6xl text-primary/40">web</span>
                        </div>
                        <button
                            onClick={() => setSelectedMediaIndex(MEDIA_INDEX_APP_PREVIEW)}
                            className="absolute inset-0 m-auto size-20 flex items-center justify-center rounded-full bg-primary/20 backdrop-blur-sm text-primary hover:bg-primary/30 hover:scale-110 transition-all duration-300 z-20"
                        >
                            <span className="material-symbols-outlined text-5xl">play_arrow</span>
                        </button>
                    </>
                ) : (
                    <img
                        src="/placeholder-app.png"
                        alt={title}
                        className="w-full h-full object-cover"
                    />
                )}
            </div>

            {/* Thumbnails Carousel */}
            {((media && media.length > 0) || hasYouTube || hasAppUrl) && (
                <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-hide snap-x">
                    {/* App Preview thumbnail - first on desktop */}
                    {hasAppUrl && !isMobile && (
                        <button
                            onClick={() => setSelectedMediaIndex(MEDIA_INDEX_APP_PREVIEW)}
                            className={`relative shrink-0 w-32 aspect-[3/2] rounded-lg overflow-hidden snap-start ${selectedMediaIndex === MEDIA_INDEX_APP_PREVIEW
                                ? 'ring-2 ring-primary ring-offset-2 ring-offset-[var(--background)]'
                                : 'border border-[var(--border)] opacity-70 hover:opacity-100'
                                } transition-opacity`}
                        >
                            <div className="w-full h-full bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
                                <span className="material-symbols-outlined text-3xl text-primary">web</span>
                            </div>
                            <div className="absolute bottom-0 inset-x-0 bg-black/60 text-white text-xs py-1 text-center font-medium">
                                Live Preview
                            </div>
                        </button>
                    )}
                    {hasYouTube && (
                        <button
                            onClick={() => setSelectedMediaIndex(MEDIA_INDEX_YOUTUBE)}
                            className={`relative shrink-0 w-32 aspect-[3/2] rounded-lg overflow-hidden snap-start ${selectedMediaIndex === MEDIA_INDEX_YOUTUBE
                                ? 'ring-2 ring-primary ring-offset-2 ring-offset-[var(--background)]'
                                : 'border border-[var(--border)] opacity-70 hover:opacity-100'
                                } transition-opacity`}
                        >
                            <img
                                className="w-full h-full object-cover"
                                src={`https://img.youtube.com/vi/${youtubeId}/mqdefault.jpg`}
                                alt="YouTube video"
                            />
                            <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                                <span className="material-symbols-outlined text-white text-2xl filled">play_arrow</span>
                            </div>
                        </button>
                    )}
                    {media?.map((item, index) => (
                        <button
                            key={item.id}
                            onClick={() => setSelectedMediaIndex(index)}
                            className={`relative shrink-0 w-32 aspect-[3/2] rounded-lg overflow-hidden snap-start ${selectedMediaIndex === index
                                ? 'ring-2 ring-primary ring-offset-2 ring-offset-[var(--background)]'
                                : 'border border-[var(--border)] opacity-70 hover:opacity-100'
                                } transition-opacity`}
                        >
                            <img
                                className="w-full h-full object-cover"
                                src={item.media_url}
                                alt={`Screenshot ${index + 1}`}
                            />
                        </button>
                    ))}
                    {/* App Preview thumbnail - last on mobile */}
                    {hasAppUrl && isMobile && (
                        <button
                            onClick={() => setSelectedMediaIndex(MEDIA_INDEX_APP_PREVIEW)}
                            className={`relative shrink-0 w-32 aspect-[3/2] rounded-lg overflow-hidden snap-start ${selectedMediaIndex === MEDIA_INDEX_APP_PREVIEW
                                ? 'ring-2 ring-primary ring-offset-2 ring-offset-[var(--background)]'
                                : 'border border-[var(--border)] opacity-70 hover:opacity-100'
                                } transition-opacity`}
                        >
                            <div className="w-full h-full bg-gradient-to-br from-primary/20 to-primary/5 flex items-center justify-center">
                                <span className="material-symbols-outlined text-3xl text-primary">web</span>
                            </div>
                            <div className="absolute bottom-0 inset-x-0 bg-black/60 text-white text-xs py-1 text-center font-medium">
                                Live Preview
                            </div>
                        </button>
                    )}
                </div>
            )}

            {/* Fullscreen Modal */}
            {hasAppUrl && (
                <MediaFullscreenModal
                    isOpen={isFullscreen}
                    onClose={() => setIsFullscreen(false)}
                    appUrl={appUrl}
                    title={title}
                />
            )}
        </section>
    );
}

import { useEffect, useState, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { appService } from '~/lib/services/app-service';
import type { App, Comment } from '~/lib/types';
import { Header } from '~/components/layout';
import {
    AppMediaGallery,
    AppActionPanel,
    AppComments,
    AppPromptSection,
    AppTools,
    ClaimOwnershipModal,
} from '~/components/apps';
import { Breadcrumbs } from '~/components/common/Breadcrumbs';
import DeleteConfirmModal from '~/components/common/DeleteConfirmModal';
import { useSEO } from '~/lib/hooks/useSEO';

// Helper to format date
function formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

// Skeleton component for loading state
function AppSkeleton() {
    return (
        <div className="min-h-screen bg-[var(--background)]">
            <Header />
            <main className="flex-1 w-full max-w-[1440px] mx-auto px-4 md:px-8 lg:px-12 py-8">
                {/* Breadcrumbs skeleton */}
                <div className="flex items-center gap-2 mb-8">
                    <div className="h-4 w-12 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                    <div className="h-4 w-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                    <div className="h-4 w-20 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
                    <div className="lg:col-span-8 flex flex-col gap-10">
                        {/* Hero skeleton */}
                        <div className="w-full aspect-video rounded-2xl bg-gray-200 dark:bg-gray-700 animate-pulse" />

                        {/* Title skeleton */}
                        <div className="border-b border-[var(--border)] pb-8">
                            <div className="h-12 w-3/4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse mb-4" />
                            <div className="flex gap-4">
                                <div className="h-5 w-32 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                                <div className="h-5 w-24 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                            </div>
                        </div>

                        {/* Content skeleton */}
                        <div className="space-y-4">
                            <div className="h-6 w-40 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                            <div className="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                            <div className="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                            <div className="h-4 w-2/3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" />
                        </div>
                    </div>

                    <div className="lg:col-span-4">
                        <div className="sticky top-24 space-y-6">
                            <div className="bg-white dark:bg-[var(--card)] rounded-2xl p-6 shadow-lg border border-[var(--border)]">
                                <div className="h-10 w-full bg-gray-200 dark:bg-gray-700 rounded-xl animate-pulse mb-4" />
                                <div className="h-14 w-full bg-gray-200 dark:bg-gray-700 rounded-xl animate-pulse" />
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

// Not Found component
function AppNotFound() {
    return (
        <div className="min-h-screen bg-[var(--background)]">
            <Header />
            <main className="flex-1 w-full max-w-[1440px] mx-auto px-4 md:px-8 lg:px-12 py-8">
                <div className="text-center py-20">
                    <span className="material-symbols-outlined text-6xl text-gray-400 mb-4">cloud_off</span>
                    <h1 className="text-2xl font-bold text-[var(--foreground)] mb-2">App not found</h1>
                    <p className="text-gray-500 mb-6">The app you're looking for doesn't exist or has been removed.</p>
                    <Link to="/" className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-white rounded-xl font-semibold hover:bg-primary-dark transition-colors">
                        <span className="material-symbols-outlined">arrow_back</span>
                        Back to Home
                    </Link>
                </div>
            </main>
        </div>
    );
}

export default function ViewApp() {
    const { slug } = useParams<{ slug: string }>();
    const navigate = useNavigate();
    const [app, setApp] = useState<App | null>(null);
    const [comments, setComments] = useState<Comment[]>([]);
    const [loading, setLoading] = useState(true);
    const [isLiked, setIsLiked] = useState(false);
    const [likesCount, setLikesCount] = useState(0);

    // Deletion state
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [isClaimModalOpen, setIsClaimModalOpen] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    // SEO - Dynamic app page with social sharing meta tags
    useSEO({
        title: app?.title || 'App',
        description: app?.prompt_text || 'Discover this AI-powered creation on Show Your App.',
        image: app?.media?.[0]?.media_url || undefined,
        url: `/apps/${slug}`,
        type: 'article',
    });

    const fetchApp = useCallback(async () => {
        // ... (fetchApp logic remains same)
        if (!slug) return;
        try {
            const appData = await appService.getApp(slug);
            setApp(appData);
            setLikesCount(appData.likes_count || 0);
            setIsLiked(!!appData.is_liked);

            const commentsData = await appService.getComments(appData.id);
            setComments(commentsData);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [slug]);

    useEffect(() => {
        fetchApp();
    }, [fetchApp]);

    const handleLike = async () => {
        // ... (handleLike logic remains same)
        if (!app) return;
        try {
            if (isLiked) {
                await appService.unlikeApp(app.id);
                setLikesCount((prev) => prev - 1);
            } else {
                await appService.likeApp(app.id);
                setLikesCount((prev) => prev + 1);
            }
            setIsLiked(!isLiked);
        } catch (err) {
            console.error('Failed to toggle like:', err);
        }
    };

    const handleShare = async () => {
        // ... (handleShare logic remains same)
        const url = window.location.href;
        if (navigator.share) {
            try {
                await navigator.share({
                    title: app?.title || 'Check out this App',
                    url,
                });
            } catch (err) {
                console.error('Share failed:', err);
            }
        } else {
            try {
                await navigator.clipboard.writeText(url);
                alert('Link copied to clipboard!');
            } catch (err) {
                console.error('Failed to copy:', err);
            }
        }
    };

    const handleDelete = async () => {
        if (!app) return;
        setIsDeleting(true);
        try {
            await appService.deleteApp(app.id);
            setIsDeleteModalOpen(false);
            navigate('/', { replace: true });
        } catch (err) {
            console.error('Failed to delete app:', err);
            alert('Failed to delete app. Please try again.');
        } finally {
            setIsDeleting(false);
        }
    };

    if (loading) return <AppSkeleton />;
    if (!app) return <AppNotFound />;

    return (
        <div className="min-h-screen bg-[var(--background)] flex flex-col">
            <Header />

            <main className="flex-1 w-full max-w-[1440px] mx-auto px-4 md:px-8 lg:px-12 py-8">
                {/* Breadcrumbs */}
                <Breadcrumbs
                    items={[
                        { label: 'Home', to: '/' },
                        ...(app.tags && app.tags.length > 0 ? [{
                            label: app.tags[0].name,
                            to: `/?tag_id=${app.tags[0].id}`
                        }] : []),
                        { label: app.title }
                    ]}
                />

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
                    <div className="lg:col-span-8 flex flex-col gap-10">
                        <AppMediaGallery
                            media={app.media}
                            youtubeUrl={app.youtube_url}
                            appUrl={app.app_url}
                            title={app.title}
                        />

                        <section className="border-b border-[var(--border)] pb-8">
                            <h1 className="text-4xl md:text-5xl font-black text-[var(--foreground)] tracking-tight mb-3">
                                {app.title}
                            </h1>
                            <div className="flex flex-wrap items-center gap-4 text-gray-500 dark:text-gray-400">
                                <div className="flex items-center gap-1.5">
                                    <span className="material-symbols-outlined text-lg">calendar_today</span>
                                    <span className="text-sm">Created {formatDate(app.created_at)}</span>
                                </div>
                                {app.tags && app.tags.length > 0 && (
                                    <>
                                        <span className="w-1 h-1 rounded-full bg-gray-300 dark:bg-gray-600" />
                                        <div className="flex items-center gap-1.5">
                                            <span className="material-symbols-outlined text-lg">category</span>
                                            <span className="text-sm">{app.tags[0].name}</span>
                                        </div>
                                    </>
                                )}
                                {app.is_agent_submitted && (
                                    <>
                                        <span className="w-1 h-1 rounded-full bg-gray-300 dark:bg-gray-600" />
                                        <div className="flex items-center gap-1.5 text-primary">
                                            <span className="material-symbols-outlined text-lg">smart_toy</span>
                                            <span className="text-sm font-medium">Agent Submitted</span>
                                        </div>
                                    </>
                                )}
                                {app.is_owner && (
                                    <>
                                        <span className="w-1 h-1 rounded-full bg-gray-300 dark:bg-gray-600" />
                                        <div className="flex items-center gap-1.5 text-emerald-600 dark:text-emerald-400">
                                            <span className="material-symbols-outlined text-lg">verified</span>
                                            <span className="text-sm font-medium">Verified Owner</span>
                                        </div>
                                    </>
                                )}
                            </div>
                        </section>

                        {app.prd_text && (
                            <section>
                                <h3 className="text-2xl font-bold text-[var(--foreground)] mb-4 flex items-center gap-2">
                                    <span className="material-symbols-outlined text-primary">auto_stories</span>
                                    The Story
                                </h3>
                                <div
                                    className="tiptap-editor prose prose-lg dark:prose-invert max-w-none text-gray-600 dark:text-gray-300 leading-relaxed"
                                    dangerouslySetInnerHTML={{ __html: app.prd_text }}
                                />
                            </section>
                        )}

                        {app.prompt_text && (
                            <AppPromptSection promptText={app.prompt_text} />
                        )}

                        {app.tools && app.tools.length > 0 && (
                            <AppTools tools={app.tools} />
                        )}

                        <AppComments
                            appId={app.id}
                            comments={comments}
                            onRefresh={fetchApp}
                        />
                    </div>

                    <div className="lg:col-span-4 relative">
                        <AppActionPanel
                            app={app}
                            likesCount={likesCount}
                            isLiked={isLiked}
                            onLike={handleLike}
                            onShare={handleShare}
                            onDelete={() => setIsDeleteModalOpen(true)}
                            onClaim={() => setIsClaimModalOpen(true)}
                        />
                    </div>
                </div>
            </main>

            <DeleteConfirmModal
                isOpen={isDeleteModalOpen}
                isDeleting={isDeleting}
                onClose={() => setIsDeleteModalOpen(false)}
                onConfirm={handleDelete}
            />

            <ClaimOwnershipModal
                isOpen={isClaimModalOpen}
                onClose={() => setIsClaimModalOpen(false)}
                appId={app.id}
                appTitle={app.title}
                onSuccess={() => {
                    alert('Ownership claim submitted successfully!');
                    fetchApp();
                }}
            />
        </div>
    );
}

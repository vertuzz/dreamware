import { useEffect, useState, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { dreamService } from '~/lib/services/dream-service';
import type { Dream, Comment } from '~/lib/types';
import { Header } from '~/components/layout';
import {
    DreamMediaGallery,
    DreamActionPanel,
    DreamComments,
    DreamPromptSection,
    DreamTools,
    ClaimOwnershipModal,
} from '~/components/dreams';
import { Breadcrumbs } from '~/components/common/Breadcrumbs';
import DeleteConfirmModal from '~/components/common/DeleteConfirmModal';
import { useSEO } from '~/lib/hooks/useSEO';

// Helper to format date
function formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

// Skeleton component for loading state
function DreamSkeleton() {
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
function DreamNotFound() {
    return (
        <div className="min-h-screen bg-[var(--background)]">
            <Header />
            <main className="flex-1 w-full max-w-[1440px] mx-auto px-4 md:px-8 lg:px-12 py-8">
                <div className="text-center py-20">
                    <span className="material-symbols-outlined text-6xl text-gray-400 mb-4">cloud_off</span>
                    <h1 className="text-2xl font-bold text-[var(--foreground)] mb-2">Dream not found</h1>
                    <p className="text-gray-500 mb-6">The dream you're looking for doesn't exist or has been removed.</p>
                    <Link to="/" className="inline-flex items-center gap-2 px-6 py-3 bg-primary text-white rounded-xl font-semibold hover:bg-primary-dark transition-colors">
                        <span className="material-symbols-outlined">arrow_back</span>
                        Back to Home
                    </Link>
                </div>
            </main>
        </div>
    );
}

export default function ViewDream() {
    const { slug } = useParams<{ slug: string }>();
    const navigate = useNavigate();
    const [dream, setDream] = useState<Dream | null>(null);
    const [comments, setComments] = useState<Comment[]>([]);
    const [loading, setLoading] = useState(true);
    const [isLiked, setIsLiked] = useState(false);
    const [likesCount, setLikesCount] = useState(0);

    // Deletion state
    const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
    const [isClaimModalOpen, setIsClaimModalOpen] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    // SEO - Dynamic dream page with social sharing meta tags
    useSEO({
        title: dream?.title || 'Dream',
        description: dream?.prompt_text || 'Discover this AI-powered creation on Dreamware.',
        image: dream?.media?.[0]?.media_url || undefined,
        url: `/dreams/${slug}`,
        type: 'article',
    });

    const fetchDream = useCallback(async () => {
        // ... (fetchDream logic remains same)
        if (!slug) return;
        try {
            const dreamData = await dreamService.getDream(slug);
            setDream(dreamData);
            setLikesCount(dreamData.likes_count || 0);
            setIsLiked(!!dreamData.is_liked);

            const commentsData = await dreamService.getComments(dreamData.id);
            setComments(commentsData);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    }, [slug]);

    useEffect(() => {
        fetchDream();
    }, [fetchDream]);

    const handleLike = async () => {
        // ... (handleLike logic remains same)
        if (!dream) return;
        try {
            if (isLiked) {
                await dreamService.unlikeDream(dream.id);
                setLikesCount((prev) => prev - 1);
            } else {
                await dreamService.likeDream(dream.id);
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
                    title: dream?.title || 'Check out this Dream',
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
        if (!dream) return;
        setIsDeleting(true);
        try {
            await dreamService.deleteDream(dream.id);
            setIsDeleteModalOpen(false);
            navigate('/', { replace: true });
        } catch (err) {
            console.error('Failed to delete dream:', err);
            alert('Failed to delete dream. Please try again.');
        } finally {
            setIsDeleting(false);
        }
    };

    if (loading) return <DreamSkeleton />;
    if (!dream) return <DreamNotFound />;

    return (
        <div className="min-h-screen bg-[var(--background)] flex flex-col">
            <Header />

            <main className="flex-1 w-full max-w-[1440px] mx-auto px-4 md:px-8 lg:px-12 py-8">
                {/* Breadcrumbs */}
                <Breadcrumbs
                    items={[
                        { label: 'Home', to: '/' },
                        ...(dream.tags && dream.tags.length > 0 ? [{
                            label: dream.tags[0].name,
                            to: `/?tag_id=${dream.tags[0].id}`
                        }] : []),
                        { label: dream.title }
                    ]}
                />

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
                    <div className="lg:col-span-8 flex flex-col gap-10">
                        <DreamMediaGallery
                            media={dream.media}
                            youtubeUrl={dream.youtube_url}
                            title={dream.title}
                        />

                        <section className="border-b border-[var(--border)] pb-8">
                            <h1 className="text-4xl md:text-5xl font-black text-[var(--foreground)] tracking-tight mb-3">
                                {dream.title}
                            </h1>
                            <div className="flex flex-wrap items-center gap-4 text-gray-500 dark:text-gray-400">
                                <div className="flex items-center gap-1.5">
                                    <span className="material-symbols-outlined text-lg">calendar_today</span>
                                    <span className="text-sm">Created {formatDate(dream.created_at)}</span>
                                </div>
                                {dream.tags && dream.tags.length > 0 && (
                                    <>
                                        <span className="w-1 h-1 rounded-full bg-gray-300 dark:bg-gray-600" />
                                        <div className="flex items-center gap-1.5">
                                            <span className="material-symbols-outlined text-lg">category</span>
                                            <span className="text-sm">{dream.tags[0].name}</span>
                                        </div>
                                    </>
                                )}
                                {dream.is_agent_submitted && (
                                    <>
                                        <span className="w-1 h-1 rounded-full bg-gray-300 dark:bg-gray-600" />
                                        <div className="flex items-center gap-1.5 text-primary">
                                            <span className="material-symbols-outlined text-lg">smart_toy</span>
                                            <span className="text-sm font-medium">Agent Submitted</span>
                                        </div>
                                    </>
                                )}
                                {dream.is_owner && (
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

                        {dream.prd_text && (
                            <section>
                                <h3 className="text-2xl font-bold text-[var(--foreground)] mb-4 flex items-center gap-2">
                                    <span className="material-symbols-outlined text-primary">auto_stories</span>
                                    The Story
                                </h3>
                                <div
                                    className="tiptap-editor prose prose-lg dark:prose-invert max-w-none text-gray-600 dark:text-gray-300 leading-relaxed"
                                    dangerouslySetInnerHTML={{ __html: dream.prd_text }}
                                />
                            </section>
                        )}

                        {dream.prompt_text && (
                            <DreamPromptSection promptText={dream.prompt_text} />
                        )}

                        {dream.tools && dream.tools.length > 0 && (
                            <DreamTools tools={dream.tools} />
                        )}

                        <DreamComments
                            dreamId={dream.id}
                            comments={comments}
                            onRefresh={fetchDream}
                        />
                    </div>

                    <div className="lg:col-span-4 relative">
                        <DreamActionPanel
                            dream={dream}
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
                dreamId={dream.id}
                dreamTitle={dream.title}
                onSuccess={() => {
                    alert('Ownership claim submitted successfully!');
                    fetchDream();
                }}
            />
        </div>
    );
}

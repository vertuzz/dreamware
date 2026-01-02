import { useEffect, useState, useCallback, useRef, useLayoutEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { dreamService, type DreamQueryParams } from '~/lib/services/dream-service';
import type { Dream, Tag, Tool } from '~/lib/types';
import DreamCard from '~/components/dreams/DreamCard';
import DreamCardSkeleton from '~/components/dreams/DreamCardSkeleton';
import FilterBar from '~/components/dreams/FilterBar';
import Header from '~/components/layout/Header';
import { useDreamCache } from '~/contexts/DreamCacheContext';

type SortOption = 'trending' | 'newest' | 'top_rated' | 'likes';

// Map aspect ratios for masonry variety
const aspectRatios: Array<'square' | 'video' | 'portrait' | 'landscape'> = [
    'landscape',
    'portrait',
    'video',
    'landscape',
    'square',
    'landscape',
    'portrait',
    'landscape',
];

// Helper to create a unique key from search params for cache validation
function createParamsKey(params: URLSearchParams): string {
    const sortedParams = new URLSearchParams([...params.entries()].sort());
    return sortedParams.toString();
}

// Helper to parse comma-separated strings/ids from URL
function parseParams(value: string | null): string[] {
    if (!value) return [];
    return value.split(',').filter(Boolean);
}

export default function Home() {
    const [searchParams, setSearchParams] = useSearchParams();
    const { saveCache, loadCache } = useDreamCache();

    // Initialize state from URL params
    const getInitialTagIds = () => parseParams(searchParams.get('tag_id')).map(Number).filter(n => !isNaN(n));
    const getInitialToolIds = () => parseParams(searchParams.get('tool_id')).map(Number).filter(n => !isNaN(n));
    const getInitialStatuses = () => parseParams(searchParams.get('status')) as Dream['status'][];
    const getInitialSort = (): SortOption => (searchParams.get('sort_by') as SortOption) || 'trending';
    const getInitialSearch = () => searchParams.get('search') || '';

    const [dreams, setDreams] = useState<Dream[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [tags, setTags] = useState<Tag[]>([]);
    const [tools, setTools] = useState<Tool[]>([]);
    const [selectedTagIds, setSelectedTagIds] = useState<number[]>(getInitialTagIds);
    const [selectedToolIds, setSelectedToolIds] = useState<number[]>(getInitialToolIds);
    const [selectedStatuses, setSelectedStatuses] = useState<Dream['status'][]>(getInitialStatuses);
    const [sortBy, setSortBy] = useState<SortOption>(getInitialSort);
    const [searchQuery, setSearchQuery] = useState(getInitialSearch);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);
    const [showSortDropdown, setShowSortDropdown] = useState(false);
    const [cacheRestored, setCacheRestored] = useState(false);
    const itemsPerPage = 20;

    // Ref for scroll restoration
    const pendingScrollRestore = useRef<number | null>(null);

    const observer = useRef<IntersectionObserver | null>(null);
    const lastDreamElementRef = useCallback(
        (node: HTMLDivElement | null) => {
            if (loading || loadingMore) return;
            if (observer.current) observer.current.disconnect();
            observer.current = new IntersectionObserver((entries) => {
                if (entries[0].isIntersecting && hasMore) {
                    setPage((prevPage) => prevPage + 1);
                }
            });
            if (node) observer.current.observe(node);
        },
        [loading, loadingMore, hasMore]
    );

    // Sync state to URL params
    useEffect(() => {
        const newParams = new URLSearchParams();
        if (selectedTagIds.length > 0) {
            newParams.set('tag_id', selectedTagIds.join(','));
        }
        if (selectedToolIds.length > 0) {
            newParams.set('tool_id', selectedToolIds.join(','));
        }
        if (selectedStatuses.length > 0) {
            newParams.set('status', selectedStatuses.join(','));
        }
        if (sortBy !== 'trending') {
            newParams.set('sort_by', sortBy);
        }
        if (searchQuery) {
            newParams.set('search', searchQuery);
        }
        setSearchParams(newParams, { replace: true });
    }, [selectedTagIds, selectedToolIds, selectedStatuses, sortBy, searchQuery, setSearchParams]);

    const fetchDreams = useCallback(async (isInitial: boolean = false) => {
        if (isInitial) {
            setLoading(true);
        } else {
            setLoadingMore(true);
        }

        try {
            const params: DreamQueryParams = {
                skip: ((isInitial ? 1 : page) - 1) * itemsPerPage,
                limit: itemsPerPage,
                sort_by: sortBy,
            };

            // Add search if present
            if (searchQuery) {
                params.search = searchQuery;
            }

            // Add multi-select filters
            if (selectedTagIds.length > 0) {
                params.tag_id = selectedTagIds;
            }
            if (selectedToolIds.length > 0) {
                params.tool_id = selectedToolIds;
            }
            if (selectedStatuses.length > 0) {
                // Backend usually takes single status or we might need to handle multi-status if supported
                // For now backend schemas.py line 68 shows status: Optional[DreamStatus]
                // Let's check how backend handles it. 
                // Currently backend only supports single status filter in get_dreams.
                // We'll just take the first one or pass as list if backend updated.
                // Looking at dreams.py:115: if status: query = query.filter(Dream.status == status)
                // It only supports one. Let's send the first one or we can update backend.
                // For now, let's keep it consistent with what backend supports.
                params.status = selectedStatuses[0];
            }

            const data = await dreamService.getDreams(params);

            if (isInitial) {
                setDreams(data);
            } else {
                setDreams((prev) => [...prev, ...data]);
            }

            setHasMore(data.length === itemsPerPage);
        } catch (err) {
            console.error('Failed to fetch dreams:', err);
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    }, [page, sortBy, selectedTagIds, selectedToolIds, selectedStatuses, searchQuery]);

    // Load filter data (tags, tools) on mount
    useEffect(() => {
        const loadInitialData = async () => {
            try {
                const [tagsData, toolsData] = await Promise.all([
                    dreamService.getTags(),
                    dreamService.getTools()
                ]);
                setTags(tagsData);
                setTools(toolsData);
            } catch (err) {
                console.error('Failed to fetch filter data:', err);
            }
        };
        loadInitialData();
    }, []);

    // Check cache on mount and restore if valid
    useEffect(() => {
        const paramsKey = createParamsKey(searchParams);
        const cached = loadCache(paramsKey);

        if (cached) {
            setDreams(cached.dreams);
            setPage(cached.page);
            setHasMore(cached.hasMore);
            pendingScrollRestore.current = cached.scrollPosition;
            setLoading(false);
            setCacheRestored(true);
        } else {
            fetchDreams(true);
        }
        // Only run on mount
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // Restore scroll position after dreams render from cache
    useLayoutEffect(() => {
        if (cacheRestored && pendingScrollRestore.current !== null && dreams.length > 0) {
            window.scrollTo(0, pendingScrollRestore.current);
            pendingScrollRestore.current = null;
            setCacheRestored(false);
        }
    }, [cacheRestored, dreams]);

    // Filter/sort changes (only if not initial cache restore)
    useEffect(() => {
        if (cacheRestored) return; // Skip if just restored from cache
        setPage(1);
        setHasMore(true);
        fetchDreams(true);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [sortBy, selectedTagIds, selectedToolIds, selectedStatuses]);

    // Fetch more when page changes (infinite scroll)
    useEffect(() => {
        if (page > 1) {
            fetchDreams(false);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [page]);

    // Debounced search handler
    useEffect(() => {
        if (cacheRestored) return;
        const timer = setTimeout(() => {
            setPage(1);
            setHasMore(true);
            fetchDreams(true);
        }, 300);
        return () => clearTimeout(timer);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchQuery]);

    // Save cache on unmount
    useEffect(() => {
        return () => {
            const paramsKey = createParamsKey(new URLSearchParams(window.location.search));
            saveCache({
                dreams,
                page,
                hasMore,
                scrollPosition: window.scrollY,
                paramsKey,
            });
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [dreams, page, hasMore, saveCache]);

    const handleFilterChange = (selected: { tagIds: number[]; toolIds: number[]; statuses: Dream['status'][] }) => {
        setCacheRestored(false); // Reset flag so filters work
        setSelectedTagIds(selected.tagIds);
        setSelectedToolIds(selected.toolIds);
        setSelectedStatuses(selected.statuses);
    };

    const handleSortChange = (sort: SortOption) => {
        setCacheRestored(false);
        setSortBy(sort);
        setShowSortDropdown(false);
    };

    const handleSearch = (query: string) => {
        setCacheRestored(false);
        setSearchQuery(query);
    };

    const sortLabels: Record<SortOption, string> = {
        trending: 'Trending',
        newest: 'Newest',
        top_rated: 'Top Rated',
        likes: 'Most Liked',
    };

    const handleLike = async (dream: Dream) => {
        // Optimistic update
        setDreams(prev => prev.map(d => {
            if (d.id === dream.id) {
                return {
                    ...d,
                    is_liked: !d.is_liked,
                    likes_count: (d.likes_count || 0) + (d.is_liked ? -1 : 1)
                };
            }
            return d;
        }));

        try {
            if (dream.is_liked) {
                await dreamService.unlikeDream(dream.id);
            } else {
                await dreamService.likeDream(dream.id);
            }
        } catch (err) {
            console.error('Failed to toggle like:', err);
            // Revert on failure
            setDreams(prev => prev.map(d => {
                if (d.id === dream.id) {
                    return {
                        ...d,
                        is_liked: dream.is_liked,
                        likes_count: dream.likes_count
                    };
                }
                return d;
            }));
        }
    };

    return (
        <div className="relative flex min-h-screen w-full flex-col overflow-x-hidden">
            {/* Header */}
            <Header onSearch={handleSearch} />

            {/* Main Content */}
            <main className="flex-1 w-full max-w-[1600px] mx-auto px-4 sm:px-6 md:px-10 py-8">
                {/* Hero Headline */}
                <div className="flex flex-col items-center justify-center text-center pb-10 pt-4 max-w-3xl mx-auto">
                    <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight text-[#0d111b] dark:text-white mb-3">
                        Discover the future of{' '}
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-purple-500">
                            AI applications
                        </span>
                    </h1>
                    <p className="text-gray-500 dark:text-gray-400 text-lg">
                        Browse thousands of community-generated agents, UI components, and full-stack dreams.
                    </p>
                </div>

                {/* Filters & Sort */}
                <div className="sticky top-[72px] z-40 bg-[var(--background)]/95 backdrop-blur-sm py-4 mb-8 flex items-center justify-between gap-4 border-b border-gray-200 dark:border-gray-800">
                    <div className="flex items-center gap-3">
                        <FilterBar
                            tags={tags}
                            tools={tools}
                            selectedTagIds={selectedTagIds}
                            selectedToolIds={selectedToolIds}
                            selectedStatuses={selectedStatuses}
                            onChange={handleFilterChange}
                        />

                        {/* Selected chips for quick individual removal */}
                        <div className="hidden md:flex flex-wrap gap-2 overflow-x-auto scrollbar-hide">
                            {selectedStatuses.map(status => (
                                <button
                                    key={`status-${status}`}
                                    onClick={() => {
                                        setCacheRestored(false);
                                        setSelectedStatuses(prev => prev.filter(s => s !== status));
                                    }}
                                    className="inline-flex h-7 items-center gap-1.5 rounded-full border border-primary/20 bg-primary/5 px-3 text-[12px] font-medium text-primary hover:bg-primary/10 transition-colors"
                                >
                                    <span className="material-symbols-outlined text-[14px]">flag</span>
                                    {status}
                                    <span className="material-symbols-outlined text-[14px]">close</span>
                                </button>
                            ))}
                            {selectedTagIds.map(id => {
                                const tag = tags.find(t => t.id === id);
                                if (!tag) return null;
                                return (
                                    <button
                                        key={`tag-${id}`}
                                        onClick={() => {
                                            setCacheRestored(false);
                                            setSelectedTagIds(prev => prev.filter(tid => tid !== id));
                                        }}
                                        className="inline-flex h-7 items-center gap-1.5 rounded-full border border-primary/20 bg-primary/5 px-3 text-[12px] font-medium text-primary hover:bg-primary/10 transition-colors"
                                    >
                                        {tag.name}
                                        <span className="material-symbols-outlined text-[14px]">close</span>
                                    </button>
                                );
                            })}
                            {selectedToolIds.map(id => {
                                const tool = tools.find(t => t.id === id);
                                if (!tool) return null;
                                return (
                                    <button
                                        key={`tool-${id}`}
                                        onClick={() => {
                                            setCacheRestored(false);
                                            setSelectedToolIds(prev => prev.filter(tid => tid !== id));
                                        }}
                                        className="inline-flex h-7 items-center gap-1.5 rounded-full border border-purple-200 bg-purple-50 px-3 text-[12px] font-medium text-purple-600 hover:bg-purple-100 transition-colors"
                                    >
                                        {tool.name}
                                        <span className="material-symbols-outlined text-[14px]">close</span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Sort Dropdown */}
                    <div className="relative">
                        <button
                            onClick={() => setShowSortDropdown(!showSortDropdown)}
                            className="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-300 hover:text-primary transition-colors whitespace-nowrap"
                        >
                            <span className="material-symbols-outlined">sort</span>
                            <span>Sort by: {sortLabels[sortBy] || 'Trending'}</span>
                            <span className="material-symbols-outlined text-[18px]">keyboard_arrow_down</span>
                        </button>

                        {showSortDropdown && (
                            <div className="absolute right-0 top-full mt-2 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 py-2 min-w-[160px] z-50">
                                {(Object.keys(sortLabels) as SortOption[]).map((option) => (
                                    <button
                                        key={option}
                                        onClick={() => handleSortChange(option)}
                                        className={`w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors ${sortBy === option
                                            ? 'text-primary font-semibold'
                                            : 'text-gray-700 dark:text-gray-300'
                                            }`}
                                    >
                                        {sortLabels[option]}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Empty State */}
                {!loading && dreams.length === 0 && (
                    <div className="flex flex-col items-center justify-center py-20 text-center">
                        <span className="material-symbols-outlined text-6xl text-gray-300 mb-4">
                            lightbulb
                        </span>
                        <h3 className="text-xl font-semibold text-gray-700 dark:text-gray-300 mb-2">
                            No dreams found
                        </h3>
                        <p className="text-gray-500 dark:text-gray-400 max-w-md">
                            {searchQuery
                                ? `No results for "${searchQuery}". Try a different search term.`
                                : 'Be the first to submit a dream and share your AI creation with the community!'}
                        </p>
                    </div>
                )}

                {/* Masonry Grid */}
                {dreams.length > 0 && (
                    <div className="masonry-grid pb-12">
                        {dreams.map((dream, index) => {
                            if (dreams.length === index + 1) {
                                return (
                                    <div ref={lastDreamElementRef} key={dream.id}>
                                        <DreamCard
                                            dream={dream}
                                            aspectRatio={aspectRatios[index % aspectRatios.length]}
                                            onLike={handleLike}
                                        />
                                    </div>
                                );
                            } else {
                                return (
                                    <DreamCard
                                        key={dream.id}
                                        dream={dream}
                                        aspectRatio={aspectRatios[index % aspectRatios.length]}
                                        onLike={handleLike}
                                    />
                                );
                            }
                        })}
                    </div>
                )}

                {/* Loading State */}
                {(loading || loadingMore) && (
                    <div className="masonry-grid pb-12">
                        {Array.from({ length: loading ? 8 : 4 }).map((_, index) => (
                            <DreamCardSkeleton key={index} />
                        ))}
                    </div>
                )}

                {/* End of List Message */}
                {!loading && !loadingMore && !hasMore && dreams.length > 0 && (
                    <div className="flex items-center justify-center py-10">
                        <p className="text-gray-400 text-sm font-medium">You've reached the end of the universe ✨</p>
                    </div>
                )}
            </main>
        </div>
    );
}

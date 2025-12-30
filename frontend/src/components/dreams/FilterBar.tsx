import { useState, useRef, useEffect } from 'react';
import type { Tag, Tool } from '~/lib/types';

interface FilterBarProps {
    tags: Tag[];
    tools: Tool[];
    selectedTagIds: number[];
    selectedToolIds: number[];
    onChange: (selected: { tagIds: number[]; toolIds: number[] }) => void;
}

export default function FilterBar({
    tags,
    tools,
    selectedTagIds,
    selectedToolIds,
    onChange,
}: FilterBarProps) {
    const [openDropdown, setOpenDropdown] = useState<'tags' | 'tools' | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const containerRef = useRef<HTMLDivElement>(null);
    const searchInputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (openDropdown) {
            setSearchQuery('');
            setTimeout(() => {
                searchInputRef.current?.focus();
            }, 100);
        }
    }, [openDropdown]);

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setOpenDropdown(null);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const toggleTag = (id: number) => {
        const newIds = selectedTagIds.includes(id)
            ? selectedTagIds.filter((tid) => tid !== id)
            : [...selectedTagIds, id];
        onChange({ tagIds: newIds, toolIds: selectedToolIds });
    };

    const toggleTool = (id: number) => {
        const newIds = selectedToolIds.includes(id)
            ? selectedToolIds.filter((tid) => tid !== id)
            : [...selectedToolIds, id];
        onChange({ tagIds: selectedTagIds, toolIds: newIds });
    };

    const clearTags = () => {
        onChange({ tagIds: [], toolIds: selectedToolIds });
    };

    const clearTools = () => {
        onChange({ tagIds: selectedTagIds, toolIds: [] });
    };

    const filteredTags = tags.filter((tag) =>
        tag.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const filteredTools = tools.filter((tool) =>
        tool.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="flex items-center gap-2" ref={containerRef}>
            {/* Tags Dropdown */}
            <div className="relative">
                <button
                    onClick={() => setOpenDropdown(openDropdown === 'tags' ? null : 'tags')}
                    className={`flex h-10 items-center gap-2 rounded-xl px-4 text-sm font-semibold transition-all border ${openDropdown === 'tags' || selectedTagIds.length > 0
                        ? 'bg-primary/5 border-primary text-primary outline-none ring-2 ring-primary/20'
                        : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:border-primary hover:text-primary'
                        }`}
                >
                    <span className="material-symbols-outlined text-[20px]">sell</span>
                    <span>Tags</span>
                    {selectedTagIds.length > 0 && (
                        <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-primary px-1.5 text-[11px] font-bold text-white">
                            {selectedTagIds.length}
                        </span>
                    )}
                    <span className="material-symbols-outlined text-[18px]">
                        {openDropdown === 'tags' ? 'expand_less' : 'expand_more'}
                    </span>
                </button>

                {openDropdown === 'tags' && (
                    <div className="absolute left-0 top-full z-50 mt-2 w-[260px] overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-xl dark:border-gray-700 dark:bg-gray-900 animate-in fade-in zoom-in duration-200">
                        <div className="border-b border-gray-100 p-2 dark:border-gray-800">
                            <div className="relative flex items-center">
                                <span className="material-symbols-outlined absolute left-3 text-[18px] text-gray-400">search</span>
                                <input
                                    ref={searchInputRef}
                                    type="text"
                                    placeholder="Search tags..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="h-9 w-full rounded-xl bg-gray-50 pl-9 pr-3 text-sm outline-none ring-primary/20 transition-all focus:bg-white focus:ring-2 dark:bg-gray-800 dark:focus:bg-gray-800"
                                />
                                {searchQuery && (
                                    <button
                                        onClick={() => setSearchQuery('')}
                                        className="absolute right-2 flex h-5 w-5 items-center justify-center rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700"
                                    >
                                        <span className="material-symbols-outlined text-[14px]">close</span>
                                    </button>
                                )}
                            </div>
                        </div>
                        <div className="max-h-[300px] overflow-y-auto p-1 scrollbar-hide">
                            <div className="grid grid-cols-1 gap-0.5">
                                {filteredTags.length > 0 ? (
                                    filteredTags.map((tag) => (
                                        <button
                                            key={tag.id}
                                            onClick={() => toggleTag(tag.id)}
                                            className={`flex items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition-colors ${selectedTagIds.includes(tag.id)
                                                ? 'bg-primary/10 text-primary font-medium'
                                                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                                                }`}
                                        >
                                            <span className="truncate">{tag.name}</span>
                                            {selectedTagIds.includes(tag.id) && (
                                                <span className="material-symbols-outlined text-[16px]">check</span>
                                            )}
                                        </button>
                                    ))
                                ) : (
                                    <div className="px-3 py-6 text-center">
                                        <p className="text-xs text-gray-500">No tags found</p>
                                    </div>
                                )}
                            </div>
                        </div>
                        <div className="flex items-center justify-between border-t border-gray-100 bg-gray-50 p-2 dark:border-gray-800 dark:bg-gray-800/50">
                            <button
                                onClick={clearTags}
                                className="px-3 py-1.5 text-xs font-semibold text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
                            >
                                Clear
                            </button>
                            <button
                                onClick={() => setOpenDropdown(null)}
                                className="rounded-lg bg-gray-900 px-4 py-1.5 text-xs font-bold text-white hover:bg-black dark:bg-white dark:text-gray-900 dark:hover:bg-gray-100 transition-colors"
                            >
                                Done
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Tools Dropdown */}
            <div className="relative">
                <button
                    onClick={() => setOpenDropdown(openDropdown === 'tools' ? null : 'tools')}
                    className={`flex h-10 items-center gap-2 rounded-xl px-4 text-sm font-semibold transition-all border ${openDropdown === 'tools' || selectedToolIds.length > 0
                        ? 'bg-purple-500/5 border-purple-500 text-purple-600 dark:text-purple-400 outline-none ring-2 ring-purple-500/20'
                        : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:border-purple-500 hover:text-purple-600'
                        }`}
                >
                    <span className="material-symbols-outlined text-[20px]">build</span>
                    <span>Tools</span>
                    {selectedToolIds.length > 0 && (
                        <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-purple-500 px-1.5 text-[11px] font-bold text-white">
                            {selectedToolIds.length}
                        </span>
                    )}
                    <span className="material-symbols-outlined text-[18px]">
                        {openDropdown === 'tools' ? 'expand_less' : 'expand_more'}
                    </span>
                </button>

                {openDropdown === 'tools' && (
                    <div className="absolute left-0 top-full z-50 mt-2 w-[260px] overflow-hidden rounded-2xl border border-gray-200 bg-white shadow-xl dark:border-gray-700 dark:bg-gray-900 animate-in fade-in zoom-in duration-200">
                        <div className="border-b border-gray-100 p-2 dark:border-gray-800">
                            <div className="relative flex items-center">
                                <span className="material-symbols-outlined absolute left-3 text-[18px] text-gray-400">search</span>
                                <input
                                    ref={searchInputRef}
                                    type="text"
                                    placeholder="Search tools..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="h-9 w-full rounded-xl bg-gray-50 pl-9 pr-3 text-sm outline-none ring-purple-500/20 transition-all focus:bg-white focus:ring-2 dark:bg-gray-800 dark:focus:bg-gray-800"
                                />
                                {searchQuery && (
                                    <button
                                        onClick={() => setSearchQuery('')}
                                        className="absolute right-2 flex h-5 w-5 items-center justify-center rounded-full text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700"
                                    >
                                        <span className="material-symbols-outlined text-[14px]">close</span>
                                    </button>
                                )}
                            </div>
                        </div>
                        <div className="max-h-[300px] overflow-y-auto p-1 scrollbar-hide">
                            <div className="grid grid-cols-1 gap-0.5">
                                {filteredTools.length > 0 ? (
                                    filteredTools.map((tool) => (
                                        <button
                                            key={tool.id}
                                            onClick={() => toggleTool(tool.id)}
                                            className={`flex items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition-colors ${selectedToolIds.includes(tool.id)
                                                ? 'bg-purple-500/10 text-purple-600 dark:text-purple-400 font-medium'
                                                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                                                }`}
                                        >
                                            <span className="truncate">{tool.name}</span>
                                            {selectedToolIds.includes(tool.id) && (
                                                <span className="material-symbols-outlined text-[16px]">check</span>
                                            )}
                                        </button>
                                    ))
                                ) : (
                                    <div className="px-3 py-6 text-center">
                                        <p className="text-xs text-gray-500">No tools found</p>
                                    </div>
                                )}
                            </div>
                        </div>
                        <div className="flex items-center justify-between border-t border-gray-100 bg-gray-50 p-2 dark:border-gray-800 dark:bg-gray-800/50">
                            <button
                                onClick={clearTools}
                                className="px-3 py-1.5 text-xs font-semibold text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
                            >
                                Clear
                            </button>
                            <button
                                onClick={() => setOpenDropdown(null)}
                                className="rounded-lg bg-gray-900 px-4 py-1.5 text-xs font-bold text-white hover:bg-black dark:bg-white dark:text-gray-900 dark:hover:bg-gray-100 transition-colors"
                            >
                                Done
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}


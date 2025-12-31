import { useState, useRef, useEffect } from 'react';

export interface MultiSelectItem {
    id: number;
    name: string;
}

interface MultiSelectProps {
    items: MultiSelectItem[];
    selectedIds: number[];
    onChange: (selectedIds: number[]) => void;
    label: string;
    icon: string;
    placeholder?: string;
    color?: 'primary' | 'purple';
}

export default function MultiSelect({
    items,
    selectedIds,
    onChange,
    label,
    icon,
    placeholder = 'Search...',
    color = 'primary'
}: MultiSelectProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const containerRef = useRef<HTMLDivElement>(null);
    const searchInputRef = useRef<HTMLInputElement>(null);

    // Color variants
    const colors = {
        primary: {
            buttonActive: 'bg-primary/5 border-primary text-primary outline-none ring-2 ring-primary/20',
            buttonInactive: 'hover:border-primary hover:text-primary',
            badge: 'bg-primary',
            ring: 'ring-primary/20',
            optionSelected: 'bg-primary/10 text-primary font-medium',
        },
        purple: {
            buttonActive: 'bg-purple-500/5 border-purple-500 text-purple-600 dark:text-purple-400 outline-none ring-2 ring-purple-500/20',
            buttonInactive: 'hover:border-purple-500 hover:text-purple-600',
            badge: 'bg-purple-500',
            ring: 'ring-purple-500/20',
            optionSelected: 'bg-purple-500/10 text-purple-600 dark:text-purple-400 font-medium',
        }
    };

    const theme = colors[color];

    useEffect(() => {
        if (isOpen) {
            setSearchQuery('');
            // Small delay to allow render before focus
            setTimeout(() => {
                searchInputRef.current?.focus();
            }, 50);
        }
    }, [isOpen]);

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const toggleItem = (id: number) => {
        const newIds = selectedIds.includes(id)
            ? selectedIds.filter((tid) => tid !== id)
            : [...selectedIds, id];
        onChange(newIds);
    };

    const clearSelection = () => {
        onChange([]);
    };

    const filteredItems = items.filter((item) =>
        item.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="relative inline-block" ref={containerRef}>
            <button
                type="button"
                onClick={() => setIsOpen(!isOpen)}
                className={`flex h-10 items-center gap-2 rounded-xl px-4 text-sm font-semibold transition-all border
                    ${isOpen || selectedIds.length > 0
                        ? theme.buttonActive
                        : `bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 ${theme.buttonInactive}`
                    }`}
            >
                <span className="material-symbols-outlined text-[20px]">{icon}</span>
                <span>{label}</span>
                {selectedIds.length > 0 && (
                    <span className={`flex h-5 min-w-[20px] items-center justify-center rounded-full px-1.5 text-[11px] font-bold text-white ${theme.badge}`}>
                        {selectedIds.length}
                    </span>
                )}
                <span className="material-symbols-outlined text-[18px]">
                    {isOpen ? 'expand_less' : 'expand_more'}
                </span>
            </button>

            {isOpen && (
                <div className="absolute left-0 top-full z-50 mt-2 w-[260px] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl dark:border-slate-700 dark:bg-slate-900 animate-in fade-in zoom-in duration-200">
                    <div className="border-b border-slate-100 p-2 dark:border-slate-800">
                        <div className="relative flex items-center">
                            <span className="material-symbols-outlined absolute left-3 text-[18px] text-slate-400">search</span>
                            <input
                                ref={searchInputRef}
                                type="text"
                                placeholder={placeholder}
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className={`h-9 w-full rounded-xl bg-slate-50 pl-9 pr-3 text-sm outline-none transition-all focus:bg-white focus:ring-2 dark:bg-slate-800 dark:focus:bg-slate-800 ${theme.ring}`}
                            />
                            {searchQuery && (
                                <button
                                    type="button"
                                    onClick={() => setSearchQuery('')}
                                    className="absolute right-2 flex h-5 w-5 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-700"
                                >
                                    <span className="material-symbols-outlined text-[14px]">close</span>
                                </button>
                            )}
                        </div>
                    </div>
                    <div className="max-h-[300px] overflow-y-auto p-1 scrollbar-hide">
                        <div className="grid grid-cols-1 gap-0.5">
                            {filteredItems.length > 0 ? (
                                filteredItems.map((item) => (
                                    <button
                                        type="button"
                                        key={item.id}
                                        onClick={() => toggleItem(item.id)}
                                        className={`flex items-center justify-between rounded-lg px-3 py-2 text-left text-sm transition-colors
                                            ${selectedIds.includes(item.id)
                                                ? theme.optionSelected
                                                : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800'
                                            }`}
                                    >
                                        <span className="truncate">{item.name}</span>
                                        {selectedIds.includes(item.id) && (
                                            <span className="material-symbols-outlined text-[16px]">check</span>
                                        )}
                                    </button>
                                ))
                            ) : (
                                <div className="px-3 py-6 text-center">
                                    <p className="text-xs text-slate-500">No items found</p>
                                </div>
                            )}
                        </div>
                    </div>
                    <div className="flex items-center justify-between border-t border-slate-100 bg-slate-50 p-2 dark:border-slate-800 dark:bg-slate-800/50">
                        <button
                            type="button"
                            onClick={clearSelection}
                            className="px-3 py-1.5 text-xs font-semibold text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 transition-colors"
                        >
                            Clear
                        </button>
                        <button
                            type="button"
                            onClick={() => setIsOpen(false)}
                            className="rounded-lg bg-slate-900 px-4 py-1.5 text-xs font-bold text-white hover:bg-black dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100 transition-colors"
                        >
                            Done
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

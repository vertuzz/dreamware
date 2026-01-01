import type { Tool, Tag } from '~/lib/types';

interface DreamPreviewProps {
    title: string;
    tagline: string;
    previews: string[];
    selectedTools: Tool[];
    selectedTags: Tag[];
    coverImage?: string;
}

export default function DreamPreview({
    title,
    tagline,
    previews,
    selectedTools,
    selectedTags,
    coverImage
}: DreamPreviewProps) {
    // Determine which image to show
    // Priority: 1. New upload (previews), 2. Existing cover image, 3. None
    const displayImage = previews.length > 0
        ? previews[previews.length - 1]
        : coverImage;

    return (
        <div className="sticky top-28 flex flex-col gap-4">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Live Preview</h3>
                <span className="px-2 py-1 bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 rounded text-[10px] font-bold">Auto-Updating</span>
            </div>

            {/* Preview Card */}
            <div className="bg-white dark:bg-[#1E2330] rounded-xl shadow-xl overflow-hidden border border-slate-100 dark:border-slate-700 group cursor-default transition-all duration-300 hover:shadow-2xl hover:shadow-primary/10 hover:-translate-y-1">
                <div className="aspect-[4/3] w-full overflow-hidden bg-slate-100 dark:bg-slate-800 relative">
                    {displayImage ? (
                        <img className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" src={displayImage} alt="Preview" />
                    ) : (
                        <div className="w-full h-full flex flex-col items-center justify-center text-slate-400 bg-slate-50 dark:bg-slate-900">
                            <span className="material-symbols-outlined text-4xl mb-2">image</span>
                            <span className="text-xs font-medium">No Image Uploaded</span>
                        </div>
                    )}
                </div>

                <div className="p-5 flex flex-col gap-3">
                    <div className="flex justify-between items-start">
                        <div className="flex-1">
                            <h3 className="text-lg font-bold text-slate-900 dark:text-white leading-tight mb-1 truncate">{title || 'Untitled Dream'}</h3>
                            <p className="text-sm text-slate-500 dark:text-slate-400 line-clamp-2 min-h-[40px]">{tagline || 'Your tagline here...'}</p>
                        </div>

                    </div>

                    <div className="flex flex-wrap gap-1.5 pt-1">
                        {selectedTools.slice(0, 2).map(t => (
                            <span key={t.id} className="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-[10px] font-medium border border-slate-200 dark:border-slate-700">{t.name}</span>
                        ))}
                        {selectedTags.slice(0, 1).map(tag => (
                            <span key={tag.id} className="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-[10px] font-medium border border-slate-200 dark:border-slate-700">{tag.name}</span>
                        ))}
                        {(selectedTools.length + selectedTags.length > 3) && (
                            <span className="px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-[10px] font-medium border border-slate-200 dark:border-slate-700">+{selectedTools.length + selectedTags.length - 3}</span>
                        )}
                    </div>

                    <div className="flex items-center justify-between pt-3 mt-1 border-t border-slate-100 dark:border-slate-800">
                        <div className="flex items-center gap-2">
                            <div className="size-6 rounded-full bg-slate-200 overflow-hidden flex items-center justify-center">
                                <span className="material-symbols-outlined text-[16px] text-slate-400">person</span>
                            </div>
                            <span className="text-[10px] font-medium text-slate-600 dark:text-slate-300">@you</span>
                        </div>
                        <div className="flex items-center gap-3 text-slate-400">
                            <div className="flex items-center gap-1">
                                <span className="material-symbols-outlined text-[16px]">favorite</span>
                                <span className="text-[10px]">0</span>
                            </div>
                            <div className="flex items-center gap-1">
                                <span className="material-symbols-outlined text-[16px]">visibility</span>
                                <span className="text-[10px]">0</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="p-4 bg-blue-50 dark:bg-blue-900/10 border border-blue-100 dark:border-blue-900/30 rounded-lg">
                <p className="text-[11px] text-blue-800 dark:text-blue-300 text-center leading-relaxed">
                    <strong>Tip:</strong> Great visuals increase engagement by 40%. Try adding a video demo!
                </p>
            </div>
        </div>
    );
}

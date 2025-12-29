import type { Tool, Tag } from '~/lib/types';

interface DetailsSectionProps {
    prdText: string;
    setPrdText: (val: string) => void;
    selectedTools: Tool[];
    setSelectedTools: (tools: Tool[]) => void;
    selectedTags: Tag[];
    setSelectedTags: (tags: Tag[]) => void;
    availableTools: Tool[];
    availableTags: Tag[];
}

export default function DetailsSection({
    prdText,
    setPrdText,
    selectedTools,
    setSelectedTools,
    selectedTags,
    setSelectedTags,
    availableTools,
    availableTags
}: DetailsSectionProps) {
    const removeTool = (id: number) => setSelectedTools(selectedTools.filter(t => t.id !== id));
    const removeTag = (id: number) => setSelectedTags(selectedTags.filter(t => t.id !== id));

    return (
        <section className="bg-white dark:bg-[#1E2330] rounded-xl p-6 md:p-8 shadow-sm border border-slate-100 dark:border-slate-800">
            <h2 className="text-slate-900 dark:text-white text-xl font-bold mb-6 flex items-center gap-2">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold">3</span>
                Details
            </h2>
            <div className="flex flex-col gap-6">
                <div className="flex flex-col gap-2">
                    <label className="text-slate-700 dark:text-slate-300 text-sm font-semibold">The Story / PRD</label>
                    <div className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 overflow-hidden focus-within:ring-1 focus-within:ring-primary focus-within:border-primary transition-all">
                        <div className="flex items-center gap-1 p-2 border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-[#1E2330]">
                            <button type="button" className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400"><span className="material-symbols-outlined text-[20px]">format_bold</span></button>
                            <button type="button" className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400"><span className="material-symbols-outlined text-[20px]">format_italic</span></button>
                            <button type="button" className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400"><span className="material-symbols-outlined text-[20px]">link</span></button>
                            <div className="w-px h-4 bg-slate-300 dark:bg-slate-600 mx-1"></div>
                            <button type="button" className="p-1.5 rounded hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400"><span className="material-symbols-outlined text-[20px]">format_list_bulleted</span></button>
                        </div>
                        <textarea
                            className="w-full bg-transparent border-none p-4 text-slate-900 dark:text-white placeholder:text-slate-400 focus:ring-0 min-h-[150px] resize-y"
                            placeholder="Tell us how you built this, what models you used, and what inspired you..."
                            value={prdText}
                            onChange={(e) => setPrdText(e.target.value)}
                        />
                    </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="flex flex-col gap-3">
                        <label className="text-slate-700 dark:text-slate-300 text-sm font-semibold">Tech Stack</label>
                        <div className="flex flex-wrap gap-2">
                            {selectedTools.map(tool => (
                                <span key={tool.id} className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-primary text-white text-xs font-medium border border-transparent shadow-sm">
                                    {tool.name}
                                    <button type="button" onClick={() => removeTool(tool.id)} className="material-symbols-outlined text-[14px] hover:text-white/80 transition-colors">close</button>
                                </span>
                            ))}
                            <div className="relative group/menu">
                                <button type="button" className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs font-medium border border-slate-200 dark:border-slate-700 shadow-sm hover:border-primary hover:text-primary transition-colors">
                                    <span className="material-symbols-outlined text-[14px]">add</span>
                                    Add Tool
                                </button>
                                <div className="invisible group-hover/menu:visible absolute bottom-full left-0 mb-2 w-48 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-100 dark:border-slate-700 py-2 max-h-48 overflow-y-auto z-10">
                                    {availableTools.filter(t => !selectedTools.find(st => st.id === t.id)).map(tool => (
                                        <button
                                            key={tool.id}
                                            type="button"
                                            onClick={() => setSelectedTools([...selectedTools, tool])}
                                            className="w-full px-4 py-2 text-left text-xs hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300"
                                        >
                                            {tool.name}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="flex flex-col gap-3">
                        <label className="text-slate-700 dark:text-slate-300 text-sm font-semibold">Aesthetic Tags</label>
                        <div className="flex flex-wrap gap-2">
                            {selectedTags.map(tag => (
                                <span key={tag.id} className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-xs font-medium border border-transparent">
                                    {tag.name}
                                    <button type="button" onClick={() => removeTag(tag.id)} className="material-symbols-outlined text-[14px] hover:opacity-70 transition-opacity">close</button>
                                </span>
                            ))}
                            <div className="relative group/menu">
                                <button type="button" className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 text-xs font-medium border border-slate-200 dark:border-slate-700 shadow-sm hover:border-primary hover:text-primary transition-colors">
                                    <span className="material-symbols-outlined text-[14px]">add</span>
                                    Add Tag
                                </button>
                                <div className="invisible group-hover/menu:visible absolute bottom-full left-0 mb-2 w-48 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-100 dark:border-slate-700 py-2 max-h-48 overflow-y-auto z-10">
                                    {availableTags.filter(t => !selectedTags.find(st => st.id === t.id)).map(tag => (
                                        <button
                                            key={tag.id}
                                            type="button"
                                            onClick={() => setSelectedTags([...selectedTags, tag])}
                                            className="w-full px-4 py-2 text-left text-xs hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300"
                                        >
                                            {tag.name}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}

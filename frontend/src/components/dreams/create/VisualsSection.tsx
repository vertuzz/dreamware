import { useRef } from 'react';
import type { DreamMedia } from '~/lib/types';

interface VisualsSectionProps {
    previews: string[];
    handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
    removeFile: (index: number) => void;
    existingMedia?: DreamMedia[];
    onRemoveExisting?: (mediaId: number) => void;
}

export default function VisualsSection({
    previews,
    handleFileChange,
    removeFile,
    existingMedia = [],
    onRemoveExisting
}: VisualsSectionProps) {
    const fileInputRef = useRef<HTMLInputElement>(null);

    return (
        <section className="bg-white dark:bg-[#1E2330] rounded-xl p-6 md:p-8 shadow-sm border border-slate-100 dark:border-slate-800">
            <h2 className="text-slate-900 dark:text-white text-xl font-bold mb-6 flex items-center gap-2">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold">2</span>
                Visuals
            </h2>
            <div className="flex flex-col gap-4">
                <label className="text-slate-700 dark:text-slate-300 text-sm font-semibold">App Screenshots / Demo</label>
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileChange}
                    className="hidden"
                    multiple
                    accept="image/*"
                />
                <div
                    onClick={() => fileInputRef.current?.click()}
                    className="group relative flex flex-col items-center justify-center w-full h-64 border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-xl bg-slate-50 dark:bg-slate-900 hover:bg-primary/5 hover:border-primary transition-all cursor-pointer"
                >
                    <div className="flex flex-col items-center justify-center pt-5 pb-6">
                        <div className="mb-4 rounded-full bg-slate-100 dark:bg-slate-800 p-4 text-primary group-hover:scale-110 transition-transform">
                            <span className="material-symbols-outlined text-[32px]">cloud_upload</span>
                        </div>
                        <p className="mb-2 text-sm text-slate-700 dark:text-slate-300">
                            <span className="font-bold">Click to upload</span> or drag and drop
                        </p>
                        <p className="text-xs text-slate-500 dark:text-slate-400">SVG, PNG, JPG or GIF (MAX. 800x400px)</p>
                    </div>
                    {previews.length > 0 && (
                        <div className="absolute inset-2 rounded-lg overflow-hidden">
                            <img className="w-full h-full object-cover" src={previews[previews.length - 1]} alt="Preview" />
                        </div>
                    )}
                    {previews.length === 0 && existingMedia.length > 0 && (
                        <div className="absolute inset-2 rounded-lg overflow-hidden">
                            <img className="w-full h-full object-cover" src={existingMedia[existingMedia.length - 1].media_url} alt="Existing media" />
                        </div>
                    )}
                </div>

                {/* Existing Media Section */}
                {existingMedia.length > 0 && (
                    <div className="flex flex-col gap-2">
                        <label className="text-slate-500 dark:text-slate-400 text-xs font-semibold uppercase tracking-wider">Existing Images</label>
                        <div className="flex gap-3 overflow-x-auto py-2 scrollbar-hide">
                            {existingMedia.map((media) => (
                                <div key={media.id} className="relative min-w-[100px] h-16 rounded-lg overflow-hidden group border-2 border-slate-200 dark:border-slate-700">
                                    <img className="w-full h-full object-cover" src={media.media_url} alt="Existing" />
                                    {onRemoveExisting && (
                                        <button
                                            type="button"
                                            onClick={(e) => { e.stopPropagation(); onRemoveExisting(media.id); }}
                                            className="absolute top-1 right-1 size-5 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                                        >
                                            <span className="material-symbols-outlined text-[14px]">close</span>
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* New Uploads Section */}
                <div className="flex gap-3 overflow-x-auto py-2 scrollbar-hide">
                    {previews.map((url, idx) => (
                        <div key={idx} className="relative min-w-[100px] h-16 rounded-lg overflow-hidden group">
                            <img className="w-full h-full object-cover" src={url} alt={`Thumb ${idx}`} />
                            <button
                                type="button"
                                onClick={(e) => { e.stopPropagation(); removeFile(idx); }}
                                className="absolute top-1 right-1 size-5 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                            >
                                <span className="material-symbols-outlined text-[14px]">close</span>
                            </button>
                        </div>
                    ))}
                    <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="flex items-center justify-center min-w-[100px] h-16 rounded-lg border border-dashed border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-slate-400 hover:text-primary hover:border-primary cursor-pointer transition-colors"
                    >
                        <span className="material-symbols-outlined">add</span>
                    </button>
                </div>
            </div>
        </section>
    );
}

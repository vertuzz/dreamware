import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { dreamService } from '~/lib/services/dream-service';
import { toolService } from '~/lib/services/tool-service';
import { tagService } from '~/lib/services/tag-service';
import { mediaService } from '~/lib/services/media-service';
import type { Tool, Tag } from '~/lib/types';
import Header from '~/components/layout/Header';

// Sub-components
import BasicsSection from '~/components/dreams/create/BasicsSection';
import VisualsSection from '~/components/dreams/create/VisualsSection';
import DetailsSection from '~/components/dreams/create/DetailsSection';
import DreamPreview from '~/components/dreams/create/DreamPreview';

export default function CreateDream() {
    const navigate = useNavigate();

    // Form State
    const [title, setTitle] = useState('');
    const [appUrl, setAppUrl] = useState('');
    const [tagline, setTagline] = useState('');
    const [prdText, setPrdText] = useState('');

    // Selection state
    const [selectedTools, setSelectedTools] = useState<Tool[]>([]);
    const [selectedTags, setSelectedTags] = useState<Tag[]>([]);
    const [availableTools, setAvailableTools] = useState<Tool[]>([]);
    const [availableTags, setAvailableTags] = useState<Tag[]>([]);

    // Media State
    const [files, setFiles] = useState<File[]>([]);
    const [previews, setPreviews] = useState<string[]>([]);

    // UI State
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [tools, tags] = await Promise.all([
                    toolService.getTools(),
                    tagService.getTags()
                ]);
                setAvailableTools(tools);
                setAvailableTags(tags);
            } catch (err) {
                console.error('Failed to fetch tools/tags:', err);
            }
        };
        fetchData();
    }, []);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files) {
            const newFiles = Array.from(e.target.files);
            setFiles(prev => [...prev, ...newFiles]);

            const newPreviews = newFiles.map(file => URL.createObjectURL(file));
            setPreviews(prev => [...prev, ...newPreviews]);
        }
    };

    const removeFile = (index: number) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
        setPreviews(prev => {
            const newPreviews = [...prev];
            URL.revokeObjectURL(newPreviews[index]);
            return newPreviews.filter((_, i) => i !== index);
        });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (isSubmitting) return;

        setIsSubmitting(true);
        setError(null);

        try {
            // 1. Create the Dream
            const newDream = await dreamService.createDream({
                title,
                prompt_text: tagline,
                prd_text: prdText,
                app_url: appUrl,
                is_agent_submitted: false,
                tool_ids: selectedTools.map(t => t.id),
                tag_ids: selectedTags.map(t => t.id),
                status: appUrl ? 'Live' : 'Concept',
                extra_specs: {}
            });

            // 2. Upload Images if any
            if (files.length > 0) {
                const uploadPromises = files.map(async (file) => {
                    const { upload_url, download_url } = await mediaService.getPresignedUrl(file.name, file.type);
                    await mediaService.uploadFile(file, upload_url);
                    await mediaService.linkMediaToDream(newDream.id, download_url);
                });

                await Promise.all(uploadPromises);
            }

            // 3. Redirect to the new dream page
            navigate(`/dreams/${newDream.slug}`);
        } catch (err: any) {
            console.error('Submission failed:', err);
            setError(err.response?.data?.detail || 'Something went wrong during submission. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleBack = () => navigate(-1);

    return (
        <div className="relative flex min-h-screen w-full flex-col overflow-x-hidden bg-[var(--background)]">
            <Header />

            <main className="flex-1 w-full max-w-[1400px] mx-auto px-4 md:px-8 py-8 lg:py-12">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
                    {/* LEFT COLUMN: Form */}
                    <form onSubmit={handleSubmit} className="lg:col-span-8 flex flex-col gap-8">
                        {/* Page Heading */}
                        <div className="flex flex-col gap-2">
                            <button
                                type="button"
                                onClick={handleBack}
                                className="flex items-center gap-2 text-primary font-medium text-sm mb-1 hover:opacity-80 transition-opacity w-fit"
                            >
                                <span className="material-symbols-outlined text-[18px]">arrow_back</span>
                                <span>Back</span>
                            </button>
                            <h1 className="text-slate-900 dark:text-white text-3xl md:text-4xl font-black leading-tight tracking-tight">Submit a new Dream</h1>
                            <p className="text-slate-500 dark:text-slate-400 text-base md:text-lg">Share your AI-generated masterpiece with the world.</p>
                        </div>

                        {error && (
                            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 rounded-xl flex items-center gap-3 text-red-700 dark:text-red-400">
                                <span className="material-symbols-outlined">error</span>
                                <p className="text-sm font-medium">{error}</p>
                            </div>
                        )}

                        <BasicsSection
                            title={title}
                            setTitle={setTitle}
                            appUrl={appUrl}
                            setAppUrl={setAppUrl}
                            tagline={tagline}
                            setTagline={setTagline}
                        />

                        <VisualsSection
                            previews={previews}
                            handleFileChange={handleFileChange}
                            removeFile={removeFile}
                        />

                        <DetailsSection
                            prdText={prdText}
                            setPrdText={setPrdText}
                            selectedTools={selectedTools}
                            setSelectedTools={setSelectedTools}
                            selectedTags={selectedTags}
                            setSelectedTags={setSelectedTags}
                            availableTools={availableTools}
                            availableTags={availableTags}
                        />

                        {/* Action Bar */}
                        <div className="flex items-center justify-end gap-4 pt-4 pb-20 md:pb-0">
                            <button
                                type="button"
                                disabled={isSubmitting}
                                className="px-6 py-3 rounded-xl text-slate-600 dark:text-slate-300 font-bold hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors disabled:opacity-50"
                            >
                                Save Draft
                            </button>
                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className="px-8 py-3 rounded-xl bg-primary text-white font-bold shadow-lg shadow-primary/30 hover:shadow-primary/50 hover:bg-primary/90 transition-all flex items-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
                            >
                                {isSubmitting ? (
                                    <>
                                        <span className="size-4 size-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                                        <span>Publishing...</span>
                                    </>
                                ) : (
                                    <>
                                        <span>Publish Dream</span>
                                        <span className="material-symbols-outlined text-[20px]">rocket_launch</span>
                                    </>
                                )}
                            </button>
                        </div>
                    </form>

                    {/* RIGHT COLUMN: Sticky Preview */}
                    <div className="hidden lg:block lg:col-span-4">
                        <DreamPreview
                            title={title}
                            tagline={tagline}
                            previews={previews}
                            selectedTools={selectedTools}
                            selectedTags={selectedTags}
                        />
                    </div>
                </div>
            </main>
        </div>
    );
}

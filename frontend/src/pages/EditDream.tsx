import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { dreamService } from '~/lib/services/dream-service';
import { toolService } from '~/lib/services/tool-service';
import { tagService } from '~/lib/services/tag-service';
import { mediaService } from '~/lib/services/media-service';
import { isValidUrl, isValidYoutubeUrl } from '~/lib/utils';
import type { Tool, Tag, Dream, DreamMedia } from '~/lib/types';
import Header from '~/components/layout/Header';
import { useAuth } from '~/contexts/AuthContext';

// Sub-components
import BasicsSection from '~/components/dreams/create/BasicsSection';
import VisualsSection from '~/components/dreams/create/VisualsSection';
import DetailsSection from '~/components/dreams/create/DetailsSection';
import DreamPreview from '~/components/dreams/create/DreamPreview';

export default function EditDream() {
    const { slug } = useParams<{ slug: string }>();
    const navigate = useNavigate();
    const { user } = useAuth();

    // Original Dream state
    const [dream, setDream] = useState<Dream | null>(null);

    // Form State
    const [title, setTitle] = useState('');
    const [appUrl, setAppUrl] = useState('');
    const [youtubeUrl, setYoutubeUrl] = useState('');
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
    const [existingMedia, setExistingMedia] = useState<DreamMedia[]>([]);

    // UI State
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchData = async () => {
            if (!slug) return;
            try {
                const [tools, tags, dreamData] = await Promise.all([
                    toolService.getTools(),
                    tagService.getTags(),
                    dreamService.getDream(slug)
                ]);

                setAvailableTools(tools);
                setAvailableTags(tags);
                setDream(dreamData);

                // Pre-populate
                setTitle(dreamData.title || '');
                setAppUrl(dreamData.app_url || '');
                setYoutubeUrl(dreamData.youtube_url || '');
                setTagline(dreamData.prompt_text || '');
                setPrdText(dreamData.prd_text || '');
                setSelectedTools(dreamData.tools || []);
                setSelectedTags(dreamData.tags || []);
                setExistingMedia(dreamData.media || []);
            } catch (err) {
                console.error('Failed to fetch data:', err);
                setError('Failed to load dream data.');
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, [slug]);

    // Check ownership
    useEffect(() => {
        if (!isLoading && dream && user && dream.creator_id !== user.id) {
            navigate(`/dreams/${slug}`);
        }
    }, [isLoading, dream, user, navigate, slug]);

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

    const handleRemoveExisting = async (mediaId: number) => {
        if (!dream) return;
        try {
            await mediaService.deleteMedia(dream.id, mediaId);
            setExistingMedia(prev => prev.filter(m => m.id !== mediaId));
        } catch (err) {
            console.error('Failed to delete media:', err);
            setError('Failed to delete media. Please try again.');
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (isSubmitting || !dream) return;

        if (appUrl && !isValidUrl(appUrl)) {
            setError('Please enter a valid Live App Link.');
            return;
        }

        if (youtubeUrl && !isValidYoutubeUrl(youtubeUrl)) {
            setError('Please enter a valid YouTube URL.');
            return;
        }

        setIsSubmitting(true);
        setError(null);

        try {
            // 1. Update the Dream
            const updatedDream = await dreamService.updateDream(dream.id, {
                title,
                prompt_text: tagline,
                prd_text: prdText,
                app_url: appUrl,
                youtube_url: youtubeUrl || undefined,
                tool_ids: selectedTools.map(t => t.id),
                tag_ids: selectedTags.map(t => t.id),
                status: appUrl ? 'Live' : 'Concept',
            });

            // 2. Upload NEW Images if any
            if (files.length > 0) {
                const uploadPromises = files.map(async (file) => {
                    const { upload_url, download_url } = await mediaService.getPresignedUrl(file.name, file.type);
                    await mediaService.uploadFile(file, upload_url);
                    await mediaService.linkMediaToDream(dream.id, download_url);
                });

                await Promise.all(uploadPromises);
            }

            // 3. Redirect back to the dream page (slug might have changed if title changed, but usually we don't change slug on update to avoid broken links, or backend handles it)
            // Backend update_dream doesn't change slug.
            navigate(`/dreams/${updatedDream.slug}`);
        } catch (err: any) {
            console.error('Update failed:', err);
            setError(err.response?.data?.detail || 'Something went wrong during update. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleBack = () => navigate(-1);

    if (isLoading) return (
        <div className="min-h-screen bg-[var(--background)]">
            <Header />
            <div className="flex items-center justify-center h-[60vh]">
                <div className="size-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
            </div>
        </div>
    );

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
                            <h1 className="text-slate-900 dark:text-white text-3xl md:text-4xl font-black leading-tight tracking-tight">Edit Dream</h1>
                            <p className="text-slate-500 dark:text-slate-400 text-base md:text-lg">Refine your vision for the AI-generated masterpiece.</p>
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
                            youtubeUrl={youtubeUrl}
                            setYoutubeUrl={setYoutubeUrl}
                            tagline={tagline}
                            setTagline={setTagline}
                        />

                        <VisualsSection
                            previews={previews}
                            handleFileChange={handleFileChange}
                            removeFile={removeFile}
                            existingMedia={existingMedia}
                            onRemoveExisting={handleRemoveExisting}
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
                                onClick={handleBack}
                                disabled={isSubmitting}
                                className="px-6 py-3 rounded-xl text-slate-600 dark:text-slate-300 font-bold hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors disabled:opacity-50"
                            >
                                Cancel
                            </button>
                            <button
                                type="submit"
                                disabled={isSubmitting}
                                className="px-8 py-3 rounded-xl bg-primary text-white font-bold shadow-lg shadow-primary/30 hover:shadow-primary/50 hover:bg-primary/90 transition-all flex items-center gap-2 disabled:opacity-70 disabled:cursor-not-allowed"
                            >
                                {isSubmitting ? (
                                    <>
                                        <span className="size-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                                        <span>Saving...</span>
                                    </>
                                ) : (
                                    <>
                                        <span>Save Changes</span>
                                        <span className="material-symbols-outlined text-[20px]">save</span>
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
                            previews={previews} // Shows new uploads only for now
                            selectedTools={selectedTools}
                            selectedTags={selectedTags}
                        />
                        {existingMedia.length > 0 && (
                            <div className="mt-8 p-6 bg-white dark:bg-[var(--card)] rounded-2xl border border-[var(--border)]">
                                <h4 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">Existing Media ({existingMedia.length})</h4>
                                <div className="grid grid-cols-2 gap-3">
                                    {existingMedia.map((m) => (
                                        <div key={m.id} className="aspect-video rounded-lg overflow-hidden border border-[var(--border)] relative group">
                                            <img src={m.media_url} alt="" className="w-full h-full object-cover" />
                                            <button
                                                type="button"
                                                onClick={() => handleRemoveExisting(m.id)}
                                                className="absolute top-2 right-2 size-6 bg-red-500 text-white rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow-lg"
                                            >
                                                <span className="material-symbols-outlined text-[16px]">close</span>
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
}


interface BasicsSectionProps {
    title: string;
    setTitle: (val: string) => void;
    appUrl: string;
    setAppUrl: (val: string) => void;
    tagline: string;
    setTagline: (val: string) => void;
}

export default function BasicsSection({
    title,
    setTitle,
    appUrl,
    setAppUrl,
    tagline,
    setTagline
}: BasicsSectionProps) {
    return (
        <section className="bg-white dark:bg-[#1E2330] rounded-xl p-6 md:p-8 shadow-sm border border-slate-100 dark:border-slate-800">
            <h2 className="text-slate-900 dark:text-white text-xl font-bold mb-6 flex items-center gap-2">
                <span className="flex items-center justify-center w-6 h-6 rounded-full bg-primary/10 text-primary text-xs font-bold">1</span>
                The Basics
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="flex flex-col gap-2">
                    <label className="text-slate-700 dark:text-slate-300 text-sm font-semibold">Project Name</label>
                    <input
                        className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-4 py-3 text-base text-slate-900 dark:text-white placeholder:text-slate-400 focus:border-primary focus:ring-primary focus:ring-1 outline-none transition-all"
                        placeholder="e.g. Retro Synthwave Generator"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        required
                    />
                </div>
                <div className="flex flex-col gap-2">
                    <label className="text-slate-700 dark:text-slate-300 text-sm font-semibold">Live App Link</label>
                    <div className="relative">
                        <input
                            className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 pl-10 pr-10 py-3 text-base text-slate-900 dark:text-white placeholder:text-slate-400 focus:border-primary focus:ring-primary focus:ring-1 outline-none transition-all"
                            placeholder="https://..."
                            value={appUrl}
                            onChange={(e) => setAppUrl(e.target.value)}
                        />
                        <span className="material-symbols-outlined absolute left-3 top-3 text-slate-400 text-[20px]">link</span>
                        {appUrl && (
                            <span className="material-symbols-outlined absolute right-3 top-3 text-green-500 text-[20px]">check_circle</span>
                        )}
                    </div>
                </div>
                <div className="flex flex-col gap-2 md:col-span-2">
                    <label className="text-slate-700 dark:text-slate-300 text-sm font-semibold">Short Tagline</label>
                    <input
                        className="w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 px-4 py-3 text-base text-slate-900 dark:text-white placeholder:text-slate-400 focus:border-primary focus:ring-primary focus:ring-1 outline-none transition-all"
                        placeholder="A brief catchy description..."
                        value={tagline}
                        onChange={(e) => setTagline(e.target.value)}
                        required
                    />
                </div>
            </div>
        </section>
    );
}

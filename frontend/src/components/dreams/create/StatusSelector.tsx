import type { Dream } from '~/lib/types';

interface StatusSelectorProps {
    status: Dream['status'];
    setStatus: (status: Dream['status']) => void;
}

const statusOptions: { value: Dream['status']; label: string; icon: string; description: string; color: string }[] = [
    {
        value: 'Concept',
        label: 'Concept',
        icon: 'lightbulb',
        description: 'Just an idea or a prompt. No functional app yet.',
        color: 'bg-blue-500',
    },
    {
        value: 'WIP',
        label: 'WIP',
        icon: 'construction',
        description: 'Work in progress. Some features might be broken.',
        color: 'bg-amber-500',
    },
    {
        value: 'Live',
        label: 'Live',
        icon: 'rocket_launch',
        description: 'Fully functional and ready to be tried out.',
        color: 'bg-emerald-500',
    },
];

export default function StatusSelector({ status, setStatus }: StatusSelectorProps) {
    return (
        <div className="flex flex-col gap-4 p-6 bg-white dark:bg-[var(--card)] rounded-2xl border border-[var(--border)]">
            <div className="flex flex-col gap-1">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary">flag</span>
                    Development Status
                </h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                    Where is this project in its lifecycle?
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {statusOptions.map((option) => (
                    <button
                        key={option.value}
                        type="button"
                        onClick={() => setStatus(option.value)}
                        className={`flex flex-col gap-3 p-4 rounded-xl border-2 transition-all text-left group
                            ${status === option.value
                                ? `border-primary bg-primary/5 ring-4 ring-primary/10`
                                : 'border-slate-100 dark:border-slate-800 hover:border-slate-200 dark:hover:border-slate-700 bg-slate-50/50 dark:bg-slate-900/50'
                            }`}
                    >
                        <div className="flex items-center justify-between">
                            <div className={`size-10 rounded-lg flex items-center justify-center text-white ${option.color} shadow-lg shadow-${option.color}/20`}>
                                <span className="material-symbols-outlined">{option.icon}</span>
                            </div>
                            {status === option.value && (
                                <div className="size-6 rounded-full bg-primary text-white flex items-center justify-center">
                                    <span className="material-symbols-outlined text-[16px] font-bold">check</span>
                                </div>
                            )}
                        </div>

                        <div>
                            <div className="font-bold text-slate-900 dark:text-white">{option.label}</div>
                            <div className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mt-1">
                                {option.description}
                            </div>
                        </div>
                    </button>
                ))}
            </div>
        </div>
    );
}

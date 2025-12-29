import { useState } from 'react';

interface DreamPromptSectionProps {
    promptText: string;
}

export default function DreamPromptSection({ promptText }: DreamPromptSectionProps) {
    const [copySuccess, setCopySuccess] = useState(false);

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(promptText);
            setCopySuccess(true);
            setTimeout(() => setCopySuccess(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    return (
        <section>
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-2xl font-bold text-[var(--foreground)] flex items-center gap-2">
                    <span className="material-symbols-outlined text-primary">terminal</span>
                    System Prompt
                </h3>
                <button
                    onClick={handleCopy}
                    className="text-xs font-bold text-primary bg-primary/10 hover:bg-primary/20 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1"
                >
                    <span className="material-symbols-outlined text-sm">
                        {copySuccess ? 'check' : 'content_copy'}
                    </span>
                    {copySuccess ? 'Copied!' : 'Copy'}
                </button>
            </div>
            <div className="bg-gray-900 rounded-xl p-5 md:p-6 shadow-inner overflow-hidden relative group">
                <code className="font-mono text-sm md:text-base text-gray-300 block whitespace-pre-wrap">
                    {promptText}
                </code>
            </div>
        </section>
    );
}

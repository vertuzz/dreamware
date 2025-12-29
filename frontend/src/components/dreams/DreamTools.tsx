import type { Tool } from '~/lib/types';

interface DreamToolsProps {
    tools: Tool[];
}

export default function DreamTools({ tools }: DreamToolsProps) {
    if (!tools.length) return null;

    return (
        <section>
            <h3 className="text-2xl font-bold text-[var(--foreground)] mb-6">Stack & Tools</h3>
            <div className="flex flex-wrap gap-4">
                {tools.map((tool) => (
                    <div
                        key={tool.id}
                        className="flex items-center gap-3 px-4 py-3 bg-white dark:bg-[var(--card)] border border-[var(--border)] rounded-xl shadow-sm hover:shadow-md transition-shadow"
                    >
                        {tool.logo_url ? (
                            <img alt={tool.name} className="w-6 h-6 object-contain" src={tool.logo_url} />
                        ) : (
                            <div className="w-6 h-6 flex items-center justify-center bg-primary/10 rounded text-primary text-xs font-bold">
                                {tool.name.charAt(0).toUpperCase()}
                            </div>
                        )}
                        <span className="font-medium text-sm">{tool.name}</span>
                    </div>
                ))}
            </div>
        </section>
    );
}

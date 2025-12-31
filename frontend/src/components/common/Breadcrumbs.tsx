import { Link } from 'react-router-dom';

export interface BreadcrumbItem {
    label: string;
    to?: string;
}

interface BreadcrumbsProps {
    items: BreadcrumbItem[];
}

export function Breadcrumbs({ items }: BreadcrumbsProps) {
    return (
        <nav className="flex flex-wrap items-center gap-2 mb-8 text-sm">
            {items.map((item, index) => {
                const isLast = index === items.length - 1;

                return (
                    <div key={index} className="flex items-center gap-2">
                        {index > 0 && (
                            <span className="text-gray-300 dark:text-gray-600">/</span>
                        )}
                        {item.to && !isLast ? (
                            <Link
                                to={item.to}
                                className="text-gray-500 dark:text-gray-400 hover:text-primary transition-colors"
                            >
                                {item.label}
                            </Link>
                        ) : (
                            <span className={`font-medium ${isLast ? 'text-[var(--foreground)]' : 'text-gray-500 dark:text-gray-400'}`}>
                                {item.label}
                            </span>
                        )}
                    </div>
                );
            })}
        </nav>
    );
}

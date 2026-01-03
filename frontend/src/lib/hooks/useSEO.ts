import { useEffect } from 'react';

interface SEOOptions {
    title?: string;
    description?: string;
    image?: string;
    url?: string;
    type?: 'website' | 'article';
}

const DEFAULT_TITLE = 'Dreamware - Discover & Share AI-Powered Apps';
const DEFAULT_DESCRIPTION = 'Dreamware is the launchpad for AI-generated software. Discover innovative AI apps, share your vibe-coded creations, and find your first users.';
const DEFAULT_IMAGE = 'https://dreamware.dev/og-image.png';
const SITE_URL = 'https://dreamware.dev';

/**
 * Custom hook for updating document title and meta tags dynamically.
 * Useful for SEO on SPA pages.
 */
export function useSEO(options: SEOOptions = {}) {
    const {
        title,
        description = DEFAULT_DESCRIPTION,
        image = DEFAULT_IMAGE,
        url,
        type = 'website',
    } = options;

    useEffect(() => {
        // Update document title
        const fullTitle = title ? `${title} | Dreamware` : DEFAULT_TITLE;
        document.title = fullTitle;

        // Helper to update or create meta tag
        const updateMeta = (selector: string, content: string, attribute = 'content') => {
            let element = document.querySelector(selector) as HTMLMetaElement | null;
            if (element) {
                element.setAttribute(attribute, content);
            } else {
                element = document.createElement('meta');
                const [attrName, attrValue] = selector.replace(/[\[\]'"]/g, '').split('=');
                if (attrName && attrValue) {
                    element.setAttribute(attrName.replace('meta', '').trim(), attrValue);
                }
                element.setAttribute(attribute, content);
                document.head.appendChild(element);
            }
        };

        // Update meta description
        updateMeta('meta[name="description"]', description);
        updateMeta('meta[name="title"]', fullTitle);

        // Update Open Graph tags
        updateMeta('meta[property="og:title"]', fullTitle);
        updateMeta('meta[property="og:description"]', description);
        updateMeta('meta[property="og:image"]', image);
        updateMeta('meta[property="og:type"]', type);
        if (url) {
            updateMeta('meta[property="og:url"]', `${SITE_URL}${url}`);
        }

        // Update Twitter Card tags
        updateMeta('meta[name="twitter:title"]', fullTitle);
        updateMeta('meta[name="twitter:description"]', description);
        updateMeta('meta[name="twitter:image"]', image);
        if (url) {
            updateMeta('meta[name="twitter:url"]', `${SITE_URL}${url}`);
        }

        // Update canonical URL
        if (url) {
            let canonical = document.querySelector('link[rel="canonical"]') as HTMLLinkElement | null;
            if (canonical) {
                canonical.href = `${SITE_URL}${url}`;
            }
        }

        // Cleanup: restore defaults on unmount
        return () => {
            document.title = DEFAULT_TITLE;
        };
    }, [title, description, image, url, type]);
}

/**
 * Shorthand for just updating the page title
 */
export function usePageTitle(title: string) {
    useSEO({ title });
}

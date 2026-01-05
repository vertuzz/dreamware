/**
 * Google Analytics 4 integration
 *
 * This module provides utilities for Google Analytics tracking.
 * It initializes GA4 and provides functions for tracking events and page views.
 */

// Extend window to include gtag
declare global {
  interface Window {
    dataLayer: unknown[];
    gtag: (...args: unknown[]) => void;
  }
}

const GA_MEASUREMENT_ID = import.meta.env.VITE_GA_MEASUREMENT_ID;

/**
 * Check if GA is properly configured
 */
export const isAnalyticsEnabled = (): boolean => {
  return Boolean(GA_MEASUREMENT_ID && GA_MEASUREMENT_ID.startsWith("G-"));
};

/**
 * Initialize Google Analytics
 * Call this once when the app loads
 */
export const initializeGA = (): void => {
  if (!isAnalyticsEnabled()) {
    if (import.meta.env.DEV) {
      console.log("[Analytics] GA not configured - skipping initialization");
    }
    return;
  }

  // Initialize dataLayer
  window.dataLayer = window.dataLayer || [];

  // Define gtag function
  window.gtag = function gtag(...args: unknown[]) {
    window.dataLayer.push(args);
  };

  // Initialize GA
  window.gtag("js", new Date());
  window.gtag("config", GA_MEASUREMENT_ID, {
    send_page_view: false, // We'll handle page views manually for SPA
  });

  // Load the GA script dynamically
  const script = document.createElement("script");
  script.async = true;
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`;
  document.head.appendChild(script);

  if (import.meta.env.DEV) {
    console.log("[Analytics] Google Analytics initialized with ID:", GA_MEASUREMENT_ID);
  }
};

/**
 * Track a page view
 * Call this on route changes
 */
export const trackPageView = (path: string, title?: string): void => {
  if (!isAnalyticsEnabled() || typeof window.gtag !== "function") {
    return;
  }

  window.gtag("event", "page_view", {
    page_path: path,
    page_title: title || document.title,
    page_location: window.location.href,
  });

  if (import.meta.env.DEV) {
    console.log("[Analytics] Page view:", path);
  }
};

/**
 * Track a custom event
 */
export const trackEvent = (
  eventName: string,
  params?: Record<string, string | number | boolean>
): void => {
  if (!isAnalyticsEnabled() || typeof window.gtag !== "function") {
    return;
  }

  window.gtag("event", eventName, params);

  if (import.meta.env.DEV) {
    console.log("[Analytics] Event:", eventName, params);
  }
};

/**
 * Track user login
 */
export const trackLogin = (method: string): void => {
  trackEvent("login", { method });
};

/**
 * Track user signup
 */
export const trackSignUp = (method: string): void => {
  trackEvent("sign_up", { method });
};

/**
 * Track app creation
 */
export const trackAppCreated = (appSlug: string): void => {
  trackEvent("app_created", { app_slug: appSlug });
};

/**
 * Track app view
 */
export const trackAppView = (appSlug: string): void => {
  trackEvent("view_item", {
    item_id: appSlug,
    content_type: "app",
  });
};

/**
 * Track search
 */
export const trackSearch = (searchTerm: string): void => {
  trackEvent("search", { search_term: searchTerm });
};

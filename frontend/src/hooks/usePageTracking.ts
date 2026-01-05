import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { trackPageView } from "~/lib/analytics";

/**
 * Hook to track page views on route changes
 * Use this in your App component to automatically track all page navigations
 */
export const usePageTracking = (): void => {
  const location = useLocation();

  useEffect(() => {
    // Track page view on route change
    trackPageView(location.pathname + location.search);
  }, [location]);
};

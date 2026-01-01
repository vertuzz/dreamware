import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function isValidUrl(url: string) {
  if (!url) return true;
  try {
    // Basic pattern check before using URL constructor
    const pattern = /^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})([/\w .-]*)*\/?$/;
    if (!pattern.test(url)) return false;

    // Final check with URL constructor
    const urlToTest = url.match(/^https?:\/\//) ? url : `https://${url}`;
    new URL(urlToTest);
    return true;
  } catch (e) {
    return false;
  }
}


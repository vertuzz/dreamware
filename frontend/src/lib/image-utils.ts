import imageCompression from 'browser-image-compression';

/**
 * Compresses an image file to be under the target size (default 200KB).
 * Returns the original file if it's not an image or already under the target size.
 */
export async function compressImage(
    file: File,
    options?: {
        maxSizeMB?: number;
        maxWidthOrHeight?: number;
    }
): Promise<File> {
    // Only process image files
    if (!file.type.startsWith('image/')) {
        return file;
    }

    // Skip if already under target size (default 200KB = 0.2MB)
    const maxSizeMB = options?.maxSizeMB ?? 0.2;
    if (file.size <= maxSizeMB * 1024 * 1024) {
        return file;
    }

    const compressionOptions = {
        maxSizeMB,
        maxWidthOrHeight: options?.maxWidthOrHeight ?? 1920,
        useWebWorker: true,
        // Preserve original file type when possible
        fileType: file.type as 'image/jpeg' | 'image/png' | 'image/webp' | undefined,
    };

    try {
        const compressedFile = await imageCompression(file, compressionOptions);
        
        // Return a new File with the original name
        return new File([compressedFile], file.name, {
            type: compressedFile.type,
            lastModified: Date.now(),
        });
    } catch (error) {
        console.error('Image compression failed:', error);
        // Return original file if compression fails
        return file;
    }
}

/**
 * Compresses multiple image files in parallel
 */
export async function compressImages(
    files: File[],
    options?: {
        maxSizeMB?: number;
        maxWidthOrHeight?: number;
    }
): Promise<File[]> {
    return Promise.all(files.map(file => compressImage(file, options)));
}

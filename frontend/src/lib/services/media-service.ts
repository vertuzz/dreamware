import api from '../api';
import axios from 'axios';
import { compressImage } from '../image-utils';

export interface MediaResponse {
    upload_url: string;
    download_url: string;
    file_key: string;
}

export const mediaService = {
    getPresignedUrl: async (filename: string, contentType: string): Promise<MediaResponse> => {
        const response = await api.post('/media/presigned-url', {
            filename,
            content_type: contentType
        });
        return response.data;
    },

    /**
     * Upload a file to S3. If it's an image, it will be compressed to under 200KB first.
     */
    uploadFile: async (file: File, uploadUrl: string): Promise<void> => {
        // Compress image files before upload
        const fileToUpload = await compressImage(file);
        
        await axios.put(uploadUrl, fileToUpload, {
            headers: {
                'Content-Type': fileToUpload.type
            }
        });
    },

    linkMediaToDream: async (dreamId: number, mediaUrl: string): Promise<void> => {
        await api.post(`/dreams/${dreamId}/media`, {
            media_url: mediaUrl
        });
    },

    deleteMedia: async (dreamId: number, mediaId: number): Promise<void> => {
        await api.delete(`/dreams/${dreamId}/media/${mediaId}`);
    }
};

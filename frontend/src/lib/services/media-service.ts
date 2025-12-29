import api from '../api';
import axios from 'axios';

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

    uploadFile: async (file: File, uploadUrl: string): Promise<void> => {
        await axios.put(uploadUrl, file, {
            headers: {
                'Content-Type': file.type
            }
        });
    },

    linkMediaToDream: async (dreamId: number, mediaUrl: string): Promise<void> => {
        await api.post(`/dreams/${dreamId}/media`, {
            media_url: mediaUrl
        });
    }
};

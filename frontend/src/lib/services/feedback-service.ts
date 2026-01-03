import api from '~/lib/api';
import type { Feedback, FeedbackCreate } from '~/lib/types';

export const feedbackService = {
    async submitFeedback(data: FeedbackCreate): Promise<Feedback> {
        const response = await api.post('/feedback/', data);
        return response.data;
    },

    async listFeedback(): Promise<Feedback[]> {
        const response = await api.get('/feedback/');
        return response.data;
    },

    async deleteFeedback(id: number): Promise<void> {
        await api.delete(`/feedback/${id}`);
    }
};

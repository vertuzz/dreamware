export interface User {
    id: number;
    username: string;
    email?: string;
    full_name?: string;
    is_active: boolean;
    profile_image_url?: string;
    avatar?: string;
    bio?: string;
    reputation_score?: number;
}

export interface DreamCreator {
    id: number;
    username: string;
    avatar?: string;
}

export interface Dream {
    id: number;
    title: string;
    prompt_text?: string;
    prd_text?: string;
    extra_specs?: any;
    status: 'Concept' | 'WIP' | 'Live';
    app_url?: string;
    youtube_url?: string;
    is_agent_submitted: boolean;
    creator_id: number;
    creator?: DreamCreator;
    created_at: string;
    updated_at?: string;
    tools?: Tool[];
    tags?: Tag[];
    media?: DreamMedia[];
    likes_count?: number;
    comments_count?: number;
}

export interface Tool {
    id: number;
    name: string;
    description?: string;
    website_url?: string;
    logo_url?: string;
}

export interface Tag {
    id: number;
    name: string;
}

export interface DreamMedia {
    id: number;
    dream_id: number;
    media_url: string;
}

export interface DreamCreate {
    title: string;
    prompt_text?: string;
    prd_text?: string;
    extra_specs?: any;
    status?: string;
    app_url?: string;
    youtube_url?: string;
    is_agent_submitted?: boolean;
    tool_ids?: number[];
    tag_ids?: number[];
}

export interface Comment {
    id: number;
    dream_id: number;
    user_id: number;
    content: string;
    created_at: string;
    likes_count: number;
    user?: {
        id: number;
        username: string;
        avatar?: string;
    };
}

export interface CommentCreate {
    content: string;
}

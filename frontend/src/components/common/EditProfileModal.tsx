import { useState, useRef, useEffect } from 'react';
import { Button } from '~/components/ui/button';
import { Input } from '~/components/ui/input';
import { Label } from '~/components/ui/label';
import { userService } from '~/lib/services/user-service';
import { mediaService } from '~/lib/services/media-service';
import type { User } from '~/lib/types';
import { X, Upload, Github, Linkedin, Trash2, Loader2 } from 'lucide-react';

// Twitter/X icon component
const XIcon = ({ size = 20 }: { size?: number }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
);

interface EditProfileModalProps {
    user: User;
    isOpen: boolean;
    onClose: () => void;
    onUpdate: (updatedUser: User) => void;
}

// Social link platforms with validation patterns
const SOCIAL_PLATFORMS = [
    { 
        label: 'X', 
        icon: XIcon,
        placeholder: 'https://x.com/username',
        pattern: /^https?:\/\/(www\.)?(x\.com|twitter\.com)\/[\w]+\/?$/i,
        errorMessage: 'Please enter a valid X/Twitter URL (e.g., https://x.com/username)'
    },
    { 
        label: 'LinkedIn', 
        icon: Linkedin,
        placeholder: 'https://linkedin.com/in/username',
        pattern: /^https?:\/\/(www\.)?linkedin\.com\/(in|company)\/[\w-]+\/?$/i,
        errorMessage: 'Please enter a valid LinkedIn URL (e.g., https://linkedin.com/in/username)'
    },
    { 
        label: 'GitHub', 
        icon: Github,
        placeholder: 'https://github.com/username',
        pattern: /^https?:\/\/(www\.)?github\.com\/[\w-]+\/?$/i,
        errorMessage: 'Please enter a valid GitHub URL (e.g., https://github.com/username)'
    },
];

export default function EditProfileModal({ user, isOpen, onClose, onUpdate }: EditProfileModalProps) {
    // Form state
    const [username, setUsername] = useState(user.username);
    const [fullName, setFullName] = useState(user.full_name || '');
    const [bio, setBio] = useState(user.bio || '');
    const [location, setLocation] = useState(user.location || '');
    const [avatarPreview, setAvatarPreview] = useState<string | null>(user.avatar || null);
    const [avatarFile, setAvatarFile] = useState<File | null>(null);
    
    // Social links state - initialized from user.links
    const [socialLinks, setSocialLinks] = useState<Record<string, { id?: number; url: string }>>(() => {
        const links: Record<string, { id?: number; url: string }> = {};
        user.links?.forEach(link => {
            links[link.label] = { id: link.id, url: link.url };
        });
        return links;
    });
    
    // UI state
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [linkErrors, setLinkErrors] = useState<Record<string, string>>({});
    
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Reset form when user changes or modal opens
    useEffect(() => {
        if (isOpen) {
            setUsername(user.username);
            setFullName(user.full_name || '');
            setBio(user.bio || '');
            setLocation(user.location || '');
            setAvatarPreview(user.avatar || null);
            setAvatarFile(null);
            
            const links: Record<string, { id?: number; url: string }> = {};
            user.links?.forEach(link => {
                links[link.label] = { id: link.id, url: link.url };
            });
            setSocialLinks(links);
            setError(null);
            setLinkErrors({});
        }
    }, [isOpen, user]);

    const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            // Validate file type
            if (!file.type.startsWith('image/')) {
                setError('Please select an image file');
                return;
            }
            
            setAvatarFile(file);
            setAvatarPreview(URL.createObjectURL(file));
            setError(null);
        }
    };

    const handleSocialLinkChange = (label: string, url: string) => {
        setSocialLinks(prev => ({
            ...prev,
            [label]: { ...prev[label], url }
        }));
        
        // Clear error when user starts typing
        if (linkErrors[label]) {
            setLinkErrors(prev => {
                const next = { ...prev };
                delete next[label];
                return next;
            });
        }
    };

    const validateSocialLinks = (): boolean => {
        const errors: Record<string, string> = {};
        
        SOCIAL_PLATFORMS.forEach(platform => {
            const link = socialLinks[platform.label];
            if (link?.url && link.url.trim() !== '') {
                if (!platform.pattern.test(link.url.trim())) {
                    errors[platform.label] = platform.errorMessage;
                }
            }
        });
        
        setLinkErrors(errors);
        return Object.keys(errors).length === 0;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        if (!validateSocialLinks()) {
            return;
        }
        
        setIsSubmitting(true);
        setError(null);

        try {
            let newAvatarUrl = user.avatar;

            // Upload avatar if changed
            if (avatarFile) {
                const { upload_url, download_url } = await mediaService.getPresignedUrl(
                    avatarFile.name,
                    avatarFile.type
                );
                await mediaService.uploadFile(avatarFile, upload_url);
                newAvatarUrl = download_url;
            }

            // Update user profile
            await userService.updateUser(user.id, {
                username,
                full_name: fullName || undefined,
                bio: bio || undefined,
                location: location || undefined,
                avatar: newAvatarUrl || undefined,
            });

            // Handle social links
            const existingLinks = user.links || [];
            
            for (const platform of SOCIAL_PLATFORMS) {
                const newLink = socialLinks[platform.label];
                const existingLink = existingLinks.find(l => l.label === platform.label);
                
                if (newLink?.url && newLink.url.trim() !== '') {
                    if (existingLink) {
                        // Link exists - delete old and create new if URL changed
                        if (existingLink.url !== newLink.url.trim()) {
                            await userService.deleteUserLink(user.id, existingLink.id);
                            await userService.createUserLink(user.id, {
                                label: platform.label,
                                url: newLink.url.trim()
                            });
                        }
                    } else {
                        // Create new link
                        await userService.createUserLink(user.id, {
                            label: platform.label,
                            url: newLink.url.trim()
                        });
                    }
                } else if (existingLink) {
                    // URL was cleared - delete the link
                    await userService.deleteUserLink(user.id, existingLink.id);
                }
            }

            // Fetch updated user with links
            const refreshedUser = await userService.getUser(user.id);
            onUpdate(refreshedUser);
            onClose();
        } catch (err: any) {
            console.error('Failed to update profile:', err);
            setError(err.response?.data?.detail || 'Failed to update profile. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div 
                className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                onClick={onClose}
            />
            
            {/* Modal */}
            <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto mx-4">
                {/* Header */}
                <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between rounded-t-2xl">
                    <h2 className="text-xl font-bold text-gray-900">Edit Profile</h2>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                    >
                        <X size={20} className="text-gray-500" />
                    </button>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="p-6 space-y-6">
                    {error && (
                        <div className="bg-red-50 border border-red-200 p-4 rounded-xl text-red-700 text-sm">
                            {error}
                        </div>
                    )}

                    {/* Avatar Upload */}
                    <div className="flex flex-col items-center gap-4">
                        <div 
                            className="relative w-28 h-28 rounded-full overflow-hidden bg-gray-100 ring-4 ring-gray-50 cursor-pointer group"
                            onClick={() => fileInputRef.current?.click()}
                        >
                            {avatarPreview ? (
                                <img 
                                    src={avatarPreview} 
                                    alt="Avatar preview" 
                                    className="w-full h-full object-cover"
                                />
                            ) : (
                                <div className="w-full h-full flex items-center justify-center text-4xl font-bold text-gray-300">
                                    {username.charAt(0).toUpperCase()}
                                </div>
                            )}
                            <div className="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                                <Upload size={24} className="text-white" />
                            </div>
                        </div>
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept="image/*"
                            onChange={handleAvatarChange}
                            className="hidden"
                        />
                        <button
                            type="button"
                            onClick={() => fileInputRef.current?.click()}
                            className="text-sm text-primary font-medium hover:underline"
                        >
                            Change profile photo
                        </button>
                    </div>

                    {/* Basic Info */}
                    <div className="space-y-4">
                        <div>
                            <Label htmlFor="username" className="text-gray-700 font-semibold">Username</Label>
                            <Input
                                id="username"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                className="mt-1.5"
                                required
                            />
                        </div>

                        <div>
                            <Label htmlFor="fullName" className="text-gray-700 font-semibold">Full Name</Label>
                            <Input
                                id="fullName"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                placeholder="Your full name"
                                className="mt-1.5"
                            />
                        </div>

                        <div>
                            <Label htmlFor="bio" className="text-gray-700 font-semibold">Bio</Label>
                            <textarea
                                id="bio"
                                value={bio}
                                onChange={(e) => setBio(e.target.value)}
                                placeholder="Tell us about yourself..."
                                rows={3}
                                className="mt-1.5 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-none"
                            />
                        </div>

                        <div>
                            <Label htmlFor="location" className="text-gray-700 font-semibold">Location</Label>
                            <Input
                                id="location"
                                value={location}
                                onChange={(e) => setLocation(e.target.value)}
                                placeholder="e.g., San Francisco, CA"
                                className="mt-1.5"
                            />
                        </div>
                    </div>

                    {/* Social Links */}
                    <div className="space-y-4">
                        <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wide">Social Links</h3>
                        
                        {SOCIAL_PLATFORMS.map(platform => {
                            const IconComponent = platform.icon;
                            const linkValue = socialLinks[platform.label]?.url || '';
                            const hasError = !!linkErrors[platform.label];
                            
                            return (
                                <div key={platform.label}>
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center text-gray-600 shrink-0">
                                            <IconComponent size={20} />
                                        </div>
                                        <div className="flex-1">
                                            <Input
                                                value={linkValue}
                                                onChange={(e) => handleSocialLinkChange(platform.label, e.target.value)}
                                                placeholder={platform.placeholder}
                                                className={hasError ? 'border-red-300 focus-visible:ring-red-500' : ''}
                                            />
                                        </div>
                                        {linkValue && (
                                            <button
                                                type="button"
                                                onClick={() => handleSocialLinkChange(platform.label, '')}
                                                className="p-2 hover:bg-gray-100 rounded-lg transition-colors text-gray-400 hover:text-red-500"
                                            >
                                                <Trash2 size={18} />
                                            </button>
                                        )}
                                    </div>
                                    {hasError && (
                                        <p className="text-red-500 text-xs mt-1 ml-13 pl-13">{linkErrors[platform.label]}</p>
                                    )}
                                </div>
                            );
                        })}
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3 pt-4 border-t border-gray-100">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={onClose}
                            disabled={isSubmitting}
                            className="flex-1"
                        >
                            Cancel
                        </Button>
                        <Button
                            type="submit"
                            disabled={isSubmitting}
                            className="flex-1"
                        >
                            {isSubmitting ? (
                                <>
                                    <Loader2 size={16} className="animate-spin" />
                                    Saving...
                                </>
                            ) : (
                                'Save Changes'
                            )}
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
}

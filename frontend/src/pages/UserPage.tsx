import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { userService } from '~/lib/services/user-service';
import { dreamService } from '~/lib/services/dream-service';
import type { User, Dream } from '~/lib/types';
import DreamCard from '~/components/dreams/DreamCard';
import NotificationList from '~/components/notifications/NotificationList';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';
import { Button } from '~/components/ui/button';
import { Badge } from '~/components/ui/badge';
import { Github, Twitter, Linkedin, MapPin, Link as LinkIcon, Calendar, UserPlus, UserCheck } from 'lucide-react';
import Header from '~/components/layout/Header';
import { useAuth } from '~/contexts/AuthContext';

export default function UserPage() {
    const { username } = useParams<{ username: string }>();
    const [user, setUser] = useState<User | null>(null);
    const [dreams, setDreams] = useState<Dream[]>([]);
    const [likedDreams, setLikedDreams] = useState<Dream[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isFollowing, setIsFollowing] = useState(false);
    const [followLoading, setFollowLoading] = useState(false);
    const { user: currentUser, isAuthenticated } = useAuth();

    useEffect(() => {
        const fetchUserData = async () => {
            if (!username) return;

            try {
                setLoading(true);
                const userData = await userService.getUser(username);
                setUser(userData);

                if (userData?.id) {
                    const [userDreams, userLikedDreams] = await Promise.all([
                        dreamService.getDreams({ creator_id: userData.id }),
                        dreamService.getDreams({ liked_by_user_id: userData.id })
                    ]);
                    setDreams(userDreams);
                    setLikedDreams(userLikedDreams);
                }
            } catch (err) {
                console.error('Failed to fetch user data:', err);
                setError('User not found or failed to load.');
            } finally {
                setLoading(false);
            }
        };

        fetchUserData();
    }, [username]);

    // Fetch follow status when user and currentUser are available
    useEffect(() => {
        const fetchFollowStatus = async () => {
            if (!user?.id || !isAuthenticated || user.id === currentUser?.id) return;
            try {
                const status = await userService.checkFollowStatus(user.id);
                setIsFollowing(status.is_following);
            } catch (err) {
                console.error('Failed to fetch follow status:', err);
            }
        };
        fetchFollowStatus();
    }, [user?.id, isAuthenticated, currentUser?.id]);

    const handleFollowClick = async () => {
        if (!user?.id || !isAuthenticated) return;

        setFollowLoading(true);
        try {
            if (isFollowing) {
                await userService.unfollowUser(user.id);
                setIsFollowing(false);
            } else {
                await userService.followUser(user.id);
                setIsFollowing(true);
            }
        } catch (err) {
            console.error('Failed to update follow status:', err);
        } finally {
            setFollowLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex flex-col min-h-screen">
                <Header />
                <div className="flex-1 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                </div>
            </div>
        );
    }

    if (error || !user) {
        return (
            <div className="flex flex-col min-h-screen">
                <Header />
                <div className="flex-1 max-w-md mx-auto mt-20 text-center">
                    <h2 className="text-2xl font-bold mb-4 text-gray-900">Oops!</h2>
                    <p className="text-gray-600 mb-6">{error || 'User not found.'}</p>
                    <Button onClick={() => window.location.href = '/'}>Back to Home</Button>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col min-h-screen">
            <Header />
            <main className="flex-1 max-w-6xl mx-auto px-4 py-8 w-full">
                {/* Header Section */}
                <div className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100 mb-8 overflow-hidden relative">
                    {/* Background Decoration */}
                    <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full -mr-32 -mt-32 blur-3xl"></div>
                    <div className="absolute bottom-0 left-0 w-48 h-48 bg-purple-500/5 rounded-full -ml-24 -mb-24 blur-3xl"></div>

                    <div className="flex flex-col md:flex-row gap-8 items-start relative z-10">
                        {/* Avatar */}
                        <div className="relative">
                            <div className="w-32 h-32 md:w-40 md:h-40 rounded-3xl overflow-hidden ring-4 ring-white shadow-xl bg-gradient-to-br from-primary/20 to-purple-500/20">
                                {user.avatar ? (
                                    <img src={user.avatar} alt={user.username} className="w-full h-full object-cover" />
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center text-5xl font-bold text-primary/40">
                                        {user.username.charAt(0).toUpperCase()}
                                    </div>
                                )}
                            </div>
                            <Badge className="absolute -bottom-2 -right-2 px-3 py-1 text-sm bg-primary hover:bg-primary shadow-lg border-2 border-white">
                                {user.reputation_score || 0} Rep
                            </Badge>
                        </div>

                        {/* Info */}
                        <div className="flex-1 space-y-4">
                            <div className="flex flex-wrap items-center justify-between gap-4">
                                <div>
                                    <h1 className="text-3xl font-extrabold text-gray-900">@{user.username}</h1>
                                    <p className="text-lg text-gray-500 font-medium">{user.full_name || 'Vibe Architect'}</p>
                                </div>
                                {currentUser?.id !== user.id && (
                                    <div className="flex gap-2">
                                        <Button
                                            className="rounded-full gap-2 px-6"
                                            variant={isFollowing ? "secondary" : "default"}
                                            onClick={handleFollowClick}
                                            disabled={followLoading || !isAuthenticated}
                                        >
                                            {isFollowing ? (
                                                <><UserCheck size={18} /> Following</>
                                            ) : (
                                                <><UserPlus size={18} /> Follow</>
                                            )}
                                        </Button>
                                    </div>
                                )}
                            </div>

                            <p className="max-w-2xl text-gray-700 leading-relaxed">
                                {user.bio || 'Building the future of AI-powered dreams. Full-stack vibe coder & generative art enthusiast. Exploring the boundaries of human-AI collaboration.'}
                            </p>

                            <div className="flex flex-wrap gap-y-2 gap-x-6 text-sm text-gray-500 font-medium">
                                <div className="flex items-center gap-1.5">
                                    <MapPin size={16} className="text-gray-400" /> Remote
                                </div>
                                <div className="flex items-center gap-1.5">
                                    <LinkIcon size={16} className="text-gray-400" /> github.com/{user.username}
                                </div>
                                <div className="flex items-center gap-1.5">
                                    <Calendar size={16} className="text-gray-400" /> Joined Dec 2025
                                </div>
                            </div>

                            {/* Social Icons */}
                            <div className="flex gap-4 pt-2">
                                <a href="#" className="w-10 h-10 rounded-full bg-gray-50 flex items-center justify-center text-gray-600 hover:bg-gray-100 transition-colors border border-gray-100 shadow-sm">
                                    <Github size={20} />
                                </a>
                                <a href="#" className="w-10 h-10 rounded-full bg-gray-50 flex items-center justify-center text-gray-600 hover:bg-gray-100 transition-colors border border-gray-100 shadow-sm">
                                    <Twitter size={20} />
                                </a>
                                <a href="#" className="w-10 h-10 rounded-full bg-gray-50 flex items-center justify-center text-gray-600 hover:bg-gray-100 transition-colors border border-gray-100 shadow-sm">
                                    <Linkedin size={20} />
                                </a>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Tabs & Content */}
                <Tabs defaultValue="dreams" className="space-y-8">
                    <TabsList className="bg-transparent border-b border-gray-200 w-full justify-start h-auto p-0 gap-8">
                        <TabsTrigger
                            value="dreams"
                            className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none py-3 px-1 text-base font-semibold"
                        >
                            Dreams <span className="ml-2 text-sm text-gray-400 font-normal">{dreams.length}</span>
                        </TabsTrigger>
                        <TabsTrigger
                            value="collections"
                            className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none py-3 px-1 text-base font-semibold"
                        >
                            Collections <span className="ml-2 text-sm text-gray-400 font-normal">0</span>
                        </TabsTrigger>
                        <TabsTrigger
                            value="likes"
                            className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none py-3 px-1 text-base font-semibold"
                        >
                            Likes <span className="ml-2 text-sm text-gray-400 font-normal">{likedDreams.length}</span>
                        </TabsTrigger>
                        {currentUser?.id === user.id && (
                            <TabsTrigger
                                value="notifications"
                                className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none py-3 px-1 text-base font-semibold"
                            >
                                Notifications
                            </TabsTrigger>
                        )}
                    </TabsList>

                    <TabsContent value="dreams" className="pt-2">
                        {dreams.length > 0 ? (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                                {dreams.map((dream) => (
                                    <DreamCard key={dream.id} dream={dream} />
                                ))}
                            </div>
                        ) : (
                            <div className="bg-white rounded-3xl p-12 text-center border border-dashed border-gray-200">
                                <h3 className="text-xl font-bold text-gray-900 mb-2">No dreams yet</h3>
                                <p className="text-gray-500 mb-6">@{user.username} hasn't shared any dreams yet.</p>
                            </div>
                        )}
                    </TabsContent>

                    <TabsContent value="collections">
                        <div className="bg-white rounded-3xl p-12 text-center border border-dashed border-gray-200">
                            <h3 className="text-xl font-bold text-gray-900 mb-2">No collections yet</h3>
                            <p className="text-gray-500">@{user.username} hasn't created any public collections yet.</p>
                        </div>
                    </TabsContent>

                    <TabsContent value="likes" className="pt-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
                        {likedDreams.length > 0 ? (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                                {likedDreams.map((dream) => (
                                    <DreamCard key={dream.id} dream={dream} />
                                ))}
                            </div>
                        ) : (
                            <div className="bg-white rounded-3xl p-12 text-center border border-dashed border-gray-200">
                                <h3 className="text-xl font-bold text-gray-900 mb-2">No likes yet</h3>
                                <p className="text-gray-500">@{user.username} hasn't liked any dreams yet.</p>
                            </div>
                        )}
                    </TabsContent>

                    <TabsContent value="notifications" className="pt-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
                        <NotificationList />
                    </TabsContent>
                </Tabs>
            </main>
        </div >
    );
}

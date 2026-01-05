import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { userService } from '~/lib/services/user-service';
import { appService } from '~/lib/services/app-service';
import type { User, App } from '~/lib/types';
import AppCard from '~/components/apps/AppCard';
import NotificationList from '~/components/notifications/NotificationList';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';
import { Button } from '~/components/ui/button';
import { Badge } from '~/components/ui/badge';
import { Github, Linkedin, MapPin, Calendar, UserPlus, UserCheck } from 'lucide-react';

// X (Twitter) icon component
const XIcon = ({ size = 20 }: { size?: number }) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
);
import Header from '~/components/layout/Header';
import { useAuth } from '~/contexts/AuthContext';
import { useSEO } from '~/lib/hooks/useSEO';

export default function UserPage() {
    const { username } = useParams<{ username: string }>();
    const [user, setUser] = useState<User | null>(null);
    const [apps, setApps] = useState<App[]>([]);
    const [likedApps, setLikedApps] = useState<App[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isFollowing, setIsFollowing] = useState(false);
    const [followLoading, setFollowLoading] = useState(false);
    const { user: currentUser, isAuthenticated } = useAuth();

    // SEO - Dynamic user page title
    useSEO({
        title: user ? `@${user.username}` : username ? `@${username}` : 'User Profile',
        description: user?.bio || `Explore apps and creations by @${username} on Show Your App.`,
        url: `/users/${username}`,
    });

    useEffect(() => {
        const fetchUserData = async () => {
            if (!username) return;

            try {
                setLoading(true);
                const userData = await userService.getUser(username);
                setUser(userData);

                if (userData?.id) {
                    const [userAppsResponse, userLikedAppsResponse] = await Promise.all([
                        appService.getApps({ creator_id: userData.id }),
                        appService.getApps({ liked_by_user_id: userData.id })
                    ]);
                    setApps(userAppsResponse.apps);
                    setLikedApps(userLikedAppsResponse.apps);
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
                                    <p className="text-lg text-gray-500 font-medium">{user.full_name}</p>
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
                                {user.bio}
                            </p>

                            <div className="flex flex-wrap gap-y-2 gap-x-6 text-sm text-gray-500 font-medium">
                                {user.location && (
                                    <div className="flex items-center gap-1.5">
                                        <MapPin size={16} className="text-gray-400" /> {user.location}
                                    </div>
                                )}
                                <div className="flex items-center gap-1.5">
                                    <Calendar size={16} className="text-gray-400" /> Joined Dec 2025
                                </div>
                            </div>

                            {/* Social Icons */}
                            <div className="flex gap-4 pt-2">
                                {user.links?.find(l => l.label === 'GitHub') && (
                                    <a
                                        href={user.links.find(l => l.label === 'GitHub')!.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="w-10 h-10 rounded-full bg-gray-50 flex items-center justify-center text-gray-600 hover:bg-gray-100 transition-colors border border-gray-100 shadow-sm"
                                    >
                                        <Github size={20} />
                                    </a>
                                )}
                                {user.links?.find(l => l.label === 'X') && (
                                    <a
                                        href={user.links.find(l => l.label === 'X')!.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="w-10 h-10 rounded-full bg-gray-50 flex items-center justify-center text-gray-600 hover:bg-gray-100 transition-colors border border-gray-100 shadow-sm"
                                    >
                                        <XIcon size={20} />
                                    </a>
                                )}
                                {user.links?.find(l => l.label === 'LinkedIn') && (
                                    <a
                                        href={user.links.find(l => l.label === 'LinkedIn')!.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="w-10 h-10 rounded-full bg-gray-50 flex items-center justify-center text-gray-600 hover:bg-gray-100 transition-colors border border-gray-100 shadow-sm"
                                    >
                                        <Linkedin size={20} />
                                    </a>
                                )}
                                {(!user.links || user.links.length === 0) && (
                                    <p className="text-sm text-gray-400 italic">No social links</p>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Tabs & Content */}
                <Tabs defaultValue="apps" className="space-y-8">
                    <TabsList className="bg-transparent border-b border-gray-200 w-full justify-start h-auto p-0 gap-8">
                        <TabsTrigger
                            value="apps"
                            className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none py-3 px-1 text-base font-semibold"
                        >
                            Apps <span className="ml-2 text-sm text-gray-400 font-normal">{apps.length}</span>
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
                            Likes <span className="ml-2 text-sm text-gray-400 font-normal">{likedApps.length}</span>
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

                    <TabsContent value="apps" className="pt-2">
                        {apps.length > 0 ? (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                                {apps.map((app) => (
                                    <AppCard key={app.id} app={app} />
                                ))}
                            </div>
                        ) : (
                            <div className="bg-white rounded-3xl p-12 text-center border border-dashed border-gray-200">
                                <h3 className="text-xl font-bold text-gray-900 mb-2">No apps yet</h3>
                                <p className="text-gray-500 mb-6">@{user.username} hasn't shared any apps yet.</p>
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
                        {likedApps.length > 0 ? (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                                {likedApps.map((app) => (
                                    <AppCard key={app.id} app={app} />
                                ))}
                            </div>
                        ) : (
                            <div className="bg-white rounded-3xl p-12 text-center border border-dashed border-gray-200">
                                <h3 className="text-xl font-bold text-gray-900 mb-2">No likes yet</h3>
                                <p className="text-gray-500">@{user.username} hasn't liked any apps yet.</p>
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

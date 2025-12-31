import { useEffect, useState } from 'react';
import { useAuth } from '~/contexts/AuthContext';
import { dreamService } from '~/lib/services/dream-service';
import type { Dream } from '~/lib/types';
import DreamCard from '~/components/dreams/DreamCard';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';
import { Button } from '~/components/ui/button';
import { Badge } from '~/components/ui/badge';
import { Github, Twitter, Linkedin, Edit2, LogOut, MapPin, Link as LinkIcon, Calendar, Key, Eye, EyeOff, Copy, Check } from 'lucide-react';
import Header from '~/components/layout/Header';
import { useNavigate } from 'react-router-dom';
import { Input } from '~/components/ui/input';

export default function Profile() {
    const { user, logout, isLoading } = useAuth();
    const [dreams, setDreams] = useState<Dream[]>([]);
    const [likedDreams, setLikedDreams] = useState<Dream[]>([]);
    const [showApiKey, setShowApiKey] = useState(false);
    const [copied, setCopied] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchUserDreams = async () => {
            if (user?.id) {
                try {
                    const [userDreams, userLikedDreams] = await Promise.all([
                        dreamService.getDreams({ creator_id: user.id }),
                        dreamService.getDreams({ liked_by_user_id: user.id })
                    ]);
                    setDreams(userDreams);
                    setLikedDreams(userLikedDreams);
                } catch (err) {
                    console.error('Failed to fetch user dreams:', err);
                }
            }
        };

        if (user) {
            fetchUserDreams();
        }
    }, [user]);

    if (isLoading) {
        return (
            <div className="flex flex-col min-h-screen">
                <Header />
                <div className="flex-1 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                </div>
            </div>
        );
    }

    if (!user) {
        return (
            <div className="flex flex-col min-h-screen">
                <Header />
                <div className="flex-1 max-w-md mx-auto mt-20 text-center">
                    <h2 className="text-2xl font-bold mb-4 text-gray-900">Please login</h2>
                    <p className="text-gray-600 mb-6">You need to be authenticated to view your profile.</p>
                    <Button onClick={() => navigate('/login')}>Go to Login</Button>
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
                                <div className="flex gap-2">
                                    <Button variant="outline" size="sm" className="rounded-full gap-2">
                                        <Edit2 size={16} /> Edit Profile
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="rounded-full text-gray-500 hover:text-red-600"
                                        onClick={() => { logout(); navigate('/login'); }}
                                    >
                                        <LogOut size={16} /> Logout
                                    </Button>
                                </div>
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

                            {/* API Key Section */}
                            <div className="pt-6 border-t border-gray-100 mt-6">
                                <div className="flex flex-col space-y-3">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-2 text-sm font-bold text-gray-900">
                                            <div className="p-1.5 bg-primary/10 rounded-lg text-primary">
                                                <Key size={16} />
                                            </div>
                                            <span>AI Agent API Key</span>
                                        </div>
                                        <button
                                            onClick={() => navigate('/agent-instructions')}
                                            className="text-xs text-primary hover:underline font-semibold flex items-center gap-1"
                                        >
                                            <span className="material-symbols-outlined text-sm">help</span>
                                            How to use?
                                        </button>
                                    </div>
                                    <p className="text-sm text-gray-500">
                                        Use this key to submit dreams programmatically using the <span className="font-semibold text-primary">Dreamware AI Agent</span>.
                                        Keep it confidential to protect your account.
                                    </p>
                                    <div className="flex gap-2">
                                        <div className="relative flex-1 group">
                                            <Input
                                                type={showApiKey ? "text" : "password"}
                                                value={user.api_key || ''}
                                                readOnly
                                                className="pr-10 bg-gray-50/50 border-gray-200 text-sm font-mono h-11 rounded-xl focus:bg-white transition-all shadow-sm"
                                            />
                                            <button
                                                onClick={() => setShowApiKey(!showApiKey)}
                                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-primary transition-colors"
                                                title={showApiKey ? "Hide API Key" : "Show API Key"}
                                            >
                                                {showApiKey ? <EyeOff size={18} /> : <Eye size={18} />}
                                            </button>
                                        </div>
                                        <Button
                                            variant="outline"
                                            className="h-11 px-4 gap-2 rounded-xl border-gray-200 hover:border-primary hover:text-primary transition-all shadow-sm"
                                            onClick={() => {
                                                if (user.api_key) {
                                                    navigator.clipboard.writeText(user.api_key);
                                                    setCopied(true);
                                                    setTimeout(() => setCopied(false), 2000);
                                                }
                                            }}
                                        >
                                            {copied ? <Check size={18} className="text-green-500" /> : <Copy size={18} />}
                                            <span className="font-semibold">{copied ? 'Copied!' : 'Copy Key'}</span>
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Tabs & Content */}
                <Tabs defaultValue="dreams" className="space-y-8">
                    <TabsList className="bg-transparent border-b border-gray-200 w-full justify-start h-auto p-0 gap-8">
                        <TabsTrigger
                            value="dreams"
                            className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none py-3 px-1 text-base font-semibold transition-all"
                        >
                            Dreams <span className="ml-2 text-sm text-gray-400 font-normal">{dreams.length}</span>
                        </TabsTrigger>
                        <TabsTrigger
                            value="collections"
                            className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none py-3 px-1 text-base font-semibold transition-all"
                        >
                            Collections <span className="ml-2 text-sm text-gray-400 font-normal">0</span>
                        </TabsTrigger>
                        <TabsTrigger
                            value="likes"
                            className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent data-[state=active]:shadow-none py-3 px-1 text-base font-semibold transition-all"
                        >
                            Likes <span className="ml-2 text-sm text-gray-400 font-normal">{likedDreams.length}</span>
                        </TabsTrigger>
                    </TabsList>

                    <TabsContent value="dreams" className="pt-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
                        {dreams.length > 0 ? (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                                {dreams.map((dream) => (
                                    <DreamCard key={dream.id} dream={dream} />
                                ))}
                            </div>
                        ) : (
                            <div className="bg-white rounded-3xl p-12 text-center border border-dashed border-gray-200">
                                <h3 className="text-xl font-bold text-gray-900 mb-2">No dreams yet</h3>
                                <p className="text-gray-500 mb-6">Start your journey by creating your first AI-powered app.</p>
                                <Button onClick={() => navigate('/dreams/create')}>Submit a Dream</Button>
                            </div>
                        )}
                    </TabsContent>

                    <TabsContent value="collections" className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                        <div className="bg-white rounded-3xl p-12 text-center border border-dashed border-gray-200">
                            <h3 className="text-xl font-bold text-gray-900 mb-2">No collections yet</h3>
                            <p className="text-gray-500">You haven't created any collections of dreams yet.</p>
                        </div>
                    </TabsContent>

                    <TabsContent value="likes" className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                        {likedDreams.length > 0 ? (
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                                {likedDreams.map((dream) => (
                                    <DreamCard key={dream.id} dream={dream} />
                                ))}
                            </div>
                        ) : (
                            <div className="bg-white rounded-3xl p-12 text-center border border-dashed border-gray-200">
                                <h3 className="text-xl font-bold text-gray-900 mb-2">No likes yet</h3>
                                <p className="text-gray-500">Dreams you like will appear here.</p>
                            </div>
                        )}
                    </TabsContent>
                </Tabs>
            </main>
        </div>
    );
}

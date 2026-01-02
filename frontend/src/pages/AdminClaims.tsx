import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '~/components/layout/Header';
import { dreamService } from '~/lib/services/dream-service';
import type { OwnershipClaim } from '~/lib/types';
import { Button } from '~/components/ui/button';
import { Badge } from '~/components/ui/badge';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '~/components/ui/card';
import { useAuth } from '~/contexts/AuthContext';
import { Clock, User, Box, Check, X, ArrowUpRight, MessageSquare } from 'lucide-react';

export default function AdminClaims() {
    const { user, isLoading: authLoading } = useAuth();
    const [claims, setClaims] = useState<OwnershipClaim[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        // Redir if not admin
        if (!authLoading && (!user || !user.is_admin)) {
            navigate('/');
            return;
        }

        const fetchClaims = async () => {
            try {
                const data = await dreamService.getPendingClaims();
                setClaims(data);
            } catch (err: any) {
                console.error('Failed to fetch claims:', err);
                setError('Failed to load pending claims.');
            } finally {
                setIsLoading(false);
            }
        };

        if (user?.is_admin) {
            fetchClaims();
        }
    }, [user, authLoading, navigate]);

    const handleResolve = async (claimId: number, status: 'approved' | 'rejected') => {
        try {
            await dreamService.resolveClaim(claimId, status);
            setClaims(prev => prev.filter(c => c.id !== claimId));
            // Show some feedback? maybe just remove from list is enough
        } catch (err: any) {
            console.error(`Failed to ${status} claim:`, err);
            alert(`Failed to ${status} claim. Please try again.`);
        }
    };

    if (authLoading || (isLoading && !error)) {
        return (
            <div className="min-h-screen bg-[var(--background)]">
                <Header />
                <div className="flex items-center justify-center h-[60vh]">
                    <div className="size-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col min-h-screen bg-slate-50 dark:bg-[var(--background)]">
            <Header />
            <main className="flex-1 max-w-6xl mx-auto px-4 py-8 w-full">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                    <div>
                        <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white flex items-center gap-3">
                            <span className="p-2 bg-primary/10 text-primary rounded-xl">
                                <Box size={28} />
                            </span>
                            Ownership Claims
                        </h1>
                        <p className="text-slate-500 dark:text-slate-400 mt-2 font-medium">
                            Manage and resolve pending ownership transfer requests.
                        </p>
                    </div>
                    <Badge variant="outline" className="w-fit h-7 px-3 bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 font-bold">
                        {claims.length} Pending
                    </Badge>
                </div>

                {error && (
                    <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 rounded-2xl flex items-center gap-3 text-red-700 dark:text-red-400 mb-8">
                        <span className="material-symbols-outlined">error</span>
                        <p className="text-sm font-semibold">{error}</p>
                    </div>
                )}

                {claims.length === 0 ? (
                    <Card className="border-dashed border-2 py-12 text-center bg-white/50 dark:bg-white/5">
                        <CardContent className="flex flex-col items-center gap-4">
                            <div className="size-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center text-slate-400">
                                <Check size={32} />
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-slate-900 dark:text-white">All caught up!</h3>
                                <p className="text-slate-500 dark:text-slate-400 mt-1">There are no pending ownership claims to review.</p>
                            </div>
                        </CardContent>
                    </Card>
                ) : (
                    <div className="grid gap-6">
                        {claims.map((claim) => (
                            <Card key={claim.id} className="overflow-hidden border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-shadow bg-white dark:bg-[var(--card)]">
                                <CardHeader className="pb-4">
                                    <div className="flex flex-wrap items-start justify-between gap-4">
                                        <div className="space-y-1">
                                            <CardTitle className="text-xl font-bold text-slate-900 dark:text-white hover:text-primary transition-colors cursor-pointer flex items-center gap-2" onClick={() => navigate(`/dreams/${claim.dream?.slug}`)}>
                                                {claim.dream?.title || 'Unknown Dream'}
                                                <ArrowUpRight size={16} className="text-slate-400" />
                                            </CardTitle>
                                            <CardDescription className="flex items-center gap-4 flex-wrap text-sm font-medium">
                                                <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
                                                    <User size={14} className="text-slate-400" />
                                                    <span>Claimed by</span>
                                                    <span className="text-primary font-bold hover:underline cursor-pointer" onClick={(e) => { e.stopPropagation(); navigate(`/users/${claim.claimant?.username}`); }}>
                                                        @{claim.claimant?.username || 'unknown'}
                                                    </span>
                                                </div>
                                                <div className="flex items-center gap-1.5 text-slate-500">
                                                    <Clock size={14} className="text-slate-400" />
                                                    {new Date(claim.created_at).toLocaleDateString('en-US', {
                                                        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                                                    })}
                                                </div>
                                            </CardDescription>
                                        </div>
                                        <Badge className="bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400 border-none px-3 py-1 font-bold">
                                            {claim.status.toUpperCase()}
                                        </Badge>
                                    </div>
                                </CardHeader>
                                <CardContent className="pb-6">
                                    {claim.message && (
                                        <div className="bg-slate-50 dark:bg-slate-900/50 p-4 rounded-xl border border-slate-100 dark:border-slate-800 flex gap-3">
                                            <MessageSquare size={18} className="text-primary/60 shrink-0 mt-0.5" />
                                            <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed italic">
                                                "{claim.message}"
                                            </p>
                                        </div>
                                    )}
                                </CardContent>
                                <CardFooter className="bg-slate-50/50 dark:bg-slate-900/20 border-t border-slate-100 dark:border-slate-800 px-6 py-4 flex justify-end gap-3">
                                    <Button
                                        variant="outline"
                                        className="h-10 px-5 gap-2 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition-all font-bold"
                                        onClick={() => handleResolve(claim.id, 'rejected')}
                                    >
                                        <X size={18} />
                                        Reject
                                    </Button>
                                    <Button
                                        className="h-10 px-5 gap-2 bg-primary hover:bg-primary-dark text-white shadow-lg shadow-primary/20 transition-all font-bold"
                                        onClick={() => handleResolve(claim.id, 'approved')}
                                    >
                                        <Check size={18} />
                                        Approve Transfer
                                    </Button>
                                </CardFooter>
                            </Card>
                        ))}
                    </div>
                )}
            </main>
        </div>
    );
}

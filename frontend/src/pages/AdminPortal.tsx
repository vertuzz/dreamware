import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '~/components/layout/Header';
import { appService } from '~/lib/services/app-service';
import { tagService } from '~/lib/services/tag-service';
import { toolService } from '~/lib/services/tool-service';
import { feedbackService } from '~/lib/services/feedback-service';
import { agentService, type AgentStatus, type AgentRunResponse } from '~/lib/services/agent-service';
import type { OwnershipClaim, TagWithCount, ToolWithCount, Feedback, DeadAppReport } from '~/lib/types';
import { Button } from '~/components/ui/button';
import { Badge } from '~/components/ui/badge';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '~/components/ui/card';
import { Input } from '~/components/ui/input';
import { Textarea } from '~/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';
import { useAuth } from '~/contexts/AuthContext';
import { Clock, User, Box, Check, X, ArrowUpRight, MessageSquare, Tag, Wrench, Plus, Pencil, Trash2, AlertCircle, MessagesSquare, Link2Off, Bot, Play, Loader2 } from 'lucide-react';

export default function AdminPortal() {
    const { user, isLoading: authLoading } = useAuth();
    const navigate = useNavigate();

    // Claims state
    const [claims, setClaims] = useState<OwnershipClaim[]>([]);
    const [claimsLoading, setClaimsLoading] = useState(true);
    const [claimsError, setClaimsError] = useState<string | null>(null);

    // Tags state
    const [tags, setTags] = useState<TagWithCount[]>([]);
    const [tagsLoading, setTagsLoading] = useState(true);
    const [tagsError, setTagsError] = useState<string | null>(null);
    const [newTagName, setNewTagName] = useState('');
    const [editingTagId, setEditingTagId] = useState<number | null>(null);
    const [editingTagName, setEditingTagName] = useState('');

    // Tools state
    const [tools, setTools] = useState<ToolWithCount[]>([]);
    const [toolsLoading, setToolsLoading] = useState(true);
    const [toolsError, setToolsError] = useState<string | null>(null);
    const [newToolName, setNewToolName] = useState('');
    const [editingToolId, setEditingToolId] = useState<number | null>(null);
    const [editingToolName, setEditingToolName] = useState('');

    // Feedback state
    const [feedbackList, setFeedbackList] = useState<Feedback[]>([]);
    const [feedbackLoading, setFeedbackLoading] = useState(true);
    const [feedbackError, setFeedbackError] = useState<string | null>(null);

    // Dead reports state
    const [deadReports, setDeadReports] = useState<DeadAppReport[]>([]);
    const [deadReportsLoading, setDeadReportsLoading] = useState(true);
    const [deadReportsError, setDeadReportsError] = useState<string | null>(null);

    // Agent state
    const [agentStatus, setAgentStatus] = useState<AgentStatus | null>(null);
    const [agentPrompt, setAgentPrompt] = useState('');
    const [agentRunning, setAgentRunning] = useState(false);
    const [agentResult, setAgentResult] = useState<AgentRunResponse | null>(null);
    const [agentError, setAgentError] = useState<string | null>(null);

    useEffect(() => {
        // Redirect if not admin
        if (!authLoading && (!user || !user.is_admin)) {
            navigate('/');
            return;
        }

        if (user?.is_admin) {
            fetchClaims();
            fetchTags();
            fetchTools();
            fetchFeedback();
            fetchDeadReports();
            fetchAgentStatus();
        }
    }, [user, authLoading, navigate]);

    // Fetch functions
    const fetchAgentStatus = async () => {
        try {
            const status = await agentService.getStatus();
            setAgentStatus(status);
        } catch (err: any) {
            console.error('Failed to fetch agent status:', err);
        }
    };

    const fetchClaims = async () => {
        try {
            setClaimsLoading(true);
            const data = await appService.getPendingClaims();
            setClaims(data);
            setClaimsError(null);
        } catch (err: any) {
            console.error('Failed to fetch claims:', err);
            setClaimsError('Failed to load pending claims.');
        } finally {
            setClaimsLoading(false);
        }
    };

    const fetchTags = async () => {
        try {
            setTagsLoading(true);
            const data = await tagService.getTagsWithCounts();
            setTags(data);
            setTagsError(null);
        } catch (err: any) {
            console.error('Failed to fetch tags:', err);
            setTagsError('Failed to load tags.');
        } finally {
            setTagsLoading(false);
        }
    };

    const fetchTools = async () => {
        try {
            setToolsLoading(true);
            const data = await toolService.getToolsWithCounts();
            setTools(data);
            setToolsError(null);
        } catch (err: any) {
            console.error('Failed to fetch tools:', err);
            setToolsError('Failed to load tools.');
        } finally {
            setToolsLoading(false);
        }
    };

    const fetchFeedback = async () => {
        try {
            setFeedbackLoading(true);
            const data = await feedbackService.listFeedback();
            setFeedbackList(data);
            setFeedbackError(null);
        } catch (err: any) {
            console.error('Failed to fetch feedback:', err);
            setFeedbackError('Failed to load feedback.');
        } finally {
            setFeedbackLoading(false);
        }
    };

    const fetchDeadReports = async () => {
        try {
            setDeadReportsLoading(true);
            const data = await appService.getPendingDeadReports();
            setDeadReports(data);
            setDeadReportsError(null);
        } catch (err: any) {
            console.error('Failed to fetch dead reports:', err);
            setDeadReportsError('Failed to load dead app reports.');
        } finally {
            setDeadReportsLoading(false);
        }
    };

    // Claims handlers
    const handleResolveClaim = async (claimId: number, status: 'approved' | 'rejected') => {
        try {
            await appService.resolveClaim(claimId, status);
            setClaims(prev => prev.filter(c => c.id !== claimId));
        } catch (err: any) {
            console.error(`Failed to ${status} claim:`, err);
            alert(`Failed to ${status} claim. Please try again.`);
        }
    };

    // Tags handlers
    const handleCreateTag = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newTagName.trim()) return;

        try {
            await tagService.createTag(newTagName.trim());
            setNewTagName('');
            fetchTags();
        } catch (err: any) {
            console.error('Failed to create tag:', err);
            setTagsError(err.response?.data?.detail || 'Failed to create tag.');
        }
    };

    const handleUpdateTag = async (id: number) => {
        if (!editingTagName.trim()) return;

        try {
            await tagService.updateTag(id, editingTagName.trim());
            setEditingTagId(null);
            setEditingTagName('');
            fetchTags();
        } catch (err: any) {
            console.error('Failed to update tag:', err);
            setTagsError(err.response?.data?.detail || 'Failed to update tag.');
        }
    };

    const handleDeleteTag = async (id: number, name: string) => {
        if (!confirm(`Are you sure you want to delete the tag "${name}"? This will remove it from all apps.`)) return;

        try {
            await tagService.deleteTag(id);
            fetchTags();
        } catch (err: any) {
            console.error('Failed to delete tag:', err);
            setTagsError(err.response?.data?.detail || 'Failed to delete tag.');
        }
    };

    // Tools handlers
    const handleCreateTool = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newToolName.trim()) return;

        try {
            await toolService.createTool(newToolName.trim());
            setNewToolName('');
            fetchTools();
        } catch (err: any) {
            console.error('Failed to create tool:', err);
            setToolsError(err.response?.data?.detail || 'Failed to create tool.');
        }
    };

    const handleUpdateTool = async (id: number) => {
        if (!editingToolName.trim()) return;

        try {
            await toolService.updateTool(id, editingToolName.trim());
            setEditingToolId(null);
            setEditingToolName('');
            fetchTools();
        } catch (err: any) {
            console.error('Failed to update tool:', err);
            setToolsError(err.response?.data?.detail || 'Failed to update tool.');
        }
    };

    const handleDeleteTool = async (id: number, name: string) => {
        if (!confirm(`Are you sure you want to delete the tool "${name}"? This will remove it from all apps.`)) return;

        try {
            await toolService.deleteTool(id);
            fetchTools();
        } catch (err: any) {
            console.error('Failed to delete tool:', err);
            setToolsError(err.response?.data?.detail || 'Failed to delete tool.');
        }
    };

    // Feedback handlers
    const handleDeleteFeedback = async (id: number) => {
        if (!confirm('Are you sure you want to delete this feedback?')) return;

        try {
            await feedbackService.deleteFeedback(id);
            setFeedbackList(prev => prev.filter(f => f.id !== id));
        } catch (err: any) {
            console.error('Failed to delete feedback:', err);
            setFeedbackError(err.response?.data?.detail || 'Failed to delete feedback.');
        }
    };

    // Dead reports handlers
    const handleResolveDeadReport = async (reportId: number, status: 'confirmed' | 'dismissed') => {
        try {
            await appService.resolveDeadReport(reportId, { status });
            // Remove all reports for the same app (they're all resolved together)
            const resolvedReport = deadReports.find(r => r.id === reportId);
            if (resolvedReport) {
                setDeadReports(prev => prev.filter(r => r.app_id !== resolvedReport.app_id));
            }
        } catch (err: any) {
            console.error(`Failed to ${status} dead report:`, err);
            alert(`Failed to ${status} report. Please try again.`);
        }
    };

    // Agent handlers
    const handleRunAgent = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!agentPrompt.trim() || agentRunning) return;

        setAgentRunning(true);
        setAgentResult(null);
        setAgentError(null);

        try {
            const result = await agentService.runAgent(agentPrompt.trim());
            setAgentResult(result);
            if (!result.success && result.error) {
                setAgentError(result.error);
            }
        } catch (err: any) {
            console.error('Agent run failed:', err);
            setAgentError(err.response?.data?.detail || err.message || 'Agent execution failed');
        } finally {
            setAgentRunning(false);
        }
    };

    if (authLoading) {
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
                            Admin Portal
                        </h1>
                        <p className="text-slate-500 dark:text-slate-400 mt-2 font-medium">
                            Manage ownership claims, tags, and tools.
                        </p>
                    </div>
                </div>

                <Tabs defaultValue="claims" className="space-y-6">
                    <TabsList className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-1 h-auto">
                        <TabsTrigger value="claims" className="gap-2 px-4 py-2 data-[state=active]:bg-primary data-[state=active]:text-white">
                            <Box size={16} />
                            Claims
                            {claims.length > 0 && (
                                <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-xs">
                                    {claims.length}
                                </Badge>
                            )}
                        </TabsTrigger>
                        <TabsTrigger value="tags" className="gap-2 px-4 py-2 data-[state=active]:bg-primary data-[state=active]:text-white">
                            <Tag size={16} />
                            Tags
                            <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-xs">
                                {tags.length}
                            </Badge>
                        </TabsTrigger>
                        <TabsTrigger value="tools" className="gap-2 px-4 py-2 data-[state=active]:bg-primary data-[state=active]:text-white">
                            <Wrench size={16} />
                            Tools
                            <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-xs">
                                {tools.length}
                            </Badge>
                        </TabsTrigger>
                        <TabsTrigger value="feedback" className="gap-2 px-4 py-2 data-[state=active]:bg-primary data-[state=active]:text-white">
                            <MessagesSquare size={16} />
                            Feedback
                            <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-xs">
                                {feedbackList.length}
                            </Badge>
                        </TabsTrigger>
                        <TabsTrigger value="dead-reports" className="gap-2 px-4 py-2 data-[state=active]:bg-primary data-[state=active]:text-white">
                            <Link2Off size={16} />
                            Dead Reports
                            {deadReports.length > 0 && (
                                <Badge variant="destructive" className="ml-1 h-5 px-1.5 text-xs">
                                    {deadReports.length}
                                </Badge>
                            )}
                        </TabsTrigger>
                        <TabsTrigger value="agent" className="gap-2 px-4 py-2 data-[state=active]:bg-primary data-[state=active]:text-white">
                            <Bot size={16} />
                            Agent
                        </TabsTrigger>
                    </TabsList>

                    {/* Claims Tab */}
                    <TabsContent value="claims">
                        {claimsError && (
                            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 rounded-2xl flex items-center gap-3 text-red-700 dark:text-red-400 mb-6">
                                <AlertCircle size={18} />
                                <p className="text-sm font-semibold">{claimsError}</p>
                            </div>
                        )}

                        {claimsLoading ? (
                            <div className="flex items-center justify-center h-40">
                                <div className="size-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
                            </div>
                        ) : claims.length === 0 ? (
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
                                                    <CardTitle className="text-xl font-bold text-slate-900 dark:text-white hover:text-primary transition-colors cursor-pointer flex items-center gap-2" onClick={() => navigate(`/apps/${claim.app?.slug}`)}>
                                                        {claim.app?.title || 'Unknown App'}
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
                                                onClick={() => handleResolveClaim(claim.id, 'rejected')}
                                            >
                                                <X size={18} />
                                                Reject
                                            </Button>
                                            <Button
                                                className="h-10 px-5 gap-2 bg-primary hover:bg-primary-dark text-white shadow-lg shadow-primary/20 transition-all font-bold"
                                                onClick={() => handleResolveClaim(claim.id, 'approved')}
                                            >
                                                <Check size={18} />
                                                Approve Transfer
                                            </Button>
                                        </CardFooter>
                                    </Card>
                                ))}
                            </div>
                        )}
                    </TabsContent>

                    {/* Tags Tab */}
                    <TabsContent value="tags">
                        {tagsError && (
                            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 rounded-2xl flex items-center gap-3 text-red-700 dark:text-red-400 mb-6">
                                <AlertCircle size={18} />
                                <p className="text-sm font-semibold">{tagsError}</p>
                                <button onClick={() => setTagsError(null)} className="ml-auto text-red-500 hover:text-red-700">
                                    <X size={16} />
                                </button>
                            </div>
                        )}

                        {/* Create Tag Form */}
                        <Card className="mb-6 bg-white dark:bg-[var(--card)] border-slate-200 dark:border-slate-800">
                            <CardHeader className="pb-4">
                                <CardTitle className="text-lg font-bold flex items-center gap-2">
                                    <Plus size={18} className="text-primary" />
                                    Create New Tag
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <form onSubmit={handleCreateTag} className="flex gap-3">
                                    <Input
                                        placeholder="Enter tag name..."
                                        value={newTagName}
                                        onChange={(e) => setNewTagName(e.target.value)}
                                        className="flex-1"
                                    />
                                    <Button type="submit" className="gap-2 bg-primary hover:bg-primary-dark">
                                        <Plus size={16} />
                                        Add Tag
                                    </Button>
                                </form>
                            </CardContent>
                        </Card>

                        {/* Tags List */}
                        {tagsLoading ? (
                            <div className="flex items-center justify-center h-40">
                                <div className="size-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
                            </div>
                        ) : tags.length === 0 ? (
                            <Card className="border-dashed border-2 py-12 text-center bg-white/50 dark:bg-white/5">
                                <CardContent className="flex flex-col items-center gap-4">
                                    <div className="size-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center text-slate-400">
                                        <Tag size={32} />
                                    </div>
                                    <div>
                                        <h3 className="text-xl font-bold text-slate-900 dark:text-white">No tags yet</h3>
                                        <p className="text-slate-500 dark:text-slate-400 mt-1">Create your first tag using the form above.</p>
                                    </div>
                                </CardContent>
                            </Card>
                        ) : (
                            <Card className="bg-white dark:bg-[var(--card)] border-slate-200 dark:border-slate-800">
                                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                                    {tags.map((tag) => (
                                        <div key={tag.id} className="flex items-center justify-between p-4 hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors">
                                            {editingTagId === tag.id ? (
                                                <div className="flex items-center gap-3 flex-1">
                                                    <Input
                                                        value={editingTagName}
                                                        onChange={(e) => setEditingTagName(e.target.value)}
                                                        className="flex-1 max-w-xs"
                                                        autoFocus
                                                        onKeyDown={(e) => {
                                                            if (e.key === 'Enter') handleUpdateTag(tag.id);
                                                            if (e.key === 'Escape') {
                                                                setEditingTagId(null);
                                                                setEditingTagName('');
                                                            }
                                                        }}
                                                    />
                                                    <Button size="sm" onClick={() => handleUpdateTag(tag.id)} className="gap-1 bg-primary hover:bg-primary-dark">
                                                        <Check size={14} />
                                                        Save
                                                    </Button>
                                                    <Button size="sm" variant="outline" onClick={() => { setEditingTagId(null); setEditingTagName(''); }}>
                                                        Cancel
                                                    </Button>
                                                </div>
                                            ) : (
                                                <>
                                                    <div className="flex items-center gap-3">
                                                        <Tag size={16} className="text-slate-400" />
                                                        <span className="font-medium text-slate-900 dark:text-white">{tag.name}</span>
                                                        <Badge variant="secondary" className="text-xs">
                                                            {tag.app_count} {tag.app_count === 1 ? 'app' : 'apps'}
                                                        </Badge>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <Button
                                                            size="sm"
                                                            variant="ghost"
                                                            className="h-8 w-8 p-0 text-slate-500 hover:text-primary"
                                                            onClick={() => {
                                                                setEditingTagId(tag.id);
                                                                setEditingTagName(tag.name);
                                                            }}
                                                        >
                                                            <Pencil size={14} />
                                                        </Button>
                                                        <Button
                                                            size="sm"
                                                            variant="ghost"
                                                            className="h-8 w-8 p-0 text-slate-500 hover:text-red-600"
                                                            onClick={() => handleDeleteTag(tag.id, tag.name)}
                                                        >
                                                            <Trash2 size={14} />
                                                        </Button>
                                                    </div>
                                                </>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </Card>
                        )}
                    </TabsContent>

                    {/* Tools Tab */}
                    <TabsContent value="tools">
                        {toolsError && (
                            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 rounded-2xl flex items-center gap-3 text-red-700 dark:text-red-400 mb-6">
                                <AlertCircle size={18} />
                                <p className="text-sm font-semibold">{toolsError}</p>
                                <button onClick={() => setToolsError(null)} className="ml-auto text-red-500 hover:text-red-700">
                                    <X size={16} />
                                </button>
                            </div>
                        )}

                        {/* Create Tool Form */}
                        <Card className="mb-6 bg-white dark:bg-[var(--card)] border-slate-200 dark:border-slate-800">
                            <CardHeader className="pb-4">
                                <CardTitle className="text-lg font-bold flex items-center gap-2">
                                    <Plus size={18} className="text-primary" />
                                    Create New Tool
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <form onSubmit={handleCreateTool} className="flex gap-3">
                                    <Input
                                        placeholder="Enter tool name..."
                                        value={newToolName}
                                        onChange={(e) => setNewToolName(e.target.value)}
                                        className="flex-1"
                                    />
                                    <Button type="submit" className="gap-2 bg-primary hover:bg-primary-dark">
                                        <Plus size={16} />
                                        Add Tool
                                    </Button>
                                </form>
                            </CardContent>
                        </Card>

                        {/* Tools List */}
                        {toolsLoading ? (
                            <div className="flex items-center justify-center h-40">
                                <div className="size-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
                            </div>
                        ) : tools.length === 0 ? (
                            <Card className="border-dashed border-2 py-12 text-center bg-white/50 dark:bg-white/5">
                                <CardContent className="flex flex-col items-center gap-4">
                                    <div className="size-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center text-slate-400">
                                        <Wrench size={32} />
                                    </div>
                                    <div>
                                        <h3 className="text-xl font-bold text-slate-900 dark:text-white">No tools yet</h3>
                                        <p className="text-slate-500 dark:text-slate-400 mt-1">Create your first tool using the form above.</p>
                                    </div>
                                </CardContent>
                            </Card>
                        ) : (
                            <Card className="bg-white dark:bg-[var(--card)] border-slate-200 dark:border-slate-800">
                                <div className="divide-y divide-slate-100 dark:divide-slate-800">
                                    {tools.map((tool) => (
                                        <div key={tool.id} className="flex items-center justify-between p-4 hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors">
                                            {editingToolId === tool.id ? (
                                                <div className="flex items-center gap-3 flex-1">
                                                    <Input
                                                        value={editingToolName}
                                                        onChange={(e) => setEditingToolName(e.target.value)}
                                                        className="flex-1 max-w-xs"
                                                        autoFocus
                                                        onKeyDown={(e) => {
                                                            if (e.key === 'Enter') handleUpdateTool(tool.id);
                                                            if (e.key === 'Escape') {
                                                                setEditingToolId(null);
                                                                setEditingToolName('');
                                                            }
                                                        }}
                                                    />
                                                    <Button size="sm" onClick={() => handleUpdateTool(tool.id)} className="gap-1 bg-primary hover:bg-primary-dark">
                                                        <Check size={14} />
                                                        Save
                                                    </Button>
                                                    <Button size="sm" variant="outline" onClick={() => { setEditingToolId(null); setEditingToolName(''); }}>
                                                        Cancel
                                                    </Button>
                                                </div>
                                            ) : (
                                                <>
                                                    <div className="flex items-center gap-3">
                                                        <Wrench size={16} className="text-slate-400" />
                                                        <span className="font-medium text-slate-900 dark:text-white">{tool.name}</span>
                                                        <Badge variant="secondary" className="text-xs">
                                                            {tool.app_count} {tool.app_count === 1 ? 'app' : 'apps'}
                                                        </Badge>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <Button
                                                            size="sm"
                                                            variant="ghost"
                                                            className="h-8 w-8 p-0 text-slate-500 hover:text-primary"
                                                            onClick={() => {
                                                                setEditingToolId(tool.id);
                                                                setEditingToolName(tool.name);
                                                            }}
                                                        >
                                                            <Pencil size={14} />
                                                        </Button>
                                                        <Button
                                                            size="sm"
                                                            variant="ghost"
                                                            className="h-8 w-8 p-0 text-slate-500 hover:text-red-600"
                                                            onClick={() => handleDeleteTool(tool.id, tool.name)}
                                                        >
                                                            <Trash2 size={14} />
                                                        </Button>
                                                    </div>
                                                </>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </Card>
                        )}
                    </TabsContent>

                    {/* Feedback Tab */}
                    <TabsContent value="feedback">
                        {feedbackError && (
                            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 rounded-2xl flex items-center gap-3 text-red-700 dark:text-red-400 mb-6">
                                <AlertCircle size={18} />
                                <p className="text-sm font-semibold">{feedbackError}</p>
                                <button onClick={() => setFeedbackError(null)} className="ml-auto text-red-500 hover:text-red-700">
                                    <X size={16} />
                                </button>
                            </div>
                        )}

                        {feedbackLoading ? (
                            <div className="flex items-center justify-center h-40">
                                <div className="size-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
                            </div>
                        ) : feedbackList.length === 0 ? (
                            <Card className="border-dashed border-2 py-12 text-center bg-white/50 dark:bg-white/5">
                                <CardContent className="flex flex-col items-center gap-4">
                                    <div className="size-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center text-slate-400">
                                        <MessagesSquare size={32} />
                                    </div>
                                    <div>
                                        <h3 className="text-xl font-bold text-slate-900 dark:text-white">No feedback yet</h3>
                                        <p className="text-slate-500 dark:text-slate-400 mt-1">User feedback will appear here.</p>
                                    </div>
                                </CardContent>
                            </Card>
                        ) : (
                            <div className="grid gap-4">
                                {feedbackList.map((feedback) => (
                                    <Card key={feedback.id} className="bg-white dark:bg-[var(--card)] border-slate-200 dark:border-slate-800">
                                        <CardHeader className="pb-3">
                                            <div className="flex items-start justify-between gap-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="size-10 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center overflow-hidden">
                                                        {feedback.user?.avatar ? (
                                                            <img src={feedback.user.avatar} alt={feedback.user.username} className="w-full h-full object-cover" />
                                                        ) : (
                                                            <User size={18} className="text-slate-400" />
                                                        )}
                                                    </div>
                                                    <div>
                                                        <p className="font-semibold text-slate-900 dark:text-white">
                                                            @{feedback.user?.username || 'Unknown'}
                                                        </p>
                                                        <p className="text-xs text-slate-500 flex items-center gap-1">
                                                            <Clock size={12} />
                                                            {new Date(feedback.created_at).toLocaleDateString('en-US', {
                                                                month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit'
                                                            })}
                                                        </p>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <Badge className={
                                                        feedback.type === 'bug' 
                                                            ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400 border-none'
                                                            : feedback.type === 'feature'
                                                            ? 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400 border-none'
                                                            : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300 border-none'
                                                    }>
                                                        {feedback.type === 'bug' && '🐛 Bug'}
                                                        {feedback.type === 'feature' && '✨ Feature'}
                                                        {feedback.type === 'other' && '💬 Other'}
                                                    </Badge>
                                                    <Button
                                                        size="sm"
                                                        variant="ghost"
                                                        className="h-8 w-8 p-0 text-slate-500 hover:text-red-600"
                                                        onClick={() => handleDeleteFeedback(feedback.id)}
                                                    >
                                                        <Trash2 size={14} />
                                                    </Button>
                                                </div>
                                            </div>
                                        </CardHeader>
                                        <CardContent>
                                            <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">
                                                {feedback.message}
                                            </p>
                                        </CardContent>
                                    </Card>
                                ))}
                            </div>
                        )}
                    </TabsContent>

                    {/* Dead Reports Tab */}
                    <TabsContent value="dead-reports">
                        {deadReportsError && (
                            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 rounded-2xl flex items-center gap-3 text-red-700 dark:text-red-400 mb-6">
                                <AlertCircle size={18} />
                                <p className="text-sm font-semibold">{deadReportsError}</p>
                                <button onClick={() => setDeadReportsError(null)} className="ml-auto text-red-500 hover:text-red-700">
                                    <X size={16} />
                                </button>
                            </div>
                        )}

                        {deadReportsLoading ? (
                            <div className="flex items-center justify-center h-40">
                                <div className="size-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
                            </div>
                        ) : deadReports.length === 0 ? (
                            <Card className="border-dashed border-2 py-12 text-center bg-white/50 dark:bg-white/5">
                                <CardContent className="flex flex-col items-center gap-4">
                                    <div className="size-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center text-slate-400">
                                        <Check size={32} />
                                    </div>
                                    <div>
                                        <h3 className="text-xl font-bold text-slate-900 dark:text-white">No dead link reports</h3>
                                        <p className="text-slate-500 dark:text-slate-400 mt-1">All apps are working correctly!</p>
                                    </div>
                                </CardContent>
                            </Card>
                        ) : (
                            <div className="grid gap-6">
                                {deadReports.map((report) => (
                                    <Card key={report.id} className="overflow-hidden border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-shadow bg-white dark:bg-[var(--card)]">
                                        <CardHeader className="pb-4">
                                            <div className="flex flex-wrap items-start justify-between gap-4">
                                                <div className="space-y-1">
                                                    <CardTitle className="text-xl font-bold text-slate-900 dark:text-white hover:text-primary transition-colors cursor-pointer flex items-center gap-2" onClick={() => navigate(`/apps/${report.app?.slug}`)}>
                                                        {report.app?.title || 'Unknown App'}
                                                        <ArrowUpRight size={16} className="text-slate-400" />
                                                    </CardTitle>
                                                    <CardDescription className="flex items-center gap-4 flex-wrap text-sm font-medium">
                                                        <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
                                                            <User size={14} className="text-slate-400" />
                                                            <span>Reported by</span>
                                                            <span className="text-primary font-bold hover:underline cursor-pointer" onClick={(e) => { e.stopPropagation(); navigate(`/users/${report.reporter?.username}`); }}>
                                                                @{report.reporter?.username || 'unknown'}
                                                            </span>
                                                        </div>
                                                        <div className="flex items-center gap-1.5 text-slate-500">
                                                            <Clock size={14} className="text-slate-400" />
                                                            {new Date(report.created_at).toLocaleDateString('en-US', {
                                                                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                                                            })}
                                                        </div>
                                                    </CardDescription>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    {(report.report_count || 1) > 1 && (
                                                        <Badge className="bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-400 border-none px-3 py-1 font-bold">
                                                            {report.report_count} REPORTS
                                                        </Badge>
                                                    )}
                                                    <Badge className="bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-400 border-none px-3 py-1 font-bold">
                                                        {report.status.toUpperCase()}
                                                    </Badge>
                                                </div>
                                            </div>
                                        </CardHeader>
                                        <CardContent className="pb-6">
                                            {report.reason ? (
                                                <div className="bg-slate-50 dark:bg-slate-900/50 p-4 rounded-xl border border-slate-100 dark:border-slate-800 flex gap-3">
                                                    <MessageSquare size={18} className="text-amber-500/60 shrink-0 mt-0.5" />
                                                    <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed italic">
                                                        "{report.reason}"
                                                    </p>
                                                </div>
                                            ) : (
                                                <p className="text-slate-500 text-sm italic">No reason provided</p>
                                            )}
                                        </CardContent>
                                        <CardFooter className="bg-slate-50/50 dark:bg-slate-900/20 border-t border-slate-100 dark:border-slate-800 px-6 py-4 flex justify-end gap-3">
                                            <Button
                                                variant="outline"
                                                className="h-10 px-5 gap-2 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:bg-green-50 hover:text-green-600 hover:border-green-200 transition-all font-bold"
                                                onClick={() => handleResolveDeadReport(report.id, 'dismissed')}
                                            >
                                                <Check size={18} />
                                                App Works
                                            </Button>
                                            <Button
                                                className="h-10 px-5 gap-2 bg-red-600 hover:bg-red-700 text-white shadow-lg shadow-red-500/20 transition-all font-bold"
                                                onClick={() => handleResolveDeadReport(report.id, 'confirmed')}
                                            >
                                                <Link2Off size={18} />
                                                Confirm Dead
                                            </Button>
                                        </CardFooter>
                                    </Card>
                                ))}
                            </div>
                        )}
                    </TabsContent>

                    {/* Agent Tab */}
                    <TabsContent value="agent">
                        {agentError && (
                            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 rounded-2xl flex items-center gap-3 text-red-700 dark:text-red-400 mb-6">
                                <AlertCircle size={18} />
                                <p className="text-sm font-semibold">{agentError}</p>
                                <button onClick={() => setAgentError(null)} className="ml-auto text-red-500 hover:text-red-700">
                                    <X size={16} />
                                </button>
                            </div>
                        )}

                        {/* Agent Status */}
                        <Card className="mb-6 bg-white dark:bg-[var(--card)] border-slate-200 dark:border-slate-800">
                            <CardHeader className="pb-4">
                                <CardTitle className="text-lg font-bold flex items-center gap-2">
                                    <Bot size={18} className="text-primary" />
                                    App Submission Agent
                                </CardTitle>
                                <CardDescription>
                                    Paste a Reddit post or description of an app. The agent will visit the app, take screenshots, and create a polished listing.
                                </CardDescription>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {agentStatus && (
                                    <div className="flex items-center gap-3 p-3 bg-slate-50 dark:bg-slate-900/50 rounded-lg">
                                        <div className={`size-3 rounded-full ${agentStatus.configured ? 'bg-green-500' : 'bg-red-500'}`} />
                                        <span className="text-sm text-slate-600 dark:text-slate-400">
                                            {agentStatus.configured ? (
                                                <>Model: <span className="font-mono text-slate-900 dark:text-white">{agentStatus.model}</span></>
                                            ) : (
                                                'Agent not configured. Set AGENT_API_KEY environment variable.'
                                            )}
                                        </span>
                                    </div>
                                )}

                                <form onSubmit={handleRunAgent} className="space-y-4">
                                    <Textarea
                                        placeholder="Paste the Reddit post, tweet, or description of an app here...

Example:
Check out this cool app I built! It's a virtual AI pet that learns your habits.
Live at: https://pixelpet.app

Built with Claude and React. Features include:
- Customizable pet appearance
- Daily mood tracking
- Mini games"
                                        value={agentPrompt}
                                        onChange={(e) => setAgentPrompt(e.target.value)}
                                        className="min-h-[200px] font-mono text-sm"
                                        disabled={agentRunning || !agentStatus?.configured}
                                    />
                                    <Button
                                        type="submit"
                                        className="gap-2 bg-primary hover:bg-primary-dark"
                                        disabled={agentRunning || !agentStatus?.configured || !agentPrompt.trim()}
                                    >
                                        {agentRunning ? (
                                            <>
                                                <Loader2 size={16} className="animate-spin" />
                                                Running Agent...
                                            </>
                                        ) : (
                                            <>
                                                <Play size={16} />
                                                Run Agent
                                            </>
                                        )}
                                    </Button>
                                </form>
                            </CardContent>
                        </Card>

                        {/* Agent Result */}
                        {agentResult && (
                            <Card className="bg-white dark:bg-[var(--card)] border-slate-200 dark:border-slate-800">
                                <CardHeader className="pb-4">
                                    <CardTitle className="text-lg font-bold flex items-center gap-2">
                                        {agentResult.success ? (
                                            <Check size={18} className="text-green-500" />
                                        ) : (
                                            <X size={18} className="text-red-500" />
                                        )}
                                        {agentResult.success ? 'Agent Completed' : 'Agent Failed'}
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    {agentResult.app_ids.length > 0 && (
                                        <div className="flex flex-wrap gap-2">
                                            <span className="text-sm text-slate-600 dark:text-slate-400">Created apps:</span>
                                            {agentResult.app_ids.map(id => (
                                                <Badge
                                                    key={id}
                                                    className="bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-400 border-none cursor-pointer hover:bg-green-200"
                                                    onClick={() => navigate(`/apps/${id}`)}
                                                >
                                                    App #{id} <ArrowUpRight size={12} className="ml-1" />
                                                </Badge>
                                            ))}
                                        </div>
                                    )}
                                    {agentResult.result && (
                                        <div className="bg-slate-50 dark:bg-slate-900/50 p-4 rounded-xl border border-slate-100 dark:border-slate-800">
                                            <pre className="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap font-mono">
                                                {agentResult.result}
                                            </pre>
                                        </div>
                                    )}
                                    {agentResult.error && (
                                        <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-xl border border-red-100 dark:border-red-800">
                                            <pre className="text-sm text-red-700 dark:text-red-300 whitespace-pre-wrap">
                                                {agentResult.error}
                                            </pre>
                                        </div>
                                    )}
                                </CardContent>
                            </Card>
                        )}
                    </TabsContent>
                </Tabs>
            </main>
        </div>
    );
}

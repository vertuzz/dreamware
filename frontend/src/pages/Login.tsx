import { useState, useEffect } from 'react';
import { authService } from '~/lib/services/auth-service';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Button } from '~/components/ui/button';
import { Input } from '~/components/ui/input';
import { Label } from '~/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '~/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '~/components/ui/tabs';
import { Github } from 'lucide-react';

export default function Login() {
    const [searchParams] = useSearchParams();
    const initialTab = searchParams.get('mode') === 'signup' ? 'signup' : 'login';
    const [activeTab, setActiveTab] = useState(initialTab);
    const [loginData, setLoginData] = useState({ username: '', password: '' });
    const [signupData, setSignupData] = useState({ username: '', email: '', password: '' });
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        const mode = searchParams.get('mode');
        if (mode === 'signup' || mode === 'login') {
            setActiveTab(mode);
        }
    }, [searchParams]);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            await authService.login(loginData);
            navigate('/profile');
        } catch (err: any) {
            console.error(err);
            alert(err.response?.data?.detail || 'Login failed');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSignup = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            await authService.signup(signupData);
            // After signup, automatically log in
            await authService.login({ username: signupData.username, password: signupData.password });
            navigate('/profile');
        } catch (err: any) {
            console.error(err);
            alert(err.response?.data?.detail || 'Signup failed');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSocialLogin = (provider: 'google' | 'github') => {
        // FLOW:
        // 1. Redirect user to Google/GitHub OAuth page
        // 2. User authenticates and is redirected back with a 'code'
        // 3. Frontend catches 'code' and calls authService.googleLogin(code) or githubLogin(code)
        // For now, we just alert since we need the OAUTH_CLIENT_ID from backend env
        alert(`Redirecting to ${provider} login... This requires setting up OAuth applications and redirecting to their auth URL.`);
    };

    return (
        <div className="min-h-screen grid lg:grid-cols-2">
            {/* Left Side: Visual Branding */}
            <div className="hidden lg:flex flex-col justify-between p-12 bg-primary text-primary-foreground relative overflow-hidden">
                <div className="relative z-10">
                    <h1 className="text-4xl font-bold mb-6 italic tracking-tight">Dreamware</h1>
                    <div className="space-y-4 max-w-md">
                        <p className="text-xl opacity-90">
                            The "itch.io for AI Apps" – a launchpad and showcase platform for AI-generated software.
                        </p>
                        <p className="text-lg opacity-75">
                            Join the vibe coding revolution. Ship your dreams, get feedback, and find your first 100 users.
                        </p>
                    </div>
                </div>

                <div className="relative z-10">
                    <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
                            <span className="material-symbols-outlined">rocket_launch</span>
                        </div>
                        <div>
                            <p className="font-semibold text-sm">Join 1,000+ creators</p>
                            <p className="text-xs opacity-75">Shipping AI toys every day</p>
                        </div>
                    </div>
                </div>

                {/* Decorative background elements */}
                <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-white/10 rounded-full blur-3xl" />
                <div className="absolute top-1/4 -right-12 w-64 h-64 bg-white/5 rounded-full blur-2xl" />
            </div>

            {/* Right Side: Auth Forms */}
            <div className="flex items-center justify-center p-6 bg-background">
                <Card className="w-full max-w-md border-none shadow-none lg:shadow-sm lg:border">
                    <CardHeader className="space-y-1">
                        <CardTitle className="text-2xl font-bold">Welcome to Dreamware</CardTitle>
                        <CardDescription>
                            Sign in to your account or create a new one to start shipping.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                            <TabsList className="grid w-full grid-cols-2 mb-8">
                                <TabsTrigger value="login">Login</TabsTrigger>
                                <TabsTrigger value="signup">Sign Up</TabsTrigger>
                            </TabsList>

                            <TabsContent value="login">
                                <form onSubmit={handleLogin} className="space-y-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="username">Username</Label>
                                        <Input
                                            id="username"
                                            placeholder="johndoe"
                                            value={loginData.username}
                                            onChange={(e) => setLoginData({ ...loginData, username: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <div className="flex items-center justify-between">
                                            <Label htmlFor="password">Password</Label>
                                            <button type="button" className="text-xs text-primary hover:underline">
                                                Forgot password?
                                            </button>
                                        </div>
                                        <Input
                                            id="password"
                                            type="password"
                                            value={loginData.password}
                                            onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <Button type="submit" className="w-full" disabled={isLoading}>
                                        {isLoading ? 'Logging in...' : 'Login'}
                                    </Button>
                                </form>
                            </TabsContent>

                            <TabsContent value="signup">
                                <form onSubmit={handleSignup} className="space-y-4">
                                    <div className="space-y-2">
                                        <Label htmlFor="signup-username">Username</Label>
                                        <Input
                                            id="signup-username"
                                            placeholder="johndoe"
                                            value={signupData.username}
                                            onChange={(e) => setSignupData({ ...signupData, username: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="email">Email</Label>
                                        <Input
                                            id="email"
                                            type="email"
                                            placeholder="john@example.com"
                                            value={signupData.email}
                                            onChange={(e) => setSignupData({ ...signupData, email: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label htmlFor="signup-password">Password</Label>
                                        <Input
                                            id="signup-password"
                                            type="password"
                                            value={signupData.password}
                                            onChange={(e) => setSignupData({ ...signupData, password: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <Button type="submit" className="w-full" disabled={isLoading}>
                                        {isLoading ? 'Creating account...' : 'Create Account'}
                                    </Button>
                                </form>
                            </TabsContent>
                        </Tabs>

                        <div className="relative my-8">
                            <div className="absolute inset-0 flex items-center">
                                <span className="w-full border-t" />
                            </div>
                            <div className="relative flex justify-center text-xs uppercase">
                                <span className="bg-background px-2 text-muted-foreground">Or continue with</span>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <Button variant="outline" type="button" onClick={() => handleSocialLogin('github')} disabled={isLoading}>
                                <Github className="mr-2 h-4 w-4" />
                                GitHub
                            </Button>
                            <Button variant="outline" type="button" onClick={() => handleSocialLogin('google')} disabled={isLoading}>
                                <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
                                    <path
                                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                                        fill="#4285F4"
                                    />
                                    <path
                                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                                        fill="#34A853"
                                    />
                                    <path
                                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                                        fill="#FBBC05"
                                    />
                                    <path
                                        d="M12 5.38c1.62 0 3.06.56 4.21 1.66l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                                        fill="#EA4335"
                                    />
                                </svg>
                                Google
                            </Button>
                        </div>
                    </CardContent>
                    <CardFooter className="flex flex-col gap-4">
                        <p className="text-center text-sm text-muted-foreground px-8">
                            By clicking continue, you agree to our{' '}
                            <button className="underline underline-offset-4 hover:text-primary">Terms of Service</button> and{' '}
                            <button className="underline underline-offset-4 hover:text-primary">Privacy Policy</button>.
                        </p>
                    </CardFooter>
                </Card>
            </div>
        </div>
    );
}

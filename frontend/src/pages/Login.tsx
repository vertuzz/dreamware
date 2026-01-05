import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '~/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '~/components/ui/card';
import { Github } from 'lucide-react';
import Header from '~/components/layout/Header';
import { usePageTitle } from '~/lib/hooks/useSEO';
import { useAuth } from '~/contexts/AuthContext';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;
const GITHUB_CLIENT_ID = import.meta.env.VITE_GITHUB_CLIENT_ID;

// OAuth popup dimensions
const POPUP_WIDTH = 500;
const POPUP_HEIGHT = 600;

export default function Login() {
    const [isLoading, setIsLoading] = useState(false);
    const { loginWithGoogle, loginWithGithub, isAuthenticated } = useAuth();
    const navigate = useNavigate();
    const popupRef = useRef<Window | null>(null);

    // SEO
    usePageTitle('Sign In');

    // Redirect if already authenticated
    useEffect(() => {
        if (isAuthenticated) {
            navigate('/');
        }
    }, [isAuthenticated, navigate]);

    // Listen for OAuth callback messages from popup
    useEffect(() => {
        let isProcessing = false;
        
        const handleMessage = async (event: MessageEvent) => {
            // Only accept messages from our own origin
            if (event.origin !== window.location.origin) return;
            
            const { type, code, provider, error } = event.data;
            
            if (type !== 'oauth-callback') return;
            
            // Prevent duplicate message handling
            if (isProcessing) return;
            isProcessing = true;

            if (error) {
                alert(`Login failed: ${error}`);
                setIsLoading(false);
                isProcessing = false;
                return;
            }

            if (code && provider) {
                try {
                    if (provider === 'google') {
                        await loginWithGoogle(code);
                    } else if (provider === 'github') {
                        await loginWithGithub(code);
                    }
                    navigate('/');
                } catch (err) {
                    console.error('OAuth login error:', err);
                    alert('Failed to complete login. Please try again.');
                    isProcessing = false;
                    setIsLoading(false);
                }
            }
        };

        window.addEventListener('message', handleMessage);
        return () => window.removeEventListener('message', handleMessage);
    }, [loginWithGoogle, loginWithGithub, navigate]);

    const openOAuthPopup = (url: string, provider: string) => {
        // Calculate popup position (centered)
        const left = window.screenX + (window.outerWidth - POPUP_WIDTH) / 2;
        const top = window.screenY + (window.outerHeight - POPUP_HEIGHT) / 2;

        // Close existing popup if open
        if (popupRef.current && !popupRef.current.closed) {
            popupRef.current.close();
        }

        // Open popup
        popupRef.current = window.open(
            url,
            `${provider}-oauth`,
            `width=${POPUP_WIDTH},height=${POPUP_HEIGHT},left=${left},top=${top},popup=yes`
        );

        // Check if popup was blocked
        if (!popupRef.current) {
            alert('Popup was blocked. Please allow popups for this site.');
            setIsLoading(false);
            return;
        }

        // Poll to detect if popup was closed without completing auth
        const pollTimer = setInterval(() => {
            if (popupRef.current?.closed) {
                clearInterval(pollTimer);
                setIsLoading(false);
            }
        }, 500);
    };

    const handleSocialLogin = (provider: 'google' | 'github') => {
        setIsLoading(true);

        if (provider === 'google') {
            if (!GOOGLE_CLIENT_ID) {
                alert('Google OAuth is not configured. Please set VITE_GOOGLE_CLIENT_ID.');
                setIsLoading(false);
                return;
            }
            const redirectUri = `${window.location.origin}/auth/callback`;
            const scope = 'email profile';
            const googleAuthUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${GOOGLE_CLIENT_ID}&redirect_uri=${encodeURIComponent(redirectUri)}&response_type=code&scope=${encodeURIComponent(scope)}&state=google`;
            openOAuthPopup(googleAuthUrl, 'google');
        } else if (provider === 'github') {
            if (!GITHUB_CLIENT_ID) {
                alert('GitHub OAuth is not configured. Please set VITE_GITHUB_CLIENT_ID.');
                setIsLoading(false);
                return;
            }
            const redirectUri = `${window.location.origin}/auth/callback`;
            const scope = 'user:email';
            const githubAuthUrl = `https://github.com/login/oauth/authorize?client_id=${GITHUB_CLIENT_ID}&redirect_uri=${encodeURIComponent(redirectUri)}&scope=${encodeURIComponent(scope)}&state=github`;
            openOAuthPopup(githubAuthUrl, 'github');
        }
    };

    return (
        <div className="flex flex-col min-h-screen">
            <Header />
            <div className="flex-1 grid lg:grid-cols-2">
                {/* Left Side: Visual Branding */}
                <div className="hidden lg:flex flex-col justify-between p-12 bg-primary text-primary-foreground relative overflow-hidden">
                    <div className="relative z-10">
                        <h1 className="text-4xl font-bold mb-6 italic tracking-tight">Show Your App</h1>
                        <div className="space-y-4 max-w-md">
                            <p className="text-xl opacity-90">
                                A launchpad and showcase platform for AI-generated software.
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

                {/* Right Side: Auth */}
                <div className="flex items-center justify-center p-6 bg-background">
                    <Card className="w-full max-w-md border-none shadow-none lg:shadow-sm lg:border">
                        <CardHeader className="space-y-1">
                            <CardTitle className="text-2xl font-bold">Welcome to Show Your App</CardTitle>
                            <CardDescription>
                                Sign in with your GitHub or Google account to start shipping.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="grid gap-4">
                                <Button 
                                    variant="outline" 
                                    size="lg" 
                                    type="button" 
                                    onClick={() => handleSocialLogin('github')} 
                                    disabled={isLoading}
                                    className="w-full"
                                >
                                    <Github className="mr-2 h-5 w-5" />
                                    Continue with GitHub
                                </Button>
                                <Button 
                                    variant="outline" 
                                    size="lg" 
                                    type="button" 
                                    onClick={() => handleSocialLogin('google')} 
                                    disabled={isLoading}
                                    className="w-full"
                                >
                                    <svg className="mr-2 h-5 w-5" viewBox="0 0 24 24">
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
                                    Continue with Google
                                </Button>
                            </div>

                            <div className="relative">
                                <div className="absolute inset-0 flex items-center">
                                    <span className="w-full border-t" />
                                </div>
                                <div className="relative flex justify-center text-xs uppercase">
                                    <span className="bg-background px-2 text-muted-foreground">Secure authentication</span>
                                </div>
                            </div>

                            <p className="text-center text-sm text-muted-foreground">
                                We use OAuth for secure authentication. No passwords to remember!
                            </p>
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
        </div>
    );
}

import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User } from '../lib/types';
import { authService } from '../lib/services/auth-service';

interface AuthContextType {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    login: (credentials: any) => Promise<void>;
    logout: () => void;
    checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
    const [isLoading, setIsLoading] = useState(true);

    const checkAuth = async () => {
        const storedToken = localStorage.getItem('token');
        if (storedToken) {
            try {
                const userData = await authService.getMe();
                setUser(userData);
                setToken(storedToken);
            } catch (error) {
                console.error('Failed to fetch user:', error);
                localStorage.removeItem('token');
                setUser(null);
                setToken(null);
            }
        } else {
            setUser(null);
            setToken(null);
        }
        setIsLoading(false);
    };

    useEffect(() => {
        checkAuth();
    }, []);

    const login = async (credentials: any) => {
        const data = await authService.login(credentials);
        if (data.access_token) {
            setToken(data.access_token);
            const userData = await authService.getMe();
            setUser(userData);
        }
    };

    const logout = () => {
        authService.logout();
        setUser(null);
        setToken(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, isLoading, login, logout, checkAuth }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

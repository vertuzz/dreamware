import { useEffect, useState } from 'react';
import { userService } from '~/lib/services/user-service';
import type { Notification } from '~/lib/types';
import { Button } from '~/components/ui/button';
import { Bell, UserPlus, Heart, MessageCircle, Code, CheckCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

function timeAgo(dateString: string) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    let interval = seconds / 31536000;
    if (interval > 1) return Math.floor(interval) + "y ago";
    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + "mo ago";
    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + "d ago";
    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + "h ago";
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + "m ago";
    return "just now";
}

export default function NotificationList() {
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchNotifications();
    }, []);

    const fetchNotifications = async () => {
        try {
            const data = await userService.getNotifications();
            setNotifications(data);
        } catch (error) {
            console.error('Failed to fetch notifications', error);
        } finally {
            setLoading(false);
        }
    };

    const markAsRead = async (id: number) => {
        try {
            await userService.markNotificationRead(id);
            setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
        } catch (error) {
            console.error('Failed to mark as read', error);
        }
    };

    const markAllRead = async () => {
        try {
            await userService.markAllNotificationsRead();
            setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
        } catch (error) {
            console.error('Failed to mark all as read', error);
        }
    };

    const getIcon = (type: string) => {
        switch (type.toLowerCase()) {
            case 'like': return <Heart className="text-red-500 fill-red-50" size={20} />;
            case 'comment': return <MessageCircle className="text-blue-500 fill-blue-50" size={20} />;
            case 'follow': return <UserPlus className="text-purple-500 fill-purple-50" size={20} />;
            case 'implementation': return <Code className="text-green-500 fill-green-50" size={20} />;
            default: return <Bell className="text-gray-500 fill-gray-50" size={20} />;
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center p-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        );
    }

    if (notifications.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-12 text-center bg-white rounded-3xl border border-dashed border-gray-200">
                <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mb-4">
                    <Bell className="text-gray-400" size={32} />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">No notifications</h3>
                <p className="text-gray-500">You're all caught up!</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="flex justify-between items-center mb-4 px-1">
                <h3 className="text-lg font-bold text-gray-900">Recent Activity</h3>
                <Button variant="ghost" size="sm" onClick={markAllRead} className="text-gray-500 hover:text-primary h-8">
                    <CheckCheck size={16} className="mr-2" /> Mark all read
                </Button>
            </div>
            <div className="space-y-3">
                {notifications.map((notification) => (
                    <div
                        key={notification.id}
                        className={`group p-4 rounded-xl border transition-all cursor-pointer relative overflow-hidden ${notification.is_read
                            ? 'bg-white border-gray-100 opacity-70 hover:opacity-100 hover:border-gray-200'
                            : 'bg-blue-50/30 border-blue-100 shadow-sm hover:shadow-md hover:bg-white'
                            }`}
                        onClick={() => !notification.is_read && markAsRead(notification.id)}
                    >
                        <div className="flex items-start gap-4">
                            <div className={`mt-1 p-2 rounded-full shadow-sm flex-shrink-0 ${notification.is_read ? 'bg-gray-50' : 'bg-white ring-2 ring-white'}`}>
                                {getIcon(notification.type)}
                            </div>
                            <div className="flex-1 min-w-0">
                                <p className="text-gray-900 font-medium truncate pr-6">
                                    {notification.link ? (
                                        <Link
                                            to={notification.link}
                                            className="hover:underline decoration-primary decoration-2 underline-offset-2"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                if (!notification.is_read) markAsRead(notification.id);
                                            }}
                                        >
                                            {notification.content}
                                        </Link>
                                    ) : (
                                        notification.content
                                    )}
                                </p>
                                <span className="text-xs text-gray-500 block mt-1">
                                    {timeAgo(notification.created_at)}
                                </span>
                            </div>
                            {!notification.is_read && (
                                <div className="absolute top-4 right-4 w-2.5 h-2.5 bg-primary rounded-full shadow-sm ring-2 ring-white"></div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

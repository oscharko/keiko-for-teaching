'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  MessageSquare,
  Lightbulb,
  Newspaper,
  Upload,
  Settings,
  PlayCircle,
  Home,
} from 'lucide-react';

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const navItems: NavItem[] = [
  {
    title: 'Home',
    href: '/',
    icon: Home,
  },
  {
    title: 'Chat',
    href: '/chat',
    icon: MessageSquare,
  },
  {
    title: 'Ideas Hub',
    href: '/ideas',
    icon: Lightbulb,
  },
  {
    title: 'News',
    href: '/news',
    icon: Newspaper,
  },
  {
    title: 'Documents',
    href: '/documents',
    icon: Upload,
  },
  {
    title: 'Playground',
    href: '/playground',
    icon: PlayCircle,
  },
  {
    title: 'Settings',
    href: '/settings',
    icon: Settings,
  },
];

interface SidebarProps {
  className?: string;
}

export function Sidebar({ className }: SidebarProps) {
  const pathname = usePathname();

  return (
    <div className={cn('pb-12 w-64 border-r bg-background', className)}>
      <div className="space-y-4 py-4">
        <div className="px-3 py-2">
          <h2 className="mb-2 px-4 text-lg font-semibold tracking-tight font-headline">
            Keiko
          </h2>
          <div className="space-y-1">
            <ScrollArea className="h-[calc(100vh-120px)]">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = pathname === item.href;
                
                return (
                  <Link key={item.href} href={item.href}>
                    <Button
                      variant={isActive ? 'secondary' : 'ghost'}
                      className={cn(
                        'w-full justify-start',
                        isActive && 'bg-keiko-primary text-keiko-black hover:bg-keiko-primary/90'
                      )}
                    >
                      <Icon className="mr-2 h-4 w-4" />
                      {item.title}
                      {item.badge && (
                        <span className="ml-auto text-xs bg-keiko-primary text-keiko-black px-2 py-0.5 rounded-full">
                          {item.badge}
                        </span>
                      )}
                    </Button>
                  </Link>
                );
              })}
            </ScrollArea>
          </div>
        </div>
      </div>
    </div>
  );
}


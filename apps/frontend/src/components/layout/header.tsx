import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Settings, Menu } from 'lucide-react';

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-keiko-primary">
            <span className="font-headline text-lg font-bold text-keiko-black">
              K
            </span>
          </div>
          <span className="font-headline text-xl font-bold">Keiko</span>
        </Link>

        <nav className="ml-auto flex items-center gap-2">
          <Button variant="ghost" size="icon" aria-label="Settings">
            <Settings className="h-5 w-5" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden"
            aria-label="Menu"
          >
            <Menu className="h-5 w-5" />
          </Button>
        </nav>
      </div>
    </header>
  );
}


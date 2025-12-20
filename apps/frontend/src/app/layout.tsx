import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Keiko - Personal Assistant',
  description: 'AI-powered personal assistant for enterprise knowledge management',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return children;
}


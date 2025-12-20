import {NextIntlClientProvider} from 'next-intl';
import {getMessages} from 'next-intl/server';
import {notFound} from 'next/navigation';
import {Providers} from '../providers';
import {Header} from '@/components/layout/header';
import React from "react";

const locales = ['en', 'de'] as const;
type Locale = (typeof locales)[number];

export function generateStaticParams() {
    return locales.map((locale) => ({locale}));
}

export default async function LocaleLayout({
                                               children,
                                               params,
                                           }: {
    children: React.ReactNode;
    params: Promise<{ locale: string }>;
}) {
    // Await params in Next.js 15
    const {locale} = await params;

    // Validate locale
    if (!locales.includes(locale as Locale)) {
        notFound();
    }

    const messages = await getMessages();

    return (
        <html lang={locale} suppressHydrationWarning>
        <body>
        <NextIntlClientProvider messages={messages}>
            <Providers>
                <div className="relative flex min-h-screen flex-col">
                    <Header/>
                    <main className="flex-1">{children}</main>
                </div>
            </Providers>
        </NextIntlClientProvider>
        </body>
        </html>
    );
}


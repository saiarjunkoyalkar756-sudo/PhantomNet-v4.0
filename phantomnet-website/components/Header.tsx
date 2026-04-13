// phantomnet-website/components/Header.tsx
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils'; // Assuming ShadCN utils path
import { useState } from 'react';
import { Menu, X } from 'lucide-react'; // Lucide icons

const navLinks = [
    { name: 'Home', href: '/' },
    { name: 'Platform Overview', href: '/platform' },
    { name: 'Architecture', href: '/architecture' },
    { name: 'AI & Intelligence', href: '/ai-intelligence' },
    { name: 'Features', href: '/features' },
    { name: 'Security & Trust', href: '/security-trust' },
    { name: 'Demo / Roadmap', href: '/roadmap' },
    { name: 'About / Vision', href: '/about' },
    // Removed Contact/Request Demo from main nav as it will be a dedicated button/CTA
];

export function Header() {
    const pathname = usePathname();
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    const toggleMenu = () => setIsMenuOpen(!isMenuOpen);

    return (
        <motion.header
            initial={{ y: -100 }}
            animate={{ y: 0 }}
            transition={{ type: 'spring', stiffness: 100, damping: 20 }}
            className="fixed top-0 left-0 right-0 z-50 bg-pn-dark-blue/80 backdrop-blur-md border-b border-pn-border shadow-lg"
        >
            <nav className="container mx-auto px-4 py-4 flex justify-between items-center">
                <Link href="/" className="text-2xl font-bold font-heading bg-gradient-to-r from-pn-neon-blue to-pn-electric-purple text-transparent bg-clip-text">
                    PhantomNet
                </Link>

                {/* Desktop Navigation */}
                <ul className="hidden md:flex gap-x-8">
                    {navLinks.map((link) => (
                        <li key={link.name}>
                            <Link href={link.href} className={cn(
                                'relative text-pn-text-light hover:text-pn-neon-blue transition-colors duration-300',
                                pathname === link.href && 'text-pn-neon-blue font-semibold'
                            )}>
                                {link.name}
                                {pathname === link.href && (
                                    <motion.span
                                        layoutId="underline"
                                        className="absolute left-0 bottom-0 h-[2px] w-full bg-pn-neon-blue"
                                    />
                                )}
                            </Link>
                        </li>
                    ))}
                    <li>
                        <Link href="/contact" className="ml-4 px-4 py-2 bg-pn-neon-blue text-pn-dark-blue font-semibold rounded-md hover:bg-pn-electric-purple hover:text-pn-heading transition-all duration-300">
                            Request Demo
                        </Link>
                    </li>
                </ul>

                {/* Mobile Menu Button */}
                <button
                    onClick={toggleMenu}
                    className="md:hidden text-pn-text-light focus:outline-none z-50"
                    aria-label="Toggle Navigation"
                >
                    {isMenuOpen ? <X size={28} /> : <Menu size={28} />}
                </button>

                {/* Mobile Navigation */}
                <motion.div
                    initial={false}
                    animate={isMenuOpen ? 'open' : 'closed'}
                    variants={{
                        open: { x: 0 },
                        closed: { x: '100%' },
                    }}
                    transition={{ type: 'spring', stiffness: 100, damping: 20 }}
                    className="fixed inset-y-0 right-0 w-full bg-pn-dark-blue p-8 flex flex-col items-center justify-center md:hidden z-40"
                >
                    <ul className="flex flex-col gap-y-8 text-center">
                        {navLinks.map((link) => (
                            <li key={link.name}>
                                <Link
                                    href={link.href}
                                    className="text-3xl font-heading text-pn-text-light hover:text-pn-neon-blue transition-colors duration-300"
                                    onClick={toggleMenu} // Close menu on link click
                                >
                                    {link.name}
                                </Link>
                            </li>
                        ))}
                         <li>
                            <Link href="/contact" className="mt-8 px-6 py-3 bg-pn-neon-blue text-pn-dark-blue font-semibold text-2xl rounded-md hover:bg-pn-electric-purple hover:text-pn-heading transition-all duration-300"
                            onClick={toggleMenu}
                            >
                                Request Demo
                            </Link>
                        </li>
                    </ul>
                </motion.div>
            </nav>
        </motion.header>
    );
}

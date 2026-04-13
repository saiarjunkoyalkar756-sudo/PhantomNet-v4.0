// phantomnet-website/components/Footer.tsx
import Link from 'next/link';
import { cn } from '@/lib/utils'; // Assuming ShadCN utils path

export function Footer() {
    const currentYear = new Date().getFullYear();

    const footerLinks = [
        {
            title: 'Product',
            links: [
                { name: 'Platform Overview', href: '/platform' },
                { name: 'Features', href: '/features' },
                { name: 'Architecture', href: '/architecture' },
                { name: 'AI & Intelligence', href: '/ai-intelligence' },
            ],
        },
        {
            title: 'Resources',
            links: [
                { name: 'Docs', href: '#', external: true }, // Placeholder
                { name: 'GitHub', href: '#', external: true }, // Placeholder
                { name: 'Support', href: '#', external: true }, // Placeholder
            ],
        },
        {
            title: 'Company',
            links: [
                { name: 'About / Vision', href: '/about' },
                { name: 'Contact', href: '/contact' },
                { name: 'Careers', href: '#', external: true }, // Placeholder
            ],
        },
    ];

    return (
        <footer className="bg-pn-dark-light text-pn-text-muted py-12 border-t border-pn-border">
            <div className="container mx-auto px-4">
                <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-10">
                    <div className="col-span-full md:col-span-1">
                        <Link href="/" className="text-3xl font-bold font-heading bg-gradient-to-r from-pn-neon-blue to-pn-electric-purple text-transparent bg-clip-text mb-4 block">
                            PhantomNet
                        </Link>
                        <p className="text-sm">Autonomous AI Cyber Defense.</p>
                        <p className="text-sm">Real-Time. Self-Healing.</p>
                    </div>

                    {footerLinks.map((section, index) => (
                        <div key={index} className="col-span-1">
                            <h4 className="text-lg font-semibold text-pn-heading mb-4">{section.title}</h4>
                            <ul>
                                {section.links.map((link, linkIndex) => (
                                    <li key={linkIndex} className="mb-2">
                                        <Link
                                            href={link.href}
                                            {...(link.external && { target: '_blank', rel: 'noopener noreferrer' })}
                                            className="hover:text-pn-neon-blue transition-colors duration-300 text-sm"
                                        >
                                            {link.name}
                                        </Link>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    ))}
                </div>

                <div className="text-center pt-8 border-t border-pn-border text-sm">
                    <p>&copy; {currentYear} PhantomNet. All rights reserved.</p>
                </div>
            </div>
        </footer>
    );
}

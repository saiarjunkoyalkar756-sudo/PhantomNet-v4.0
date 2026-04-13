// phantomnet-website/app/contact/page.tsx
'use client';

import { motion } from 'framer-motion';
import { Mail, Phone, MapPin, Send } from 'lucide-react'; // Lucide icons

const sectionVariants = {
    hidden: { opacity: 0, y: 50 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
};

const formFieldVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: { opacity: 1, x: 0, transition: { duration: 0.4, ease: 'easeOut' } },
};

export default function ContactPage() {
    return (
        <div className="bg-pn-dark-blue text-pn-text-light py-16 md:py-24">
            <div className="container mx-auto px-4">
                <motion.h1
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="text-4xl md:text-5xl font-bold font-heading text-center mb-12 bg-gradient-to-r from-pn-neon-blue to-pn-electric-purple text-transparent bg-clip-text"
                >
                    Contact Us / Request a Demo
                </motion.h1>

                <motion.section
                    initial="hidden"
                    whileInView="visible"
                    viewport={{ once: true, amount: 0.3 }}
                    variants={sectionVariants}
                    className="mb-16 md:mb-24 p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border text-center"
                >
                    <h2 className="text-3xl font-semibold font-heading mb-6 text-pn-heading">Unlock Autonomous Cyber Defense for Your Enterprise</h2>
                    <p className="text-lg text-pn-text-muted leading-relaxed max-w-4xl mx-auto">
                        Ready to revolutionize your security operations? Fill out the form below to
                        request a personalized demo, discuss your specific needs, or connect with our
                        cybersecurity experts. We're here to help you build a resilient, future-proof defense.
                    </p>
                </motion.section>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
                    {/* Contact Form */}
                    <motion.div
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, amount: 0.3 }}
                        variants={sectionVariants}
                        className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border"
                    >
                        <h2 className="text-2xl font-semibold font-heading mb-6 text-pn-heading">Request a Personalized Demo</h2>
                        <form className="space-y-6">
                            <motion.div variants={formFieldVariants}>
                                <label htmlFor="fullName" className="block text-sm font-medium text-pn-text-light mb-2">Full Name</label>
                                <input
                                    type="text"
                                    id="fullName"
                                    name="fullName"
                                    className="w-full p-3 rounded-md bg-pn-dark-blue border border-pn-border focus:ring-2 focus:ring-pn-neon-blue focus:border-transparent transition-all duration-300 text-pn-text-light"
                                    placeholder="John Doe"
                                    required
                                />
                            </motion.div>
                            <motion.div variants={formFieldVariants}>
                                <label htmlFor="workEmail" className="block text-sm font-medium text-pn-text-light mb-2">Work Email</label>
                                <input
                                    type="email"
                                    id="workEmail"
                                    name="workEmail"
                                    className="w-full p-3 rounded-md bg-pn-dark-blue border border-pn-border focus:ring-2 focus:ring-pn-neon-blue focus:border-transparent transition-all duration-300 text-pn-text-light"
                                    placeholder="john.doe@enterprise.com"
                                    required
                                />
                            </motion.div>
                            <motion.div variants={formFieldVariants}>
                                <label htmlFor="companyName" className="block text-sm font-medium text-pn-text-light mb-2">Company Name</label>
                                <input
                                    type="text"
                                    id="companyName"
                                    name="companyName"
                                    className="w-full p-3 rounded-md bg-pn-dark-blue border border-pn-border focus:ring-2 focus:ring-pn-neon-blue focus:border-transparent transition-all duration-300 text-pn-text-light"
                                    placeholder="Acme Corp."
                                    required
                                />
                            </motion.div>
                            <motion.div variants={formFieldVariants}>
                                <label htmlFor="jobTitle" className="block text-sm font-medium text-pn-text-light mb-2">Job Title</label>
                                <input
                                    type="text"
                                    id="jobTitle"
                                    name="jobTitle"
                                    className="w-full p-3 rounded-md bg-pn-dark-blue border border-pn-border focus:ring-2 focus:ring-pn-neon-blue focus:border-transparent transition-all duration-300 text-pn-text-light"
                                    placeholder="CISO, Security Architect, etc."
                                />
                            </motion.div>
                            <motion.div variants={formFieldVariants}>
                                <label htmlFor="message" className="block text-sm font-medium text-pn-text-light mb-2">Your Message (Optional)</label>
                                <textarea
                                    id="message"
                                    name="message"
                                    rows={4}
                                    className="w-full p-3 rounded-md bg-pn-dark-blue border border-pn-border focus:ring-2 focus:ring-pn-neon-blue focus:border-transparent transition-all duration-300 text-pn-text-light"
                                    placeholder="How can we help you?"
                                ></textarea>
                            </motion.div>
                            <motion.div variants={formFieldVariants}>
                                <button
                                    type="submit"
                                    className="w-full flex items-center justify-center px-6 py-3 bg-pn-neon-blue text-pn-dark-blue font-semibold rounded-md hover:bg-pn-electric-purple hover:text-pn-heading transition-all duration-300 text-lg shadow-lg"
                                >
                                    <Send size={20} className="mr-2" />
                                    Submit Request
                                </button>
                            </motion.div>
                        </form>
                    </motion.div>

                    {/* Contact Information */}
                    <motion.div
                        initial="hidden"
                        whileInView="visible"
                        viewport={{ once: true, amount: 0.3 }}
                        variants={sectionVariants}
                        className="p-8 bg-pn-dark-light rounded-lg shadow-xl border border-pn-border"
                    >
                        <h2 className="text-2xl font-semibold font-heading mb-6 text-pn-heading">General Inquiries</h2>
                        <div className="space-y-6 text-lg text-pn-text-muted">
                            <motion.div variants={itemVariants} className="flex items-center">
                                <Mail size={24} className="text-pn-neon-blue mr-4" />
                                <a href="mailto:info@phantomnet.com" className="hover:text-pn-electric-purple transition-colors duration-300">info@phantomnet.com</a>
                            </motion.div>
                            <motion.div variants={itemVariants} className="flex items-center">
                                <Phone size={24} className="text-pn-neon-blue mr-4" />
                                <a href="tel:+18005550199" className="hover:text-pn-electric-purple transition-colors duration-300">+1 (800) 555-0199</a>
                            </motion.div>
                            <motion.div variants={itemVariants} className="flex items-center">
                                <MapPin size={24} className="text-pn-neon-blue mr-4" />
                                <p>123 Cyber Street, Suite 400, Tech City, TX 78701</p>
                            </motion.div>
                        </div>

                        <h2 className="text-2xl font-semibold font-heading mt-10 mb-6 text-pn-heading">Global Offices</h2>
                        <ul className="space-y-4 text-lg text-pn-text-muted">
                            <motion.li variants={itemVariants}>
                                <p><MapPin size={20} className="inline-block text-pn-electric-purple mr-3" /> London, UK</p>
                            </motion.li>
                            <motion.li variants={itemVariants}>
                                <p><MapPin size={20} className="inline-block text-pn-electric-purple mr-3" /> Singapore</p>
                            </motion.li>
                            <motion.li variants={itemVariants}>
                                <p><MapPin size={20} className="inline-block text-pn-electric-purple mr-3" /> Sydney, Australia</p>
                            </motion.li>
                        </ul>
                    </motion.div>
                </div>
            </div>
        </div>
    );
}

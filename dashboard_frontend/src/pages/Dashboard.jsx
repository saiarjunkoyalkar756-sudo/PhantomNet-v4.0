import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import PageHeader from '@/components/shared/PageHeader';
import MetricsWidget from '@/features/dashboard/MetricsWidget';
import WorldAttackMap from '@/features/dashboard/WorldAttackMap';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
    Plus, 
    Shield, 
    AlertTriangle, 
    Cpu, 
    Activity, 
    Brain, 
    MessageSquare,
    Zap,
    Wind
} from 'lucide-react';

const Dashboard = () => {
    const [summary, setSummary] = useState(null);
    const [isZenMode, setIsZenMode] = useState(false);
    const [isAIAssistantOpen, setIsAIAssistantOpen] = useState(false);

    // Fetch real metrics from the Dashboard Service
    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await axios.get('http://localhost:8000/api/dashboard/executive-summary');
                setSummary(response.data);
            } catch (err) {
                console.error("Failed to fetch dashboard summary:", err);
            }
        };
        fetchData();
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, []);

    const metrics = [
        { 
            title: "Automated Responses", 
            value: summary?.automated_remediations_count_24h || "450", 
            change: "100% Autonomous", 
            icon: Zap, 
            color: "primary" 
        },
        { 
            title: "Overall Risk Score", 
            value: summary?.overall_risk_score || "42", 
            change: `${summary?.risk_trend_percent_7d || -12.5}% vs last week`, 
            icon: Brain, 
            color: summary?.overall_risk_score > 70 ? "destructive" : "secondary" 
        },
        { 
            title: "Manual Escalations", 
            value: summary?.manual_escalations_count_24h || "3", 
            change: "Low Analyst Friction", 
            icon: Shield, 
            color: "primary" 
        },
    ];

    const containerVariants = {
        hidden: { opacity: 0 },
        visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
    };

    return (
        <div className={`relative min-h-screen transition-all duration-700 ${isZenMode ? 'bg-[#05070a] grayscale-[0.5]' : ''}`}>
            {/* Zen Mode Toggle Overlay */}
            <AnimatePresence>
                {isZenMode && (
                    <motion.div 
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 pointer-events-none z-50 border-[20px] border-primary/5 shadow-[inset_0_0_100px_rgba(139,92,246,0.1)]"
                    />
                )}
            </AnimatePresence>

            <PageHeader 
                title={isZenMode ? "ZEN DEFENSE ACTIVE" : "GLOBAL THREAT COMMAND"}
                subtitle={isZenMode ? "UI simplified for cognitive load optimization." : "Real-time autonomous security orchestration overview."}
                actions={
                    <div className="flex items-center space-x-3">
                        <Button 
                            variant="outline" 
                            onClick={() => setIsZenMode(!isZenMode)}
                            className={`transition-all ${isZenMode ? 'bg-primary text-primary-foreground border-primary' : 'border-primary/20 hover:border-primary/50'}`}
                        >
                            <Wind className={`w-4 h-4 mr-2 ${isZenMode ? 'animate-spin-slow' : ''}`} />
                            {isZenMode ? "EXIT ZEN" : "ZEN MODE"}
                        </Button>
                        <Button className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-[0_0_15px_rgba(139,92,246,0.4)]">
                            <Plus className="w-4 h-4 mr-2" />
                            NEW INVESTIGATION
                        </Button>
                    </div>
                }
            />

            <motion.div 
                className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6"
                variants={containerVariants}
                initial="hidden"
                animate="visible"
            >
                {metrics.map((metric, index) => (
                    <motion.div key={index} variants={{ hidden: { y: 20, opacity: 0 }, visible: { y: 0, opacity: 1 } }}>
                        <MetricsWidget {...metric} />
                    </motion.div>
                ))}
            </motion.div>

            <div className={`grid grid-cols-1 lg:grid-cols-5 gap-6 transition-all duration-500 ${isZenMode ? 'scale-[0.98]' : ''}`}>
                <div className="lg:col-span-3 h-[450px]">
                    <WorldAttackMap />
                </div>
                
                <div className="lg:col-span-2 space-y-6">
                    <Card className="glass-panel border-primary/20 flex-1 overflow-hidden">
                        <CardHeader className="flex flex-row items-center justify-between pb-2 border-b border-border/50 bg-muted/20">
                            <CardTitle className="text-xs font-bold tracking-widest text-text-secondary flex items-center">
                                <Activity className="w-4 h-4 mr-2 text-primary animate-pulse" />
                                LIVE PROPAGATION FEED
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-0 h-[350px] overflow-y-auto custom-scrollbar">
                           {!isZenMode ? (
                                <ul className="divide-y divide-border/30">
                                    {(summary?.top_attack_vectors || []).map((vector, i) => (
                                        <li key={i} className="p-4 hover:bg-primary/5 transition-colors flex items-center justify-between group">
                                            <div className="flex items-center space-x-3">
                                                <div className="w-1 h-8 bg-primary/20 group-hover:bg-primary rounded-full transition-all" />
                                                <div>
                                                    <p className="text-xs font-bold uppercase tracking-tighter">{vector.vector}</p>
                                                    <p className="text-[10px] text-muted-foreground font-mono">MITRE ATT&CK: T10{i}x</p>
                                                </div>
                                            </div>
                                            <span className="text-xl font-black font-mono opacity-20 group-hover:opacity-100 transition-opacity">
                                                {vector.count}
                                            </span>
                                        </li>
                                    ))}
                                </ul>
                           ) : (
                                <div className="h-full flex items-center justify-center text-center p-8">
                                    <p className="text-sm text-muted-foreground italic font-light italic">
                                        "Noise suppressed. Focus on critical path. 450 automated remediations successful in last update."
                                    </p>
                                </div>
                           )}
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* AI Assistant Floating Toggle */}
            <motion.button 
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={() => setIsAIAssistantOpen(!isAIAssistantOpen)}
                className="fixed bottom-8 right-8 w-14 h-14 bg-primary rounded-full flex items-center justify-center shadow-[0_0_20px_rgba(139,92,246,0.6)] z-50 text-white"
            >
                <MessageSquare />
            </motion.button>

            {/* AI Assistant Chat UI */}
            <AnimatePresence>
                {isAIAssistantOpen && (
                    <motion.div 
                        initial={{ opacity: 0, y: 50, scale: 0.9 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 50, scale: 0.9 }}
                        className="fixed bottom-24 right-8 w-80 h-[400px] glass-panel border-primary/30 rounded-2xl z-50 flex flex-col shadow-2xl overflow-hidden"
                    >
                        <div className="p-4 bg-primary text-primary-foreground flex items-center space-x-2">
                            <Brain className="w-5 h-5" />
                            <span className="text-xs font-bold uppercase tracking-widest">PHANTOM SENTINEL</span>
                        </div>
                        <div className="flex-1 p-4 overflow-y-auto custom-scrollbar space-y-4">
                            <div className="bg-muted/50 p-3 rounded-tr-xl rounded-br-xl rounded-bl-xl text-[11px] leading-relaxed">
                                Hello Admin. I'm monitoring the colony. Current stress levels are low. 
                                <span className="block mt-2 font-bold text-primary">Status: No manual intervention required.</span>
                            </div>
                        </div>
                        <div className="p-4 border-t border-border/50 flex">
                            <input 
                                disabled
                                placeholder="Chat with Sentinel (AI)..." 
                                className="flex-1 bg-transparent text-[11px] outline-none placeholder:text-muted-foreground"
                            />
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default Dashboard;

import React from 'react';
import { motion } from 'framer-motion';
import PageHeader from '@/components/shared/PageHeader';
import MetricsWidget from '@/features/dashboard/MetricsWidget';
import WorldAttackMap from '@/features/dashboard/WorldAttackMap';
import { Button } from '@/components/ui/Button';
import { Plus, Shield, AlertTriangle, Cpu, Activity } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shared/Card';

// Mock data for charts
const generateMetricData = () => Array.from({ length: 20 }, (_, i) => ({ name: `Day ${i + 1}`, uv: Math.floor(Math.random() * 300) }));
const generateEventData = () => Array.from({ length: 10 }, (_, i) => ({
    id: i,
    time: new Date(Date.now() - i * 60 * 1000).toLocaleTimeString(),
    type: ["Alert", "Detection", "Info", "Warning"][Math.floor(Math.random() * 4)],
    source: `Sensor-${Math.floor(Math.random() * 100)}`,
    description: `Potential threat detected from IP 192.168.1.${i} on port 808${i}`,
    severity: ["High", "Medium", "Low"][Math.floor(Math.random() * 3)]
}));


const Dashboard = () => {
    
    const metrics = [
        { title: "Open Alerts", value: "147", change: "+12.5% vs last week", data: generateMetricData(), dataKey: "uv", icon: AlertTriangle, color: "destructive" },
        { title: "Agents Deployed", value: "2,453", change: "+50 this week", data: generateMetricData(), dataKey: "uv", icon: Shield, color: "primary" },
        { title: "High-Risk Endpoints", value: "89", change: "-2.1% vs last week", data: generateMetricData(), dataKey: "uv", icon: Cpu, color: "secondary" },
    ];

    const events = generateEventData();

    const cardVariants = {
      hidden: { opacity: 0, y: 20 },
      visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
    };


    return (
        <div className="font-sans">
            <PageHeader 
                title="GLOBAL THREAT DASHBOARD"
                subtitle="Welcome back, Admin. Here's your security overview."
                actions={<Button className="bg-primary hover:bg-primary/90 text-primary-foreground"><Plus className="w-4 h-4 mr-2" />NEW REPORT</Button>}
            />

            <motion.div 
                className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-6"
                initial="hidden"
                animate="visible"
                variants={{ visible: { transition: { staggerChildren: 0.1 } } }}
            >
                {metrics.map((metric, index) => (
                    <motion.div key={index} variants={cardVariants}>
                        <MetricsWidget {...metric} />
                    </motion.div>
                ))}
            </motion.div>

            <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                <motion.div variants={cardVariants} className="lg:col-span-3">
                    <WorldAttackMap />
                </motion.div>
                <motion.div variants={cardVariants} className="lg:col-span-2">
                    <Card className="h-full flex flex-col">
                        <CardHeader className="flex flex-row items-center justify-between pb-2">
                            <CardTitle className="text-sm font-medium text-text-secondary flex items-center">
                                <Activity className="w-4 h-4 mr-2 text-primary animate-pulse" />
                                Recent Events
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="flex-1 overflow-y-auto custom-scrollbar">
                            <ul className="space-y-3">
                                {events.map(event => (
                                    <li key={event.id} className="text-xs text-text-secondary flex items-start">
                                        <span className="text-muted-foreground mr-2">{event.time}</span>
                                        <span className={`font-bold mr-2 
                                            ${event.severity === 'High' ? 'text-destructive' : ''}
                                            ${event.severity === 'Medium' ? 'text-secondary' : ''}
                                            ${event.severity === 'Low' ? 'text-primary' : ''}
                                        `}>[{event.severity}]</span>
                                        <span className="flex-1">{event.description}</span>
                                    </li>
                                ))}
                            </ul>
                        </CardContent>
                    </Card>
                </motion.div>
            </div>
        </div>
    );
};

export default Dashboard;

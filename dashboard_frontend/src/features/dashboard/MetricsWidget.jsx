import React from 'react';
import { AreaChart, Area, ResponsiveContainer, Tooltip } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/shared/Card';
import { cn } from '@/lib/utils';
import { ArrowUpRight } from 'lucide-react';

const TinyChart = ({ data, dataKey, stroke, fill }) => (
    <ResponsiveContainer width="100%" height={50}>
        <AreaChart data={data} margin={{ top: 5, right: 0, left: 0, bottom: 0 }}>
            <Tooltip
                contentStyle={{
                    background: "hsl(var(--background) / 0.8)",
                    borderColor: "hsl(var(--border))",
                    color: "hsl(var(--foreground))"
                }}
                itemStyle={{ color: "hsl(var(--foreground))" }}
                labelStyle={{ color: "hsl(var(--muted-foreground))" }}
            />
            <Area type="monotone" dataKey={dataKey} stroke={stroke} fill={fill} strokeWidth={2} />
        </AreaChart>
    </ResponsiveContainer>
);


const MetricsWidget = ({ title, value, change, data, dataKey, "icon": Icon, "color": color = 'primary' }) => {
    
    const colors = {
        primary: { stroke: 'hsl(var(--primary))', fill: 'hsl(var(--primary) / 0.1)'},
        secondary: { stroke: 'hsl(var(--secondary))', fill: 'hsl(var(--secondary) / 0.1)'},
        destructive: { stroke: 'hsl(var(--destructive))', fill: 'hsl(var(--destructive) / 0.1)'},
    }

    const {stroke, fill} = colors[color] || colors.primary;

    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-text-secondary">{title}</CardTitle>
                {Icon && <Icon className={cn("w-5 h-5", `text-${color}`)} />}
            </CardHeader>
            <CardContent>
                <div className="text-3xl font-bold" style={{color: `hsl(var(--${color}))`}}>{value}</div>
                <p className="text-xs text-green-400 flex items-center">
                    <ArrowUpRight className="w-4 h-4 mr-1" />
                    {change}
                </p>
                <div className="mt-4">
                    <TinyChart data={data} dataKey={dataKey} stroke={stroke} fill={fill} />
                </div>
            </CardContent>
        </Card>
    );
};

export default MetricsWidget;

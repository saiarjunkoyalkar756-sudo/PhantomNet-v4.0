// phantomnet-website/components/ArchitectureDiagram.tsx
'use client';

import React from 'react';
import { motion } from 'framer-motion';
import {
    Server,
    Database,
    Cloud,
    Cpu,
    ArrowRight,
    Lock,
    GitFork,
    MessageCircle,
    Book,
    ShieldCheck,
} from 'lucide-react';

const nodeVariants = {
    hidden: { opacity: 0, scale: 0.8 },
    visible: { opacity: 1, scale: 1, transition: { duration: 0.5, ease: 'easeOut' } },
    hover: { scale: 1.05, boxShadow: '0px 0px 15px rgba(0, 240, 255, 0.4)' },
};

const arrowVariants = {
    hidden: { pathLength: 0, opacity: 0 },
    visible: { pathLength: 1, opacity: 1, transition: { duration: 1, ease: 'easeInOut' } },
};

const Node = ({ icon: Icon, label, color, delay, x, y, width = 120, height = 80 }) => (
    <motion.g
        initial="hidden"
        animate="visible"
        variants={nodeVariants}
        transition={{ delay }}
        whileHover="hover"
        className="cursor-pointer group"
        transform={`translate(${x}, ${y})`}
    >
        <rect
            width={width}
            height={height}
            rx="10"
            ry="10"
            className={`fill-pn-dark-light stroke-[2px]`}
            style={{ stroke: color }}
        />
        <g className="group-hover:animate-pulse">
            <Icon
                size={32}
                className="text-pn-text-light absolute"
                x={width / 2 - 16}
                y={15}
                style={{ color }}
            />
        </g>
        <text
            x={width / 2}
            y={height - 20}
            textAnchor="middle"
            className="fill-pn-text-light font-sans text-xs font-semibold"
        >
            {label}
        </text>
    </motion.g>
);

const Arrow = ({ d, delay }) => (
    <motion.path
        d={d}
        className="stroke-pn-electric-purple fill-none stroke-[2px]"
        initial="hidden"
        animate="visible"
        variants={arrowVariants}
        transition={{ delay }}
        markerEnd="url(#arrowhead)"
    />
);

export function ArchitectureDiagram() {
    const nodeWidth = 120;
    const nodeHeight = 80;
    const spacingX = 80;
    const spacingY = 60;

    // Define positions for nodes
    const positions = {
        agent: { x: 0, y: nodeHeight + spacingY + nodeHeight },
        telemetry: { x: nodeWidth + spacingX, y: nodeHeight + spacingY + nodeHeight },
        kafka: { x: (nodeWidth + spacingX) * 2, y: nodeHeight + spacingY + nodeHeight },
        aiEngine: { x: (nodeWidth + spacingX) * 3, y: nodeHeight + spacingY + nodeHeight },
        correlation: { x: (nodeWidth + spacingX) * 4, y: nodeHeight + spacingY + nodeHeight },
        soar: { x: (nodeWidth + spacingX) * 5, y: nodeHeight + spacingY + nodeHeight },
        blockchain: { x: (nodeWidth + spacingX) * 6, y: nodeHeight + spacingY + nodeHeight },

        microservices: { x: (nodeWidth + spacingX) * 2.5, y: 0 },
        secureApi: { x: (nodeWidth + spacingX) * 2.5, y: (nodeHeight + spacingY) * 2.8 },
    };

    const totalWidth = (nodeWidth + spacingX) * 7 - spacingX; // Adjust for actual number of elements
    const totalHeight = (nodeHeight + spacingY) * 4;

    return (
        <div className="flex justify-center items-center py-10">
            <svg
                width="100%"
                height="auto"
                viewBox={`0 0 ${totalWidth} ${totalHeight}`}
                className="overflow-visible"
                xmlns="http://www.w3.org/2000/svg"
            >
                <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="8" refY="3.5" orient="auto">
                        <polygon points="0 0, 10 3.5, 0 7" className="fill-pn-electric-purple" />
                    </marker>
                </defs>

                {/* Main Flow Nodes */}
                <Node icon={ShieldCheck} label="Agent" color="#00F0FF" delay={0.2} {...positions.agent} />
                <Node icon={Database} label="Telemetry Ingestor" color="#00F0FF" delay={0.4} {...positions.telemetry} />
                <Node icon={MessageCircle} label="Kafka Event Stream" color="#8A2BE2" delay={0.6} {...positions.kafka} />
                <Node icon={Cpu} label="AI Engine" color="#00F0FF" delay={0.8} {...positions.aiEngine} />
                <Node icon={GitFork} label="Correlation Engine" color="#8A2BE2" delay={1.0} {...positions.correlation} />
                <Node icon={Zap} label="SOAR" color="#00F0FF" delay={1.2} {...positions.soar} />
                <Node icon={Book} label="Blockchain Audit" color="#8A2BE2" delay={1.4} {...positions.blockchain} />

                {/* Central Microservices Node */}
                <Node icon={Server} label="Microservices Core" color="#8A2BE2" delay={0.5} x={positions.microservices.x} y={positions.microservices.y} width={200} height={100} />
                {/* Secure API Gateway Node */}
                <Node icon={Lock} label="Secure API Gateway" color="#00F0FF" delay={0.7} x={positions.secureApi.x} y={positions.secureApi.y} width={200} height={100} />


                {/* Arrows for Main Flow */}
                <Arrow d={`M ${positions.agent.x + nodeWidth},${positions.agent.y + nodeHeight / 2} L ${positions.telemetry.x},${positions.telemetry.y + nodeHeight / 2}`} delay={1.6} />
                <Arrow d={`M ${positions.telemetry.x + nodeWidth},${positions.telemetry.y + nodeHeight / 2} L ${positions.kafka.x},${positions.kafka.y + nodeHeight / 2}`} delay={1.8} />
                <Arrow d={`M ${positions.kafka.x + nodeWidth},${positions.kafka.y + nodeHeight / 2} L ${positions.aiEngine.x},${positions.aiEngine.y + nodeHeight / 2}`} delay={2.0} />
                <Arrow d={`M ${positions.aiEngine.x + nodeWidth},${positions.aiEngine.y + nodeHeight / 2} L ${positions.correlation.x},${positions.correlation.y + nodeHeight / 2}`} delay={2.2} />
                <Arrow d={`M ${positions.correlation.x + nodeWidth},${positions.correlation.y + nodeHeight / 2} L ${positions.soar.x},${positions.soar.y + nodeHeight / 2}`} delay={2.4} />
                <Arrow d={`M ${positions.soar.x + nodeWidth},${positions.soar.y + nodeHeight / 2} L ${positions.blockchain.x},${positions.blockchain.y + nodeHeight / 2}`} delay={2.6} />

                {/* Arrows to/from Microservices Core */}
                <Arrow d={`M ${positions.kafka.x + nodeWidth / 2},${positions.kafka.y} L ${positions.kafka.x + nodeWidth / 2},${positions.microservices.y + nodeHeight} M ${positions.microservices.x + nodeWidth / 2},${positions.microservices.y + nodeHeight} L ${positions.aiEngine.x + nodeWidth / 2},${positions.aiEngine.y}`} delay={2.8} />
                <Arrow d={`M ${positions.microservices.x + nodeWidth / 2 + 30},${positions.microservices.y + nodeHeight} L ${positions.correlation.x + nodeWidth / 2},${positions.correlation.y}`} delay={3.0} />
                <Arrow d={`M ${positions.microservices.x + nodeWidth / 2 - 30},${positions.microservices.y + nodeHeight} L ${positions.soar.x + nodeWidth / 2},${positions.soar.y}`} delay={3.2} />


                {/* Arrows to/from Secure API Gateway */}
                <Arrow d={`M ${positions.microservices.x + nodeWidth / 2},${positions.microservices.y} L ${positions.secureApi.x + nodeWidth / 2},${positions.secureApi.y + nodeHeight}`} delay={3.4} />
                <Arrow d={`M ${positions.secureApi.x + nodeWidth / 2},${positions.secureApi.y} L ${positions.telemetry.x + nodeWidth / 2},${positions.telemetry.y + nodeHeight}`} delay={3.6} />

            </svg>
        </div>
    );
}

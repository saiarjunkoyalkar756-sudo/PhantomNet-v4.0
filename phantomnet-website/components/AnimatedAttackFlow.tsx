// phantomnet-website/components/AnimatedAttackFlow.tsx
'use client';

import React from 'react';
import { motion } from 'framer-motion';

const attackFlowSteps = [
    { id: 'agent', label: 'Agent' },
    { id: 'telemetry', label: 'Telemetry' },
    { id: 'ai', label: 'AI Engine' },
    { id: 'correlation', label: 'Correlation' },
    { id: 'soar', label: 'SOAR' },
    { id: 'blockchain', label: 'Audit Ledger' },
];

const pathVariants = {
    hidden: { pathLength: 0, opacity: 0 },
    visible: {
        pathLength: 1,
        opacity: 1,
        transition: {
            duration: 1.5,
            ease: 'easeInOut',
        },
    },
};

const textVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.5, delay: 1.2 } },
};

export function AnimatedAttackFlow() {
    // Determine SVG width based on steps and spacing
    const boxWidth = 120;
    const arrowWidth = 60;
    const totalWidth = attackFlowSteps.length * boxWidth + (attackFlowSteps.length - 1) * arrowWidth;
    const boxHeight = 40;
    const arrowHeight = boxHeight / 2; // Approximate height for arrow lines

    let currentX = 0;
    const elements = [];
    const arrows = [];

    attackFlowSteps.forEach((step, index) => {
        // Box for the step
        elements.push(
            <motion.rect
                key={`rect-${step.id}`}
                x={currentX}
                y={0}
                width={boxWidth}
                height={boxHeight}
                rx="8"
                ry="8"
                className="fill-pn-dark-light stroke-pn-neon-blue stroke-[1px]"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5, delay: index * 0.2 }}
            />
        );

        // Text for the step
        elements.push(
            <motion.text
                key={`text-${step.id}`}
                x={currentX + boxWidth / 2}
                y={boxHeight / 2 + 5} // Adjust text vertical position
                textAnchor="middle"
                className="fill-pn-text-light font-sans text-sm font-semibold"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.2 + 0.3 }}
            >
                {step.label}
            </motion.text>
        );

        // Add arrow if not the last step
        if (index < attackFlowSteps.length - 1) {
            const arrowStartX = currentX + boxWidth;
            const arrowEndX = arrowStartX + arrowWidth;
            const arrowCenterY = boxHeight / 2;

            arrows.push(
                <motion.path
                    key={`arrow-${step.id}`}
                    d={`M ${arrowStartX},${arrowCenterY} L ${arrowEndX},${arrowCenterY} M ${arrowEndX - 10},${arrowCenterY - 5} L ${arrowEndX},${arrowCenterY} L ${arrowEndX - 10},${arrowCenterY + 5}`}
                    className="stroke-pn-electric-purple fill-none stroke-[2px]"
                    variants={pathVariants}
                    initial="hidden"
                    animate="visible"
                    transition={{ delay: index * 0.2 + 0.5, duration: 0.8 }}
                />
            );
        }

        currentX += boxWidth + arrowWidth;
    });

    return (
        <div className="flex justify-center items-center py-10 px-4">
            <svg
                width={totalWidth}
                height={boxHeight}
                viewBox={`0 0 ${totalWidth} ${boxHeight}`}
                xmlns="http://www.w3.org/2000/svg"
                className="overflow-visible"
            >
                {elements}
                {arrows}
            </svg>
        </div>
    );
}

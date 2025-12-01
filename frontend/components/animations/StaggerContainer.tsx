'use client';

import { motion, HTMLMotionProps, Variants } from 'framer-motion';
import { ANIMATION } from '@/lib/constants';

interface StaggerContainerProps extends HTMLMotionProps<'div'> {
  staggerDelay?: number;
  delayChildren?: number;
}

export const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1,
    },
  },
};

export const itemVariants: Variants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: ANIMATION.MEDIUM,
      ease: [0.34, 1.56, 0.64, 1],
    },
  },
};

export function StaggerContainer({
  children,
  staggerDelay = 0.05,
  delayChildren = 0.1,
  ...props
}: StaggerContainerProps) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: {
            staggerChildren: staggerDelay,
            delayChildren,
          },
        },
      }}
      {...props}
    >
      {children}
    </motion.div>
  );
}

export function StaggerItem({
  children,
  ...props
}: HTMLMotionProps<'div'>) {
  return (
    <motion.div variants={itemVariants} {...props}>
      {children}
    </motion.div>
  );
}

export default StaggerContainer;

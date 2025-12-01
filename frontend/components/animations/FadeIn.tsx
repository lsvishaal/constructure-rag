'use client';

import { motion, HTMLMotionProps } from 'framer-motion';
import { ANIMATION, EASING } from '@/lib/constants';

interface FadeInProps extends HTMLMotionProps<'div'> {
  delay?: number;
  duration?: number;
  direction?: 'up' | 'down' | 'left' | 'right' | 'none';
  distance?: number;
}

export function FadeIn({
  children,
  delay = 0,
  duration = ANIMATION.MEDIUM,
  direction = 'up',
  distance = 20,
  ...props
}: FadeInProps) {
  const directions = {
    up: { y: distance },
    down: { y: -distance },
    left: { x: distance },
    right: { x: -distance },
    none: {},
  };

  return (
    <motion.div
      initial={{ opacity: 0, ...directions[direction] }}
      animate={{ opacity: 1, x: 0, y: 0 }}
      transition={{
        duration,
        delay,
        ease: EASING.ENTRANCE,
      }}
      {...props}
    >
      {children}
    </motion.div>
  );
}

export default FadeIn;

// Animation constants following the architecture guide
// Motion Timing (2025 industry standard)

export const TIMING = {
  fast: 0.15,      // UI feedback (150ms)
  medium: 0.3,     // Transitions (300ms)
  slow: 0.5,       // Announcements (500ms)
  verySlow: 0.8,   // Hero animations (800ms)
} as const;

// Easing curves (cubic bezier)
export const EASING = {
  // Entrance animations - ease out
  entrance: [0.0, 0.0, 0.2, 1.0],
  // Exit animations - ease in
  exit: [0.4, 0.0, 1.0, 1.0],
  // Interactive - spring-like feel
  interactive: [0.34, 1.56, 0.64, 1.0],
  // Smooth scroll/large movements
  smooth: [0.16, 1.0, 0.3, 1.0],
} as const;

// Spring configurations
export const SPRING = {
  // Snappy for buttons
  snappy: { type: 'spring', stiffness: 400, damping: 30 },
  // Bouncy for attention-grabbing
  bouncy: { type: 'spring', stiffness: 300, damping: 15 },
  // Smooth for page transitions
  smooth: { type: 'spring', stiffness: 200, damping: 25 },
  // Gentle for subtle movements
  gentle: { type: 'spring', stiffness: 150, damping: 20 },
} as const;

// Common animation variants
export const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: TIMING.medium, ease: EASING.entrance }
  },
  exit: { 
    opacity: 0, 
    y: -10,
    transition: { duration: TIMING.fast, ease: EASING.exit }
  }
};

export const fadeInScale = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: { 
    opacity: 1, 
    scale: 1,
    transition: { duration: TIMING.medium, ease: EASING.entrance }
  },
  exit: { 
    opacity: 0, 
    scale: 0.95,
    transition: { duration: TIMING.fast, ease: EASING.exit }
  }
};

export const slideInLeft = {
  hidden: { opacity: 0, x: -30 },
  visible: { 
    opacity: 1, 
    x: 0,
    transition: { duration: TIMING.medium, ease: EASING.entrance }
  },
  exit: { 
    opacity: 0, 
    x: -20,
    transition: { duration: TIMING.fast, ease: EASING.exit }
  }
};

export const slideInRight = {
  hidden: { opacity: 0, x: 30 },
  visible: { 
    opacity: 1, 
    x: 0,
    transition: { duration: TIMING.medium, ease: EASING.entrance }
  },
  exit: { 
    opacity: 0, 
    x: 20,
    transition: { duration: TIMING.fast, ease: EASING.exit }
  }
};

// Stagger container for lists
export const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1,
    }
  }
};

// Child item for stagger animations
export const staggerItem = {
  hidden: { opacity: 0, y: 15 },
  visible: { 
    opacity: 1, 
    y: 0,
    transition: { duration: TIMING.medium, ease: EASING.entrance }
  }
};

// Chat message variants with index-based stagger
export const chatMessageVariants = (index: number = 0) => ({
  hidden: { opacity: 0, y: 20, scale: 0.98 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      duration: TIMING.medium,
      ease: EASING.interactive,
      delay: index * 0.05,
    }
  }
});

// Interactive button variants
export const buttonVariants = {
  idle: { scale: 1 },
  hover: { 
    scale: 1.02, 
    y: -2,
    transition: { ...SPRING.snappy }
  },
  tap: { 
    scale: 0.95,
    transition: { ...SPRING.snappy }
  },
  disabled: { 
    opacity: 0.5,
    scale: 1
  }
};

// Modal/dialog variants
export const modalVariants = {
  hidden: { 
    opacity: 0, 
    scale: 0.95,
    y: 20
  },
  visible: { 
    opacity: 1, 
    scale: 1,
    y: 0,
    transition: { 
      duration: TIMING.medium,
      ease: EASING.entrance
    }
  },
  exit: { 
    opacity: 0, 
    scale: 0.95,
    y: 10,
    transition: { 
      duration: TIMING.fast,
      ease: EASING.exit
    }
  }
};

// Overlay backdrop variants
export const overlayVariants = {
  hidden: { opacity: 0 },
  visible: { 
    opacity: 1,
    transition: { duration: TIMING.fast }
  },
  exit: { 
    opacity: 0,
    transition: { duration: TIMING.fast }
  }
};

// Typing indicator dots
export const typingDotVariants = {
  animate: {
    y: [0, -6, 0],
    transition: {
      duration: 0.6,
      repeat: Infinity,
      ease: 'easeInOut'
    }
  }
};

// Pulse animation for notifications/badges
export const pulseVariants = {
  animate: {
    scale: [1, 1.05, 1],
    opacity: [1, 0.8, 1],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: 'easeInOut'
    }
  }
};

// Shimmer loading animation
export const shimmerVariants = {
  animate: {
    backgroundPosition: ['200% 0', '-200% 0'],
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: 'linear'
    }
  }
};

// Sidebar variants
export const sidebarVariants = {
  hidden: { x: -280, opacity: 0 },
  visible: { 
    x: 0, 
    opacity: 1,
    transition: { ...SPRING.smooth }
  },
  exit: { 
    x: -280, 
    opacity: 0,
    transition: { duration: TIMING.fast, ease: EASING.exit }
  }
};

// Source citation expand/collapse
export const expandVariants = {
  hidden: { 
    opacity: 0, 
    height: 0,
    transition: { duration: TIMING.fast }
  },
  visible: { 
    opacity: 1, 
    height: 'auto',
    transition: { duration: TIMING.medium, ease: EASING.entrance }
  }
};

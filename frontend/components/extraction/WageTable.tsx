'use client';

import { motion } from 'framer-motion';
import { WageEntry } from '@/types/extraction';
import { ANIMATION, EASING } from '@/lib/constants';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Download, DollarSign } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface WageTableProps {
  entries: WageEntry[];
  onExport?: () => void;
}

const tableVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
    },
  },
};

const rowVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: {
    opacity: 1,
    x: 0,
    transition: {
      duration: ANIMATION.duration.fast,
      ease: EASING.easeOut,
    },
  },
};

function formatCurrency(value: number | undefined): string {
  if (value === undefined || value === null) return '-';
  if (isNaN(value)) return '-';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
  }).format(value);
}

export function WageTable({ entries, onExport }: WageTableProps) {
  if (!entries || entries.length === 0) {
    return (
      <Card className="bg-card/50 backdrop-blur">
        <CardContent className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <DollarSign className="h-12 w-12 mb-4 opacity-50" />
          <p>No wage entries found</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card/50 backdrop-blur">
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <DollarSign className="h-5 w-5 text-green-500" />
          <CardTitle className="text-lg">Prevailing Wages</CardTitle>
          <Badge variant="secondary">{entries.length} classifications</Badge>
        </div>
        {onExport && (
          <Button variant="outline" size="sm" onClick={onExport}>
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
        )}
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <motion.table
            className="w-full text-sm"
            variants={tableVariants}
            initial="hidden"
            animate="visible"
          >
            <thead>
              <tr className="border-b border-border/50">
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">Classification</th>
                <th className="text-right py-3 px-4 font-medium text-muted-foreground">Base Rate</th>
                <th className="text-right py-3 px-4 font-medium text-muted-foreground">Fringe</th>
                <th className="text-right py-3 px-4 font-medium text-muted-foreground">Total</th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">Effective Date</th>
              </tr>
            </thead>
            <motion.tbody>
              {entries.map((entry, index) => (
                <motion.tr
                  key={entry.classification || index}
                  variants={rowVariants}
                  className="border-b border-border/30 hover:bg-accent/50 transition-colors"
                >
                  <td className="py-3 px-4 font-medium">{entry.classification}</td>
                  <td className="py-3 px-4 text-right font-mono text-green-400">
                    {formatCurrency(entry.base_rate)}
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-blue-400">
                    {formatCurrency(entry.fringe_benefits)}
                  </td>
                  <td className="py-3 px-4 text-right font-mono font-bold text-primary">
                    {formatCurrency(entry.total_rate)}
                  </td>
                  <td className="py-3 px-4 text-muted-foreground">
                    {entry.effective_date || '-'}
                  </td>
                </motion.tr>
              ))}
            </motion.tbody>
          </motion.table>
        </div>
      </CardContent>
    </Card>
  );
}

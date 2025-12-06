'use client';

import { motion } from 'framer-motion';
import { DoorScheduleEntry } from '@/types/extraction';
import { ANIMATION, EASING } from '@/lib/constants';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Download, DoorOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface DoorScheduleTableProps {
  entries: DoorScheduleEntry[];
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

function formatSize(width?: number, height?: number): string {
  if (!width && !height) return '-';
  return `${width || '?'} × ${height || '?'} mm`;
}

export function DoorScheduleTable({ entries, onExport }: DoorScheduleTableProps) {
  if (!entries || entries.length === 0) {
    return (
      <Card className="bg-card/50 backdrop-blur">
        <CardContent className="flex flex-col items-center justify-center py-12 text-muted-foreground">
          <DoorOpen className="h-12 w-12 mb-4 opacity-50" />
          <p>No door schedule entries found</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card/50 backdrop-blur">
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <DoorOpen className="h-5 w-5 text-primary" />
          <CardTitle className="text-lg">Door Schedule</CardTitle>
          <Badge variant="secondary">{entries.length} entries</Badge>
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
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">Mark</th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">Location</th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">Size (W×H)</th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">Material</th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">Hardware Set</th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">Fire Rating</th>
                <th className="text-left py-3 px-4 font-medium text-muted-foreground">Notes</th>
              </tr>
            </thead>
            <motion.tbody>
              {entries.map((entry, index) => (
                <motion.tr
                  key={entry.mark || index}
                  variants={rowVariants}
                  className="border-b border-border/30 hover:bg-accent/50 transition-colors"
                >
                  <td className="py-3 px-4 font-mono text-primary">{entry.mark}</td>
                  <td className="py-3 px-4">{entry.location || '-'}</td>
                  <td className="py-3 px-4 font-mono">{formatSize(entry.width_mm, entry.height_mm)}</td>
                  <td className="py-3 px-4">{entry.material || '-'}</td>
                  <td className="py-3 px-4 max-w-[200px] truncate" title={entry.hardware_set ?? undefined}>
                    {entry.hardware_set || '-'}
                  </td>
                  <td className="py-3 px-4">
                    {entry.fire_rating ? (
                      <Badge variant="destructive" className="font-mono">
                        {entry.fire_rating}
                      </Badge>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td className="py-3 px-4 max-w-[150px] truncate text-muted-foreground" title={entry.notes ?? undefined}>
                    {entry.notes || '-'}
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

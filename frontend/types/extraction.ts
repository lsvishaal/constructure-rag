// Extraction Types for Door Schedules and Wage Tables

export interface DoorScheduleEntry {
  mark: string;
  location: string;
  width_mm: number;
  height_mm: number;
  fire_rating: string;
  material: string;
  hardware_set?: string | null;
  notes?: string | null;
}

export interface WageEntry {
  classification: string;
  base_rate: number;
  fringe_benefits: number;
  total_rate: number;
  effective_date?: string | null;
}

export interface ExtractionResult<T> {
  data: T[];
  sources: string[];
  extraction_type: 'door_schedule' | 'wage_table' | 'custom';
  confidence: number;
  raw_text?: string;
}

export type DoorScheduleResult = ExtractionResult<DoorScheduleEntry>;
export type WageTableResult = ExtractionResult<WageEntry>;

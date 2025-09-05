export type SelectionItem = {
  code: string;
  group?: string | number;
  source: string;
};

export type Selection = {
  master_year?: string;
  parcours?: string;
  items: SelectionItem[];
  calendar_name?: string;
};

export type Bundle = {
  master_year: string;
  parcours: string;
  courses: Array<{
    name: string;
    code: string;
    special?: boolean;
    groups: string[];
    variants: Array<{
      group?: string;
      type?: string;
      events: Array<{
        uid: string;
        summary: string;
        location?: string;
        start: string;
        end: string;
        rrule?: string;
        exdates?: string[];
        recurrence_id?: string;
      }>;
    }>;
  }>;
};

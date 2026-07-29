import { z } from 'zod';

export const departmentSchema = z.object({
  code: z.string().min(2, 'Department Code must be at least 2 characters.').max(20, 'Department Code must be at most 20 characters.'),
  name: z.string().min(2, 'Department Name must be at least 2 characters.').max(150),
  description: z.string().max(255).optional().or(z.literal('')),
});
export type DepartmentFormData = z.infer<typeof departmentSchema>;

export const academicYearSchema = z
  .object({
    name: z
      .string()
      .min(4, 'Academic Year Code must be at least 4 characters.')
      .max(50, 'Academic Year Code must be at most 50 characters.'),
    start_date: z.string().min(1, 'Start date is required.'),
    end_date: z.string().min(1, 'End date is required.'),
    is_current: z.boolean(),
  })
  .refine((data) => !data.start_date || !data.end_date || data.end_date > data.start_date, {
    message: 'End date must be after the start date.',
    path: ['end_date'],
  });
export type AcademicYearFormData = z.infer<typeof academicYearSchema>;

export const STUDY_YEARS = [1, 2, 3, 4] as const;
export const STUDY_YEAR_LABELS: Record<number, string> = {
  1: 'First Year',
  2: 'Second Year',
  3: 'Third Year',
  4: 'Fourth Year',
};

export const sectionSchema = z.object({
  department_id: z.string().min(1, 'Please select a department.'),
  year: z.coerce
    .number({ message: 'Please select a study year.' })
    .int()
    .min(1, 'Please select a study year.')
    .max(4, 'Please select a study year.'),
  name: z
    .string()
    .min(1, 'Section Name is required.')
    .max(20, 'Section Name must be at most 20 characters.')
    .regex(/^[A-Za-z0-9-]+$/, 'Use letters, numbers, or hyphens only.'),
  batch_year: z.coerce
    .number()
    .int()
    .min(2000, 'Batch Year must be 2000 or later.')
    .max(2100, 'Batch Year must be 2100 or earlier.'),
});
export type SectionFormData = z.infer<typeof sectionSchema>;

export const subjectSchema = z.object({
  department_id: z.string().min(1, 'Please select a department.'),
  code: z.string().min(2, 'Course Code must be at least 2 characters.').max(20),
  name: z.string().min(2, 'Subject Title must be at least 2 characters.').max(150),
  credits: z.coerce.number().int().min(1, 'Credits must be at least 1.').max(10, 'Credits must be at most 10.'),
  max_mid_marks: z.coerce.number().min(0, 'Must be 0 or greater.'),
  max_internal_marks: z.coerce.number().min(0, 'Must be 0 or greater.'),
  max_external_marks: z.coerce.number().min(0, 'Must be 0 or greater.'),
});
export type SubjectFormData = z.infer<typeof subjectSchema>;

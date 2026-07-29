import { z } from 'zod';

export const ASSIGNABLE_ROLES = ['HOD', 'COUNSELLOR', 'FACULTY', 'STUDENT'] as const;

export const createUserSchema = z
  .object({
    first_name: z.string().min(2, 'First Name must be at least 2 characters.').max(100),
    last_name: z.string().min(2, 'Last Name must be at least 2 characters.').max(100),
    email: z.string().min(1, 'Email is required.').email('Please enter a valid email address.'),
    phone: z.string().optional().or(z.literal('')),
    role: z.enum(ASSIGNABLE_ROLES),
    department_id: z.string().optional().or(z.literal('')),
    password: z.string().optional().or(z.literal('')),
    roll_number: z.string().optional().or(z.literal('')),
    registration_number: z.string().optional().or(z.literal('')),
    date_of_birth: z.string().optional().or(z.literal('')),
    batch_year: z.coerce.number().optional(),
    section_id: z.string().optional().or(z.literal('')),
    semester_id: z.string().optional().or(z.literal('')),
  })
  .superRefine((data, ctx) => {
    if (data.role === 'STUDENT') {
      if (!data.department_id) {
        ctx.addIssue({ path: ['department_id'], code: z.ZodIssueCode.custom, message: 'Department is required for students.' });
      }
      if (!data.roll_number) {
        ctx.addIssue({ path: ['roll_number'], code: z.ZodIssueCode.custom, message: 'Roll Number is required.' });
      }
      if (!data.registration_number) {
        ctx.addIssue({ path: ['registration_number'], code: z.ZodIssueCode.custom, message: 'Registration Number is required.' });
      }
      if (!data.date_of_birth) {
        ctx.addIssue({ path: ['date_of_birth'], code: z.ZodIssueCode.custom, message: 'Date of Birth is required.' });
      }
      if (!data.batch_year) {
        ctx.addIssue({ path: ['batch_year'], code: z.ZodIssueCode.custom, message: 'Batch Year is required.' });
      }
      if (!data.section_id) {
        ctx.addIssue({ path: ['section_id'], code: z.ZodIssueCode.custom, message: 'Please select a section.' });
      }
      if (!data.semester_id) {
        ctx.addIssue({ path: ['semester_id'], code: z.ZodIssueCode.custom, message: 'Please select a semester.' });
      }
    }
    if (data.password && data.password.length > 0 && data.password.length < 6) {
      ctx.addIssue({ path: ['password'], code: z.ZodIssueCode.custom, message: 'Password must be at least 6 characters.' });
    }
  });

export type CreateUserFormData = z.infer<typeof createUserSchema>;

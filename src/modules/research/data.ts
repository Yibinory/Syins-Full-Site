export type ResearchStatus = 'Planning' | 'Active' | 'Completed' | 'Paused'
export interface ResearchProject { id: number; number: string; title: string; subtitle: string; question: string; summary: string; status: ResearchStatus; period: string; area: string; keywords: string[]; image: string; featured: boolean }

export const researchAreas = [
  { title: 'Medical Image Analysis', summary: 'Learning clinically meaningful structure from complex, imperfect imaging data.' },
  { title: 'Medical Image Generation', summary: 'Generating anatomically faithful images for simulation, augmentation, and prediction.' },
  { title: 'Domain Generalization', summary: 'Building models that remain useful beyond the data distribution where they were trained.' },
]

export const researchProjects: ResearchProject[] = [
  { id: 1, number: '01', title: 'Longitudinal Medical Image Generation', subtitle: 'Patient-specific futures from sparse observations', question: 'Can a model predict change while preserving the identity and anatomy of a patient?', summary: 'A generative framework for temporally coherent follow-up synthesis with calibrated uncertainty across irregular clinical timepoints.', status: 'Active', period: '2026 — Present', area: 'Medical Image Generation', keywords: ['Longitudinal', 'MRI', 'Diffusion'], image: '/images/longitudinal-mri-mock.png', featured: true },
  { id: 2, number: '02', title: 'Anatomy-invariant representations', subtitle: 'Generalizing across unseen clinical domains', question: 'Which features remain reliable when scanner, protocol, and population all shift?', summary: 'Separating anatomical content from acquisition-specific appearance for robust medical segmentation.', status: 'Active', period: '2025 — Present', area: 'Domain Generalization', keywords: ['Segmentation', 'OOD', 'Representation'], image: '', featured: true },
  { id: 3, number: '03', title: 'Controllable pathology synthesis', subtitle: 'Changing disease, preserving everything else', question: 'How can generative controls correspond to clinical concepts instead of visual shortcuts?', summary: 'Structured generation for localized pathology edits with explicit anatomy preservation.', status: 'Planning', period: '2026 —', area: 'Medical Image Generation', keywords: ['Control', 'Pathology', 'CT'], image: '', featured: false },
]

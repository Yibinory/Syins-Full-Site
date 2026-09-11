export type PublicationType = 'Conference' | 'Journal' | 'Preprint'
export interface Publication { id: number; title: string; authors: string; venue: string; venueShort: string; year: number; type: PublicationType; tags: string[]; featured: boolean; image?: string }
export const publications: Publication[] = [
  { id: 1, title: 'Anatomy-Preserving Generative Priors for Cross-Domain Medical Segmentation', authors: 'Syins Yibinory, Yiming Chen, Ming Li', venue: 'European Conference on Computer Vision', venueShort: 'ECCV', year: 2026, type: 'Conference', tags: ['Domain Generalization', 'Segmentation'], featured: true, image: '/images/longitudinal-mri-mock.png' },
  { id: 2, title: 'Temporal Anatomy as a Prior for Longitudinal MR Image Synthesis', authors: 'Syins Yibinory, Jiawen Wu, Rui Zhang', venue: 'Medical Image Computing and Computer Assisted Intervention', venueShort: 'MICCAI', year: 2025, type: 'Conference', tags: ['Generation', 'Longitudinal MRI'], featured: true },
  { id: 3, title: 'Uncertainty-aware Harmonization under Unseen Acquisition Shifts', authors: 'Syins Yibinory, Lin Zhou, Ming Li', venue: 'IEEE Transactions on Medical Imaging', venueShort: 'TMI', year: 2025, type: 'Journal', tags: ['Harmonization', 'Uncertainty'], featured: false },
  { id: 4, title: 'Counterfactual Pathology Editing with Spatially Grounded Diffusion', authors: 'Syins Yibinory, Yiming Chen', venue: 'arXiv preprint', venueShort: 'arXiv', year: 2024, type: 'Preprint', tags: ['Diffusion', 'Counterfactual'], featured: false },
]

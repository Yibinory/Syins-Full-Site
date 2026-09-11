export type NoteKind = 'Research Note' | 'Essay' | 'Guide' | 'Reference'

export interface PublicNote {
  id: number
  slug: string
  title: string
  summary: string
  excerpt: string
  kind: NoteKind
  publishedAt: string
  displayDate: string
  readingTime: string
  tags: string[]
  featured: boolean
}


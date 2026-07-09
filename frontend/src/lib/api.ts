import { http } from './http'

export interface Thread {
  id: string
  title: string
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  thread_id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
  citations?: any[]
  metadata_json?: {
    confidence_summary?: string
    has_sufficient_evidence?: boolean
    [key: string]: any
  }
}


export interface SourceDocument {
  id: string
  filename: string
  file_size: number
  mime_type: string
  created_at: string
}

export const api = {
  threads: {
    list: () => http.get<Thread[]>('/threads'),
    create: (title: string) => http.post<Thread>('/threads', { title }),
    update: (id: string, title: string) => http.patch<Thread>(`/threads/${id}`, { title }),
    delete: (id: string) => http.delete<void>(`/threads/${id}`),
  },
  messages: {
    list: (threadId: string) => http.get<Message[]>(`/threads/${threadId}/messages`),
  },
  documents: {
    list: () => http.get<SourceDocument[]>('/documents'),
    upload: (formData: FormData) => http.post<SourceDocument>('/documents', formData),
    delete: (id: string) => http.delete<void>(`/documents/${id}`),
  },
}

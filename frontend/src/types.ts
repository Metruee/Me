export interface Expert {
  id: string
  key: string
  name: string
  title: string
  emoji: string
  color: string
  domain: string
  summon: string
  response: string
  system_prompt?: string
}

export interface Message {
  type: 'user' | 'expert' | 'system'
  content: string
  expertId?: string
  expertName?: string
  archived?: boolean
  timestamp: number
}

export interface Metadata {
  file_name: string;
  year?: number;
  content?: string;
}

export interface Message {
  content: string;
  sender: "user" | "bot";
  metadata?: Metadata[];
  has_error?: boolean;
}
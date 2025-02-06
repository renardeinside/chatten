export interface Metadata {
  file_name: string;
  year: number | null;
  chunk_num: number;
  char_length: number;
  content?: string;
}

export interface Message {
  content: string;
  sender: "user" | "bot";
  metadata?: Metadata[];
  has_error?: boolean;
}
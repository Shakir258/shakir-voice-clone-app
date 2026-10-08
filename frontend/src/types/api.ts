export interface ModelStatus {
  status: "not_started" | "loading" | "ready" | "error";
  device: string;
  detail: string | null;
}

export interface ApiErrorBody {
  detail?: string;
  error?: string;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

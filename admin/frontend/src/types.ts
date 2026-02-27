export type User = {
  id: number;
  username: string | null;
  first_name?: string | null;
  last_name?: string | null;
  user_type: "horeca" | "retail" | "all";
  establishment: string;
  is_active?: boolean;
  registered_at?: string;
  last_activity?: string | null;
};

export type ContentItem = {
  id: number;
  title: string;
  description: string;
  image_url?: string | null;
  user_type: "horeca" | "retail" | "all";
  published_at?: string | null;
  is_active: boolean;
};

export type DashboardStats = {
  total: number;
  horeca: number;
  retail: number;
  active_content: number;
  total_mailings: number;
  new_today?: number;
  new_week?: number;
  new_month?: number;
  mailings_month?: number;
  active_promotions?: number;
  active_news?: number;
  active_deliveries?: number;
};

export type GenericResp = { message: string; data?: Record<string, unknown> };
export type GenericDataResponse = { message: string; data: Record<string, unknown> };
export type LogsResponse = {
  message: string;
  data: { items: Array<{ id: number; action: string; details?: string; admin_id?: number; created_at: string }> };
};
export type SettingsResponse = { message: string; data: Record<string, string> };
export type BackupsResponse = { message: string; data: { files: string[] } };

export type Mailing = {
  id: number;
  text: string;
  media_url: string | null;
  media_type: "photo" | "video" | "none";
  target_type: "all" | "horeca" | "retail" | "custom";
  custom_targets: number[] | null;
  scheduled_at: string | null;
  sent_at: string | null;
  status: "draft" | "scheduled" | "sent" | "cancelled";
  send_attempts?: number;
  last_error?: string | null;
};

export type MailingStats = {
  sent: number;
  opened: number;
  clicked: number;
  open_rate: number;
  ctr: number;
};

export type ContentKind = "promotions" | "news" | "deliveries";

export type AdminAccount = {
  id: number;
  username: string;
  role: "superadmin" | "admin" | "manager";
  is_active: boolean;
  last_login?: string | null;
};

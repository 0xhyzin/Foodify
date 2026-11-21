import type { AppNotification, NotificationPage } from "./models";

export interface NotificationRepository {
  list(
    options?: { unreadOnly?: boolean; offset?: number; limit?: number },
    signal?: AbortSignal,
  ): Promise<NotificationPage>;
  markRead(notificationId: string): Promise<AppNotification>;
  markAllRead(): Promise<number>;
}

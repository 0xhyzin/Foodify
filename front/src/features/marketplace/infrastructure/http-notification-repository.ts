import type { HttpClient } from "@/infrastructure/http/contracts";
import type { NotificationRepository } from "../domain/notification-repository";
import type { Envelope, NotificationDto, PaginationDto } from "./dto";
import { notificationFromDto } from "./mappers";

export class HttpNotificationRepository implements NotificationRepository {
  constructor(private readonly client: HttpClient) {}

  async list(
    options: { unreadOnly?: boolean; offset?: number; limit?: number } = {},
    signal?: AbortSignal,
  ) {
    const query = new URLSearchParams({
      limit: String(options.limit ?? 20),
      offset: String(options.offset ?? 0),
    });
    if (options.unreadOnly) query.set("unread_only", "true");
    const result = await this.client.request<
      Envelope<{
        notifications: NotificationDto[];
        unread_count: number;
        pagination: PaginationDto;
      }>
    >(`/notifications?${query}`, { signal });
    return {
      items: result.data.notifications.map(notificationFromDto),
      unreadCount: result.data.unread_count,
      hasMore: result.data.pagination.has_more,
    };
  }

  async markRead(notificationId: string) {
    const result = await this.client.request<
      Envelope<{ notification: NotificationDto }>
    >(`/notifications/${encodeURIComponent(notificationId)}/read`, {
      method: "PATCH",
    });
    return notificationFromDto(result.data.notification);
  }

  async markAllRead() {
    const result = await this.client.request<
      Envelope<{ updated_count: number }>
    >("/notifications/read-all", {
      method: "POST",
    });
    return result.data.updated_count;
  }
}

import { Injectable, Logger } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';
import { RateLimitService } from './rate-limit.service';
import { NotificationChannel, NotificationStatus } from './enums/notification.enums';
import { QueryNotificationsDto } from './dto/query-notifications.dto';

@Injectable()
export class NotificationService {
  private readonly logger = new Logger(NotificationService.name);

  constructor(
    private readonly prisma: PrismaService,
    private readonly rateLimitService: RateLimitService,
  ) {}

  /**
   * Create notifications from an alert event
   * Determines which channels to use based on alert severity
   */
  async createFromAlert(alertEvent: any): Promise<void> {
    this.logger.log('Processing alert for notifications', {
      eventId: alertEvent.event_id,
      patientId: alertEvent.patient_id,
      alertType: alertEvent.alert_type,
      severity: alertEvent.severity,
    });

    // Check rate limiting
    const isRateLimited = await this.rateLimitService.isRateLimited(alertEvent.patient_id);
    if (isRateLimited) {
      this.logger.warn('Rate limit exceeded for patient', {
        patientId: alertEvent.patient_id,
        eventId: alertEvent.event_id,
      });
      // Still create notification but mark it as failed due to rate limit
      await this.createNotification({
        patientId: alertEvent.patient_id,
        alertId: alertEvent.event_id,
        channel: NotificationChannel.EMAIL, // Default channel
        message: this.buildNotificationMessage(alertEvent),
        subject: this.buildNotificationSubject(alertEvent),
        metadata: alertEvent,
        status: NotificationStatus.FAILED,
      });
      return;
    }

    // Determine channels based on severity
    const channels = this.determineChannels(alertEvent.severity);
    
    const message = this.buildNotificationMessage(alertEvent);
    const subject = this.buildNotificationSubject(alertEvent);

    // Create notifications for each channel
    const notifications = await Promise.all(
      channels.map((channel) =>
        this.createNotification({
          patientId: alertEvent.patient_id,
          alertId: alertEvent.event_id,
          channel,
          message,
          subject,
          metadata: alertEvent,
          status: NotificationStatus.PENDING,
        }),
      ),
    );

    // Simulate sending notifications (in a real implementation, this would call actual providers)
    await Promise.all(
      notifications.map((notification) => this.sendNotification(notification.id, notification.channel)),
    );

    this.logger.log('Created notifications from alert', {
      eventId: alertEvent.event_id,
      patientId: alertEvent.patient_id,
      notificationCount: notifications.length,
    });
  }

  private determineChannels(severity: string): NotificationChannel[] {
    const normalizedSeverity = severity?.toLowerCase();
    
    switch (normalizedSeverity) {
      case 'critical':
        return [NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.PUSH];
      case 'high':
        return [NotificationChannel.EMAIL, NotificationChannel.PUSH];
      case 'medium':
        return [NotificationChannel.EMAIL];
      case 'low':
        return [NotificationChannel.EMAIL];
      default:
        return [NotificationChannel.EMAIL];
    }
  }

  private buildNotificationSubject(alertEvent: any): string {
    const severity = alertEvent.severity?.toUpperCase() || 'UNKNOWN';
    const alertType = alertEvent.alert_type?.replace(/_/g, ' ').toUpperCase() || 'ALERT';
    return `[${severity}] ${alertType} - Patient ${alertEvent.patient_id}`;
  }

  private buildNotificationMessage(alertEvent: any): string {
    const condition = alertEvent.condition;
    const description = condition?.description || 'An alert has been raised';
    const vitalSign = condition?.vital_sign || '';
    const currentValue = condition?.current_value;
    
    let message = `Alert Notification\n\n`;
    message += `Patient ID: ${alertEvent.patient_id}\n`;
    message += `Alert Type: ${alertEvent.alert_type}\n`;
    message += `Severity: ${alertEvent.severity}\n`;
    message += `Description: ${description}\n`;

    if (vitalSign) {
      message += `Vital Sign: ${vitalSign}\n`;
    }

    if (currentValue) {
      const valueStr = typeof currentValue === 'object' 
        ? `${currentValue.value} ${currentValue.unit || ''}`
        : String(currentValue);
      message += `Current Value: ${valueStr}\n`;
    }

    if (alertEvent.recommended_actions && alertEvent.recommended_actions.length > 0) {
      message += `\nRecommended Actions:\n`;
      alertEvent.recommended_actions.forEach((action: any, index: number) => {
        message += `${index + 1}. ${action.action}\n`;
      });
    }

    message += `\nTimestamp: ${alertEvent.timestamp}`;

    return message;
  }

  private async createNotification(data: {
    patientId: string;
    alertId?: string;
    channel: NotificationChannel;
    message: string;
    subject?: string;
    metadata?: any;
    status: NotificationStatus;
  }) {
    return this.prisma.notification.create({
      data: {
        patientId: data.patientId,
        alertId: data.alertId,
        channel: data.channel,
        message: data.message,
        subject: data.subject,
        metadata: data.metadata || {},
        status: data.status,
      },
    });
  }

  /**
   * Simulate sending notification via the specified channel
   * In production, this would integrate with actual email/SMS/push notification providers
   */
  private async sendNotification(notificationId: string, channel: NotificationChannel): Promise<void> {
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 100));

    try {
      // Simulate sending (always succeeds in this simulation)
      const simulatedSuccess = Math.random() > 0.05; // 95% success rate

      if (simulatedSuccess) {
        await this.prisma.notification.update({
          where: { id: notificationId },
          data: {
            status: NotificationStatus.SENT,
            sentAt: new Date(),
          },
        });

        this.logger.debug(`Notification sent via ${channel}`, {
          notificationId,
          channel,
        });
      } else {
        // Simulate failure
        await this.prisma.notification.update({
          where: { id: notificationId },
          data: {
            status: NotificationStatus.FAILED,
          },
        });

        this.logger.warn(`Notification failed to send via ${channel}`, {
          notificationId,
          channel,
        });
      }
    } catch (error) {
      this.logger.error('Error updating notification status', {
        notificationId,
        channel,
        error: error instanceof Error ? error.message : String(error),
      });

      // Update status to failed
      try {
        await this.prisma.notification.update({
          where: { id: notificationId },
          data: {
            status: NotificationStatus.FAILED,
          },
        });
      } catch (updateError) {
        this.logger.error('Failed to update notification status to FAILED', updateError);
      }
    }
  }

  async findAll(query: QueryNotificationsDto) {
    const page = query.page || 1;
    const limit = Math.min(query.limit || 20, 100); // Max 100 per page
    const skip = (page - 1) * limit;

    const where: any = {};
    if (query.patientId) {
      where.patientId = query.patientId;
    }
    if (query.channel) {
      where.channel = query.channel;
    }
    if (query.status) {
      where.status = query.status;
    }

    const [notifications, total] = await Promise.all([
      this.prisma.notification.findMany({
        where,
        skip,
        take: limit,
        orderBy: {
          createdAt: 'desc',
        },
      }),
      this.prisma.notification.count({ where }),
    ]);

    return {
      data: notifications,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  async findOne(id: string) {
    return this.prisma.notification.findUnique({
      where: { id },
    });
  }
}


import { Injectable, OnModuleInit, OnModuleDestroy, Logger } from '@nestjs/common';
import Redis from 'ioredis';
import { ConfigService } from '../config/config.service';

@Injectable()
export class RateLimitService implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(RateLimitService.name);
  private redis?: Redis;
  private inMemoryStore: Map<string, { count: number; resetAt: number }> = new Map();

  constructor(private readonly configService: ConfigService) {}

  async onModuleInit() {
    if (this.configService.redisEnabled) {
      try {
        const redisOptions: any = {
          host: this.configService.redisHost,
          port: this.configService.redisPort,
          retryStrategy: (times: number) => {
            const delay = Math.min(times * 50, 2000);
            return delay;
          },
          maxRetriesPerRequest: 3,
        };

        if (this.configService.redisPassword) {
          redisOptions.password = this.configService.redisPassword;
        }

        this.redis = new Redis(redisOptions);

        this.redis.on('connect', () => {
          this.logger.log('Connected to Redis');
        });

        this.redis.on('error', (error) => {
          this.logger.warn('Redis connection error, falling back to in-memory store', {
            error: error.message,
          });
          // Fallback to in-memory store
          this.redis = undefined;
        });

        // Test connection
        await this.redis.ping();
        this.logger.log('Successfully connected to Redis');
      } catch (error) {
        this.logger.warn('Failed to connect to Redis, using in-memory store', {
          error: error instanceof Error ? error.message : String(error),
        });
        this.redis = undefined;
      }
    } else {
      this.logger.log('Redis disabled, using in-memory store for rate limiting');
    }
  }

  async onModuleDestroy() {
    if (this.redis) {
      await this.redis.quit();
      this.logger.log('Disconnected from Redis');
    }
  }

  /**
   * Check if a patient has exceeded the rate limit
   * @param patientId Patient ID
   * @returns true if rate limit is exceeded, false otherwise
   */
  async isRateLimited(patientId: string): Promise<boolean> {
    const windowMs = this.configService.rateLimitWindowMs;
    const maxNotifications = this.configService.rateLimitMaxNotifications;
    const key = `rate_limit:notification:${patientId}`;
    const now = Date.now();

    if (this.redis) {
      try {
        const count = await this.redis.incr(key);
        
        if (count === 1) {
          // First request in the window, set expiry
          await this.redis.pexpire(key, windowMs);
        }

        return count > maxNotifications;
      } catch (error) {
        this.logger.warn('Redis error, falling back to in-memory store', {
          error: error instanceof Error ? error.message : String(error),
        });
        // Fallback to in-memory
        return this.isRateLimitedInMemory(patientId);
      }
    }

    return this.isRateLimitedInMemory(patientId);
  }

  private isRateLimitedInMemory(patientId: string): boolean {
    const windowMs = this.configService.rateLimitWindowMs;
    const maxNotifications = this.configService.rateLimitMaxNotifications;
    const now = Date.now();
    const entry = this.inMemoryStore.get(patientId);

    if (!entry || entry.resetAt < now) {
      // No entry or window expired, create new entry
      this.inMemoryStore.set(patientId, {
        count: 1,
        resetAt: now + windowMs,
      });
      // Cleanup expired entries periodically
      this.cleanupInMemoryStore();
      return false;
    }

    // Increment count
    entry.count++;
    return entry.count > maxNotifications;
  }

  private cleanupInMemoryStore() {
    const now = Date.now();
    for (const [key, value] of this.inMemoryStore.entries()) {
      if (value.resetAt < now) {
        this.inMemoryStore.delete(key);
      }
    }
  }

  /**
   * Reset rate limit for a patient (useful for testing or manual override)
   */
  async resetRateLimit(patientId: string): Promise<void> {
    const key = `rate_limit:notification:${patientId}`;

    if (this.redis) {
      try {
        await this.redis.del(key);
      } catch (error) {
        this.logger.warn('Failed to reset rate limit in Redis', {
          error: error instanceof Error ? error.message : String(error),
        });
      }
    }

    this.inMemoryStore.delete(patientId);
  }
}


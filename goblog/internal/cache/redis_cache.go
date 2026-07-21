package cache

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"time"

	"github.com/redis/go-redis/v9"
)

type RedisCache struct {
	client *redis.Client
}

func NewRedisCache(client *redis.Client) *RedisCache {
	return &RedisCache{client: client}
}

func (c *RedisCache) IsAvailable() bool {
	return c.client != nil
}

func (c *RedisCache) Get(ctx context.Context, key string, dest interface{}) bool {
	if c.client == nil {
		return false
	}
	data, err := c.client.Get(ctx, key).Bytes()
	if err != nil {
		return false
	}
	if err := json.Unmarshal(data, dest); err != nil {
		slog.Warn("cache unmarshal failed", "key", key, "error", err)
		return false
	}
	return true
}

func (c *RedisCache) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) {
	if c.client == nil {
		return
	}
	data, err := json.Marshal(value)
	if err != nil {
		return
	}
	c.client.Set(ctx, key, data, ttl)
}

func (c *RedisCache) Delete(ctx context.Context, keys ...string) {
	if c.client == nil || len(keys) == 0 {
		return
	}
	c.client.Del(ctx, keys...)
}

func (c *RedisCache) DeletePattern(ctx context.Context, pattern string) {
	if c.client == nil {
		return
	}
	keys, err := c.client.Keys(ctx, pattern).Result()
	if err != nil {
		return
	}
	if len(keys) > 0 {
		c.client.Del(ctx, keys...)
	}
}

// SetNXEx sets key only if it does not exist, with TTL. Returns true if set.
func (c *RedisCache) SetNXEx(ctx context.Context, key string, ttl time.Duration) bool {
	if c.client == nil {
		return false
	}
	ok, err := c.client.SetNX(ctx, key, "1", ttl).Result()
	if err != nil {
		return false
	}
	return ok
}

func (c *RedisCache) ViewDedupKey(articleID uint, clientIP string) string {
	return fmt.Sprintf("view:%d:%s", articleID, clientIP)
}

func (c *RedisCache) ArticleDetailKey(slug string) string {
	return fmt.Sprintf("article:slug:%s", slug)
}

func (c *RedisCache) HotArticlesKey() string {
	return "hot_articles"
}

func (c *RedisCache) CategoriesKey() string {
	return "categories:all"
}

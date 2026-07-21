package middleware

import (
	"github.com/dream/goblog/internal/cache"
	"github.com/dream/goblog/internal/pkg/errcode"
	"github.com/dream/goblog/pkg/response"
	"github.com/gin-gonic/gin"
)

// Lua script for token bucket rate limiting.
// KEYS[1] = the rate limit key, ARGV[1] = max requests, ARGV[2] = window in seconds.
const rateLimitScript = `
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])

local current = redis.call("GET", key)
if current == false then
    redis.call("SET", key, 1, "EX", window)
    return 1
end

current = tonumber(current)
if current < limit then
    redis.call("INCR", key)
    return current + 1
end

return -1
`

func RateLimiter(c *cache.RedisCache, maxReq int, windowSec int) gin.HandlerFunc {
	return func(ctx *gin.Context) {
		if !c.IsAvailable() || maxReq <= 0 {
			ctx.Next()
			return
		}

		key := "ratelimit:" + ctx.ClientIP()
		result, err := c.EvalScript(ctx.Request.Context(), rateLimitScript, []string{key}, maxReq, windowSec)
		if err != nil {
			// Redis error: allow the request
			ctx.Next()
			return
		}

		count, ok := result.(int64)
		if !ok || count < 0 {
			response.Error(ctx, errcode.ErrRateLimit)
			return
		}

		ctx.Next()
	}
}

package cache

import (
	"context"
	"crypto/sha1"
	"encoding/hex"
)

// EvalScript runs a Lua script on Redis. Uses SHA-based script caching.
func (c *RedisCache) EvalScript(ctx context.Context, script string, keys []string, args ...interface{}) (interface{}, error) {
	if c.client == nil {
		return nil, nil
	}
	sha := sha1Hash(script)
	result, err := c.client.EvalSha(ctx, sha, keys, args...).Result()
	if err != nil && isNoScript(err) {
		result, err = c.client.Eval(ctx, script, keys, args...).Result()
	}
	return result, err
}

func sha1Hash(s string) string {
	h := sha1.Sum([]byte(s))
	return hex.EncodeToString(h[:])
}

func isNoScript(err error) bool {
	return err != nil && containsNoScript(err.Error())
}

func containsNoScript(s string) bool {
	return len(s) > 0 && (s[0:12] == "NOSCRIPT No " || (len(s) >= 9 && s[0:9] == "NOSCRIPT"))
}

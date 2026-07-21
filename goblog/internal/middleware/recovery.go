package middleware

import (
	"log/slog"
	"runtime/debug"

	"github.com/dream/goblog/pkg/response"
	"github.com/gin-gonic/gin"
)

func Recovery() gin.HandlerFunc {
	return func(c *gin.Context) {
		defer func() {
			if r := recover(); r != nil {
				stack := string(debug.Stack())
				requestID, _ := c.Get("request_id")
				slog.Error("panic recovered",
					"panic", r,
					"method", c.Request.Method,
					"path", c.Request.URL.Path,
					"request_id", requestID,
					"stack", stack,
				)
				c.AbortWithStatusJSON(500, response.Response{
					Code:    50001,
					Message: "internal server error",
					Data:    nil,
				})
			}
		}()
		c.Next()
	}
}

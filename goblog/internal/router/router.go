package router

import (
	"github.com/dream/goblog/internal/cache"
	"github.com/dream/goblog/internal/config"
	"github.com/dream/goblog/internal/handler"
	"github.com/dream/goblog/internal/middleware"
	"github.com/gin-gonic/gin"
)

func Setup(
	cfg *config.Config,
	redisCache *cache.RedisCache,
	authH *handler.AuthHandler,
	articleH *handler.ArticleHandler,
	categoryH *handler.CategoryHandler,
	tagH *handler.TagHandler,
	uploadH *handler.UploadHandler,
	commentH *handler.CommentHandler,
) *gin.Engine {
	r := gin.New()

	r.Use(middleware.Recovery())
	r.Use(middleware.RequestID())
	r.Use(middleware.Logger())
	r.Use(middleware.CORS(cfg.CORS))

	if cfg.RateLimit.Enabled {
		r.Use(middleware.RateLimiter(redisCache, cfg.RateLimit.RequestsPerMinute, 60))
	}

	r.Static("/uploads", cfg.Upload.Path)

	v1 := r.Group("/api/v1")
	{
		auth := v1.Group("/auth")
		{
			auth.POST("/register", authH.Register)
			auth.POST("/login", authH.Login)
			auth.POST("/refresh", authH.Refresh)
			auth.POST("/logout", authH.Logout)
		}

		v1.GET("/articles", articleH.List)
		v1.GET("/articles/hot", articleH.HotArticles)
		v1.GET("/articles/:id", articleH.GetBySlug)
		v1.GET("/articles/:id/comments", commentH.ListByArticle)

		v1.GET("/categories", categoryH.List)
		v1.GET("/categories/:slug", categoryH.GetBySlug)
		v1.GET("/tags", tagH.List)
		v1.GET("/tags/:slug", tagH.GetBySlug)
	}

	optionalAuth := v1.Group("")
	optionalAuth.Use(middleware.Auth(cfg.JWT.Secret))
	{
		users := optionalAuth.Group("/users")
		users.Use(middleware.RequireAuth())
		{
			users.GET("/me", authH.GetProfile)
			users.PUT("/me", authH.UpdateProfile)
		}

		articles := optionalAuth.Group("/articles")
		articles.Use(middleware.RequireAuth())
		{
			articles.POST("", articleH.Create)
			articles.PUT("/:id", articleH.Update)
			articles.DELETE("/:id", articleH.Delete)
			articles.PATCH("/:id/status", articleH.UpdateStatus)
			articles.POST("/:id/cover", uploadH.UploadCover)
			articles.POST("/:id/comments", commentH.Create)
		}

		comments := optionalAuth.Group("/comments")
		comments.Use(middleware.RequireAuth())
		{
			comments.PUT("/:id", commentH.Update)
			comments.DELETE("/:id", commentH.Delete)
		}

		adminCategories := optionalAuth.Group("/categories")
		adminCategories.Use(middleware.RequireAuth(), middleware.RequireAdmin())
		{
			adminCategories.POST("", categoryH.Create)
			adminCategories.PUT("/:id", categoryH.Update)
			adminCategories.DELETE("/:id", categoryH.Delete)
		}

		adminTags := optionalAuth.Group("/tags")
		adminTags.Use(middleware.RequireAuth(), middleware.RequireAdmin())
		{
			adminTags.POST("", tagH.Create)
			adminTags.PUT("/:id", tagH.Update)
			adminTags.DELETE("/:id", tagH.Delete)
		}
	}

	return r
}

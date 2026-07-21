package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/dream/goblog/internal/cache"
	"github.com/dream/goblog/internal/config"
	"github.com/dream/goblog/internal/database"
	"github.com/dream/goblog/internal/handler"
	"github.com/dream/goblog/internal/model"
	"github.com/dream/goblog/internal/repository"
	"github.com/dream/goblog/internal/router"
	"github.com/dream/goblog/internal/service"
	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
)

func main() {
	configPath := flag.String("config", "./configs/config.yaml", "path to config file")
	flag.Parse()

	cfg, err := config.Load(*configPath)
	if err != nil {
		log.Fatalf("failed to load config: %v", err)
	}

	if cfg.Server.Mode != "release" {
		slog.SetLogLoggerLevel(slog.LevelDebug)
	}

	// database
	db, err := database.NewMySQL(cfg.Database)
	if err != nil {
		log.Fatalf("failed to connect mysql: %v", err)
	}
	if err := autoMigrate(db); err != nil {
		log.Fatalf("failed to auto-migrate: %v", err)
	}

	// redis
	rdb, err := database.NewRedis(cfg.Redis)
	if err != nil {
		slog.Warn("redis not available, caching disabled", "error", err)
		rdb = nil
	}

	// cache (nil-safe — all methods become no-ops if Redis not available)
	redisCache := cache.NewRedisCache(rdb)

	// repositories
	userRepo := repository.NewUserRepo(db)
	articleRepo := repository.NewArticleRepo(db)
	categoryRepo := repository.NewCategoryRepo(db)
	tagRepo := repository.NewTagRepo(db)
	commentRepo := repository.NewCommentRepo(db)

	// services
	authSvc := service.NewAuthService(userRepo, cfg.JWT)
	articleSvc := service.NewArticleService(articleRepo, categoryRepo, tagRepo, redisCache)
	categorySvc := service.NewCategoryService(categoryRepo, redisCache)
	tagSvc := service.NewTagService(tagRepo)
	uploadSvc := service.NewUploadService(cfg.Upload)
	commentSvc := service.NewCommentService(commentRepo, articleRepo)

	// handlers
	authH := handler.NewAuthHandler(authSvc)
	articleH := handler.NewArticleHandler(articleSvc)
	categoryH := handler.NewCategoryHandler(categorySvc)
	tagH := handler.NewTagHandler(tagSvc)
	uploadH := handler.NewUploadHandler(uploadSvc, articleSvc)
	commentH := handler.NewCommentHandler(commentSvc)

	// router
	app := router.Setup(cfg, redisCache, authH, articleH, categoryH, tagH, uploadH, commentH)
	app.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "ok"})
	})

	srv := &http.Server{
		Addr:    cfg.Server.Port,
		Handler: app,
	}

	// graceful shutdown
	go func() {
		fmt.Printf("server starting on %s\n", cfg.Server.Port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("server error: %v", err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	slog.Info("shutting down gracefully...")
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		slog.Error("server forced to shutdown", "error", err)
	}

	if rdb != nil {
		rdb.Close()
	}
	sqlDB, _ := db.DB()
	if sqlDB != nil {
		sqlDB.Close()
	}
	slog.Info("server stopped")
}

func autoMigrate(db *gorm.DB) error {
	return db.AutoMigrate(
		&model.User{},
		&model.Article{},
		&model.Category{},
		&model.Tag{},
		&model.Comment{},
		&model.RefreshToken{},
	)
}

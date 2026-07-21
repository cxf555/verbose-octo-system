package handler

import (
	"context"
	"strconv"

	"github.com/dream/goblog/internal/dto"
	"github.com/dream/goblog/internal/middleware"
	"github.com/dream/goblog/internal/pkg/errcode"
	"github.com/dream/goblog/internal/pkg/pagination"
	"github.com/dream/goblog/internal/service"
	"github.com/dream/goblog/pkg/response"
	"github.com/gin-gonic/gin"
)

type ArticleHandler struct {
	svc *service.ArticleService
}

func NewArticleHandler(svc *service.ArticleService) *ArticleHandler {
	return &ArticleHandler{svc: svc}
}

func (h *ArticleHandler) List(c *gin.Context) {
	var query dto.PaginationQuery
	if err := c.ShouldBindQuery(&query); err != nil {
		query = dto.PaginationQuery{}
	}
	query.Defaults()

	categorySlug := c.Query("category")
	tagSlug := c.Query("tag")

	items, total, appErr := h.svc.List(c.Request.Context(), query, categorySlug, tagSlug)
	if appErr != nil {
		response.Error(c, appErr)
		return
	}

	response.Paginated(c, items, pagination.New(query.Page, query.PerPage, total))
}

func (h *ArticleHandler) GetBySlug(c *gin.Context) {
	slug := c.Param("id")
	article, appErr := h.svc.GetBySlug(c.Request.Context(), slug)
	if appErr != nil {
		response.Error(c, appErr)
		return
	}

	// increment view count asynchronously with IP dedup
	clientIP := c.ClientIP()
	go func(articleID uint, ip string) {
		h.svc.IncrementView(context.Background(), articleID, ip)
	}(article.ID, clientIP)

	response.Success(c, article)
}

func (h *ArticleHandler) Create(c *gin.Context) {
	var req dto.CreateArticleRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, errcode.ErrInvalidParams)
		return
	}

	userID := middleware.GetUserID(c)
	article, appErr := h.svc.Create(c.Request.Context(), userID, req)
	if appErr != nil {
		response.Error(c, appErr)
		return
	}
	response.Created(c, article)
}

func (h *ArticleHandler) Update(c *gin.Context) {
	articleID, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil {
		response.Error(c, errcode.ErrInvalidParams)
		return
	}

	var req dto.UpdateArticleRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, errcode.ErrInvalidParams)
		return
	}

	userID := middleware.GetUserID(c)
	article, appErr := h.svc.Update(c.Request.Context(), uint(articleID), userID, req)
	if appErr != nil {
		response.Error(c, appErr)
		return
	}
	response.Success(c, article)
}

func (h *ArticleHandler) Delete(c *gin.Context) {
	articleID, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil {
		response.Error(c, errcode.ErrInvalidParams)
		return
	}

	userID := middleware.GetUserID(c)
	if appErr := h.svc.Delete(c.Request.Context(), uint(articleID), userID); appErr != nil {
		response.Error(c, appErr)
		return
	}
	response.Success(c, gin.H{"message": "deleted"})
}

func (h *ArticleHandler) UpdateStatus(c *gin.Context) {
	articleID, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil {
		response.Error(c, errcode.ErrInvalidParams)
		return
	}

	var req dto.UpdateArticleStatusRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, errcode.ErrInvalidParams)
		return
	}

	userID := middleware.GetUserID(c)
	article, appErr := h.svc.UpdateStatus(c.Request.Context(), uint(articleID), userID, req)
	if appErr != nil {
		response.Error(c, appErr)
		return
	}
	response.Success(c, article)
}

func (h *ArticleHandler) HotArticles(c *gin.Context) {
	articles, appErr := h.svc.HotArticles(c.Request.Context())
	if appErr != nil {
		response.Error(c, appErr)
		return
	}
	response.Success(c, articles)
}

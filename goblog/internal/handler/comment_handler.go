package handler

import (
	"strconv"

	"github.com/dream/goblog/internal/dto"
	"github.com/dream/goblog/internal/middleware"
	"github.com/dream/goblog/internal/pkg/errcode"
	"github.com/dream/goblog/internal/service"
	"github.com/dream/goblog/pkg/response"
	"github.com/gin-gonic/gin"
)

type CommentHandler struct {
	svc *service.CommentService
}

func NewCommentHandler(svc *service.CommentService) *CommentHandler {
	return &CommentHandler{svc: svc}
}

func (h *CommentHandler) ListByArticle(c *gin.Context) {
	slug := c.Param("id")
	comments, appErr := h.svc.ListByArticle(c.Request.Context(), slug)
	if appErr != nil {
		response.Error(c, appErr)
		return
	}
	if comments == nil {
		comments = []*dto.CommentResponse{}
	}
	response.Success(c, comments)
}

func (h *CommentHandler) Create(c *gin.Context) {
	slug := c.Param("id")
	var req dto.CreateCommentRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, errcode.ErrInvalidParams)
		return
	}

	userID := middleware.GetUserID(c)
	comment, appErr := h.svc.Create(c.Request.Context(), slug, userID, req)
	if appErr != nil {
		response.Error(c, appErr)
		return
	}
	response.Created(c, comment)
}

func (h *CommentHandler) Update(c *gin.Context) {
	commentID, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil {
		response.Error(c, errcode.ErrInvalidParams)
		return
	}

	var req dto.UpdateCommentRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, errcode.ErrInvalidParams)
		return
	}

	userID := middleware.GetUserID(c)
	comment, appErr := h.svc.Update(c.Request.Context(), uint(commentID), userID, req)
	if appErr != nil {
		response.Error(c, appErr)
		return
	}
	response.Success(c, comment)
}

func (h *CommentHandler) Delete(c *gin.Context) {
	commentID, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil {
		response.Error(c, errcode.ErrInvalidParams)
		return
	}

	userID := middleware.GetUserID(c)
	role, _ := c.Get("role")
	appErr := h.svc.Delete(c.Request.Context(), uint(commentID), userID, role.(string))
	if appErr != nil {
		response.Error(c, appErr)
		return
	}
	response.Success(c, gin.H{"message": "deleted"})
}

package handler

import (
	"strconv"

	"github.com/dream/goblog/internal/dto"
	"github.com/dream/goblog/internal/pkg/errcode"
	"github.com/dream/goblog/internal/service"
	"github.com/dream/goblog/pkg/response"
	"github.com/gin-gonic/gin"
)

type CategoryHandler struct {
	svc *service.CategoryService
}

func NewCategoryHandler(svc *service.CategoryService) *CategoryHandler {
	return &CategoryHandler{svc: svc}
}

func (h *CategoryHandler) List(c *gin.Context) {
	categories, appErr := h.svc.List(c.Request.Context())
	if appErr != nil {
		response.Error(c, appErr)
		return
	}
	response.Success(c, categories)
}

func (h *CategoryHandler) GetBySlug(c *gin.Context) {
	slug := c.Param("slug")
	category, appErr := h.svc.GetBySlug(c.Request.Context(), slug)
	if appErr != nil {
		response.Error(c, appErr)
		return
	}
	response.Success(c, category)
}

func (h *CategoryHandler) Create(c *gin.Context) {
	var req dto.CreateCategoryRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, errcode.ErrInvalidParams)
		return
	}

	category, appErr := h.svc.Create(c.Request.Context(), req)
	if appErr != nil {
		response.Error(c, appErr)
		return
	}
	response.Created(c, category)
}

func (h *CategoryHandler) Update(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil {
		response.Error(c, errcode.ErrInvalidParams)
		return
	}

	var req dto.UpdateCategoryRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, errcode.ErrInvalidParams)
		return
	}

	category, appErr := h.svc.Update(c.Request.Context(), uint(id), req)
	if appErr != nil {
		response.Error(c, appErr)
		return
	}
	response.Success(c, category)
}

func (h *CategoryHandler) Delete(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil {
		response.Error(c, errcode.ErrInvalidParams)
		return
	}

	if appErr := h.svc.Delete(c.Request.Context(), uint(id)); appErr != nil {
		response.Error(c, appErr)
		return
	}
	response.Success(c, gin.H{"message": "deleted"})
}

package handler

import (
	"strconv"

	"github.com/dream/goblog/internal/dto"
	"github.com/dream/goblog/internal/pkg/errcode"
	"github.com/dream/goblog/internal/service"
	"github.com/dream/goblog/pkg/response"
	"github.com/gin-gonic/gin"
)

type TagHandler struct {
	svc *service.TagService
}

func NewTagHandler(svc *service.TagService) *TagHandler {
	return &TagHandler{svc: svc}
}

func (h *TagHandler) List(c *gin.Context) {
	tags, appErr := h.svc.List(c.Request.Context())
	if appErr != nil {
		response.Error(c, appErr)
		return
	}
	response.Success(c, tags)
}

func (h *TagHandler) GetBySlug(c *gin.Context) {
	slug := c.Param("slug")
	tag, appErr := h.svc.GetBySlug(c.Request.Context(), slug)
	if appErr != nil {
		response.Error(c, appErr)
		return
	}
	response.Success(c, tag)
}

func (h *TagHandler) Create(c *gin.Context) {
	var req dto.CreateTagRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, errcode.ErrInvalidParams)
		return
	}

	tag, appErr := h.svc.Create(c.Request.Context(), req)
	if appErr != nil {
		response.Error(c, appErr)
		return
	}
	response.Created(c, tag)
}

func (h *TagHandler) Update(c *gin.Context) {
	id, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil {
		response.Error(c, errcode.ErrInvalidParams)
		return
	}

	var req dto.UpdateTagRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		response.Error(c, errcode.ErrInvalidParams)
		return
	}

	tag, appErr := h.svc.Update(c.Request.Context(), uint(id), req)
	if appErr != nil {
		response.Error(c, appErr)
		return
	}
	response.Success(c, tag)
}

func (h *TagHandler) Delete(c *gin.Context) {
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

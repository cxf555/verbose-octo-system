package handler

import (
	"strconv"

	"github.com/dream/goblog/internal/middleware"
	"github.com/dream/goblog/internal/pkg/errcode"
	"github.com/dream/goblog/internal/service"
	"github.com/dream/goblog/pkg/response"
	"github.com/gin-gonic/gin"
)

type UploadHandler struct {
	uploadSvc  *service.UploadService
	articleSvc *service.ArticleService
}

func NewUploadHandler(uploadSvc *service.UploadService, articleSvc *service.ArticleService) *UploadHandler {
	return &UploadHandler{uploadSvc: uploadSvc, articleSvc: articleSvc}
}

func (h *UploadHandler) UploadCover(c *gin.Context) {
	articleID, err := strconv.ParseUint(c.Param("id"), 10, 64)
	if err != nil {
		response.Error(c, errcode.ErrInvalidParams)
		return
	}

	file, err := c.FormFile("cover")
	if err != nil {
		response.Error(c, errcode.ErrInvalidParams)
		return
	}

	url, appErr := h.uploadSvc.SaveFile(file)
	if appErr != nil {
		response.Error(c, appErr)
		return
	}

	userID := middleware.GetUserID(c)
	article, appErr := h.articleSvc.UpdateCover(c.Request.Context(), uint(articleID), userID, url)
	if appErr != nil {
		response.Error(c, appErr)
		return
	}
	response.Success(c, article)
}

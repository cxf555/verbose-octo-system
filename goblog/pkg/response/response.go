package response

import (
	"net/http"

	"github.com/dream/goblog/internal/pkg/errcode"
	"github.com/gin-gonic/gin"
)

type Response struct {
	Code    int         `json:"code"`
	Message string      `json:"message"`
	Data    interface{} `json:"data"`
}

type PaginatedData struct {
	Items      interface{} `json:"items"`
	Pagination Pagination  `json:"pagination"`
}

type Pagination struct {
	Page       int   `json:"page"`
	PerPage    int   `json:"per_page"`
	Total      int64 `json:"total"`
	TotalPages int64 `json:"total_pages"`
}

func Success(c *gin.Context, data interface{}) {
	c.JSON(http.StatusOK, Response{
		Code:    0,
		Message: "ok",
		Data:    data,
	})
}

func Created(c *gin.Context, data interface{}) {
	c.JSON(http.StatusCreated, Response{
		Code:    0,
		Message: "created",
		Data:    data,
	})
}

func NoContent(c *gin.Context) {
	c.JSON(http.StatusNoContent, nil)
}

func Error(c *gin.Context, appErr *errcode.AppError) {
	c.AbortWithStatusJSON(appErr.HttpCode, Response{
		Code:    appErr.Code,
		Message: appErr.Message,
		Data:    nil,
	})
}

func ErrorWithData(c *gin.Context, appErr *errcode.AppError, data interface{}) {
	c.AbortWithStatusJSON(appErr.HttpCode, Response{
		Code:    appErr.Code,
		Message: appErr.Message,
		Data:    data,
	})
}

func Paginated(c *gin.Context, items interface{}, pagination Pagination) {
	c.JSON(http.StatusOK, Response{
		Code:    0,
		Message: "ok",
		Data: PaginatedData{
			Items:      items,
			Pagination: pagination,
		},
	})
}

package pagination

import (
	"math"

	"github.com/dream/goblog/pkg/response"
)

func New(page, perPage int, total int64) response.Pagination {
	totalPages := int64(math.Ceil(float64(total) / float64(perPage)))
	return response.Pagination{
		Page:       page,
		PerPage:    perPage,
		Total:      total,
		TotalPages: totalPages,
	}
}

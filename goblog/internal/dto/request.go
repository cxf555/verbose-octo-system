package dto

type RegisterRequest struct {
	Username string `json:"username" binding:"required,min=2,max=64"`
	Email    string `json:"email"    binding:"required,email,max=128"`
	Password string `json:"password" binding:"required,min=6,max=128"`
}

type LoginRequest struct {
	Email    string `json:"email"    binding:"required,email"`
	Password string `json:"password" binding:"required"`
}

type RefreshRequest struct {
	RefreshToken string `json:"refresh_token" binding:"required"`
}

type LogoutRequest struct {
	RefreshToken string `json:"refresh_token" binding:"required"`
}

type UpdateProfileRequest struct {
	Username *string `json:"username" binding:"omitempty,min=2,max=64"`
	Email    *string `json:"email"    binding:"omitempty,email,max=128"`
	Bio      *string `json:"bio"`
	Avatar   *string `json:"avatar"`
}

type CreateArticleRequest struct {
	Title       string   `json:"title"       binding:"required,min=1,max=255"`
	Content     string   `json:"content"     binding:"required,min=1"`
	Summary     string   `json:"summary"     binding:"max=512"`
	CategoryIDs []uint   `json:"category_ids"`
	TagNames    []string `json:"tag_names"`
	Status      string   `json:"status"      binding:"omitempty,oneof=draft published"`
}

type UpdateArticleRequest struct {
	Title       *string  `json:"title"       binding:"omitempty,min=1,max=255"`
	Content     *string  `json:"content"     binding:"omitempty,min=1"`
	Summary     *string  `json:"summary"     binding:"omitempty,max=512"`
	CategoryIDs *[]uint  `json:"category_ids"`
	TagNames    *[]string `json:"tag_names"`
}

type UpdateArticleStatusRequest struct {
	Status string `json:"status" binding:"required,oneof=draft published"`
}

type CreateCategoryRequest struct {
	Name        string `json:"name"        binding:"required,min=1,max=64"`
	Description string `json:"description" binding:"max=512"`
}

type UpdateCategoryRequest struct {
	Name        *string `json:"name"        binding:"omitempty,min=1,max=64"`
	Description *string `json:"description" binding:"omitempty,max=512"`
}

type CreateTagRequest struct {
	Name string `json:"name" binding:"required,min=1,max=64"`
}

type UpdateTagRequest struct {
	Name *string `json:"name" binding:"omitempty,min=1,max=64"`
}

type CreateCommentRequest struct {
	Content  string `json:"content"  binding:"required,min=1"`
	ParentID *uint  `json:"parent_id"`
}

type UpdateCommentRequest struct {
	Content string `json:"content" binding:"required,min=1"`
}

type PaginationQuery struct {
	Page    int    `form:"page"     binding:"omitempty,min=1"`
	PerPage int    `form:"per_page" binding:"omitempty,min=1,max=50"`
	Search  string `form:"search"`
	Sort    string `form:"sort"     binding:"omitempty,oneof=latest popular"`
}

func (q *PaginationQuery) Defaults() {
	if q.Page < 1 {
		q.Page = 1
	}
	if q.PerPage < 1 {
		q.PerPage = 10
	}
	if q.Sort == "" {
		q.Sort = "latest"
	}
}

func (q *PaginationQuery) Offset() int {
	return (q.Page - 1) * q.PerPage
}

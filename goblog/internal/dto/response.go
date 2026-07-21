package dto

import "time"

type UserResponse struct {
	ID        uint      `json:"id"`
	Username  string    `json:"username"`
	Email     string    `json:"email"`
	Avatar    string    `json:"avatar"`
	Bio       string    `json:"bio"`
	Role      string    `json:"role"`
	CreatedAt time.Time `json:"created_at"`
}

type AuthResponse struct {
	User         UserResponse `json:"user"`
	AccessToken  string       `json:"access_token"`
	RefreshToken string       `json:"refresh_token"`
}

type TokenResponse struct {
	AccessToken  string `json:"access_token"`
	RefreshToken string `json:"refresh_token"`
}

type ArticleResponse struct {
	ID          uint              `json:"id"`
	AuthorID    uint              `json:"author_id"`
	Title       string            `json:"title"`
	Slug        string            `json:"slug"`
	Content     string            `json:"content"`
	Summary     string            `json:"summary"`
	CoverImage  string            `json:"cover_image"`
	Status      string            `json:"status"`
	ViewCount   uint64            `json:"view_count"`
	CreatedAt   time.Time         `json:"created_at"`
	UpdatedAt   time.Time         `json:"updated_at"`
	PublishedAt *time.Time        `json:"published_at"`
	Author      *UserResponse     `json:"author,omitempty"`
	Categories  []CategoryResponse `json:"categories,omitempty"`
	Tags        []TagResponse      `json:"tags,omitempty"`
}

type ArticleListResponse struct {
	ID          uint              `json:"id"`
	Title       string            `json:"title"`
	Slug        string            `json:"slug"`
	Summary     string            `json:"summary"`
	CoverImage  string            `json:"cover_image"`
	Status      string            `json:"status"`
	ViewCount   uint64            `json:"view_count"`
	CreatedAt   time.Time         `json:"created_at"`
	PublishedAt *time.Time        `json:"published_at"`
	Author      *UserResponse     `json:"author,omitempty"`
	Categories  []CategoryResponse `json:"categories,omitempty"`
	Tags        []TagResponse      `json:"tags,omitempty"`
}

type CategoryResponse struct {
	ID          uint   `json:"id"`
	Name        string `json:"name"`
	Slug        string `json:"slug"`
	Description string `json:"description"`
	ArticleCount int64 `json:"article_count,omitempty"`
}

type TagResponse struct {
	ID           uint   `json:"id"`
	Name         string `json:"name"`
	Slug         string `json:"slug"`
	ArticleCount int64  `json:"article_count,omitempty"`
}

type CommentResponse struct {
	ID        uint               `json:"id"`
	ArticleID uint               `json:"article_id"`
	UserID    uint               `json:"user_id"`
	ParentID  *uint              `json:"parent_id"`
	Content   string             `json:"content"`
	CreatedAt time.Time          `json:"created_at"`
	UpdatedAt time.Time          `json:"updated_at"`
	User      *UserResponse      `json:"user,omitempty"`
	Replies   []*CommentResponse `json:"replies,omitempty"`
}

type UploadResponse struct {
	URL string `json:"url"`
}

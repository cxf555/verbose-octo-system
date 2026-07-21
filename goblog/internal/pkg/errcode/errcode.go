package errcode

import "fmt"

type AppError struct {
	Code     int    `json:"code"`
	Message  string `json:"message"`
	HttpCode int    `json:"-"`
	Err      error  `json:"-"`
}

func (e *AppError) Error() string {
	if e.Err != nil {
		return fmt.Sprintf("code=%d, message=%s, err=%v", e.Code, e.Message, e.Err)
	}
	return fmt.Sprintf("code=%d, message=%s", e.Code, e.Message)
}

func New(code int, message string) *AppError {
	return &AppError{
		Code:     code,
		Message:  message,
		HttpCode: code / 100,
	}
}

func Wrap(code int, message string, err error) *AppError {
	return &AppError{
		Code:     code,
		Message:  message,
		HttpCode: code / 100,
		Err:      err,
	}
}

// 400xx — bad request / validation
var (
	ErrInvalidParams  = New(40001, "invalid request parameters")
	ErrSlugExists     = New(40002, "slug already exists")
	ErrInvalidFile    = New(40003, "invalid file type or size")
)

// 401xx — authentication
var (
	ErrInvalidToken   = New(40101, "invalid or expired access token")
	ErrInvalidRefresh = New(40102, "invalid or revoked refresh token")
	ErrWrongPassword  = New(40103, "wrong email or password")
)

// 403xx — forbidden
var (
	ErrForbidden      = New(40301, "you don't have permission for this action")
	ErrAdminRequired  = New(40302, "admin privileges required")
)

// 404xx — not found
var (
	ErrUserNotFound    = New(40401, "user not found")
	ErrArticleNotFound = New(40402, "article not found")
	ErrCategoryNotFound = New(40403, "category not found")
	ErrTagNotFound     = New(40404, "tag not found")
	ErrCommentNotFound = New(40405, "comment not found")
)

// 409xx — conflict
var (
	ErrEmailTaken   = New(40901, "email already registered")
	ErrUsernameTaken = New(40902, "username already taken")
)

// 429xx — rate limit
var (
	ErrRateLimit = New(42901, "too many requests, please try again later")
)

// 500xx — internal
var (
	ErrInternal = New(50001, "internal server error")
)

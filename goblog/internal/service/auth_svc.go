package service

import (
	"context"
	"time"

	"github.com/dream/goblog/internal/config"
	"github.com/dream/goblog/internal/dto"
	"github.com/dream/goblog/internal/model"
	"github.com/dream/goblog/internal/pkg/errcode"
	"github.com/dream/goblog/internal/pkg/hash"
	jwtpkg "github.com/dream/goblog/internal/pkg/jwt"
	"github.com/dream/goblog/internal/repository"
	"github.com/gosimple/slug"
	"gorm.io/gorm"
)

type AuthService struct {
	userRepo *repository.UserRepo
	cfg      config.JWTConfig
}

func NewAuthService(userRepo *repository.UserRepo, cfg config.JWTConfig) *AuthService {
	return &AuthService{userRepo: userRepo, cfg: cfg}
}

func (s *AuthService) Register(ctx context.Context, req dto.RegisterRequest) (*dto.AuthResponse, *errcode.AppError) {
	// check duplicate
	if _, err := s.userRepo.FindByEmail(ctx, req.Email); err == nil {
		return nil, errcode.ErrEmailTaken
	}
	if _, err := s.userRepo.FindByUsername(ctx, req.Username); err == nil {
		return nil, errcode.ErrUsernameTaken
	}

	passwordHash, err := hash.HashPassword(req.Password)
	if err != nil {
		return nil, errcode.Wrap(50001, "failed to hash password", err)
	}

	user := &model.User{
		Username:     req.Username,
		Email:        req.Email,
		PasswordHash: passwordHash,
	}
	if err := s.userRepo.Create(ctx, user); err != nil {
		return nil, errcode.Wrap(50001, "failed to create user", err)
	}

	accessToken, _ := jwtpkg.GenerateAccessToken(user.ID, user.Username, user.Role, s.cfg.Secret, s.cfg.AccessTTL)
	refreshToken, _ := jwtpkg.GenerateRefreshToken()
	_ = s.userRepo.SaveRefreshToken(ctx, user.ID, jwtpkg.HashToken(refreshToken),
		time.Now().Add(time.Duration(s.cfg.RefreshTTL)*time.Second))

	return &dto.AuthResponse{
		User:         toUserResponse(user),
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
	}, nil
}

func (s *AuthService) Login(ctx context.Context, req dto.LoginRequest) (*dto.AuthResponse, *errcode.AppError) {
	user, err := s.userRepo.FindByEmail(ctx, req.Email)
	if err != nil {
		return nil, errcode.ErrWrongPassword
	}
	if !hash.CheckPassword(req.Password, user.PasswordHash) {
		return nil, errcode.ErrWrongPassword
	}

	accessToken, _ := jwtpkg.GenerateAccessToken(user.ID, user.Username, user.Role, s.cfg.Secret, s.cfg.AccessTTL)
	refreshToken, _ := jwtpkg.GenerateRefreshToken()
	_ = s.userRepo.SaveRefreshToken(ctx, user.ID, jwtpkg.HashToken(refreshToken),
		time.Now().Add(time.Duration(s.cfg.RefreshTTL)*time.Second))

	return &dto.AuthResponse{
		User:         toUserResponse(user),
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
	}, nil
}

func (s *AuthService) Refresh(ctx context.Context, req dto.RefreshRequest) (*dto.TokenResponse, *errcode.AppError) {
	hash := jwtpkg.HashToken(req.RefreshToken)
	stored, err := s.userRepo.FindRefreshToken(ctx, hash)
	if err != nil {
		return nil, errcode.ErrInvalidRefresh
	}
	if stored.Revoked || time.Now().After(stored.ExpiresAt) {
		return nil, errcode.ErrInvalidRefresh
	}

	// rotate: revoke old, issue new
	_ = s.userRepo.RevokeRefreshToken(ctx, hash)

	user, err := s.userRepo.FindByID(ctx, stored.UserID)
	if err != nil {
		return nil, errcode.ErrUserNotFound
	}

	accessToken, _ := jwtpkg.GenerateAccessToken(user.ID, user.Username, user.Role, s.cfg.Secret, s.cfg.AccessTTL)
	newRefreshToken, _ := jwtpkg.GenerateRefreshToken()
	_ = s.userRepo.SaveRefreshToken(ctx, user.ID, jwtpkg.HashToken(newRefreshToken),
		time.Now().Add(time.Duration(s.cfg.RefreshTTL)*time.Second))

	return &dto.TokenResponse{
		AccessToken:  accessToken,
		RefreshToken: newRefreshToken,
	}, nil
}

func (s *AuthService) Logout(ctx context.Context, req dto.LogoutRequest) *errcode.AppError {
	hash := jwtpkg.HashToken(req.RefreshToken)
	if err := s.userRepo.RevokeRefreshToken(ctx, hash); err != nil {
		return errcode.Wrap(50001, "failed to revoke token", err)
	}
	return nil
}

func (s *AuthService) GetProfile(ctx context.Context, userID uint) (*dto.UserResponse, *errcode.AppError) {
	user, err := s.userRepo.FindByID(ctx, userID)
	if err != nil {
		return nil, errcode.ErrUserNotFound
	}
	resp := toUserResponse(user)
	return &resp, nil
}

func (s *AuthService) UpdateProfile(ctx context.Context, userID uint, req dto.UpdateProfileRequest) (*dto.UserResponse, *errcode.AppError) {
	user, err := s.userRepo.FindByID(ctx, userID)
	if err != nil {
		return nil, errcode.ErrUserNotFound
	}

	if req.Username != nil {
		// check uniqueness
		existing, _ := s.userRepo.FindByUsername(ctx, *req.Username)
		if existing != nil && existing.ID != userID {
			return nil, errcode.ErrUsernameTaken
		}
		user.Username = *req.Username
	}
	if req.Email != nil {
		existing, _ := s.userRepo.FindByEmail(ctx, *req.Email)
		if existing != nil && existing.ID != userID {
			return nil, errcode.ErrEmailTaken
		}
		user.Email = *req.Email
	}
	if req.Bio != nil {
		user.Bio = *req.Bio
	}
	if req.Avatar != nil {
		user.Avatar = *req.Avatar
	}

	if err := s.userRepo.Update(ctx, user); err != nil {
		return nil, errcode.Wrap(50001, "failed to update profile", err)
	}

	resp := toUserResponse(user)
	return &resp, nil
}

// helpers

func toUserResponse(user *model.User) dto.UserResponse {
	return dto.UserResponse{
		ID:        user.ID,
		Username:  user.Username,
		Email:     user.Email,
		Avatar:    user.Avatar,
		Bio:       user.Bio,
		Role:      user.Role,
		CreatedAt: user.CreatedAt,
	}
}

func MakeSlug(title string) string {
	return slug.Make(title)
}

func IsNotFound(err error) bool {
	return err == gorm.ErrRecordNotFound
}

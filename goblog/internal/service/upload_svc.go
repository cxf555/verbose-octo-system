package service

import (
	"fmt"
	"io"
	"mime/multipart"
	"os"
	"path/filepath"
	"strings"

	"github.com/dream/goblog/internal/config"
	"github.com/dream/goblog/internal/pkg/errcode"
	"github.com/google/uuid"
)

type UploadService struct {
	cfg config.UploadConfig
}

func NewUploadService(cfg config.UploadConfig) *UploadService {
	return &UploadService{cfg: cfg}
}

func (s *UploadService) SaveFile(file *multipart.FileHeader) (string, *errcode.AppError) {
	if file.Size > s.cfg.MaxSize {
		return "", errcode.ErrInvalidFile
	}

	ext := strings.ToLower(filepath.Ext(file.Filename))
	allowed := false
	for _, allowedExt := range s.cfg.AllowedExts {
		if ext == allowedExt {
			allowed = true
			break
		}
	}
	if !allowed {
		return "", errcode.ErrInvalidFile
	}

	src, err := file.Open()
	if err != nil {
		return "", errcode.Wrap(50001, "failed to open uploaded file", err)
	}
	defer src.Close()

	if err := os.MkdirAll(s.cfg.Path, 0755); err != nil {
		return "", errcode.Wrap(50001, "failed to create upload directory", err)
	}

	filename := fmt.Sprintf("%s%s", uuid.New().String(), ext)
	dst, err := os.Create(filepath.Join(s.cfg.Path, filename))
	if err != nil {
		return "", errcode.Wrap(50001, "failed to save file", err)
	}
	defer dst.Close()

	if _, err := io.Copy(dst, src); err != nil {
		return "", errcode.Wrap(50001, "failed to write file", err)
	}

	return fmt.Sprintf("/uploads/%s", filename), nil
}

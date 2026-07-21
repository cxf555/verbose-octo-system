package service

import (
	"context"

	"github.com/dream/goblog/internal/dto"
	"github.com/dream/goblog/internal/model"
	"github.com/dream/goblog/internal/pkg/errcode"
	"github.com/dream/goblog/internal/repository"
	"github.com/gosimple/slug"
)

type TagService struct {
	tagRepo *repository.TagRepo
}

func NewTagService(tagRepo *repository.TagRepo) *TagService {
	return &TagService{tagRepo: tagRepo}
}

func (s *TagService) Create(ctx context.Context, req dto.CreateTagRequest) (*dto.TagResponse, *errcode.AppError) {
	tag := &model.Tag{
		Name: req.Name,
		Slug: slug.Make(req.Name),
	}

	if existing, _ := s.tagRepo.FindBySlug(ctx, tag.Slug); existing != nil {
		return nil, errcode.ErrSlugExists
	}

	if err := s.tagRepo.Create(ctx, tag); err != nil {
		return nil, errcode.Wrap(50001, "failed to create tag", err)
	}
	resp := toTagResponse(tag)
	return &resp, nil
}

func (s *TagService) List(ctx context.Context) ([]dto.TagResponse, *errcode.AppError) {
	tags, err := s.tagRepo.FindAll(ctx)
	if err != nil {
		return nil, errcode.Wrap(50001, "failed to list tags", err)
	}

	result := make([]dto.TagResponse, len(tags))
	for i, t := range tags {
		count, _ := s.tagRepo.ArticleCount(ctx, t.ID)
		result[i] = toTagResponse(&t)
		result[i].ArticleCount = count
	}
	return result, nil
}

func (s *TagService) GetBySlug(ctx context.Context, slug string) (*dto.TagResponse, *errcode.AppError) {
	tag, err := s.tagRepo.FindBySlug(ctx, slug)
	if err != nil {
		return nil, errcode.ErrTagNotFound
	}
	count, _ := s.tagRepo.ArticleCount(ctx, tag.ID)
	resp := toTagResponse(tag)
	resp.ArticleCount = count
	return &resp, nil
}

func (s *TagService) Update(ctx context.Context, id uint, req dto.UpdateTagRequest) (*dto.TagResponse, *errcode.AppError) {
	tag, err := s.tagRepo.FindByID(ctx, id)
	if err != nil {
		return nil, errcode.ErrTagNotFound
	}
	if req.Name != nil {
		tag.Name = *req.Name
		tag.Slug = slug.Make(*req.Name)
	}
	if err := s.tagRepo.Update(ctx, tag); err != nil {
		return nil, errcode.Wrap(50001, "failed to update tag", err)
	}
	resp := toTagResponse(tag)
	return &resp, nil
}

func (s *TagService) Delete(ctx context.Context, id uint) *errcode.AppError {
	if _, err := s.tagRepo.FindByID(ctx, id); err != nil {
		return errcode.ErrTagNotFound
	}
	if err := s.tagRepo.Delete(ctx, id); err != nil {
		return nil
	}
	return nil
}

func toTagResponse(t *model.Tag) dto.TagResponse {
	return dto.TagResponse{
		ID:   t.ID,
		Name: t.Name,
		Slug: t.Slug,
	}
}

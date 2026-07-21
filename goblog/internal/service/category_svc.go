package service

import (
	"context"
	"time"

	"github.com/dream/goblog/internal/cache"
	"github.com/dream/goblog/internal/dto"
	"github.com/dream/goblog/internal/model"
	"github.com/dream/goblog/internal/pkg/errcode"
	"github.com/dream/goblog/internal/repository"
	"github.com/gosimple/slug"
)

type CategoryService struct {
	categoryRepo *repository.CategoryRepo
	cache        *cache.RedisCache
}

func NewCategoryService(categoryRepo *repository.CategoryRepo, c *cache.RedisCache) *CategoryService {
	return &CategoryService{categoryRepo: categoryRepo, cache: c}
}

func (s *CategoryService) Create(ctx context.Context, req dto.CreateCategoryRequest) (*dto.CategoryResponse, *errcode.AppError) {
	category := &model.Category{
		Name:        req.Name,
		Slug:        slug.Make(req.Name),
		Description: req.Description,
	}

	if existing, _ := s.categoryRepo.FindBySlug(ctx, category.Slug); existing != nil {
		return nil, errcode.ErrSlugExists
	}

	if err := s.categoryRepo.Create(ctx, category); err != nil {
		return nil, errcode.Wrap(50001, "failed to create category", err)
	}

	s.cache.Delete(context.Background(), s.cache.CategoriesKey())

	resp := toCategoryResponse(category)
	return &resp, nil
}

func (s *CategoryService) List(ctx context.Context) ([]dto.CategoryResponse, *errcode.AppError) {
	cacheKey := s.cache.CategoriesKey()
	var cached []dto.CategoryResponse
	if s.cache.Get(ctx, cacheKey, &cached) {
		return cached, nil
	}

	categories, err := s.categoryRepo.FindAll(ctx)
	if err != nil {
		return nil, errcode.Wrap(50001, "failed to list categories", err)
	}

	result := make([]dto.CategoryResponse, len(categories))
	for i, c := range categories {
		count, _ := s.categoryRepo.ArticleCount(ctx, c.ID)
		result[i] = toCategoryResponse(&c)
		result[i].ArticleCount = count
	}

	s.cache.Set(ctx, cacheKey, result, 30*time.Minute)
	return result, nil
}

func (s *CategoryService) GetBySlug(ctx context.Context, slug string) (*dto.CategoryResponse, *errcode.AppError) {
	category, err := s.categoryRepo.FindBySlug(ctx, slug)
	if err != nil {
		return nil, errcode.ErrCategoryNotFound
	}
	count, _ := s.categoryRepo.ArticleCount(ctx, category.ID)
	resp := toCategoryResponse(category)
	resp.ArticleCount = count
	return &resp, nil
}

func (s *CategoryService) Update(ctx context.Context, id uint, req dto.UpdateCategoryRequest) (*dto.CategoryResponse, *errcode.AppError) {
	category, err := s.categoryRepo.FindByID(ctx, id)
	if err != nil {
		return nil, errcode.ErrCategoryNotFound
	}
	if req.Name != nil {
		category.Name = *req.Name
		category.Slug = slug.Make(*req.Name)
	}
	if req.Description != nil {
		category.Description = *req.Description
	}
	if err := s.categoryRepo.Update(ctx, category); err != nil {
		return nil, errcode.Wrap(50001, "failed to update category", err)
	}

	s.cache.Delete(context.Background(), s.cache.CategoriesKey())

	resp := toCategoryResponse(category)
	return &resp, nil
}

func (s *CategoryService) Delete(ctx context.Context, id uint) *errcode.AppError {
	if _, err := s.categoryRepo.FindByID(ctx, id); err != nil {
		return errcode.ErrCategoryNotFound
	}
	if err := s.categoryRepo.Delete(ctx, id); err != nil {
		return errcode.Wrap(50001, "failed to delete category", err)
	}

	s.cache.Delete(context.Background(), s.cache.CategoriesKey())

	return nil
}

func toCategoryResponse(c *model.Category) dto.CategoryResponse {
	return dto.CategoryResponse{
		ID:          c.ID,
		Name:        c.Name,
		Slug:        c.Slug,
		Description: c.Description,
	}
}

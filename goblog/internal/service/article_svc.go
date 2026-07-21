package service

import (
	"context"
	"fmt"
	"time"

	"github.com/dream/goblog/internal/cache"
	"github.com/dream/goblog/internal/dto"
	"github.com/dream/goblog/internal/model"
	"github.com/dream/goblog/internal/pkg/errcode"
	"github.com/dream/goblog/internal/repository"
	"github.com/gosimple/slug"
)

type ArticleService struct {
	articleRepo  *repository.ArticleRepo
	categoryRepo *repository.CategoryRepo
	tagRepo      *repository.TagRepo
	cache        *cache.RedisCache
}

func NewArticleService(
	articleRepo *repository.ArticleRepo,
	categoryRepo *repository.CategoryRepo,
	tagRepo *repository.TagRepo,
	c *cache.RedisCache,
) *ArticleService {
	return &ArticleService{
		articleRepo:  articleRepo,
		categoryRepo: categoryRepo,
		tagRepo:      tagRepo,
		cache:        c,
	}
}

func (s *ArticleService) Create(ctx context.Context, authorID uint, req dto.CreateArticleRequest) (*dto.ArticleResponse, *errcode.AppError) {
	articleSlug := slug.Make(req.Title)
	if existing, _ := s.articleRepo.FindBySlug(ctx, articleSlug); existing != nil {
		articleSlug = fmt.Sprintf("%s-%s", articleSlug, slug.Make(time.Now().Format("20060102-150405")))
	}

	article := &model.Article{
		AuthorID:   authorID,
		Title:      req.Title,
		Slug:       articleSlug,
		Content:    req.Content,
		Summary:    req.Summary,
		Status:     "draft",
	}

	if req.Status == "published" {
		article.Status = "published"
		now := time.Now()
		article.PublishedAt = &now
	}

	if err := s.articleRepo.Create(ctx, article); err != nil {
		return nil, errcode.Wrap(50001, "failed to create article", err)
	}

	if len(req.CategoryIDs) > 0 {
		categories, err := s.categoryRepo.FindByIDs(ctx, req.CategoryIDs)
		if err != nil {
			return nil, errcode.Wrap(50001, "failed to find categories", err)
		}
		if err := s.articleRepo.ReplaceCategories(ctx, article.ID, categories); err != nil {
			return nil, errcode.Wrap(50001, "failed to associate categories", err)
		}
	}

	if len(req.TagNames) > 0 {
		tags := make([]model.Tag, 0, len(req.TagNames))
		for _, name := range req.TagNames {
			tag, err := s.tagRepo.FindOrCreate(ctx, name, slug.Make(name))
			if err != nil {
				return nil, errcode.Wrap(50001, "failed to create tag", err)
			}
			tags = append(tags, *tag)
		}
		if err := s.articleRepo.ReplaceTags(ctx, article.ID, tags); err != nil {
			return nil, errcode.Wrap(50001, "failed to associate tags", err)
		}
	}

	s.invalidateCaches()

	created, err := s.articleRepo.FindByID(ctx, article.ID)
	if err != nil {
		return nil, errcode.Wrap(50001, "failed to load article", err)
	}

	resp := toArticleResponse(created)
	return &resp, nil
}

func (s *ArticleService) GetBySlug(ctx context.Context, slug string) (*dto.ArticleResponse, *errcode.AppError) {
	// cache-aside: try cache first
	cacheKey := s.cache.ArticleDetailKey(slug)
	var cached dto.ArticleResponse
	if s.cache.Get(ctx, cacheKey, &cached) {
		return &cached, nil
	}

	article, err := s.articleRepo.FindBySlug(ctx, slug)
	if err != nil {
		if IsNotFound(err) {
			return nil, errcode.ErrArticleNotFound
		}
		return nil, errcode.Wrap(50001, "failed to get article", err)
	}
	resp := toArticleResponse(article)

	s.cache.Set(ctx, cacheKey, resp, 10*time.Minute)
	return &resp, nil
}

func (s *ArticleService) GetByID(ctx context.Context, id uint) (*dto.ArticleResponse, *errcode.AppError) {
	article, err := s.articleRepo.FindByID(ctx, id)
	if err != nil {
		if IsNotFound(err) {
			return nil, errcode.ErrArticleNotFound
		}
		return nil, errcode.Wrap(50001, "failed to get article", err)
	}
	resp := toArticleResponse(article)
	return &resp, nil
}

func (s *ArticleService) List(ctx context.Context, query dto.PaginationQuery, categorySlug, tagSlug string) ([]dto.ArticleListResponse, int64, *errcode.AppError) {
	query.Defaults()

	filter := repository.ArticleFilter{
		Status:       "published",
		Search:       query.Search,
		CategorySlug: categorySlug,
		TagSlug:      tagSlug,
		Sort:         query.Sort,
	}

	articles, total, err := s.articleRepo.List(ctx, query.Offset(), query.PerPage, filter)
	if err != nil {
		return nil, 0, errcode.Wrap(50001, "failed to list articles", err)
	}

	items := make([]dto.ArticleListResponse, len(articles))
	for i, a := range articles {
		items[i] = toArticleListResponse(&a)
	}

	return items, total, nil
}

func (s *ArticleService) Update(ctx context.Context, articleID, userID uint, req dto.UpdateArticleRequest) (*dto.ArticleResponse, *errcode.AppError) {
	article, err := s.articleRepo.FindByID(ctx, articleID)
	if err != nil {
		return nil, errcode.ErrArticleNotFound
	}
	if article.AuthorID != userID {
		return nil, errcode.ErrForbidden
	}

	if req.Title != nil {
		article.Title = *req.Title
		article.Slug = slug.Make(*req.Title)
	}
	if req.Content != nil {
		article.Content = *req.Content
	}
	if req.Summary != nil {
		article.Summary = *req.Summary
	}

	if req.CategoryIDs != nil {
		categories, err := s.categoryRepo.FindByIDs(ctx, *req.CategoryIDs)
		if err != nil {
			return nil, errcode.Wrap(50001, "failed to find categories", err)
		}
		if err := s.articleRepo.ReplaceCategories(ctx, article.ID, categories); err != nil {
			return nil, errcode.Wrap(50001, "failed to associate categories", err)
		}
	}

	if req.TagNames != nil {
		tags := make([]model.Tag, 0, len(*req.TagNames))
		for _, name := range *req.TagNames {
			tag, err := s.tagRepo.FindOrCreate(ctx, name, slug.Make(name))
			if err != nil {
				return nil, errcode.Wrap(50001, "failed to create tag", err)
			}
			tags = append(tags, *tag)
		}
		if err := s.articleRepo.ReplaceTags(ctx, article.ID, tags); err != nil {
			return nil, errcode.Wrap(50001, "failed to associate tags", err)
		}
	}

	if err := s.articleRepo.Update(ctx, article); err != nil {
		return nil, errcode.Wrap(50001, "failed to update article", err)
	}

	s.invalidateArticleCache(article.Slug)
	s.invalidateCaches()

	updated, _ := s.articleRepo.FindByID(ctx, article.ID)
	resp := toArticleResponse(updated)
	return &resp, nil
}

func (s *ArticleService) Delete(ctx context.Context, articleID, userID uint) *errcode.AppError {
	article, err := s.articleRepo.FindByID(ctx, articleID)
	if err != nil {
		return errcode.ErrArticleNotFound
	}
	if article.AuthorID != userID {
		return errcode.ErrForbidden
	}

	s.invalidateArticleCache(article.Slug)
	s.invalidateCaches()

	if err := s.articleRepo.Delete(ctx, articleID); err != nil {
		return errcode.Wrap(50001, "failed to delete article", err)
	}
	return nil
}

func (s *ArticleService) UpdateStatus(ctx context.Context, articleID, userID uint, req dto.UpdateArticleStatusRequest) (*dto.ArticleResponse, *errcode.AppError) {
	article, err := s.articleRepo.FindByID(ctx, articleID)
	if err != nil {
		return nil, errcode.ErrArticleNotFound
	}
	if article.AuthorID != userID {
		return nil, errcode.ErrForbidden
	}

	article.Status = req.Status
	if req.Status == "published" && article.PublishedAt == nil {
		now := time.Now()
		article.PublishedAt = &now
	}

	if err := s.articleRepo.Update(ctx, article); err != nil {
		return nil, errcode.Wrap(50001, "failed to update status", err)
	}

	s.invalidateArticleCache(article.Slug)
	s.invalidateCaches()

	updated, _ := s.articleRepo.FindByID(ctx, article.ID)
	resp := toArticleResponse(updated)
	return &resp, nil
}

func (s *ArticleService) UpdateCover(ctx context.Context, articleID, userID uint, coverURL string) (*dto.ArticleResponse, *errcode.AppError) {
	article, err := s.articleRepo.FindByID(ctx, articleID)
	if err != nil {
		return nil, errcode.ErrArticleNotFound
	}
	if article.AuthorID != userID {
		return nil, errcode.ErrForbidden
	}

	article.CoverImage = coverURL
	if err := s.articleRepo.Update(ctx, article); err != nil {
		return nil, errcode.Wrap(50001, "failed to update cover", err)
	}

	s.invalidateArticleCache(article.Slug)

	updated, _ := s.articleRepo.FindByID(ctx, article.ID)
	resp := toArticleResponse(updated)
	return &resp, nil
}

func (s *ArticleService) HotArticles(ctx context.Context) ([]dto.ArticleListResponse, *errcode.AppError) {
	cacheKey := s.cache.HotArticlesKey()
	var cached []dto.ArticleListResponse
	if s.cache.Get(ctx, cacheKey, &cached) {
		return cached, nil
	}

	articles, err := s.articleRepo.HotArticles(ctx, 10)
	if err != nil {
		return nil, errcode.Wrap(50001, "failed to get hot articles", err)
	}

	items := make([]dto.ArticleListResponse, len(articles))
	for i, a := range articles {
		items[i] = toArticleListResponse(&a)
	}

	s.cache.Set(ctx, cacheKey, items, 5*time.Minute)
	return items, nil
}

func (s *ArticleService) IncrementView(ctx context.Context, articleID uint, clientIP string) {
	if s.cache == nil {
		_ = s.articleRepo.IncrementViewCount(ctx, articleID)
		return
	}

	dedupKey := s.cache.ViewDedupKey(articleID, clientIP)
	if s.cache.SetNXEx(ctx, dedupKey, 30*time.Minute) {
		_ = s.articleRepo.IncrementViewCount(ctx, articleID)
	}
}

func (s *ArticleService) invalidateArticleCache(slug string) {
	s.cache.Delete(context.Background(), s.cache.ArticleDetailKey(slug))
}

func (s *ArticleService) invalidateCaches() {
	s.cache.Delete(context.Background(), s.cache.HotArticlesKey())
}

func toArticleResponse(a *model.Article) dto.ArticleResponse {
	resp := dto.ArticleResponse{
		ID:          a.ID,
		AuthorID:    a.AuthorID,
		Title:       a.Title,
		Slug:        a.Slug,
		Content:     a.Content,
		Summary:     a.Summary,
		CoverImage:  a.CoverImage,
		Status:      a.Status,
		ViewCount:   a.ViewCount,
		CreatedAt:   a.CreatedAt,
		UpdatedAt:   a.UpdatedAt,
		PublishedAt: a.PublishedAt,
	}
	if a.Author.ID != 0 {
		user := toUserResponse(&a.Author)
		resp.Author = &user
	}
	resp.Categories = toCategoryResponses(a.Categories)
	resp.Tags = toTagResponses(a.Tags)
	return resp
}

func toArticleListResponse(a *model.Article) dto.ArticleListResponse {
	resp := dto.ArticleListResponse{
		ID:          a.ID,
		Title:       a.Title,
		Slug:        a.Slug,
		Summary:     a.Summary,
		CoverImage:  a.CoverImage,
		Status:      a.Status,
		ViewCount:   a.ViewCount,
		CreatedAt:   a.CreatedAt,
		PublishedAt: a.PublishedAt,
	}
	if a.Author.ID != 0 {
		user := toUserResponse(&a.Author)
		resp.Author = &user
	}
	resp.Categories = toCategoryResponses(a.Categories)
	resp.Tags = toTagResponses(a.Tags)
	return resp
}

func toCategoryResponses(categories []model.Category) []dto.CategoryResponse {
	if len(categories) == 0 {
		return []dto.CategoryResponse{}
	}
	result := make([]dto.CategoryResponse, len(categories))
	for i, c := range categories {
		result[i] = dto.CategoryResponse{
			ID:   c.ID,
			Name: c.Name,
			Slug: c.Slug,
		}
	}
	return result
}

func toTagResponses(tags []model.Tag) []dto.TagResponse {
	if len(tags) == 0 {
		return []dto.TagResponse{}
	}
	result := make([]dto.TagResponse, len(tags))
	for i, t := range tags {
		result[i] = dto.TagResponse{
			ID:   t.ID,
			Name: t.Name,
			Slug: t.Slug,
		}
	}
	return result
}

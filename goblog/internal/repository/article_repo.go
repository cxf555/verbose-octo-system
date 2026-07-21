package repository

import (
	"context"

	"github.com/dream/goblog/internal/model"
	"gorm.io/gorm"
)

type ArticleRepo struct {
	db *gorm.DB
}

func NewArticleRepo(db *gorm.DB) *ArticleRepo {
	return &ArticleRepo{db: db}
}

func (r *ArticleRepo) Create(ctx context.Context, article *model.Article) error {
	return r.db.WithContext(ctx).Create(article).Error
}

func (r *ArticleRepo) FindByID(ctx context.Context, id uint) (*model.Article, error) {
	var article model.Article
	err := r.db.WithContext(ctx).
		Preload("Author").
		Preload("Categories").
		Preload("Tags").
		First(&article, id).Error
	if err != nil {
		return nil, err
	}
	return &article, nil
}

func (r *ArticleRepo) FindBySlug(ctx context.Context, slug string) (*model.Article, error) {
	var article model.Article
	err := r.db.WithContext(ctx).
		Preload("Author").
		Preload("Categories").
		Preload("Tags").
		Where("slug = ?", slug).
		First(&article).Error
	if err != nil {
		return nil, err
	}
	return &article, nil
}

func (r *ArticleRepo) Update(ctx context.Context, article *model.Article) error {
	return r.db.WithContext(ctx).Save(article).Error
}

func (r *ArticleRepo) Delete(ctx context.Context, id uint) error {
	return r.db.WithContext(ctx).Delete(&model.Article{}, id).Error
}

func (r *ArticleRepo) List(ctx context.Context, offset, limit int, filter ArticleFilter) ([]model.Article, int64, error) {
	query := r.db.WithContext(ctx).Model(&model.Article{})

	if filter.Status != "" {
		query = query.Where("articles.status = ?", filter.Status)
	}
	if filter.AuthorID != 0 {
		query = query.Where("articles.author_id = ?", filter.AuthorID)
	}
	if filter.Search != "" {
		search := "%" + filter.Search + "%"
		query = query.Where("articles.title LIKE ? OR articles.summary LIKE ?", search, search)
	}
	if filter.CategorySlug != "" {
		query = query.Joins("JOIN article_categories ac ON ac.article_id = articles.id").
			Joins("JOIN categories c ON c.id = ac.category_id").
			Where("c.slug = ?", filter.CategorySlug)
	}
	if filter.TagSlug != "" {
		query = query.Joins("JOIN article_tags at ON at.article_id = articles.id").
			Joins("JOIN tags t ON t.id = at.tag_id").
			Where("t.slug = ?", filter.TagSlug)
	}

	var total int64
	if err := query.Count(&total).Error; err != nil {
		return nil, 0, err
	}

	var articles []model.Article
	order := "articles.published_at DESC"
	if filter.Sort == "popular" {
		order = "articles.view_count DESC"
	}

	err := query.
		Preload("Author").
		Preload("Categories").
		Preload("Tags").
		Limit(limit).Offset(offset).
		Order(order).
		Find(&articles).Error

	return articles, total, err
}

func (r *ArticleRepo) IncrementViewCount(ctx context.Context, id uint) error {
	return r.db.WithContext(ctx).Model(&model.Article{}).
		Where("id = ?", id).
		UpdateColumn("view_count", gorm.Expr("view_count + 1")).Error
}

func (r *ArticleRepo) HotArticles(ctx context.Context, limit int) ([]model.Article, error) {
	var articles []model.Article
	err := r.db.WithContext(ctx).
		Preload("Author").
		Preload("Categories").
		Preload("Tags").
		Where("status = ?", "published").
		Order("view_count DESC").
		Limit(limit).
		Find(&articles).Error
	return articles, err
}

func (r *ArticleRepo) ReplaceCategories(ctx context.Context, articleID uint, categories []model.Category) error {
	return r.db.WithContext(ctx).Model(&model.Article{ID: articleID}).
		Association("Categories").Replace(categories)
}

func (r *ArticleRepo) ReplaceTags(ctx context.Context, articleID uint, tags []model.Tag) error {
	return r.db.WithContext(ctx).Model(&model.Article{ID: articleID}).
		Association("Tags").Replace(tags)
}

type ArticleFilter struct {
	Status       string
	AuthorID     uint
	Search       string
	CategorySlug string
	TagSlug      string
	Sort         string
}

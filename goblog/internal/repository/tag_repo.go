package repository

import (
	"context"

	"github.com/dream/goblog/internal/model"
	"gorm.io/gorm"
)

type TagRepo struct {
	db *gorm.DB
}

func NewTagRepo(db *gorm.DB) *TagRepo {
	return &TagRepo{db: db}
}

func (r *TagRepo) Create(ctx context.Context, tag *model.Tag) error {
	return r.db.WithContext(ctx).Create(tag).Error
}

func (r *TagRepo) FindByID(ctx context.Context, id uint) (*model.Tag, error) {
	var tag model.Tag
	err := r.db.WithContext(ctx).First(&tag, id).Error
	if err != nil {
		return nil, err
	}
	return &tag, nil
}

func (r *TagRepo) FindBySlug(ctx context.Context, slug string) (*model.Tag, error) {
	var tag model.Tag
	err := r.db.WithContext(ctx).Where("slug = ?", slug).First(&tag).Error
	if err != nil {
		return nil, err
	}
	return &tag, nil
}

func (r *TagRepo) FindByName(ctx context.Context, name string) (*model.Tag, error) {
	var tag model.Tag
	err := r.db.WithContext(ctx).Where("name = ?", name).First(&tag).Error
	if err != nil {
		return nil, err
	}
	return &tag, nil
}

func (r *TagRepo) FindAll(ctx context.Context) ([]model.Tag, error) {
	var tags []model.Tag
	err := r.db.WithContext(ctx).Order("name ASC").Find(&tags).Error
	return tags, err
}

func (r *TagRepo) Update(ctx context.Context, tag *model.Tag) error {
	return r.db.WithContext(ctx).Save(tag).Error
}

func (r *TagRepo) Delete(ctx context.Context, id uint) error {
	return r.db.WithContext(ctx).Delete(&model.Tag{}, id).Error
}

func (r *TagRepo) FindOrCreate(ctx context.Context, name, slug string) (*model.Tag, error) {
	tag, err := r.FindByName(ctx, name)
	if err == nil {
		return tag, nil
	}
	if err != gorm.ErrRecordNotFound {
		return nil, err
	}
	tag = &model.Tag{Name: name, Slug: slug}
	if err := r.Create(ctx, tag); err != nil {
		return nil, err
	}
	return tag, nil
}

func (r *TagRepo) ArticleCount(ctx context.Context, tagID uint) (int64, error) {
	var count int64
	err := r.db.WithContext(ctx).Table("article_tags").
		Where("tag_id = ?", tagID).
		Count(&count).Error
	return count, err
}

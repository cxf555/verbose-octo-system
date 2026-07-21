package model

import "time"

type Article struct {
	ID          uint       `gorm:"primaryKey" json:"id"`
	AuthorID    uint       `gorm:"not null;index" json:"author_id"`
	Title       string     `gorm:"size:255;not null" json:"title"`
	Slug        string     `gorm:"size:300;uniqueIndex;not null" json:"slug"`
	Content     string     `gorm:"type:longtext;not null" json:"content"`
	Summary     string     `gorm:"size:512;default:''" json:"summary"`
	CoverImage  string     `gorm:"size:512;default:''" json:"cover_image"`
	Status      string     `gorm:"size:16;default:draft;index" json:"status"`
	ViewCount   uint64     `gorm:"default:0;index" json:"view_count"`
	CreatedAt   time.Time  `json:"created_at"`
	UpdatedAt   time.Time  `json:"updated_at"`
	PublishedAt *time.Time `json:"published_at"`

	Author     User       `gorm:"foreignKey:AuthorID" json:"author,omitempty"`
	Categories []Category `gorm:"many2many:article_categories;" json:"categories,omitempty"`
	Tags       []Tag      `gorm:"many2many:article_tags;" json:"tags,omitempty"`
	Comments   []Comment  `gorm:"foreignKey:ArticleID" json:"comments,omitempty"`
}

func (Article) TableName() string { return "articles" }

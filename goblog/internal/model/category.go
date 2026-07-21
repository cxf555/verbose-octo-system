package model

import "time"

type Category struct {
	ID          uint      `gorm:"primaryKey" json:"id"`
	Name        string    `gorm:"size:64;not null" json:"name"`
	Slug        string    `gorm:"size:80;uniqueIndex;not null" json:"slug"`
	Description string    `gorm:"type:text" json:"description"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`

	Articles []Article `gorm:"many2many:article_categories;" json:"articles,omitempty"`
}

func (Category) TableName() string { return "categories" }

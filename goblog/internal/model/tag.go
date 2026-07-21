package model

import "time"

type Tag struct {
	ID        uint      `gorm:"primaryKey" json:"id"`
	Name      string    `gorm:"size:64;not null" json:"name"`
	Slug      string    `gorm:"size:80;uniqueIndex;not null" json:"slug"`
	CreatedAt time.Time `json:"created_at"`

	Articles []Article `gorm:"many2many:article_tags;" json:"articles,omitempty"`
}

func (Tag) TableName() string { return "tags" }

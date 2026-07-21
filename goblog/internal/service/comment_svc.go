package service

import (
	"context"

	"github.com/dream/goblog/internal/dto"
	"github.com/dream/goblog/internal/model"
	"github.com/dream/goblog/internal/pkg/errcode"
	"github.com/dream/goblog/internal/repository"
)

type CommentService struct {
	commentRepo *repository.CommentRepo
	articleRepo *repository.ArticleRepo
}

func NewCommentService(commentRepo *repository.CommentRepo, articleRepo *repository.ArticleRepo) *CommentService {
	return &CommentService{commentRepo: commentRepo, articleRepo: articleRepo}
}

func (s *CommentService) Create(ctx context.Context, articleSlug string, userID uint, req dto.CreateCommentRequest) (*dto.CommentResponse, *errcode.AppError) {
	article, err := s.articleRepo.FindBySlug(ctx, articleSlug)
	if err != nil {
		return nil, errcode.ErrArticleNotFound
	}

	comment := &model.Comment{
		ArticleID: article.ID,
		UserID:    userID,
		Content:   req.Content,
		ParentID:  req.ParentID,
	}

	// validate parent exists if provided
	if req.ParentID != nil {
		parent, err := s.commentRepo.FindByID(ctx, *req.ParentID)
		if err != nil || parent.ArticleID != article.ID {
			return nil, errcode.ErrCommentNotFound
		}
	}

	if err := s.commentRepo.Create(ctx, comment); err != nil {
		return nil, errcode.Wrap(50001, "failed to create comment", err)
	}

	created, _ := s.commentRepo.FindByID(ctx, comment.ID)
	resp := toCommentResponse(created)
	return &resp, nil
}

func (s *CommentService) ListByArticle(ctx context.Context, articleSlug string) ([]*dto.CommentResponse, *errcode.AppError) {
	article, err := s.articleRepo.FindBySlug(ctx, articleSlug)
	if err != nil {
		return nil, errcode.ErrArticleNotFound
	}

	comments, err := s.commentRepo.FindByArticleID(ctx, article.ID)
	if err != nil {
		return nil, errcode.Wrap(50001, "failed to get comments", err)
	}

	return buildCommentTree(comments), nil
}

func (s *CommentService) Update(ctx context.Context, commentID, userID uint, req dto.UpdateCommentRequest) (*dto.CommentResponse, *errcode.AppError) {
	comment, err := s.commentRepo.FindByID(ctx, commentID)
	if err != nil {
		return nil, errcode.ErrCommentNotFound
	}
	if comment.UserID != userID {
		return nil, errcode.ErrForbidden
	}

	comment.Content = req.Content
	if err := s.commentRepo.Update(ctx, comment); err != nil {
		return nil, errcode.Wrap(50001, "failed to update comment", err)
	}

	resp := toCommentResponse(comment)
	return &resp, nil
}

func (s *CommentService) Delete(ctx context.Context, commentID, userID uint, role string) *errcode.AppError {
	comment, err := s.commentRepo.FindByID(ctx, commentID)
	if err != nil {
		return errcode.ErrCommentNotFound
	}
	if comment.UserID != userID && role != "admin" {
		return errcode.ErrForbidden
	}

	if err := s.commentRepo.Delete(ctx, commentID); err != nil {
		return errcode.Wrap(50001, "failed to delete comment", err)
	}
	return nil
}

// buildCommentTree converts a flat list of comments into a nested tree structure.
func buildCommentTree(comments []model.Comment) []*dto.CommentResponse {
	nodeMap := make(map[uint]*dto.CommentResponse, len(comments))
	var roots []*dto.CommentResponse

	// first pass: create all nodes
	for i := range comments {
		node := toCommentResponse(&comments[i])
		node.Replies = []*dto.CommentResponse{}
		nodeMap[comments[i].ID] = &node
	}

	// second pass: build tree
	for _, c := range comments {
		node := nodeMap[c.ID]
		if c.ParentID != nil {
			parent, ok := nodeMap[*c.ParentID]
			if ok {
				parent.Replies = append(parent.Replies, node)
			}
		} else {
			roots = append(roots, node)
		}
	}

	return roots
}

func toCommentResponse(c *model.Comment) dto.CommentResponse {
	resp := dto.CommentResponse{
		ID:        c.ID,
		ArticleID: c.ArticleID,
		UserID:    c.UserID,
		ParentID:  c.ParentID,
		Content:   c.Content,
		CreatedAt: c.CreatedAt,
		UpdatedAt: c.UpdatedAt,
	}
	if c.User.ID != 0 {
		user := toUserResponse(&c.User)
		resp.User = &user
	}
	return resp
}

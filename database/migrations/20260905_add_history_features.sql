ALTER TABLE chat_sessions ADD COLUMN is_favorite TINYINT DEFAULT 0 COMMENT '是否收藏';
ALTER TABLE chat_sessions ADD COLUMN is_pinned TINYINT DEFAULT 0 COMMENT '是否置顶';

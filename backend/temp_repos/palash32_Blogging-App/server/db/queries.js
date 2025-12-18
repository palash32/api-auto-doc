const db = require('./init');

const createUser = db.prepare(`
  INSERT INTO users (email, password_hash) 
  VALUES (?, ?)
`);

const getUserByEmail = db.prepare(`
  SELECT * FROM users WHERE email = ?
`);

const getUserById = db.prepare(`
  SELECT id, email, created_at FROM users WHERE id = ?
`);

const getAllBlogs = db.prepare(`
  SELECT 
    b.id,
    b.user_id,
    b.title,
    b.content,
    b.created_at,
    u.email as authorEmail
  FROM blogs b
  INNER JOIN users u ON b.user_id = u.id
  ORDER BY b.created_at DESC
`);

const createBlog = db.prepare(`
  INSERT INTO blogs (user_id, title, content)
  VALUES (?, ?, ?)
`);

const getBlogById = db.prepare(`
  SELECT 
    b.id,
    b.user_id,
    b.title,
    b.content,
    b.created_at,
    u.email as authorEmail
  FROM blogs b
  INNER JOIN users u ON b.user_id = u.id
  WHERE b.id = ?
`);

const getUserBlogs = db.prepare(`
  SELECT * FROM blogs WHERE user_id = ? ORDER BY created_at DESC
`);

const updateBlog = db.prepare(`
  UPDATE blogs 
  SET title = ?, content = ?
  WHERE id = ? AND user_id = ?
`);

const deleteBlog = db.prepare(`
  DELETE FROM blogs 
  WHERE id = ? AND user_id = ?
`);

module.exports = {
  createUser,
  getUserByEmail,
  getUserById,
  getAllBlogs,
  createBlog,
  getBlogById,
  getUserBlogs,
  updateBlog,
  deleteBlog
};

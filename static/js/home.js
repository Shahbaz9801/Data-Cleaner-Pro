// Home page JavaScript for enhanced comments functionality
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const commentForm = document.getElementById('commentForm');
    const parentCommentIdInput = document.getElementById('parentCommentId');
    const commentNameInput = document.getElementById('commentName');
    const commentTextInput = document.getElementById('commentText');
    const commentLabel = document.getElementById('commentLabel');
    const submitCommentBtn = document.getElementById('submitCommentBtn');
    const submitBtnText = document.getElementById('submitBtnText');
    const cancelReplyBtn = document.getElementById('cancelReply');
    const commentsContainer = document.getElementById('commentsContainer');
    const refreshCommentsBtn = document.getElementById('refreshComments');
    const loadMoreBtn = document.getElementById('loadMoreComments');
    const commentsCount = document.getElementById('commentsCount');
    const noCommentsTemplate = document.getElementById('noCommentsTemplate');
    
    // State variables
    let allComments = [];
    let displayedComments = 5;
    let replyingTo = null;
    
    // Initialize
    loadComments();
    
    // Event Listeners
    commentForm.addEventListener('submit', handleCommentSubmit);
    refreshCommentsBtn.addEventListener('click', loadComments);
    loadMoreBtn.addEventListener('click', loadMoreComments);
    cancelReplyBtn.addEventListener('click', cancelReply);
    
    // Functions
    
    // Load comments from server
    async function loadComments() {
        try {
            showLoadingState();
            
            const response = await fetch('/api/comments');
            const result = await response.json();
            
            if (result.success) {
                allComments = result.comments;
                updateCommentsDisplay();
                updateCommentsCount();
            } else {
                showError('Failed to load comments: ' + result.error);
            }
        } catch (error) {
            console.error('Error loading comments:', error);
            showError('Network error: ' + error.message);
        }
    }
    
    // Handle comment submission
    async function handleCommentSubmit(e) {
        e.preventDefault();
        
        const name = commentNameInput.value.trim();
        const comment = commentTextInput.value.trim();
        const parentId = parentCommentIdInput.value || null;
        
        if (!name || !comment) {
            showAlert('Please fill in both name and comment fields', 'error');
            return;
        }
        
        // Disable submit button
        const originalText = submitBtnText.textContent;
        submitBtnText.textContent = 'Submitting...';
        submitCommentBtn.disabled = true;
        
        try {
            const response = await fetch('/api/comments/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: name,
                    comment: comment,
                    parent_id: parentId
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Reload comments
                await loadComments();
                
                // Clear form
                commentForm.reset();
                cancelReply();
                
                // Show success message
                showAlert(
                    parentId ? 'Reply submitted successfully!' : 'Comment submitted successfully!',
                    'success'
                );
                
                // Scroll to the new comment
                setTimeout(() => {
                    const newCommentElement = document.querySelector(`[data-comment-id="${result.comment.id}"]`);
                    if (newCommentElement) {
                        newCommentElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        newCommentElement.classList.add('fade-in');
                    }
                }, 500);
                
            } else {
                showError(result.error || 'Failed to submit comment');
            }
        } catch (error) {
            console.error('Error submitting comment:', error);
            showError('Network error: ' + error.message);
        } finally {
            // Re-enable submit button
            submitBtnText.textContent = originalText;
            submitCommentBtn.disabled = false;
        }
    }
    
    // Update comments display
    function updateCommentsDisplay() {
        if (allComments.length === 0) {
            commentsContainer.innerHTML = noCommentsTemplate.innerHTML;
            loadMoreBtn.style.display = 'none';
            return;
        }
        
        // Show top-level comments up to displayedComments limit
        const visibleComments = allComments.slice(0, displayedComments);
        
        let html = '';
        visibleComments.forEach(comment => {
            html += renderComment(comment, 0);
        });
        
        commentsContainer.innerHTML = html;
        
        // Add event listeners to newly rendered elements
        addCommentEventListeners();
        
        // Show/hide load more button
        if (allComments.length > displayedComments) {
            loadMoreBtn.style.display = 'block';
        } else {
            loadMoreBtn.style.display = 'none';
        }
    }
    
    // Render a single comment (recursive for replies)
    function renderComment(comment, level) {
        const isDeleted = comment.deleted || false;
        const hasReplies = comment.replies && comment.replies.length > 0;
        const replyClass = level > 0 ? `reply reply-level-${Math.min(level, 3)}` : '';
        
        let html = `
            <div class="comment-item ${replyClass} fade-in" data-comment-id="${comment.id}">
                <div class="comment-header">
                    <div class="comment-author-info">
                        <div class="comment-author">
                            ${escapeHtml(comment.name)}
                            ${isDeleted ? '<span class="badge bg-secondary comment-badge">Deleted</span>' : ''}
                        </div>
                        <div class="comment-meta">
                            <span class="comment-time">
                                <i class="far fa-clock me-1"></i>
                                ${comment.date} at ${comment.time}
                            </span>
                        </div>
                    </div>
                    <div class="comment-actions">
                        ${!isDeleted ? `
                        <button class="comment-action-btn reply-btn" data-comment-id="${comment.id}" data-author="${escapeHtml(comment.name)}">
                            <i class="fas fa-reply me-1"></i>Reply
                        </button>
                        <button class="comment-action-btn delete-btn" data-comment-id="${comment.id}">
                            <i class="fas fa-trash-alt me-1"></i>Delete
                        </button>
                        ` : ''}
                    </div>
                </div>
                
                <div class="comment-body">
                    <p>${escapeHtml(comment.comment).replace(/\n/g, '<br>')}</p>
                </div>
        `;
        
        // Replies section
        if (hasReplies) {
            html += `
                <div class="replies-section">
                    <div class="replies-header" data-comment-id="${comment.id}">
                        <i class="fas fa-chevron-down"></i>
                        <span>Replies</span>
                        <span class="replies-count">${comment.replies.length}</span>
                    </div>
                    <div class="replies-container" id="replies-${comment.id}" style="max-height: 1000px;">
            `;
            
            // Render replies
            comment.replies.forEach(reply => {
                html += renderComment(reply, level + 1);
            });
            
            html += `
                    </div>
                </div>
            `;
        }
        
        // Reply form (hidden by default)
        html += `
            <div class="reply-form" id="reply-form-${comment.id}">
                <div class="reply-form-header">
                    <h6>Reply to ${escapeHtml(comment.name)}</h6>
                    <button type="button" class="btn-close" data-comment-id="${comment.id}"></button>
                </div>
                <div class="reply-to-info">
                    Replying to: <strong>${escapeHtml(comment.name)}</strong>
                </div>
                <form class="reply-form-inner">
                    <input type="hidden" name="parent_id" value="${comment.id}">
                    <div class="mb-3">
                        <input type="text" class="form-control form-control-sm" 
                               placeholder="Your Name" required>
                    </div>
                    <div class="mb-2">
                        <textarea class="form-control form-control-sm" 
                                  placeholder="Your reply..." rows="2" required></textarea>
                    </div>
                    <div class="reply-form-actions">
                        <button type="button" class="btn btn-sm btn-secondary cancel-reply-btn" 
                                data-comment-id="${comment.id}">Cancel</button>
                        <button type="submit" class="btn btn-sm btn-primary">Submit Reply</button>
                    </div>
                </form>
            </div>
        `;
        
        html += '</div>';
        return html;
    }
    
    // Add event listeners to comment elements
    function addCommentEventListeners() {
        // Reply buttons
        document.querySelectorAll('.reply-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const commentId = this.dataset.commentId;
                const authorName = this.dataset.author;
                startReply(commentId, authorName);
            });
        });
        
        // Delete buttons
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const commentId = this.dataset.commentId;
                deleteComment(commentId);
            });
        });
        
        // Replies toggle
        document.querySelectorAll('.replies-header').forEach(header => {
            header.addEventListener('click', function() {
                const commentId = this.dataset.commentId;
                const container = document.getElementById(`replies-${commentId}`);
                const icon = this.querySelector('i');
                
                if (container.classList.contains('collapsed')) {
                    container.classList.remove('collapsed');
                    icon.style.transform = 'rotate(0deg)';
                } else {
                    container.classList.add('collapsed');
                    icon.style.transform = 'rotate(-90deg)';
                }
            });
        });
        
        // Reply form close buttons
        document.querySelectorAll('.reply-form .btn-close').forEach(btn => {
            btn.addEventListener('click', function() {
                const commentId = this.dataset.commentId;
                hideReplyForm(commentId);
            });
        });
        
        // Cancel reply buttons
        document.querySelectorAll('.cancel-reply-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const commentId = this.dataset.commentId;
                hideReplyForm(commentId);
            });
        });
        
        // Reply form submissions
        document.querySelectorAll('.reply-form-inner').forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                const parentId = this.querySelector('input[name="parent_id"]').value;
                const nameInput = this.querySelector('input[type="text"]');
                const commentInput = this.querySelector('textarea');
                
                const name = nameInput.value.trim();
                const comment = commentInput.value.trim();
                
                if (!name || !comment) {
                    showAlert('Please fill in both name and reply fields', 'error');
                    return;
                }
                
                submitReply(parentId, name, comment, this);
            });
        });
    }
    
    // Start replying to a comment
    function startReply(commentId, authorName) {
        // Hide any other open reply forms
        document.querySelectorAll('.reply-form.active').forEach(form => {
            form.classList.remove('active');
        });
        
        // Show reply form for this comment
        const replyForm = document.getElementById(`reply-form-${commentId}`);
        replyForm.classList.add('active');
        
        // Scroll to reply form
        replyForm.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Focus on textarea
        const textarea = replyForm.querySelector('textarea');
        setTimeout(() => textarea.focus(), 300);
    }
    
    // Hide reply form
    function hideReplyForm(commentId) {
        const replyForm = document.getElementById(`reply-form-${commentId}`);
        if (replyForm) {
            replyForm.classList.remove('active');
        }
    }
    
    // Submit a reply
    async function submitReply(parentId, name, comment, formElement) {
        // Disable form
        const submitBtn = formElement.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Submitting...';
        submitBtn.disabled = true;
        
        try {
            const response = await fetch('/api/comments/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: name,
                    comment: comment,
                    parent_id: parentId
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Reload comments
                await loadComments();
                
                // Show success message
                showAlert('Reply submitted successfully!', 'success');
                
            } else {
                showError(result.error || 'Failed to submit reply');
            }
        } catch (error) {
            console.error('Error submitting reply:', error);
            showError('Network error: ' + error.message);
        } finally {
            // Re-enable button
            submitBtn.textContent = originalText;
            submitBtn.disabled = false;
        }
    }
    
    // Delete a comment
    async function deleteComment(commentId) {
        if (!confirm('Are you sure you want to delete this comment?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/comments/delete/${commentId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Reload comments
                await loadComments();
                showAlert('Comment deleted successfully!', 'success');
            } else {
                showError(result.error || 'Failed to delete comment');
            }
        } catch (error) {
            console.error('Error deleting comment:', error);
            showError('Network error: ' + error.message);
        }
    }
    
    // Load more comments
    function loadMoreComments() {
        displayedComments += 5;
        updateCommentsDisplay();
    }
    
    // Cancel reply mode
    function cancelReply() {
        parentCommentIdInput.value = '';
        commentLabel.textContent = 'Your Comment/Suggestion *';
        submitBtnText.textContent = 'Submit Comment';
        cancelReplyBtn.style.display = 'none';
        replyingTo = null;
    }
    
    // Update comments count
    function updateCommentsCount() {
        const totalComments = countTotalComments(allComments);
        commentsCount.textContent = `${totalComments} comment${totalComments !== 1 ? 's' : ''}`;
    }
    
    // Count total comments including replies
    function countTotalComments(comments) {
        let count = 0;
        comments.forEach(comment => {
            count++; // Count this comment
            if (comment.replies && comment.replies.length > 0) {
                count += countTotalComments(comment.replies); // Count replies recursively
            }
        });
        return count;
    }
    
    // Show loading state
    function showLoadingState() {
        commentsContainer.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="text-muted mt-2">Loading comments...</p>
            </div>
        `;
    }
    
    // Utility functions
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    function showAlert(message, type = 'success') {
        // Remove existing alerts
        const existingAlerts = document.querySelectorAll('.alert-dismissible.position-fixed');
        existingAlerts.forEach(alert => alert.remove());
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'success' ? 'success' : 'danger'} 
                            alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        
        const icon = type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle';
        
        alertDiv.innerHTML = `
            <i class="fas ${icon} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
    
    function showError(message) {
        showAlert(message, 'error');
    }
});
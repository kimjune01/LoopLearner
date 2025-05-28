import React, { useState } from 'react';
import { EmailDraft, DraftReason } from '../types/email';

interface DraftViewerProps {
  drafts: EmailDraft[];
  onDraftAction: (draftId: string, action: 'accept' | 'reject' | 'edit' | 'ignore', reason?: string, editedContent?: string) => void;
  onReasonRating: (draftId: string, reasonText: string, liked: boolean) => void;
}

interface DraftCardProps {
  draft: EmailDraft;
  onAction: (action: 'accept' | 'reject' | 'edit' | 'ignore', reason?: string, editedContent?: string) => void;
  onReasonRating: (reasonText: string, liked: boolean) => void;
}

const DraftCard: React.FC<DraftCardProps> = ({ draft, onAction, onReasonRating }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(draft.content);
  const [actionReason, setActionReason] = useState('');

  const handleEdit = () => {
    setIsEditing(true);
  };

  const handleSaveEdit = () => {
    onAction('edit', actionReason, editedContent);
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditedContent(draft.content);
    setIsEditing(false);
  };

  return (
    <div className="draft-card">
      <div className="draft-content">
        {isEditing ? (
          <textarea
            value={editedContent}
            onChange={(e) => setEditedContent(e.target.value)}
            className="draft-editor"
          />
        ) : (
          <p>{draft.content}</p>
        )}
      </div>
      
      <div className="draft-reasons">
        <h4>Reasoning:</h4>
        {draft.reasons.map((reason, index) => (
          <div key={index} className="reason-item">
            <span>{reason.text} (confidence: {reason.confidence})</span>
            <div className="reason-rating">
              <button onClick={() => onReasonRating(reason.text, true)}>👍</button>
              <button onClick={() => onReasonRating(reason.text, false)}>👎</button>
            </div>
          </div>
        ))}
      </div>

      <div className="draft-actions">
        {isEditing ? (
          <>
            <button onClick={handleSaveEdit}>Save Edit</button>
            <button onClick={handleCancelEdit}>Cancel</button>
          </>
        ) : (
          <>
            <button onClick={() => onAction('accept')}>Accept</button>
            <button onClick={() => onAction('reject', actionReason)}>Reject</button>
            <button onClick={handleEdit}>Edit</button>
            <button onClick={() => onAction('ignore')}>Ignore</button>
          </>
        )}
      </div>

      <div className="action-reason">
        <input
          type="text"
          placeholder="Optional reason for action..."
          value={actionReason}
          onChange={(e) => setActionReason(e.target.value)}
        />
      </div>
    </div>
  );
};

export const DraftViewer: React.FC<DraftViewerProps> = ({ 
  drafts, 
  onDraftAction, 
  onReasonRating 
}) => {
  return (
    <div className="draft-viewer">
      <h3>Draft Responses ({drafts.length})</h3>
      {drafts.map(draft => (
        <DraftCard
          key={draft.id}
          draft={draft}
          onAction={(action, reason, editedContent) => onDraftAction(draft.id, action, reason, editedContent)}
          onReasonRating={(reasonText, liked) => onReasonRating(draft.id, reasonText, liked)}
        />
      ))}
    </div>
  );
};
import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { AuthService } from 'app/services/auth.service';

export interface CommentNode {
  id_commentaire: number;
  contenu: string;
  date_commentaire: string | null;
  sentiment: string | null;
  auteur: string | null;
  role_auteur: 'association' | 'donator' | 'admin' | null;
  replies: CommentNode[];
}

@Component({
  selector: 'app-comment-thread',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule, MatFormFieldModule, MatInputModule],
  templateUrl: './comment-thread.component.html',
  styleUrls: ['./comment-thread.component.scss']
})
export class CommentThreadComponent {
  @Input() comments: CommentNode[] = [];
  @Input() canReply = false;              // défini depuis le parent (association => true)
  @Output() replied = new EventEmitter<void>(); // pour que le parent puisse rafraîchir

  // états locaux par commentaire (ouvert/fermé + texte)
  replyOpen: Record<number, boolean> = {};
  replyText: Record<number, string> = {};

  constructor(private auth: AuthService) {}

  toggleReplyBox(commentId: number) {
    this.replyOpen[commentId] = !this.replyOpen[commentId];
  }

  sendReply(parentId: number) {
    const texte = (this.replyText[parentId] || '').trim();
    if (!texte) return;

    this.auth.replyComment(parentId, texte).subscribe({
      next: _ => {
        this.replyText[parentId] = '';
        this.replyOpen[parentId] = false;
        // Laisse le parent décider de recharger la publication
        this.replied.emit();
      },
      error: err => {
        console.error('❌ Erreur reply:', err);
        alert(err?.error?.error || 'Erreur lors de la réponse');
      }
    });
  }
}

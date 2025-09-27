import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatFormField, MatFormFieldModule, MatLabel } from '@angular/material/form-field';
import { MatIcon, MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { RouterModule } from '@angular/router';
import { AuthService } from 'app/services/auth.service';
import { CommentThreadComponent } from '../comment-thread/comment-thread.component'; 
import { CommentNode } from '../comment-thread/comment-thread.component'; 
@Component({
  selector: 'app-body-front',
  standalone: true,
  imports: [CommonModule,HttpClientModule,FormsModule,MatIconModule,MatFormFieldModule,MatInputModule, RouterModule, CommentThreadComponent],
  templateUrl: './body-front.component.html',
  styleUrl: './body-front.component.scss'
})
export class BodyFrontComponent implements OnInit {
  dons: any[] = [];
  searchTerm: string = '';
  allDons: any[] = [];
  publications: any[] = [];
  selectedPublication: any = null;
  newComment: string = '';
  donParticipants: { [key: number]: number } = {};
   role: string | null = null;
   userId: number | null = null;
editingCommentId: number | null = null;
editBuffer: string = '';
replyBuffers: Record<number, string> = {};
replyingOpen: Record<number, boolean> = {};

likeBusy = false;
likedSelected: boolean | null = null; 
  constructor(private authService: AuthService) {}

  
  scrollToCatalog() {
    document.getElementById('catalog')?.scrollIntoView({ behavior: 'smooth' });
  }
  
  scrollToPublications() {
    document.getElementById('publication')?.scrollIntoView({ behavior: 'smooth' });
  }
  
@ViewChild('carousel', { static: false }) carousel!: ElementRef;

scrollLeft() {
  this.carousel.nativeElement.scrollBy({ left: -350, behavior: 'smooth' });
}

scrollRight() {
  this.carousel.nativeElement.scrollBy({ left: 350, behavior: 'smooth' });
}

currentSlide = 0;

get totalSlides(): number {
  return Math.ceil(this.publications.length / 4);
}

prevSlide() {
  if (this.currentSlide > 0) {
    this.currentSlide--;
  }
}

nextSlide() {
  if (this.currentSlide < this.totalSlides - 1) {
    this.currentSlide++;
  }
}


  animateCard(event: Event) {
    const card = event.currentTarget as HTMLElement;
    card.style.transform = 'translateY(-5px)';
    setTimeout(() => {
      card.style.transform = 'translateY(0)';
    }, 300);
  }

 ngOnInit(): void {
    this.role = this.authService.getRole();      
    this.refreshDonsAndParticipants();
    this.userId = this.authService.getUserId();
    this.authService.getPublications().subscribe({
      next: (data) => { this.publications = data; },
      error: (err) => console.error('Erreur chargement publications :', err)
      
    });
  }

  refreshDonsAndParticipants() {
    this.authService.getAllDonsPublic().subscribe({
      next: (data) => {
        this.allDons = data;
        this.dons = data;
      },
      error: (err) => {
        console.error('Erreur lors du chargement des dons publics :', err);
      }
    });
    this.authService.getDonParticipants().subscribe({
      next: (res) => {
        res.forEach(p => {
          this.donParticipants[p.id_don] = p.nb_participants;
        });
      },
      error: (err) => {
        console.error('Erreur lors du chargement des participants :', err);
      }
    });
  

    
  }

  onSearch() {
    const search = this.searchTerm.toLowerCase().trim();
    this.dons = this.allDons.filter(don =>
      don.titre.toLowerCase().includes(search) ||
      don.description?.toLowerCase().includes(search)
    );
  }
  
  

  
selectPublication(pub: any) {
  this.selectedPublication = pub;
  this.likedSelected = null;   
  this.likeBusy = false;

  this.authService.isPublicationLiked(pub.id_publication).subscribe({
    next: (res) => this.likedSelected = !!res?.liked,
    error: () => this.likedSelected = false
  });
}


reloadSelectedPublication() {
  if (!this.selectedPublication) return;
  const id = this.selectedPublication.id_publication;
  this.authService.getPublicationById(id).subscribe({
    next: (pub) => {
      this.selectedPublication = pub;
     
      this.authService.isPublicationLiked(id).subscribe({
        next: (res) => this.likedSelected = !!res?.liked,
        error: () => this.likedSelected = false
      });
    },
    error: (err) => console.error('Erreur reload publication :', err)
  });
}

   openReply(commentId: number) {
    this.replyingOpen[commentId] = true;
    if (this.replyBuffers[commentId] == null) this.replyBuffers[commentId] = '';
  }

  cancelReply(commentId: number) {
    this.replyingOpen[commentId] = false;
    this.replyBuffers[commentId] = '';
  }
   sendReply(parent: any) {
    const cid = parent.id_commentaire;
    const contenu = (this.replyBuffers[cid] || '').trim();
    if (!contenu) return;

    this.authService.replyComment(cid, contenu).subscribe({
      next: () => {
        this.replyBuffers[cid] = '';
        this.replyingOpen[cid] = false;
        this.reloadSelectedPublication();
      },
      error: (err) => {
        console.error('Reply error:', err);
        alert(err?.error?.error || 'Erreur lors de la réponse');
      }
    });
  }
 onReplied() {
    this.reloadSelectedPublication();
  }
   addComment() {
    const contenu = this.newComment.trim();
    const publicationId = this.selectedPublication?.id_publication;

    if (contenu && publicationId) {
      this.authService.addComment(publicationId, contenu).subscribe({
        next: _ => {
          this.newComment = '';
          this.reloadSelectedPublication();  // on rafraîchit pour voir le nouveau commentaire
        },
        error: (err) => {
          console.error('❌ Erreur lors de l’ajout du commentaire :', err);
          alert(err.error?.error || 'Erreur inconnue');
        }
      });
    }
  }
  get selectedComments() {
  return this.selectedPublication?.commentaires ?? [];
}




startEditComment(c: any) {
  if (this.role !== 'donator' || !c.is_owner) return;
  this.editingCommentId = c.id_commentaire;
  this.editBuffer = c.contenu;
}

cancelEditComment() {
  this.editingCommentId = null;
  this.editBuffer = '';
}

saveEditComment(c: any) {
  const contenu = (this.editBuffer || '').trim();
  if (!contenu) return;

  this.authService.updateComment(c.id_commentaire, contenu).subscribe({
    next: (res: any) => {
      c.contenu = res?.comment?.contenu ?? contenu;
      c.sentiment = res?.comment?.sentiment ?? c.sentiment;
      this.editingCommentId = null;
      this.editBuffer = '';
    },
    error: (err) => {
      console.error('Update comment error:', err);
      alert(err.error?.error || 'Erreur lors de la modification');
    }
  });
}

deleteComment(c: any, parentArray?: any[]) {
  if (!confirm('Supprimer ce commentaire ?')) return;
  this.authService.deleteComment(c.id_commentaire).subscribe({
    next: () => {
      // Enlève le commentaire supprimé du tableau courant
      const removeFrom = parentArray ?? this.selectedPublication.commentaires;
      const idx = removeFrom.findIndex((x: any) => x.id_commentaire === c.id_commentaire);
      if (idx >= 0) removeFrom.splice(idx, 1);
      // Décrémente l’affichage local (optionnel)
      if (this.selectedPublication && typeof this.selectedPublication.nb_commentaires === 'number') {
        this.selectedPublication.nb_commentaires = Math.max(0, this.selectedPublication.nb_commentaires - 1);
      }
    },
    error: (err) => {
      console.error('Delete comment error:', err);
      alert(err.error?.error || 'Erreur lors de la suppression');
    }
  });
}

toggleLikeSelectedPublication() {
  if (!this.selectedPublication || this.likeBusy) return;
  if (this.likedSelected === (null as any)) return; 

  this.likeBusy = true;
  const id = this.selectedPublication.id_publication;

  const doUnlike = () => this.authService.unlikePublication(id).subscribe({
    next: (res: any) => {
      this.selectedPublication.nb_likes = Number(res?.nb_likes) || 0;
      this.likedSelected = false;
      this.likeBusy = false;
    },
    error: (err) => { alert(err?.error?.error || 'Erreur unlike'); this.likeBusy = false; }
  });

  if (this.likedSelected) {
    // UNLIKE
    return doUnlike();
  }

  // LIKE
  this.authService.likePublication(id).subscribe({
    next: (res: any) => {
      this.selectedPublication.nb_likes = Number(res?.nb_likes) || ((this.selectedPublication.nb_likes || 0) + 1);
      this.likedSelected = true;
      this.likeBusy = false;
    },
    error: (err) => {
      if (err?.status === 409) {
      
        this.likedSelected = true;
        this.likeBusy = false;
       
      } else {
        alert(err?.error?.error || 'Erreur like');
        this.likeBusy = false;
      }
    }
  });
}


  
  

}
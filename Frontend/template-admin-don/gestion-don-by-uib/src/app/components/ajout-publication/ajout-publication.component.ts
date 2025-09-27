import { CommonModule } from '@angular/common';
import { Component, Inject, OnDestroy } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { AuthService } from 'app/services/auth.service';
import { MatChipsModule } from '@angular/material/chips';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { TextFieldModule } from '@angular/cdk/text-field';
import { MatSelectModule } from '@angular/material/select';
import { HttpClient, HttpHeaders } from '@angular/common/http';
type Visibility = 'public' | 'private';

@Component({
  selector: 'app-ajout-publication',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatSlideToggleModule,
    MatProgressBarModule,
    MatTooltipModule,
    TextFieldModule,
     MatSelectModule
  ],
  templateUrl: './ajout-publication.component.html',
  styleUrl: './ajout-publication.component.scss'
})
export class AjoutPublicationComponent {
  titre = '';
  contenu = '';
  errorMessage = '';
  isSubmitting = false;

  // Admin bits
  isAdmin = false;
  id_association: number | null = null;
  associations: Array<{ id_association: number; nom_complet: string }> = [];

  // Counters
  maxTitle = 120;
  maxContent = 2000;

  constructor(
    private http: HttpClient,                    
    private authService: AuthService,
    public dialogRef: MatDialogRef<AjoutPublicationComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any
  ) {}

  ngOnInit(): void {
    // Determine role from JWT (implement getRoleFromToken() in AuthService if not already)
    const role = (this.authService.getRoleFromToken() || '').toLowerCase();
    this.isAdmin = role === 'admin';

    if (this.isAdmin) {
      const headers = new HttpHeaders({
        Authorization: `Bearer ${this.authService.getToken()}`
      });
      // Load associations list for the selector (endpoint admin-only)
      this.http.get<any[]>('http://127.0.0.1:5000/associations', { headers }).subscribe({
        next: rows => {
          this.associations = (rows || []).map(r => ({
            id_association: r.id_association,
            nom_complet: r.nom_complet
          }));
        },
        error: err => console.error('Erreur chargement associations', err)
      });
    }
  }

  submitPublication(): void {
    if (!this.titre.trim() || !this.contenu.trim()) {
      this.errorMessage = 'Le titre et le contenu sont requis.';
      return;
    }
    if (this.titre.length > this.maxTitle || this.contenu.length > this.maxContent) {
      this.errorMessage = 'Vous avez dépassé la longueur autorisée.';
      return;
    }
    if (this.isAdmin && !this.id_association) {
      this.errorMessage = 'Veuillez choisir une association.';
      return;
    }

    this.errorMessage = '';
    this.isSubmitting = true;

    
    const payload: any = {
      titre: this.titre.trim(),
      contenu: this.contenu.trim()
    };
    if (this.isAdmin) {
      payload.id_association = this.id_association;
    }

    this.authService.addPublication(payload).subscribe({
      next: () => this.dialogRef.close(true),
      error: (err) => {
        this.isSubmitting = false;
        this.errorMessage = err?.error?.error || err?.error?.message || 'Erreur lors de l’ajout.';
      }
    });
  }

  closeDialog(): void {
    this.dialogRef.close(false);
  }
}
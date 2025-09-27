import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { AuthService } from 'app/services/auth.service';
import { CommonModule } from '@angular/common';
import { MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
@Component({
  selector: 'app-ajout-don',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule
  ],
  templateUrl: './ajout-don.component.html',
  styleUrl: './ajout-don.component.scss'
})
export class AjoutDonComponent  implements OnInit {
  donForm: FormGroup;
  selectedFile: File | null = null;

  // ↓ pour savoir si on doit exiger id_association
  isAdmin = false;
  // ↓ liste des asso à choisir (admin)
  associations: Array<{ id_association: number; nom_complet: string }> = [];

  constructor(
    private fb: FormBuilder,
    private http: HttpClient,
    private authService: AuthService,
    private dialogRef: MatDialogRef<AjoutDonComponent>
  ) {
    this.donForm = this.fb.group({
      titre: [''],
      description: [''],
      objectif: [''],
      date_fin_collecte: [''],
      // ↓ champ ajouté (requis seulement si admin)
      id_association: [null]
    });
  }

  ngOnInit(): void {
  this.isAdmin = this.authService.getRoleFromToken() === 'admin';

  if (this.isAdmin) {
    this.donForm.get('id_association')?.addValidators([Validators.required]);
    this.donForm.get('id_association')?.updateValueAndValidity();

    const headers = new HttpHeaders({ Authorization: `Bearer ${this.authService.getToken()}` });

    // endpoint qui liste les associations, réservé admin
    this.http.get<any[]>('http://127.0.0.1:5000/associations', { headers }).subscribe({
      next: rows => this.associations = (rows || []).map(r => ({
        id_association: r.id_association,
        nom_complet: r.nom_complet
      })),
      error: e => console.error('Erreur chargement associations', e)
    });
  }
}



  onFileSelected(event: any) {
    this.selectedFile = event.target.files?.[0] || null;
  }

  ajouterDon() {
    // si admin, s’assurer que id_association est rempli
    if (this.isAdmin && !this.donForm.value.id_association) {
      console.error('id_association est requis pour l’admin');
      this.donForm.get('id_association')?.markAsTouched();
      return;
    }

    const formData = new FormData();
    // append champs du formulaire
    Object.entries(this.donForm.value).forEach(([key, val]) => {
      if (val !== null && val !== undefined && val !== '') {
        formData.append(key, String(val));
      }
    });

    // append fichier si présent
    if (this.selectedFile) {
      formData.append('photo_file', this.selectedFile);
    }

    const headers = new HttpHeaders({
      Authorization: `Bearer ${this.authService.getToken()}`
      // surtout ne pas fixer Content-Type pour FormData
    });

    this.http.post('http://127.0.0.1:5000/create-don', formData, { headers }).subscribe({
      next: (response) => {
        console.log('✅ Don ajouté avec succès:', response);
        this.dialogRef.close(true);
      },
      error: (err) => {
        console.error('❌ Erreur lors de l’ajout du don:', err);
      }
    });
  }

  onCancel(): void {
    this.dialogRef.close(false);
  }
}
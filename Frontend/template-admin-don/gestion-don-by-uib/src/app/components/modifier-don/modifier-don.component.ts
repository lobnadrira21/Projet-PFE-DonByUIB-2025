import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatNativeDateModule } from '@angular/material/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from 'app/services/auth.service';
import { MatDatepickerModule } from '@angular/material/datepicker';

@Component({
  selector: 'app-modifier-don',
  standalone: true,
  imports: [ CommonModule,
    ReactiveFormsModule,
    FormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatIconModule,
    MatDatepickerModule,
    MatNativeDateModule,
  
        MatCardModule],
  templateUrl: './modifier-don.component.html',
  styleUrl: './modifier-don.component.scss'
})
export class ModifierDonComponent implements OnInit {
  donForm!: FormGroup;
  id_don!: number;
  imagePreview: string | null = null;
  currentPhoto: string | null = null;
   private readonly API_BASE = 'http://127.0.0.1:5000';
  constructor(
    private route: ActivatedRoute,
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.id_don = +this.route.snapshot.paramMap.get('id')!;
    this.initForm();
    this.loadDon();
  }

  initForm() {
    this.donForm = this.fb.group({
      titre: ['', Validators.required],
      description: [''],
      objectif: ['', Validators.required],
      date_fin_collecte: ['', Validators.required],
      photo_file: [null]
    });
  }

   loadDon() {
    this.authService.getDonById(this.id_don).subscribe({
      next: (don) => {
        this.currentPhoto = don?.photo_don ? `${this.API_BASE}${don.photo_don}` : null;

        this.donForm.patchValue({
          titre: don?.titre ?? '',
          description: don?.description ?? '',
          objectif: don?.objectif ?? null,
          // Convert ISO/string -> Date for the datepicker
          date_fin_collecte: don?.date_fin_collecte ? new Date(don.date_fin_collecte) : null
        });
      },
      error: (err) => console.error('Erreur chargement don:', err)
    });
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    this.donForm.patchValue({ photo_file: file });

    const reader = new FileReader();
    reader.onload = () => (this.imagePreview = reader.result as string);
    reader.readAsDataURL(file);
  }

  onSubmit() {
    if (this.donForm.invalid) return;

    const v = this.donForm.value;
    const fd = new FormData();

    fd.append('titre', v.titre);
    fd.append('description', v.description || '');
    fd.append('objectif', String(v.objectif));

    // Date: always send YYYY-MM-DD to your Flask backend
    if (v.date_fin_collecte instanceof Date) {
      const y = v.date_fin_collecte.getFullYear();
      const m = String(v.date_fin_collecte.getMonth() + 1).padStart(2, '0');
      const d = String(v.date_fin_collecte.getDate()).padStart(2, '0');
      fd.append('date_fin_collecte', `${y}-${m}-${d}`);
    } else if (v.date_fin_collecte) {
      fd.append('date_fin_collecte', v.date_fin_collecte); // fallback
    }

    if (v.photo_file) fd.append('photo_file', v.photo_file);

    this.authService.updateDon(this.id_don, fd).subscribe({
      next: () => {
        alert('✅ Don modifié avec succès');
        this.router.navigate(['/dashboard-association/table-list']);
      },
      error: (err) => {
        console.error('Erreur lors de la modification', err);
        alert('❌ Erreur lors de la modification');
      }
    });
  }
cancel() {
    this.router.navigate(['/dashboard-association/table-list']);
  }
}

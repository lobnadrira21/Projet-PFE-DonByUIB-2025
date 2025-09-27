import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule, MatLabel } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from 'app/services/auth.service';

@Component({
  selector: 'app-modifier-publication-admin',
  standalone: true,
  imports: [CommonModule,ReactiveFormsModule,FormsModule,MatLabel,   MatFormFieldModule,
    MatInputModule,     // ✅ nécessaire pour matInput
    MatButtonModule ],
  templateUrl: './modifier-publication-admin.component.html',
  styleUrl: './modifier-publication-admin.component.scss'
})
export class ModifierPublicationAdminComponent implements OnInit {
  id!: number;
  publication = { titre: '', contenu: '' };

  constructor(
    private route: ActivatedRoute,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    this.authService.getPublicationById(this.id).subscribe({
      next: (res) => {
        // Vérifie que l’API renvoie bien ces champs
        this.publication.titre = res?.titre ?? '';
        this.publication.contenu = res?.contenu ?? '';
      },
      error: (err) => console.error(err)
    });
  }

  onUpdate(): void {
    this.authService.updatePublication(this.id, this.publication).subscribe({
      next: () => {
        alert('✅ Publication mise à jour avec succès');
        this.router.navigate(['/dashboard/gestion-publications']);
      },
      error: (err) => console.error(err)
    });
  }
}